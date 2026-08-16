import uuid

from engine.normalization import normalize_new_order
from engine.types import Action, NewOrder, OrderType, Side, TimeInForce


def _order(**overrides) -> NewOrder:
    defaults = {
        "market_id": "m",
        "owner_id": "alice",
        "side": Side.yes,
        "action": Action.buy,
        "order_type": OrderType.limit,
        "quantity": 5,
        "price_cents": 45,
        "time_in_force": TimeInForce.gtc,
        "order_id": uuid.uuid4(),
    }
    defaults.update(overrides)
    return NewOrder(**defaults)


def test_yes_order_passes_through_unchanged():
    order = _order(side=Side.yes, action=Action.buy, price_cents=45)
    normalized = normalize_new_order(order)
    assert normalized is order


def test_buy_no_becomes_sell_yes_at_complementary_price():
    order = _order(side=Side.no, action=Action.buy, price_cents=30)
    normalized = normalize_new_order(order)
    assert normalized.side == Side.yes
    assert normalized.action == Action.sell
    assert normalized.price_cents == 70


def test_sell_no_becomes_buy_yes_at_complementary_price():
    order = _order(side=Side.no, action=Action.sell, price_cents=30)
    normalized = normalize_new_order(order)
    assert normalized.side == Side.yes
    assert normalized.action == Action.buy
    assert normalized.price_cents == 70


def test_no_market_order_normalizes_action_without_touching_price():
    order = _order(side=Side.no, action=Action.buy, order_type=OrderType.market, price_cents=None)
    normalized = normalize_new_order(order)
    assert normalized.side == Side.yes
    assert normalized.action == Action.sell
    assert normalized.price_cents is None
