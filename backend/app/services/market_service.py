from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import Market, MarketGroup


def create_market_group(
    db: Session,
    *,
    title: str,
    description: str | None,
    outcomes: list[str],
    close_at: datetime | None,
) -> MarketGroup:
    group = MarketGroup(title=title, description=description, close_at=close_at)
    db.add(group)
    db.flush()

    for label in outcomes:
        db.add(Market(market_group_id=group.id, label=label, close_at=close_at))

    db.commit()
    db.refresh(group)
    return group
