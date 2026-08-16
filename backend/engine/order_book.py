import itertools
import uuid
from collections import deque

from engine.exceptions import InvalidOrderError
from engine.types import (
    PRICE_MAX,
    PRICE_MIN,
    Action,
    BookSnapshot,
    CancelResult,
    Fill,
    NewOrder,
    OrderResult,
    OrderStatus,
    OrderType,
    PriceLevel,
    RestingOrder,
    TimeInForce,
)

# Arrays are indexed directly by price (1-99); index 0 and 100 are unused
# sentinel slots that let the "no bids"/"no asks" pointers sit just outside
# the real range without special-casing bounds checks.
_NO_BID = PRICE_MIN - 1  # 0
_NO_ASK = PRICE_MAX + 1  # 100


class OrderBook:
    """A single market's limit order book: price-time priority, YES-only.

    Callers must submit orders already normalized to YES terms (see
    normalization.py) — this class has no notion of YES/NO, only buy/sell.
    """

    def __init__(self, market_id: str) -> None:
        self.market_id = market_id
        self._bids: list[deque[RestingOrder]] = [deque() for _ in range(_NO_ASK + 1)]
        self._asks: list[deque[RestingOrder]] = [deque() for _ in range(_NO_ASK + 1)]
        self._bids_qty: list[int] = [0] * (_NO_ASK + 1)
        self._asks_qty: list[int] = [0] * (_NO_ASK + 1)
        self._best_bid = _NO_BID
        self._best_ask = _NO_ASK
        self._order_index: dict[uuid.UUID, RestingOrder] = {}
        self._sequence = itertools.count(1)

    # -- public API -----------------------------------------------------

    def best_bid(self) -> int | None:
        price = self._current_best_bid()
        return price if price != _NO_BID else None

    def best_ask(self) -> int | None:
        price = self._current_best_ask()
        return price if price != _NO_ASK else None

    def snapshot(self, depth: int = 10) -> BookSnapshot:
        bids: list[PriceLevel] = []
        price = self._current_best_bid()
        while price != _NO_BID and len(bids) < depth:
            if self._bids_qty[price] > 0:
                bids.append(PriceLevel(price, self._bids_qty[price]))
            price -= 1

        asks: list[PriceLevel] = []
        price = self._current_best_ask()
        while price != _NO_ASK and len(asks) < depth:
            if self._asks_qty[price] > 0:
                asks.append(PriceLevel(price, self._asks_qty[price]))
            price += 1

        return BookSnapshot(market_id=self.market_id, bids=bids, asks=asks)

    def submit(self, order: NewOrder) -> OrderResult:
        """Submit an order already normalized to YES buy/sell terms."""
        if order.quantity <= 0:
            raise InvalidOrderError("quantity must be positive")

        if order.order_type == OrderType.limit:
            if order.price_cents is None or not (PRICE_MIN <= order.price_cents <= PRICE_MAX):
                raise InvalidOrderError(f"limit price must be in [{PRICE_MIN}, {PRICE_MAX}]")
            limit_price = order.price_cents
        else:
            # A market order is a marketable limit at the book's boundary, so
            # it can never rest and never needs an unbounded price.
            limit_price = PRICE_MAX if order.action == Action.buy else PRICE_MIN

        # Known edge case: this counts aggregate resting quantity without
        # regard to ownership, but matching itself skips same-owner resting
        # orders via self-trade prevention. A FOK order that only clears this
        # precheck because of same-owner liquidity can still come back
        # partially filled.
        if (
            order.time_in_force == TimeInForce.fok
            and self._available_quantity(order.action, limit_price) < order.quantity
        ):
            # remaining_quantity is "still resting," not "unfilled" — a
            # cancelled order rests nothing, so this must be 0 for the same
            # reason every other terminal/non-resting path below is.
            return OrderResult(order.order_id, OrderStatus.cancelled, [], 0)

        fills = self._match(order, limit_price)
        filled_qty = sum(fill.quantity for fill in fills)
        remaining = order.quantity - filled_qty

        rests = (
            order.order_type == OrderType.limit
            and order.time_in_force == TimeInForce.gtc
            and remaining > 0
        )

        if rests:
            resting = RestingOrder(
                order_id=order.order_id,
                owner_id=order.owner_id,
                action=order.action,
                price_cents=limit_price,
                original_quantity=order.quantity,
                remaining=remaining,
                status=OrderStatus.partially_filled if filled_qty else OrderStatus.open,
                sequence=next(self._sequence),
            )
            self._insert(resting)
            status = resting.status
        elif remaining == 0:
            status = OrderStatus.filled
        elif filled_qty > 0:
            # IOC/FOK/market with a partial fill: the unfilled remainder is
            # discarded rather than left resting.
            status = OrderStatus.partially_filled
            remaining = 0
        else:
            # Not resting, nothing filled: IOC/FOK/market found no crossing
            # liquidity at all.
            status = OrderStatus.cancelled
            remaining = 0

        return OrderResult(order.order_id, status, fills, remaining)

    def cancel(self, order_id: uuid.UUID) -> CancelResult:
        resting = self._order_index.pop(order_id, None)
        if resting is None:
            return CancelResult(order_id, OrderStatus.not_found, 0)
        if resting.status in (OrderStatus.filled, OrderStatus.cancelled):
            return CancelResult(order_id, resting.status, 0)

        levels_qty = self._bids_qty if resting.action == Action.buy else self._asks_qty
        levels_qty[resting.price_cents] -= resting.remaining
        remaining = resting.remaining
        resting.status = OrderStatus.cancelled
        resting.remaining = 0
        return CancelResult(order_id, OrderStatus.cancelled, remaining)

    # -- internals --------------------------------------------------------

    def _current_best_bid(self) -> int:
        while self._best_bid != _NO_BID and self._bids_qty[self._best_bid] == 0:
            self._best_bid -= 1
        return self._best_bid

    def _current_best_ask(self) -> int:
        while self._best_ask != _NO_ASK and self._asks_qty[self._best_ask] == 0:
            self._best_ask += 1
        return self._best_ask

    def _crosses(self, action: Action, limit_price: int) -> bool:
        if action == Action.buy:
            return self._current_best_ask() <= limit_price
        return self._current_best_bid() >= limit_price

    def _available_quantity(self, action: Action, limit_price: int) -> int:
        total = 0
        if action == Action.buy:
            price = self._current_best_ask()
            while price != _NO_ASK and price <= limit_price:
                total += self._asks_qty[price]
                price += 1
        else:
            price = self._current_best_bid()
            while price != _NO_BID and price >= limit_price:
                total += self._bids_qty[price]
                price -= 1
        return total

    def _insert(self, resting: RestingOrder) -> None:
        book = self._bids if resting.action == Action.buy else self._asks
        qty = self._bids_qty if resting.action == Action.buy else self._asks_qty
        book[resting.price_cents].append(resting)
        qty[resting.price_cents] += resting.remaining
        if resting.action == Action.buy:
            self._best_bid = max(self._best_bid, resting.price_cents)
        else:
            self._best_ask = min(self._best_ask, resting.price_cents)
        self._order_index[resting.order_id] = resting

    def _match(self, order: NewOrder, limit_price: int) -> list[Fill]:
        fills: list[Fill] = []
        remaining = order.quantity
        opposite_book = self._asks if order.action == Action.buy else self._bids
        opposite_qty = self._asks_qty if order.action == Action.buy else self._bids_qty

        while remaining > 0 and self._crosses(order.action, limit_price):
            price = self._current_best_ask() if order.action == Action.buy else self._current_best_bid()
            level = opposite_book[price]

            while level and remaining > 0:
                maker = level[0]

                if maker.status == OrderStatus.cancelled:
                    level.popleft()
                    continue

                if maker.owner_id == order.owner_id:
                    # Self-trade prevention: pull the resting order rather than match it.
                    level.popleft()
                    opposite_qty[price] -= maker.remaining
                    del self._order_index[maker.order_id]
                    maker.status = OrderStatus.cancelled
                    maker.remaining = 0
                    continue

                trade_qty = min(remaining, maker.remaining)
                fills.append(
                    Fill(
                        trade_id=uuid.uuid4(),
                        market_id=self.market_id,
                        price_cents=price,
                        quantity=trade_qty,
                        taker_order_id=order.order_id,
                        maker_order_id=maker.order_id,
                        taker_owner_id=order.owner_id,
                        maker_owner_id=maker.owner_id,
                    )
                )
                remaining -= trade_qty
                maker.remaining -= trade_qty
                opposite_qty[price] -= trade_qty

                if maker.remaining == 0:
                    maker.status = OrderStatus.filled
                    level.popleft()
                    del self._order_index[maker.order_id]
                # else: partial fill, maker stays at the front of the FIFO queue

            # Deque emptiness and the qty counter are always kept in lockstep
            # above, so once this level's deque is empty its qty is already 0
            # and the next _current_best_*() call will scan past it lazily.

        return fills
