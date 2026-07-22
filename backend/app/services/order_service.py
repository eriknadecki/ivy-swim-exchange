import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Account, AccountOwnerType, LedgerEntryType, Market, MarketStatus, Order, Position, Trade
from app.services import ledger_service
from app.services.errors import InsufficientFundsError, MarketNotTradableError, NotFoundError
from app.services.ledger_service import LedgerEntryInput
from app.services.position_math import PositionState, apply_fill
from app.ws import events as ws_events
from engine.engine import MatchingEngine
from engine.normalization import normalize_new_order
from engine.types import (
    PRICE_MAX,
    PRICE_MIN,
    Action,
    Fill,
    NewOrder,
    OrderStatus,
    OrderType,
    Side,
    TimeInForce,
)


def _unit_collateral(action: Action, price_cents: int) -> int:
    """Worst-case cost per contract for holding this side of a YES trade."""
    return price_cents if action == Action.buy else (100 - price_cents)


def _normalized_terms(order: Order) -> tuple[Action, int]:
    """An order's YES-terms action and its own reference price (limit price,
    or the book boundary for a market order) — the two things collateral
    sizing and position accounting need, independent of engine execution."""
    temp = NewOrder(
        market_id=str(order.market_id),
        owner_id=order.user_id,
        side=order.side,
        action=order.action,
        order_type=order.order_type,
        quantity=order.quantity,
        price_cents=order.limit_price_cents,
        time_in_force=order.time_in_force,
        order_id=order.id,
    )
    normalized = normalize_new_order(temp)
    price = normalized.price_cents
    if price is None:
        price = PRICE_MAX if normalized.action == Action.buy else PRICE_MIN
    return normalized.action, price


def _get_user_account(db: Session, user_id: uuid.UUID) -> Account:
    return db.execute(
        select(Account)
        .where(Account.owner_type == AccountOwnerType.user, Account.owner_id == user_id)
        .with_for_update()
    ).scalar_one()


def _get_user_account_readonly(db: Session, user_id: uuid.UUID) -> Account:
    return db.execute(
        select(Account).where(Account.owner_type == AccountOwnerType.user, Account.owner_id == user_id)
    ).scalar_one()


def _publish_order_and_balance(db: Session, order: Order) -> None:
    account = _get_user_account_readonly(db, order.user_id)
    ws_events.publish_order_update(order.user_id, order.id, order.status.value, order.filled_quantity)
    ws_events.publish_balance_update(
        order.user_id, account.cash_balance_cents, account.cash_balance_cents - account.held_collateral_cents
    )


def _get_or_create_position(db: Session, user_id: uuid.UUID, market_id: uuid.UUID) -> Position:
    position = db.execute(
        select(Position)
        .where(Position.user_id == user_id, Position.market_id == market_id)
        .with_for_update()
    ).scalar_one_or_none()
    if position is None:
        position = Position(user_id=user_id, market_id=market_id)
        db.add(position)
        db.flush()
    return position


def submit_order(
    db: Session,
    engine: MatchingEngine,
    *,
    user_id: uuid.UUID,
    market_id: uuid.UUID,
    side: Side,
    action: Action,
    order_type: OrderType,
    quantity: int,
    price_cents: int | None,
    time_in_force: TimeInForce,
) -> Order:
    market = db.get(Market, market_id)
    if market is None:
        raise NotFoundError("unknown market")
    if market.status != MarketStatus.open:
        raise MarketNotTradableError(f"market is {market.status}, not open for trading")

    order_row = Order(
        id=uuid.uuid4(),
        market_id=market_id,
        user_id=user_id,
        side=side,
        action=action,
        order_type=order_type,
        time_in_force=time_in_force,
        limit_price_cents=price_cents,
        quantity=quantity,
        filled_quantity=0,
        status=OrderStatus.open,
        collateral_cents=0,
    )
    normalized_action, own_price = _normalized_terms(order_row)
    required = _unit_collateral(normalized_action, own_price) * quantity

    account = _get_user_account(db, user_id)
    available = account.cash_balance_cents - account.held_collateral_cents
    if available < required:
        raise InsufficientFundsError(f"order requires {required} cents, only {available} available")

    account.held_collateral_cents += required
    order_row.collateral_cents = required
    db.add(order_row)
    db.flush()

    engine_order = NewOrder(
        market_id=str(market_id),
        owner_id=user_id,
        side=side,
        action=action,
        order_type=order_type,
        quantity=quantity,
        price_cents=price_cents,
        time_in_force=time_in_force,
        order_id=order_row.id,
    )
    result = engine.submit_order(engine_order)

    maker_orders = [_settle_fill(db, market, order_row, fill) for fill in result.fills]

    order_row.filled_quantity = sum(fill.quantity for fill in result.fills)
    order_row.status = result.status
    unit_collateral = _unit_collateral(normalized_action, own_price)
    new_hold = unit_collateral * result.remaining_quantity
    account.held_collateral_cents -= order_row.collateral_cents - new_hold
    order_row.collateral_cents = new_hold

    db.commit()
    db.refresh(order_row)

    # Broadcast only after a successful commit — never announce state that
    # could still have been rolled back.
    _publish_order_and_balance(db, order_row)
    seen_makers: set[uuid.UUID] = set()
    for maker_order, fill in zip(maker_orders, result.fills):
        ws_events.publish_trade(market.id, fill.price_cents, fill.quantity)
        if maker_order.id not in seen_makers:
            db.refresh(maker_order)
            _publish_order_and_balance(db, maker_order)
            seen_makers.add(maker_order.id)
    if result.fills or result.status in (OrderStatus.open, OrderStatus.partially_filled):
        ws_events.publish_book_update(market.id, engine.get_book_snapshot(str(market.id)))

    return order_row


def _settle_fill(db: Session, market: Market, taker_order: Order, fill: Fill) -> Order:
    maker_order = db.get(Order, fill.maker_order_id, with_for_update=True)
    if maker_order is None:
        raise NotFoundError(f"maker order {fill.maker_order_id} not found")

    escrow = ledger_service.get_market_escrow_account(db, market.id)
    taker_action, _ = _normalized_terms(taker_order)

    for order in (taker_order, maker_order):
        normalized_action, own_price = _normalized_terms(order)
        account = _get_user_account(db, order.user_id)

        # Release this order's own pre-trade hold for the filled quantity,
        # then move the *actual* collateral for that quantity — priced at
        # the real fill price, not this order's own limit — into escrow.
        # A buy and its matching sell always sum to exactly 100/contract,
        # which is exactly what escrow needs to pay out 100/contract to
        # whichever side wins at resolution.
        released = _unit_collateral(normalized_action, own_price) * fill.quantity
        actual_required = _unit_collateral(normalized_action, fill.price_cents) * fill.quantity
        account.held_collateral_cents -= released
        # Keep the order row's own collateral_cents in sync with the account.
        # For the taker this gets overwritten with an authoritative absolute
        # value at the end of submit_order regardless; for the maker (a
        # resting order this function never gets called for again from that
        # caller) this is the only place its held amount is ever reduced.
        order.collateral_cents -= released

        ledger_service.post_entry_group(
            db,
            [
                LedgerEntryInput(
                    account_id=account.id,
                    entry_type=LedgerEntryType.trade_settlement,
                    amount_cents=-actual_required,
                    reference_type="trade",
                    reference_id=fill.trade_id,
                ),
                LedgerEntryInput(
                    account_id=escrow.id,
                    entry_type=LedgerEntryType.trade_settlement,
                    amount_cents=actual_required,
                    reference_type="trade",
                    reference_id=fill.trade_id,
                ),
            ],
        )

        position = _get_or_create_position(db, order.user_id, market.id)
        delta = fill.quantity if normalized_action == Action.buy else -fill.quantity
        new_state = apply_fill(
            PositionState(position.net_yes_quantity, position.avg_cost_cents, position.realized_pnl_cents),
            delta,
            fill.price_cents,
        )
        position.net_yes_quantity, position.avg_cost_cents, position.realized_pnl_cents = new_state

    buy_order_id = taker_order.id if taker_action == Action.buy else maker_order.id
    sell_order_id = maker_order.id if taker_action == Action.buy else taker_order.id
    db.add(
        Trade(
            id=fill.trade_id,
            market_id=market.id,
            buy_order_id=buy_order_id,
            sell_order_id=sell_order_id,
            price_cents=fill.price_cents,
            quantity=fill.quantity,
        )
    )
    maker_order.filled_quantity += fill.quantity
    if maker_order.filled_quantity >= maker_order.quantity:
        maker_order.status = OrderStatus.filled
        maker_order.collateral_cents = 0
    else:
        maker_order.status = OrderStatus.partially_filled

    return maker_order


def cancel_order(db: Session, engine: MatchingEngine, *, user_id: uuid.UUID, order_id: uuid.UUID) -> Order:
    order_row = db.get(Order, order_id, with_for_update=True)
    if order_row is None or order_row.user_id != user_id:
        raise NotFoundError("order not found")

    if order_row.status in (OrderStatus.filled, OrderStatus.cancelled):
        return order_row

    result = engine.cancel_order(str(order_row.market_id), order_id)
    if result.status == OrderStatus.cancelled:
        account = _get_user_account(db, user_id)
        account.held_collateral_cents -= order_row.collateral_cents
        order_row.collateral_cents = 0
        order_row.status = OrderStatus.cancelled

    db.commit()
    db.refresh(order_row)

    if result.status == OrderStatus.cancelled:
        _publish_order_and_balance(db, order_row)
        ws_events.publish_book_update(order_row.market_id, engine.get_book_snapshot(str(order_row.market_id)))

    return order_row
