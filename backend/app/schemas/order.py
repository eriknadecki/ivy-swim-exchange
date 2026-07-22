import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from engine.types import Action, OrderStatus, OrderType, Side, TimeInForce


class CreateOrderRequest(BaseModel):
    market_id: uuid.UUID
    side: Side
    action: Action
    order_type: OrderType = OrderType.limit
    quantity: int = Field(gt=0)
    price_cents: int | None = Field(default=None, ge=1, le=99)
    time_in_force: TimeInForce = TimeInForce.gtc

    @model_validator(mode="after")
    def _limit_orders_need_a_price(self) -> "CreateOrderRequest":
        if self.order_type == OrderType.limit and self.price_cents is None:
            raise ValueError("price_cents is required for limit orders")
        return self


class OrderOut(BaseModel):
    id: uuid.UUID
    market_id: uuid.UUID
    side: Side
    action: Action
    order_type: OrderType
    time_in_force: TimeInForce
    limit_price_cents: int | None
    quantity: int
    filled_quantity: int
    status: OrderStatus
    collateral_cents: int
    created_at: datetime

    model_config = {"from_attributes": True}


class PositionOut(BaseModel):
    market_id: uuid.UUID
    net_yes_quantity: int
    avg_cost_cents: int
    realized_pnl_cents: int

    model_config = {"from_attributes": True}
