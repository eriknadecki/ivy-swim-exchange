from datetime import datetime

from pydantic import BaseModel, Field


class CreateInviteRequest(BaseModel):
    max_uses: int = Field(default=1, ge=1, le=1000)
    expires_in_days: int | None = Field(default=30, ge=1, le=365)


class InviteOut(BaseModel):
    code: str
    max_uses: int
    uses_count: int
    expires_at: datetime | None


class InviteCheckOut(BaseModel):
    valid: bool
    reason: str | None = None
