# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
from __future__ import annotations

import os
import time
from typing import Any, Dict

import jwt

APPLE_ISSUER = "https://appleid.apple.com"


def verify_apple_identity_token(identity_token: str) -> Dict[str, Any]:
    token = str(identity_token or "").strip()
    if not token:
        raise ValueError("missing Apple identity token")

    try:
        payload = jwt.decode(token, options={"verify_signature": False, "verify_exp": False, "verify_aud": False})
    except Exception as exc:
        raise ValueError("invalid Apple identity token format") from exc

    issuer = str(payload.get("iss") or "")
    if issuer != APPLE_ISSUER:
        raise ValueError("invalid Apple issuer")

    provider_sub = str(payload.get("sub") or "").strip()
    if not provider_sub:
        raise ValueError("missing Apple subject")

    exp = int(payload.get("exp") or 0)
    if exp and exp < int(time.time()):
        raise ValueError("expired Apple identity token")

    aud = str(payload.get("aud") or "")
    expected_aud = str(os.getenv("APPLE_CLIENT_ID") or "").strip()
    if expected_aud and aud and aud != expected_aud:
        raise ValueError("invalid Apple audience")

    return {
        "sub": provider_sub,
        "email": payload.get("email"),
        "aud": aud,
        "iss": issuer,
        "verifiedMode": "claims_only",
    }
