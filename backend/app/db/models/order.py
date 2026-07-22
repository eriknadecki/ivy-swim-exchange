import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from engine.types import Action, OrderStatus, OrderType, Side, TimeInForce


class Order(Base):
    """Mirrors an order submitted to the matching engine.

    The primary key is deliberately the same UUID passed to the engine as
    NewOrder.order_id — one identity across both systems, no id-translation
    bookkeeping needed when reconciling engine results back to this row.
    """

    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    market_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("markets.id"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    side: Mapped[Side] = mapped_column(Enum(Side, name="order_side"))
    action: Mapped[Action] = mapped_column(Enum(Action, name="order_action"))
    order_type: Mapped[OrderType] = mapped_column(Enum(OrderType, name="order_type"))
    time_in_force: Mapped[TimeInForce] = mapped_column(Enum(TimeInForce, name="order_time_in_force"))
    limit_price_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer)
    filled_quantity: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus, name="order_status"))
    # Collateral currently held on the owner's account for this order's
    # still-resting quantity; 0 once the order reaches a terminal state.
    collateral_cents: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
