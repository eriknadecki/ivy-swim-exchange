import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class TickerUpdate(Base):
    """A pure information feed for a meet — posting one never moves any
    market's price directly. Only real trades move prices; a ticker post is
    just what traders react to. See order_service for where actual price
    movement happens."""

    __tablename__ = "ticker_updates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("meets.id"), index=True)
    meet_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meet_events.id"), nullable=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
