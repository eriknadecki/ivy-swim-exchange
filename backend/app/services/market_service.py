import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import Market, MarketGroup, MarketStatus
from app.services.errors import NotFoundError


def create_market_group(
    db: Session,
    *,
    title: str,
    description: str | None,
    outcomes: list[str],
    close_at: datetime | None,
    meet_id: uuid.UUID | None = None,
    meet_event_id: uuid.UUID | None = None,
) -> MarketGroup:
    group = MarketGroup(
        title=title, description=description, close_at=close_at, meet_id=meet_id, meet_event_id=meet_event_id
    )
    db.add(group)
    db.flush()

    for label in outcomes:
        db.add(Market(market_group_id=group.id, label=label, close_at=close_at))

    db.commit()
    db.refresh(group)
    return group


def close_market(db: Session, market_id: uuid.UUID) -> Market:
    market = db.get(Market, market_id)
    if market is None:
        raise NotFoundError("unknown market")
    market.status = MarketStatus.closed
    db.commit()
    db.refresh(market)
    return market
