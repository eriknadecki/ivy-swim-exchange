import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class LedgerEntryType(StrEnum):
    initial_grant = "initial_grant"
    trade_settlement = "trade_settlement"
    resolution_payout = "resolution_payout"
    fee = "fee"


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), index=True)
    entry_group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    entry_type: Mapped[LedgerEntryType] = mapped_column(Enum(LedgerEntryType, name="ledger_entry_type"))
    amount_cents: Mapped[int] = mapped_column(Integer)
    balance_after_cents: Mapped[int] = mapped_column(Integer)
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
