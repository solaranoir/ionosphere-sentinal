"""Run all feed checks concurrently using structured concurrency."""

import asyncio
import random
from collections.abc import Sequence
from dataclasses import dataclass

from sentinel.feeds import IonosondeFeed, SolarWindFeed, SunspotFeed
from sentinel.interfaces import HealthChecker, HealthResult, Status
from sentinel.retry import RetryPolicy, Sleep, check_with_retry


@dataclass(frozen=True)
class HealthReport:
    results: tuple[HealthResult, ...]

    @property
    def healthy(self) -> bool:
        return all(r.status is Status.HEALTHY for r in self.results)

    @property
    def down(self) -> tuple[HealthResult, ...]:
        return tuple(r for r in self.results if r.status is Status.DOWN)


def default_feeds() -> list[HealthChecker]:
    return [SolarWindFeed(), SunspotFeed(), IonosondeFeed()]


async def run_health_checks(
    checkers: Sequence[HealthChecker],
    policy: RetryPolicy = RetryPolicy(),
    *,
    sleep: Sleep = asyncio.sleep,
    rng: random.Random | None = None,
) -> HealthReport:
    """Check every feed concurrently and return results in input order.

    Feed outages become DOWN results and never cancel sibling checks.
    Unexpected exceptions (bugs) cancel the group and surface as an
    ExceptionGroup, which is the behavior you want for bugs.
    """
    async with asyncio.TaskGroup() as tg:
        tasks = [
            tg.create_task(
                check_with_retry(checker, policy, sleep=sleep, rng=rng),
                name=checker.name,
            )
            for checker in checkers
        ]
    # Leaving the `async with` block guarantees every task has finished.
    return HealthReport(tuple(task.result() for task in tasks))
