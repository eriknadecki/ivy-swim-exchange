"""Property-based tests for the matching engine's core invariants.

Each generated order uses a unique owner_id (its own order_id) so self-trade
prevention never fires here — that behavior is covered deterministically in
test_order_book.py::test_self_trade_prevention_cancels_resting_order_instead_of_matching.
Keeping it out of this file lets conservation accounting stay a simple
per-order equation instead of also having to model silent maker cancellations.
"""

import uuid
from dataclasses import dataclass

from hypothesis import given, settings
from hypothesis import strategies as st

from engine.order_book import OrderBook
from engine.types import PRICE_MAX, PRICE_MIN, Action, NewOrder, OrderStatus, OrderType, Side, TimeInForce


@dataclass
class _Tracker:
    quantity: int
    filled: int = 0
    cancelled: int = 0


def _make_order(order_id: uuid.UUID, action: Action, price: int, qty: int) -> NewOrder:
    return NewOrder(
        market_id="m",
        owner_id=order_id,
        side=Side.yes,
        action=action,
        order_type=OrderType.limit,
        quantity=qty,
        price_cents=price,
        time_in_force=TimeInForce.gtc,
        order_id=order_id,
    )


def _assert_no_crossed_book(book: OrderBook) -> None:
    bid, ask = book.best_bid(), book.best_ask()
    if bid is not None and ask is not None:
        assert bid < ask


def _assert_level_aggregate_consistency(book: OrderBook) -> None:
    for price in range(PRICE_MIN, PRICE_MAX + 1):
        live_bid_qty = sum(
            o.remaining for o in book._bids[price] if o.status != OrderStatus.cancelled
        )
        assert live_bid_qty == book._bids_qty[price]
        live_ask_qty = sum(
            o.remaining for o in book._asks[price] if o.status != OrderStatus.cancelled
        )
        assert live_ask_qty == book._asks_qty[price]


@given(data=st.data())
@settings(max_examples=200)
def test_matching_invariants_hold_under_random_operations(data):
    book = OrderBook("m")
    trackers: dict[uuid.UUID, _Tracker] = {}
    live_ids: list[uuid.UUID] = []
    next_id = 1

    num_ops = data.draw(st.integers(min_value=1, max_value=60))
    for _ in range(num_ops):
        if live_ids and data.draw(st.booleans()):
            order_id = data.draw(st.sampled_from(live_ids))
            result = book.cancel(order_id)
            if result.status == OrderStatus.cancelled:
                trackers[order_id].cancelled += result.remaining_quantity
                live_ids.remove(order_id)
        else:
            action = data.draw(st.sampled_from([Action.buy, Action.sell]))
            price = data.draw(st.integers(min_value=PRICE_MIN, max_value=PRICE_MAX))
            qty = data.draw(st.integers(min_value=1, max_value=20))
            order_id = uuid.UUID(int=next_id)
            next_id += 1

            order = _make_order(order_id, action, price, qty)
            trackers[order_id] = _Tracker(quantity=qty)
            result = book.submit(order)
            for fill in result.fills:
                trackers[fill.taker_order_id].filled += fill.quantity
                trackers[fill.maker_order_id].filled += fill.quantity
            if result.status in (OrderStatus.open, OrderStatus.partially_filled):
                live_ids.append(order_id)

        _assert_no_crossed_book(book)
        _assert_level_aggregate_consistency(book)

    for order_id, tracker in trackers.items():
        entry = book._order_index.get(order_id)
        resting = entry.remaining if entry is not None and entry.status != OrderStatus.cancelled else 0
        assert tracker.quantity == tracker.filled + resting + tracker.cancelled, (
            f"conservation violated for order {order_id}: "
            f"quantity={tracker.quantity} filled={tracker.filled} "
            f"resting={resting} cancelled={tracker.cancelled}"
        )


_submit_op = st.tuples(
    st.sampled_from([Action.buy, Action.sell]),
    st.integers(min_value=PRICE_MIN, max_value=PRICE_MAX),
    st.integers(min_value=1, max_value=20),
)


@given(ops=st.lists(_submit_op, min_size=1, max_size=40))
@settings(max_examples=100)
def test_replaying_identical_operations_is_deterministic(ops):
    def run():
        book = OrderBook("m")
        fills_log = []
        for i, (action, price, qty) in enumerate(ops):
            order = _make_order(uuid.UUID(int=i + 1), action, price, qty)
            result = book.submit(order)
            fills_log.append(
                [(f.price_cents, f.quantity, f.taker_order_id, f.maker_order_id) for f in result.fills]
            )
        return fills_log, book.snapshot(depth=PRICE_MAX)

    fills_a, snapshot_a = run()
    fills_b, snapshot_b = run()

    assert fills_a == fills_b
    assert snapshot_a == snapshot_b
