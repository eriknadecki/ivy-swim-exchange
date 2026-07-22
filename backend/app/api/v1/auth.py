import uuid

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import TokenType, create_access_token, create_refresh_token, decode_token
from app.db.session import get_db
from app.schemas.auth import LoginRequest, RefreshRequest, SignupRequest, TokenResponse
from app.services import auth_service
from app.services.errors import InvalidCredentialsError, InviteInvalidError, UserAlreadyExistsError

router = APIRouter(prefix="/auth", tags=["auth"])


def _tokens_for(user_id: uuid.UUID) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        user = auth_service.signup(
            db,
            invite_code=payload.invite_code,
            email=payload.email,
            username=payload.username,
            password=payload.password,
        )
    except InviteInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _tokens_for(user.id)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        user = auth_service.authenticate(db, payload.email, payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return _tokens_for(user.id)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest) -> TokenResponse:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
    )
    try:
        claims = decode_token(payload.refresh_token)
    except jwt.PyJWTError as exc:
        raise unauthorized from exc
    if claims.get("type") != TokenType.refresh.value:
        raise unauthorized
    return _tokens_for(uuid.UUID(claims["sub"]))
