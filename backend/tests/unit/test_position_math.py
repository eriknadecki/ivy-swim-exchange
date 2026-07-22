from app.services.position_math import PositionState, apply_fill


def test_zero_delta_is_a_no_op():
    state = PositionState(5, 40, 10)
    assert apply_fill(state, 0, 99) == state


def test_opening_a_new_long_position():
    state = apply_fill(PositionState(0, 0, 0), 10, 40)
    assert state == PositionState(10, 40, 0)


def test_adding_to_a_long_position_weight_averages_cost():
    state = apply_fill(PositionState(10, 40, 0), 5, 60)
    assert state == PositionState(15, 47, 0)  # (10*40 + 5*60) / 15 = 46.67 -> 47


def test_partially_closing_a_long_realizes_pnl_and_keeps_cost_basis():
    state = apply_fill(PositionState(15, 47, 0), -5, 70)
    assert state == PositionState(10, 47, 115)  # 5 * (70 - 47) = 115


def test_fully_closing_a_long_zeroes_out_and_realizes_final_pnl():
    state = apply_fill(PositionState(10, 47, 115), -10, 50)
    assert state == PositionState(0, 0, 145)  # 115 + 10 * (50 - 47)


def test_overclosing_a_long_flips_to_a_fresh_short():
    state = apply_fill(PositionState(10, 50, 0), -15, 60)
    # Realize P&L on the 10 closed units, then open -5 fresh at the fill price.
    assert state == PositionState(-5, 60, 100)  # 10 * (60 - 50) = 100


def test_adding_to_a_short_position_weight_averages_cost():
    state = apply_fill(PositionState(-10, 30, 0), -5, 20)
    assert state == PositionState(-15, 27, 0)  # (10*30 + 5*20) / 15 = 26.67 -> 27


def test_partially_closing_a_short_realizes_pnl():
    state = apply_fill(PositionState(-15, 27, 0), 5, 20)
    assert state == PositionState(-10, 27, 35)  # 5 * (27 - 20) = 35
