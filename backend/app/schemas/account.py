from pydantic import BaseModel


class BalanceOut(BaseModel):
    cash_balance_cents: int
    held_collateral_cents: int
    available_cents: int
