import uuid
from datetime import datetime, timezone

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
            "executed_at": datetime.now(timezone.utc).isoformat(),
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
