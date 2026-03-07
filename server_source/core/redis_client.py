import os
from typing import Optional, Any

def get_redis() -> Optional[Any]:
    """Return a redis client if redis is configured, else None.

    Env:
      - REDIS_URL (e.g. redis://localhost:6379/0)

    The project keeps Redis OPTIONAL so local dev/tests work without it.
    """
    url = os.getenv("REDIS_URL")
    if not url:
        return None
    try:
        import redis  # type: ignore
    except Exception:
        return None
    return redis.Redis.from_url(url, decode_responses=True)

def try_idempotent_lock(r: Any, key: str, ttl_sec: int = 86400) -> bool:
    """Best-effort idempotency lock using SET NX EX.

    Returns True if lock acquired (first call), False if already exists.
    """
    try:
        # redis-py: set(name, value, ex, nx)
        return bool(r.set(key, "1", ex=int(ttl_sec), nx=True))
    except Exception:
        # Redis down/unreachable -> treat as not acquired (we still have SQLite as truth)
        return False