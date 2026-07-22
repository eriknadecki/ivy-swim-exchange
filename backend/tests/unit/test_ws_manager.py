import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.ws.manager import ConnectionManager


class FakeWebSocket:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send_json(self, data: dict) -> None:
        self.sent.append(data)


async def test_broadcast_delivers_to_subscribers() -> None:
    manager = ConnectionManager()
    ws = FakeWebSocket()
    await manager.subscribe(ws, "market:1")

    await manager._broadcast_async("market:1", {"type": "trade"})

    assert ws.sent == [{"type": "trade"}]


async def test_broadcast_only_reaches_subscribers_of_that_topic() -> None:
    manager = ConnectionManager()
    ws = FakeWebSocket()
    await manager.subscribe(ws, "market:1")

    await manager._broadcast_async("market:2", {"type": "trade"})

    assert ws.sent == []


async def test_unsubscribe_stops_delivery() -> None:
    manager = ConnectionManager()
    ws = FakeWebSocket()
    await manager.subscribe(ws, "market:1")
    await manager.unsubscribe(ws, "market:1")

    await manager._broadcast_async("market:1", {"type": "trade"})

    assert ws.sent == []


async def test_disconnect_removes_from_all_subscribed_topics() -> None:
    manager = ConnectionManager()
    ws = FakeWebSocket()
    await manager.subscribe(ws, "market:1")
    await manager.subscribe(ws, "user:alice")

    manager.disconnect(ws)

    await manager._broadcast_async("market:1", {"type": "trade"})
    await manager._broadcast_async("user:alice", {"type": "balance_update"})
    assert ws.sent == []


def test_broadcast_without_bound_loop_is_a_safe_noop() -> None:
    manager = ConnectionManager()
    manager.broadcast("market:1", {"type": "trade"})  # must not raise


async def test_broadcast_reaches_subscriber_when_called_from_a_worker_thread() -> None:
    """The realistic path: order_service runs synchronously in FastAPI's
    worker threadpool and calls broadcast() from there, not from the event
    loop itself — this is what actually exercises run_coroutine_threadsafe."""
    manager = ConnectionManager()
    manager.bind_loop(asyncio.get_running_loop())
    ws = FakeWebSocket()
    await manager.subscribe(ws, "market:1")

    with ThreadPoolExecutor(max_workers=1) as pool:
        pool.submit(manager.broadcast, "market:1", {"type": "trade"}).result()

    for _ in range(50):
        if ws.sent:
            break
        await asyncio.sleep(0.01)

    assert ws.sent == [{"type": "trade"}]


def test_sequence_numbers_increment_independently_per_topic() -> None:
    manager = ConnectionManager()
    assert manager.next_sequence("market:1") == 1
    assert manager.next_sequence("market:1") == 2
    assert manager.next_sequence("market:2") == 1
