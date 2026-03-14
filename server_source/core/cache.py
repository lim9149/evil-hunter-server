# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
from __future__ import annotations

import threading
import time
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class SimpleTTLCache(Generic[T]):
    def __init__(self, ttl_sec: int = 30):
        self.ttl_sec = max(1, int(ttl_sec))
        self._lock = threading.RLock()
        self._value: T | None = None
        self._expires_at: float = 0.0

    def get_or_set(self, factory: Callable[[], T]) -> T:
        now = time.time()
        with self._lock:
            if self._value is not None and now < self._expires_at:
                return self._value
            self._value = factory()
            self._expires_at = now + self.ttl_sec
            return self._value

    def invalidate(self) -> None:
        with self._lock:
            self._value = None
            self._expires_at = 0.0
