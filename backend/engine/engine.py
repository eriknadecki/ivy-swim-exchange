import threading
import uuid

from engine.normalization import normalize_new_order
from engine.order_book import OrderBook
from engine.types import BookSnapshot, CancelResult, NewOrder, OrderResult


class MatchingEngine:
    """Holds one OrderBook per market and serializes access to each.

    Note on cancel/snapshot taking `market_id` explicitly: a global
    order_id -> market_id index would let callers omit it, but the DB-backed
    caller (the `orders` table) always already knows an order's market, so
    requiring it here avoids extra bookkeeping for no real benefit.
    """

    def __init__(self) -> None:
        self._books: dict[str, OrderBook] = {}
        self._locks: dict[str, threading.Lock] = {}
        self._registry_lock = threading.Lock()

    def _get_book(self, market_id: str) -> tuple[OrderBook, threading.Lock]:
        with self._registry_lock:
            if market_id not in self._books:
                self._books[market_id] = OrderBook(market_id)
                self._locks[market_id] = threading.Lock()
            return self._books[market_id], self._locks[market_id]

    def submit_order(self, order: NewOrder) -> OrderResult:
        normalized = normalize_new_order(order)
        book, lock = self._get_book(order.market_id)
        with lock:
            return book.submit(normalized)

    def cancel_order(self, market_id: str, order_id: uuid.UUID) -> CancelResult:
        book, lock = self._get_book(market_id)
        with lock:
            return book.cancel(order_id)

    def get_book_snapshot(self, market_id: str, depth: int = 10) -> BookSnapshot:
        book, lock = self._get_book(market_id)
        with lock:
            return book.snapshot(depth)
