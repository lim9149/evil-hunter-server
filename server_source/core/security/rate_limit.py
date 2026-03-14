# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
import time
from typing import Dict, Tuple

from core.redis_client import get_redis

_mem: Dict[str, Tuple[int, float]] = {}  # key -> (count, reset_epoch)

def _now() -> float:
    return time.time()

def hit_rate_limit(key: str, limit: int, window_sec: int) -> bool:
    """Return True if allowed, False if rate-limited."""
    r = get_redis()
    if r is not None:
        rk = f"rl:{key}:{int(_now() // window_sec)}"
        n = r.incr(rk)
        if n == 1:
            r.expire(rk, window_sec + 1)
        return n <= limit

    now = _now()
    cnt, reset = _mem.get(key, (0, now + window_sec))
    if now > reset:
        cnt, reset = 0, now + window_sec
    cnt += 1
    _mem[key] = (cnt, reset)
    return cnt <= limit