from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.invite import InviteCheckOut
from app.services import auth_service

router = APIRouter(prefix="/invites", tags=["invites"])


@router.get("/{code}", response_model=InviteCheckOut)
def check_invite(code: str, db: Session = Depends(get_db)) -> InviteCheckOut:
    reason = auth_service.check_invite(db, code)
    return InviteCheckOut(valid=reason is None, reason=reason)
