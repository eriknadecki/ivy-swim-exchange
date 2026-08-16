import uuid
from datetime import UTC, datetime

from app.ws.manager import manager
from engine.types import BookSnapshot


def publish_book_update(market_id: uuid.UUID, snapshot: BookSnapshot) -> None:
    topic = f"market:{market_id}"
    manager.broadcast(
        topic,
        {
            "type": "book_update",
            "market_id": str(market_id),
            "bids": [{"price_cents": lvl.price_cents, "total_quantity": lvl.total_quantity} for lvl in snapshot.bids],
            "asks": [{"price_cents": lvl.price_cents, "total_quantity": lvl.total_quantity} for lvl in snapshot.asks],
            "sequence": manager.next_sequence(topic),
        },
    )


def publish_trade(market_id: uuid.UUID, price_cents: int, quantity: int) -> None:
    topic = f"market:{market_id}"
    manager.broadcast(
        topic,
        {
            "type": "trade",
            "market_id": str(market_id),
            "price_cents": price_cents,
            "quantity": quantity,
            "executed_at": datetime.now(UTC).isoformat(),
            "sequence": manager.next_sequence(topic),
        },
    )


def publish_order_update(user_id: uuid.UUID, order_id: uuid.UUID, order_status: str, filled_quantity: int) -> None:
    manager.broadcast(
        f"user:{user_id}",
        {
            "type": "order_update",
            "order_id": str(order_id),
            "status": order_status,
            "filled_quantity": filled_quantity,
        },
    )


def publish_balance_update(user_id: uuid.UUID, cash_balance_cents: int, available_cents: int) -> None:
    manager.broadcast(
        f"user:{user_id}",
        {
            "type": "balance_update",
            "cash_balance_cents": cash_balance_cents,
            "available_cents": available_cents,
        },
    )


def publish_market_resolved(
    market_id: uuid.UUID, market_group_id: uuid.UUID, winning_market_id: uuid.UUID, resolved_outcome: str
) -> None:
    manager.broadcast(
        f"market:{market_id}",
        {
            "type": "market_resolved",
            "market_id": str(market_id),
            "market_group_id": str(market_group_id),
            "winning_market_id": str(winning_market_id),
            "resolved_outcome": resolved_outcome,
        },
    )


def publish_ticker_update(meet_id: uuid.UUID, meet_event_id: uuid.UUID | None, body: str, created_at: datetime) -> None:
    manager.broadcast(
        f"meet:{meet_id}:ticker",
        {
            "type": "ticker_update",
            "meet_id": str(meet_id),
            "meet_event_id": str(meet_event_id) if meet_event_id else None,
            "body": body,
            "created_at": created_at.isoformat(),
        },
    )
