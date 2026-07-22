import uuid

from engine.engine import MatchingEngine
from engine.types import Action, NewOrder, OrderStatus, OrderType, Side, TimeInForce


def _order(market_id, owner_id, side, action, price, qty=5, order_id=None):
    return NewOrder(
        market_id=market_id,
        owner_id=owner_id,
        side=side,
        action=action,
        order_type=OrderType.limit,
        quantity=qty,
        price_cents=price,
        time_in_force=TimeInForce.gtc,
        order_id=order_id or uuid.uuid4(),
    )


def test_markets_are_fully_isolated():
    engine = MatchingEngine()
    engine.submit_order(_order("market-a", "bob", Side.yes, Action.sell, price=60, qty=10))

    # A crossing order on a *different* market must not see market-a's book.
    result = engine.submit_order(_order("market-b", "alice", Side.yes, Action.buy, price=60, qty=10))

    assert result.fills == []
    assert result.status == OrderStatus.open
    assert engine.get_book_snapshot("market-a").asks[0].total_quantity == 10
    assert engine.get_book_snapshot("market-b").asks == []


def test_no_side_order_matches_against_yes_side_order_via_normalization():
    engine = MatchingEngine()
    # Alice offers to sell YES @ 70 (a resting ask at 70).
    engine.submit_order(_order("m", "alice", Side.yes, Action.sell, price=70, qty=10))

    # Bob sells NO @ 30, which the engine must normalize to BUY YES @ 70
    # (SELL NO @ q == BUY YES @ (100 - q)) so it crosses Alice's ask.
    result = engine.submit_order(_order("m", "bob", Side.no, Action.sell, price=30, qty=10))

    assert result.status == OrderStatus.filled
    assert len(result.fills) == 1
    assert result.fills[0].price_cents == 70


def test_cancel_order_roundtrip():
    engine = MatchingEngine()
    order_id = uuid.uuid4()
    engine.submit_order(_order("m", "bob", Side.yes, Action.buy, price=40, qty=5, order_id=order_id))

    cancel_result = engine.cancel_order("m", order_id)

    assert cancel_result.status == OrderStatus.cancelled
    assert cancel_result.remaining_quantity == 5
    assert engine.get_book_snapshot("m").bids == []
