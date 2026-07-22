import uuid

import pytest

from app.db.models import LedgerEntryType
from app.services.ledger_service import LedgerEntryInput, post_entry_group


def test_post_entry_group_rejects_unbalanced_entries() -> None:
    entries = [
        LedgerEntryInput(account_id=uuid.uuid4(), entry_type=LedgerEntryType.initial_grant, amount_cents=100),
        LedgerEntryInput(account_id=uuid.uuid4(), entry_type=LedgerEntryType.initial_grant, amount_cents=-99),
    ]
    with pytest.raises(ValueError, match="sum to zero"):
        post_entry_group(db=None, entries=entries)  # type: ignore[arg-type]
