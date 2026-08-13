from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Timer:
    name: str = "timer"
    start: float = field(default=0.0, init=False)
    elapsed: float = field(default=0.0, init=False)

    def __enter__(self) -> "Timer":
        self.start = time.monotonic()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.elapsed = time.monotonic() - self.start


@dataclass
class RateLimiter:
    period_s: float
    _last_time: float = field(default=0.0, init=False)

    def ready(self, now: float | None = None) -> bool:
        current = time.monotonic() if now is None else now
        if current - self._last_time >= self.period_s:
            self._last_time = current
            return True
        return False


def wait_until(predicate: Callable[[], bool], timeout_s: float, interval_s: float = 0.01) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval_s)
    return predicate()
