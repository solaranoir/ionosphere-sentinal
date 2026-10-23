"""Simulated space-weather feeds.

Each class satisfies the HealthChecker protocol structurally.
None of them inherits from it.
"""

import asyncio
import random
from collections.abc import Iterable, Iterator

from sentinel.interfaces import FeedUnavailable


class SolarWindFeed:
    """Simulates NOAA SWPC real-time solar wind speed and planetary K-index."""

    def __init__(self, *, latency: float = 0.05, rng: random.Random | None = None) -> None:
        self.name = "solar-wind"
        self._latency = latency
        self._rng = rng or random.Random()

    async def check_health(self) -> str:
        await asyncio.sleep(self._latency)
        speed = self._rng.uniform(300, 700)
        kp = round(self._rng.uniform(0, 6) * 3) / 3  # Kp is reported in thirds
        return f"speed={speed:.0f} km/s, Kp={kp:.1f}"


class SunspotFeed:
    """Simulates the SILSO daily sunspot number, a proxy for solar cycle activity."""

    def __init__(self, *, latency: float = 0.05, rng: random.Random | None = None) -> None:
        self.name = "sunspot-number"
        self._latency = latency
        self._rng = rng or random.Random()

    async def check_health(self) -> str:
        await asyncio.sleep(self._latency)
        ssn = self._rng.randint(80, 180)
        return f"SSN={ssn}"


class IonosondeFeed:
    """Simulates a GIRO ionosonde reporting foF2, the F2-layer critical frequency.

    Real ionosondes drop offline often, so this feed fails intermittently.

    Pass `schedule` for deterministic behavior: an iterable of booleans where
    True means "fail this call". Once the schedule runs out, calls succeed.
    Without a schedule, each call fails with probability `failure_rate`.
    """

    # Rough multiplier from foF2 to the maximum usable frequency over a 3000 km path.
    M3000_FACTOR = 3.0

    def __init__(
        self,
        *,
        station: str = "BC840",
        schedule: Iterable[bool] | None = None,
        failure_rate: float = 0.4,
        latency: float = 0.05,
        rng: random.Random | None = None,
    ) -> None:
        self.name = f"ionosonde-{station}"
        self._schedule: Iterator[bool] | None = iter(schedule) if schedule is not None else None
        self._failure_rate = failure_rate
        self._latency = latency
        self._rng = rng or random.Random()
        self.calls = 0

    def _should_fail(self) -> bool:
        if self._schedule is not None:
            return next(self._schedule, False)
        return self._rng.random() < self._failure_rate

    async def check_health(self) -> str:
        self.calls += 1
        await asyncio.sleep(self._latency)
        if self._should_fail():
            raise FeedUnavailable(f"{self.name}: no ionogram received (call {self.calls})")
        fof2 = self._rng.uniform(4.0, 11.0)
        muf = fof2 * self.M3000_FACTOR
        return f"foF2={fof2:.1f} MHz, est. MUF(3000)={muf:.1f} MHz"
