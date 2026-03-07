from fastapi import Header, HTTPException
from typing import Optional

from core.security.jwt import decode_token, get_scope, get_subject

def _parse_bearer(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2:
        return None
    if parts[0].lower() != "bearer":
        return None
    return parts[1].strip()

from storage.sqlite_db import is_banned  # ✅ 상단 import에 추가

def require_player(authorization: Optional[str] = Header(default=None)) -> str:
    token = _parse_bearer(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="missing bearer token")
    try:
        decoded = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="invalid token")

    if get_scope(decoded) not in ("player", "admin"):
        raise HTTPException(status_code=403, detail="insufficient scope")

    sub = get_subject(decoded)
    if not sub:
        raise HTTPException(status_code=401, detail="invalid token sub")

    # ✅ 밴 차단
    if is_banned(sub):
        raise HTTPException(status_code=403, detail="banned account")

    return sub

def require_admin(authorization: Optional[str] = Header(default=None)) -> str:
    token = _parse_bearer(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="missing bearer token")
    try:
        decoded = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="invalid token")
    if get_scope(decoded) != "admin":
        raise HTTPException(status_code=403, detail="admin only")
    sub = get_subject(decoded)
    if not sub:
        raise HTTPException(status_code=401, detail="invalid token sub")
    return sub