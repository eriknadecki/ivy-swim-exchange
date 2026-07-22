import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_engine
from app.db.models import Order, User
from app.db.session import get_db
from app.schemas.order import CreateOrderRequest, OrderOut
from app.services import order_service
from app.services.errors import InsufficientFundsError, MarketNotTradableError, NotFoundError
from engine.engine import MatchingEngine

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def submit_order(
    payload: CreateOrderRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    engine: MatchingEngine = Depends(get_engine),
) -> Order:
    try:
        return order_service.submit_order(
            db,
            engine,
            user_id=user.id,
            market_id=payload.market_id,
            side=payload.side,
            action=payload.action,
            order_type=payload.order_type,
            quantity=payload.quantity,
            price_cents=payload.price_cents,
            time_in_force=payload.time_in_force,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MarketNotTradableError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except InsufficientFundsError as exc:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(exc)) from exc


@router.delete("/{order_id}", response_model=OrderOut)
def cancel_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    engine: MatchingEngine = Depends(get_engine),
) -> Order:
    try:
        return order_service.cancel_order(db, engine, user_id=user.id, order_id=order_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("", response_model=list[OrderOut])
def list_my_orders(
    market_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Order]:
    query = select(Order).where(Order.user_id == user.id)
    if market_id is not None:
        query = query.where(Order.market_id == market_id)
    return list(db.execute(query.order_by(Order.created_at.desc())).scalars().all())
