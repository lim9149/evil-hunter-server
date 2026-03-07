import time
from core.redis_client import get_redis

MAX_SKEW_SEC = 30
NONCE_TTL_SEC = 60

def verify_replay_guard(account_id: str, ts: int, nonce: str) -> None:
    now = int(time.time())
    if abs(now - int(ts)) > MAX_SKEW_SEC:
        raise ValueError("request timestamp skew too large")

    r = get_redis()
    if r is None:
        # dev/test 환경: redis 없으면 noop (프로덕션에서는 redis 권장)
        return

    key = f"nonce:{account_id}:{nonce}"
    ok = r.setnx(key, "1")
    if not ok:
        raise ValueError("replayed request")
    r.expire(key, NONCE_TTL_SEC)