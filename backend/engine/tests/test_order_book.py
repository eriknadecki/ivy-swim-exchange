import uuid

from engine.order_book import OrderBook
from engine.types import Action, NewOrder, OrderStatus, OrderType, TimeInForce


def _order(owner_id, action, price=None, qty=5, order_type=OrderType.limit, tif=TimeInForce.gtc, order_id=None):
    from engine.types import Side

    return NewOrder(
        market_id="m",
        owner_id=owner_id,
        side=Side.yes,
        action=action,
        order_type=order_type,
        quantity=qty,
        price_cents=price,
        time_in_force=tif,
        order_id=order_id or uuid.uuid4(),
    )


def test_order_rests_on_empty_book():
    book = OrderBook("m")
    result = book.submit(_order("alice", Action.buy, price=50, qty=10))
    assert result.status == OrderStatus.open
    assert result.fills == []
    assert result.remaining_quantity == 10
    assert book.best_bid() == 50
    assert book.best_ask() is None


def test_exact_match_fills_both_sides():
    book = OrderBook("m")
    maker_id = uuid.uuid4()
    book.submit(_order("bob", Action.sell, price=60, qty=10, order_id=maker_id))

    result = book.submit(_order("alice", Action.buy, price=60, qty=10))

    assert result.status == OrderStatus.filled
    assert len(result.fills) == 1
    fill = result.fills[0]
    assert fill.price_cents == 60
    assert fill.quantity == 10
    assert fill.maker_order_id == maker_id
    assert book.best_bid() is None
    assert book.best_ask() is None


def test_partial_fill_on_maker_side_leaves_remainder_resting():
    book = OrderBook("m")
    maker_id = uuid.uuid4()
    book.submit(_order("bob", Action.sell, price=60, qty=20, order_id=maker_id))

    result = book.submit(_order("alice", Action.buy, price=60, qty=10))

    assert result.status == OrderStatus.filled
    assert result.fills[0].quantity == 10
    assert book.best_ask() == 60
    snapshot = book.snapshot()
    assert snapshot.asks[0].total_quantity == 10


def test_partial_fill_on_taker_side_rests_the_remainder():
    book = OrderBook("m")
    book.submit(_order("bob", Action.sell, price=60, qty=5))

    result = book.submit(_order("alice", Action.buy, price=60, qty=10))

    assert result.status == OrderStatus.partially_filled
    assert result.remaining_quantity == 5
    assert sum(f.quantity for f in result.fills) == 5
    assert book.best_bid() == 60


def test_sweeps_multiple_price_levels_best_price_first():
    book = OrderBook("m")
    book.submit(_order("bob", Action.sell, price=60, qty=5))
    book.submit(_order("carol", Action.sell, price=61, qty=5))

    result = book.submit(_order("alice", Action.buy, price=62, qty=8))

    assert result.status == OrderStatus.filled
    assert [f.price_cents for f in result.fills] == [60, 61]
    assert [f.quantity for f in result.fills] == [5, 3]
    snapshot = book.snapshot()
    assert snapshot.asks[0].price_cents == 61
    assert snapshot.asks[0].total_quantity == 2


def test_fifo_priority_within_a_price_level():
    book = OrderBook("m")
    first_id = uuid.uuid4()
    second_id = uuid.uuid4()
    book.submit(_order("bob", Action.sell, price=60, qty=5, order_id=first_id))
    book.submit(_order("carol", Action.sell, price=60, qty=5, order_id=second_id))

    result = book.submit(_order("alice", Action.buy, price=60, qty=7))

    assert [f.maker_order_id for f in result.fills] == [first_id, second_id]
    assert [f.quantity for f in result.fills] == [5, 2]


def test_cancelled_order_is_skipped_when_encountered_mid_match():
    book = OrderBook("m")
    first_id = uuid.uuid4()
    second_id = uuid.uuid4()
    book.submit(_order("bob", Action.sell, price=60, qty=5, order_id=first_id))
    book.submit(_order("carol", Action.sell, price=60, qty=5, order_id=second_id))

    cancel_result = book.cancel(first_id)
    assert cancel_result.status == OrderStatus.cancelled
    assert cancel_result.remaining_quantity == 5

    result = book.submit(_order("alice", Action.buy, price=60, qty=5))

    assert result.status == OrderStatus.filled
    assert len(result.fills) == 1
    assert result.fills[0].maker_order_id == second_id


def test_self_trade_prevention_cancels_resting_order_instead_of_matching():
    book = OrderBook("m")
    resting_id = uuid.uuid4()
    book.submit(_order("alice", Action.sell, price=60, qty=10, order_id=resting_id))

    result = book.submit(_order("alice", Action.buy, price=60, qty=5))

    assert result.fills == []
    assert result.status == OrderStatus.open
    assert result.remaining_quantity == 5
    assert book.best_ask() is None  # the resting sell was pulled, not matched


def test_market_order_sweeps_and_discards_unfilled_remainder():
    book = OrderBook("m")
    book.submit(_order("bob", Action.sell, price=60, qty=5))

    result = book.submit(_order("alice", Action.buy, order_type=OrderType.market, qty=10))

    assert result.status == OrderStatus.partially_filled
    assert result.remaining_quantity == 0
    assert sum(f.quantity for f in result.fills) == 5
    assert book.best_bid() is None  # nothing rests from a market order


def test_ioc_order_fills_available_and_discards_rest():
    book = OrderBook("m")
    book.submit(_order("bob", Action.sell, price=60, qty=3))

    result = book.submit(_order("alice", Action.buy, price=60, qty=10, tif=TimeInForce.ioc))

    assert result.status == OrderStatus.partially_filled
    assert result.remaining_quantity == 0
    assert book.best_bid() is None


def test_fok_order_cancels_entirely_when_liquidity_insufficient():
    book = OrderBook("m")
    book.submit(_order("bob", Action.sell, price=60, qty=3))

    result = book.submit(_order("alice", Action.buy, price=60, qty=10, tif=TimeInForce.fok))

    assert result.status == OrderStatus.cancelled
    assert result.fills == []
    assert result.remaining_quantity == 0  # nothing rests; a cancelled order leaves nothing working
    # The resting order must be untouched — FOK never partially executes.
    assert book.best_ask() == 60
    assert book.snapshot().asks[0].total_quantity == 3


def test_fok_order_fills_fully_when_liquidity_sufficient():
    book = OrderBook("m")
    book.submit(_order("bob", Action.sell, price=60, qty=3))
    book.submit(_order("carol", Action.sell, price=61, qty=5))

    result = book.submit(_order("alice", Action.buy, price=61, qty=8, tif=TimeInForce.fok))

    assert result.status == OrderStatus.filled
    assert result.remaining_quantity == 0
    assert sum(f.quantity for f in result.fills) == 8


def test_snapshot_orders_bids_descending_and_asks_ascending_and_respects_depth():
    book = OrderBook("m")
    for price in (40, 45, 50):
        book.submit(_order("bob", Action.buy, price=price, qty=1))
    for price in (60, 65, 70):
        book.submit(_order("carol", Action.sell, price=price, qty=1))

    snapshot = book.snapshot(depth=2)

    assert [level.price_cents for level in snapshot.bids] == [50, 45]
    assert [level.price_cents for level in snapshot.asks] == [60, 65]


def test_cancel_unknown_order_returns_not_found():
    book = OrderBook("m")
    result = book.cancel(uuid.uuid4())
    assert result.status == OrderStatus.not_found
    assert result.remaining_quantity == 0
