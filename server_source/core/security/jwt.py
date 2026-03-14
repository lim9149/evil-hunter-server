# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
import os
import time
from typing import Any, Dict, Optional

import jwt

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ISSUER = os.getenv("JWT_ISSUER", "evil-hunter-tycoon")
JWT_ALG = os.getenv("JWT_ALG", "HS256")

ACCESS_TTL_SEC = int(os.getenv("ACCESS_TTL_SEC", "900"))   # 15m
ADMIN_ACCESS_TTL_SEC = int(os.getenv("ADMIN_ACCESS_TTL_SEC", "900"))  # 15m

def _now() -> int:
    return int(time.time())

def create_access_token(account_id: str, scope: str = "player") -> str:
    now = _now()
    payload = {
        "iss": JWT_ISSUER,
        "sub": str(account_id),
        "scope": str(scope),
        "iat": now,
        "exp": now + ACCESS_TTL_SEC,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def create_admin_token(admin_id: str, scope: str = "admin") -> str:
    now = _now()
    payload = {
        "iss": JWT_ISSUER,
        "sub": str(admin_id),
        "scope": str(scope),
        "iat": now,
        "exp": now + ADMIN_ACCESS_TTL_SEC,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG], issuer=JWT_ISSUER)

def get_scope(decoded: Dict[str, Any]) -> str:
    return str(decoded.get("scope", ""))

def get_subject(decoded: Dict[str, Any]) -> Optional[str]:
    sub = decoded.get("sub")
    return str(sub) if sub is not None else None