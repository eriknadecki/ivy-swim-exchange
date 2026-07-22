from dataclasses import replace

from engine.types import PRICE_MAX, PRICE_MIN, Action, NewOrder, Side


def normalize_new_order(order: NewOrder) -> NewOrder:
    """Translate a client-facing order into the engine's unified YES instrument.

    The engine only ever matches a single "YES" instrument priced 1-99 cents.
    A NO order is the mirror image of a YES order at the complementary price:
    BUY NO @ q  == SELL YES @ (100 - q)
    SELL NO @ q == BUY YES @ (100 - q)
    This keeps every branch of the matching algorithm free of NO-specific logic.
    """
    if order.side == Side.yes:
        return order

    normalized_action = Action.sell if order.action == Action.buy else Action.buy
    normalized_price = None if order.price_cents is None else (100 - order.price_cents)
    return replace(order, side=Side.yes, action=normalized_action, price_cents=normalized_price)


def denormalize_price_for_no(yes_price_cents: int) -> int:
    """Complementary NO price for a given YES price, both in 1-99 range."""
    assert PRICE_MIN <= yes_price_cents <= PRICE_MAX
    return 100 - yes_price_cents
