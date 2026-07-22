from typing import NamedTuple


class PositionState(NamedTuple):
    net_yes_quantity: int
    avg_cost_cents: int
    realized_pnl_cents: int


def apply_fill(state: PositionState, delta_qty: int, price_cents: int) -> PositionState:
    """Fold one fill into a position's running cost basis and realized P&L.

    `delta_qty` is signed from the position holder's point of view: positive
    for a fill that bought YES, negative for a fill that sold YES. avg_cost
    is a plain weighted average of entry price; rounding here only affects
    the displayed cost basis, never account balances (those are driven by
    the ledger/collateral movements in order_service, not this function).
    """
    net, avg_cost, realized = state
    if delta_qty == 0:
        return state

    if net == 0:
        return PositionState(delta_qty, price_cents, realized)

    same_direction = (net > 0) == (delta_qty > 0)
    if same_direction:
        new_net = net + delta_qty
        new_avg = round((abs(net) * avg_cost + abs(delta_qty) * price_cents) / abs(new_net))
        return PositionState(new_net, new_avg, realized)

    # Opposite directions: closing some (or all, or more than all) of the
    # existing position realizes P&L on the closed portion.
    closing_qty = min(abs(net), abs(delta_qty))
    pnl_per_unit = (price_cents - avg_cost) if net > 0 else (avg_cost - price_cents)
    new_realized = realized + pnl_per_unit * closing_qty
    new_net = net + delta_qty

    if new_net == 0:
        return PositionState(0, 0, new_realized)
    if (new_net > 0) == (net > 0):
        # Partial close: remaining exposure keeps its original cost basis.
        return PositionState(new_net, avg_cost, new_realized)
    # Flip: the excess beyond closing the old position opens a fresh one.
    return PositionState(new_net, price_cents, new_realized)
