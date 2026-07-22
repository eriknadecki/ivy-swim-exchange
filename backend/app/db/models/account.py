import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base

HOUSE_ACCOUNT_CODE = "house"


class AccountOwnerType(StrEnum):
    user = "user"
    house = "house"
    market_escrow = "market_escrow"


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        # Only real user wallets are forbidden from going negative. The house
        # account intentionally goes negative as it mints virtual currency on
        # signup grants; market_escrow accounts are addressed once markets exist.
        CheckConstraint(
            "owner_type != 'user' OR cash_balance_cents >= 0",
            name="ck_accounts_user_cash_nonnegative",
        ),
        CheckConstraint("held_collateral_cents >= 0", name="ck_accounts_held_nonnegative"),
        CheckConstraint(
            "owner_type != 'user' OR cash_balance_cents >= held_collateral_cents",
            name="ck_accounts_cash_covers_held",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_type: Mapped[AccountOwnerType] = mapped_column(Enum(AccountOwnerType, name="account_owner_type"))
    owner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, unique=True)
    cash_balance_cents: Mapped[int] = mapped_column(Integer, default=0)
    held_collateral_cents: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
