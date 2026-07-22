import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Hashable

PRICE_MIN = 1
PRICE_MAX = 99


class Side(StrEnum):
    """Client-facing contract side. The engine internally trades only YES;
    NO orders are normalized to their complementary YES order at the
    boundary (see normalization.py)."""

    yes = "yes"
    no = "no"


class Action(StrEnum):
    buy = "buy"
    sell = "sell"


class OrderType(StrEnum):
    limit = "limit"
    market = "market"


class TimeInForce(StrEnum):
    gtc = "gtc"  # rest on the book until filled or cancelled
    ioc = "ioc"  # fill what's immediately available, cancel the remainder
    fok = "fok"  # fill the entire quantity immediately, or cancel all of it


class OrderStatus(StrEnum):
    open = "open"
    partially_filled = "partially_filled"
    filled = "filled"
    cancelled = "cancelled"
    not_found = "not_found"


@dataclass(frozen=True)
class NewOrder:
    """An order as submitted by a caller, in client-facing (YES/NO) terms."""

    market_id: str
    owner_id: Hashable
    side: Side
    action: Action
    order_type: OrderType
    quantity: int
    price_cents: int | None = None
    time_in_force: TimeInForce = TimeInForce.gtc
    order_id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class RestingOrder:
    """An order resting in the book, always normalized to YES terms."""

    order_id: uuid.UUID
    owner_id: Hashable
    action: Action
    price_cents: int
    original_quantity: int
    remaining: int
    status: OrderStatus
    sequence: int


@dataclass(frozen=True)
class Fill:
    trade_id: uuid.UUID
    market_id: str
    price_cents: int
    quantity: int
    taker_order_id: uuid.UUID
    maker_order_id: uuid.UUID
    taker_owner_id: Hashable
    maker_owner_id: Hashable


@dataclass(frozen=True)
class OrderResult:
    order_id: uuid.UUID
    status: OrderStatus
    fills: list[Fill]
    remaining_quantity: int


@dataclass(frozen=True)
class CancelResult:
    order_id: uuid.UUID
    status: OrderStatus
    remaining_quantity: int


@dataclass(frozen=True)
class PriceLevel:
    price_cents: int
    total_quantity: int


@dataclass(frozen=True)
class BookSnapshot:
    market_id: str
    bids: list[PriceLevel]
    asks: list[PriceLevel]
