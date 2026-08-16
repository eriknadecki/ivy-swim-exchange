import asyncio
import itertools
from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    """Topic-based WebSocket pub/sub.

    Service code that publishes events (order_service, etc.) runs
    synchronously inside FastAPI's worker threadpool, not on the event loop
    that owns the actual WebSocket connections. `broadcast()` is the
    thread-safe entry point for that: it schedules the real async send onto
    the bound event loop via asyncio.run_coroutine_threadsafe rather than
    trying to await anything directly from a worker thread.
    """

    def __init__(self) -> None:
        self._topic_subscribers: dict[str, set[WebSocket]] = defaultdict(set)
        self._sequences: dict[str, itertools.count] = defaultdict(lambda: itertools.count(1))
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def next_sequence(self, topic: str) -> int:
        return next(self._sequences[topic])

    async def subscribe(self, websocket: WebSocket, topic: str) -> None:
        self._topic_subscribers[topic].add(websocket)

    async def unsubscribe(self, websocket: WebSocket, topic: str) -> None:
        self._topic_subscribers[topic].discard(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        for subscribers in self._topic_subscribers.values():
            subscribers.discard(websocket)

    async def _broadcast_async(self, topic: str, message: dict) -> None:
        for websocket in list(self._topic_subscribers.get(topic, ())):
            try:
                await websocket.send_json(message)
            except Exception:  # noqa: BLE001 — any send failure means a dead socket; disconnect regardless of cause
                self.disconnect(websocket)

    def broadcast(self, topic: str, message: dict) -> None:
        if self._loop is None:
            return  # no event loop bound yet (e.g. plain unit tests) — no-op
        asyncio.run_coroutine_threadsafe(self._broadcast_async(topic, message), self._loop)


manager = ConnectionManager()
