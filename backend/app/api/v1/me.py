from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.models import Account, User
from app.db.session import get_db
from app.schemas.account import BalanceOut
from app.schemas.auth import UserOut

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)) -> User:
    return user


@router.get("/balance", response_model=BalanceOut)
def get_balance(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> BalanceOut:
    account = db.execute(select(Account).where(Account.owner_id == user.id)).scalar_one()
    return BalanceOut(
        cash_balance_cents=account.cash_balance_cents,
        held_collateral_cents=account.held_collateral_cents,
        available_cents=account.cash_balance_cents - account.held_collateral_cents,
    )
