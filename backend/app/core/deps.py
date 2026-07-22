import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import TokenType, decode_token
from app.db.models import User, UserRole
from app.db.session import get_db
from engine.engine import MatchingEngine

bearer_scheme = HTTPBearer()

# One matching engine for the process lifetime: order books are in-memory,
# so every request must share this instance rather than getting a fresh
# (empty) engine each time. Known MVP limitation: book state does not
# survive a process restart — recovering it from the `orders` table on
# startup is future work, not needed until this runs somewhere that restarts
# under live trading.
_matching_engine = MatchingEngine()


def get_engine() -> MatchingEngine:
    return _matching_engine


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials)
    except jwt.PyJWTError as exc:
        raise unauthorized from exc

    if payload.get("type") != TokenType.access.value:
        raise unauthorized

    user = db.get(User, uuid.UUID(payload["sub"]))
    if user is None:
        raise unauthorized
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user
