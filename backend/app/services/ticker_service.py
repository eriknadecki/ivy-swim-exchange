import uuid

from sqlalchemy.orm import Session

from app.db.models import TickerUpdate
from app.ws import events as ws_events


def post_ticker_update(
    db: Session, *, meet_id: uuid.UUID, meet_event_id: uuid.UUID | None, author_id: uuid.UUID, body: str
) -> TickerUpdate:
    """Pure information — posting this never touches any market's price.
    Traders read it and react by placing orders; that reaction is what
    actually moves the book."""
    update = TickerUpdate(meet_id=meet_id, meet_event_id=meet_event_id, author_id=author_id, body=body)
    db.add(update)
    db.commit()
    db.refresh(update)

    ws_events.publish_ticker_update(meet_id, meet_event_id, body, update.created_at)
    return update
