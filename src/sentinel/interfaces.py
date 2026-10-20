"""Core contracts shared by every feed and the monitor."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class FeedUnavailable(ConnectionError):
    """Raised when a data feed can't be reached or returns unusable data."""


class Status(StrEnum):
    HEALTHY = "healthy"
    DOWN = "down"


@dataclass(frozen=True)
class HealthResult:
    feed: str
    status: Status
    attempts: int
    detail: str = ""


class HealthChecker(Protocol):
    """Anything with a name and an async check_health() is a valid feed.

    Implementations return a short human-readable reading on success
    (e.g. "foF2=7.2 MHz") and raise FeedUnavailable on failure.
    """

    name: str

    async def check_health(self) -> str: ...
