import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Account, AccountOwnerType


def get_user_account(db: Session, user_id: uuid.UUID, *, for_update: bool = True) -> Account:
    query = select(Account).where(Account.owner_type == AccountOwnerType.user, Account.owner_id == user_id)
    if for_update:
        query = query.with_for_update()
    return db.execute(query).scalar_one()
