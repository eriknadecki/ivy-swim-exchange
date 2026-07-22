from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.db.models import User
from app.db.session import get_db
from app.schemas.invite import CreateInviteRequest, InviteOut
from app.services import auth_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/invites", response_model=InviteOut)
def create_invite(
    payload: CreateInviteRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> InviteOut:
    invite = auth_service.create_invite(
        db,
        created_by_user_id=admin.id,
        max_uses=payload.max_uses,
        expires_in_days=payload.expires_in_days,
    )
    return InviteOut(
        code=invite.code,
        max_uses=invite.max_uses,
        uses_count=invite.uses_count,
        expires_at=invite.expires_at,
    )
