"""Retry with exponential backoff and jitter."""

import asyncio
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from sentinel.interfaces import FeedUnavailable, HealthChecker, HealthResult, Status

Sleep = Callable[[float], Awaitable[None]]


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay: float = 0.1       # seconds before the first retry
    multiplier: float = 2.0       # 0.1s -> 0.2s -> 0.4s ...
    max_delay: float = 2.0        # ceiling so backoff can't grow forever
    jitter: float = 0.1           # +/- 10% randomization
    attempt_timeout: float = 1.0  # per-attempt deadline

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if not 0 <= self.jitter < 1:
            raise ValueError("jitter must be in [0, 1)")

    def delay_for(self, retry_number: int, rng: random.Random) -> float:
        """Seconds to wait before retry `retry_number` (1 = first retry)."""
        delay = min(self.base_delay * self.multiplier ** (retry_number - 1), self.max_delay)
        if self.jitter:
            delay *= rng.uniform(1 - self.jitter, 1 + self.jitter)
        return delay


async def check_with_retry(
    checker: HealthChecker,
    policy: RetryPolicy = RetryPolicy(),
    *,
    sleep: Sleep = asyncio.sleep,
    rng: random.Random | None = None,
) -> HealthResult:
    """Run checker.check_health(), retrying transient failures per `policy`.

    Never raises for FeedUnavailable or timeouts: exhausting retries
    produces a DOWN result so sibling checks keep running.
    """
    rng = rng or random.Random()
    last_error = ""

    for attempt in range(1, policy.max_attempts + 1):
        try:
            async with asyncio.timeout(policy.attempt_timeout):
                detail = await checker.check_health()
        except TimeoutError:
            last_error = f"timed out after {policy.attempt_timeout}s"
        except FeedUnavailable as exc:
            last_error = str(exc)
        else:
            return HealthResult(checker.name, Status.HEALTHY, attempt, detail)

        if attempt < policy.max_attempts:
            await sleep(policy.delay_for(attempt, rng))

    return HealthResult(checker.name, Status.DOWN, policy.max_attempts, last_error)
