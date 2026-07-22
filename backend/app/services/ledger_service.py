import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Account, AccountOwnerType, LedgerEntry, LedgerEntryType


@dataclass(frozen=True)
class LedgerEntryInput:
    account_id: uuid.UUID
    entry_type: LedgerEntryType
    amount_cents: int
    reference_type: str | None = None
    reference_id: uuid.UUID | None = None


def get_house_account(db: Session) -> Account:
    account = db.execute(
        select(Account).where(Account.owner_type == AccountOwnerType.house)
    ).scalar_one_or_none()
    if account is None:
        account = Account(owner_type=AccountOwnerType.house, owner_id=None, cash_balance_cents=0)
        db.add(account)
        db.flush()
    return account


def get_market_escrow_account(db: Session, market_id: uuid.UUID) -> Account:
    account = db.execute(
        select(Account).where(
            Account.owner_type == AccountOwnerType.market_escrow, Account.owner_id == market_id
        )
    ).scalar_one_or_none()
    if account is None:
        account = Account(
            owner_type=AccountOwnerType.market_escrow, owner_id=market_id, cash_balance_cents=0
        )
        db.add(account)
        db.flush()
    return account


def post_entry_group(db: Session, entries: list[LedgerEntryInput]) -> uuid.UUID:
    """Atomically apply a set of balanced ledger entries.

    Every call must move real (virtual) cash in a closed loop: the amounts
    must sum to zero across accounts, so no group can create or destroy money
    except a deliberate mint/burn against the house account.
    """
    if sum(entry.amount_cents for entry in entries) != 0:
        raise ValueError("ledger entry group must sum to zero")

    group_id = uuid.uuid4()
    for entry in entries:
        account = db.get(Account, entry.account_id, with_for_update=True)
        if account is None:
            raise ValueError(f"unknown account {entry.account_id}")
        account.cash_balance_cents += entry.amount_cents
        db.add(
            LedgerEntry(
                account_id=account.id,
                entry_group_id=group_id,
                entry_type=entry.entry_type,
                amount_cents=entry.amount_cents,
                balance_after_cents=account.cash_balance_cents,
                reference_type=entry.reference_type,
                reference_id=entry.reference_id,
            )
        )
    db.flush()
    return group_id
