# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
import os
import json
from typing import Any, Dict, Optional, Tuple

import jwt
from jwt.algorithms import RSAAlgorithm, ECAlgorithm

from core.security.jwks_client import JWKSClient


DEFAULT_APPLE_JWKS_URL = "https://appleid.apple.com/auth/keys"


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return bool(default)
    return str(v).strip().lower() in ("1", "true", "yes", "y", "on")


def allow_stub_verify() -> bool:
    """If False, verification failures must raise (prod hardening).

    Default True for dev convenience.
    Recommend setting ALLOW_STUB_VERIFY=0 in prod.
    """
    return _env_bool("ALLOW_STUB_VERIFY", True)


_apple_jwks_client: Optional[JWKSClient] = None


def _get_apple_jwks_client() -> JWKSClient:
    global _apple_jwks_client
    if _apple_jwks_client is None:
        url = os.getenv("APPLE_JWKS_URL", DEFAULT_APPLE_JWKS_URL)
        ttl = int(os.getenv("APPLE_JWKS_TTL_SEC", "3600"))
        # For offline tests: set APPLE_JWKS_JSON to a JWKS object.
        _apple_jwks_client = JWKSClient(
            jwks_url=url,
            cache_ttl_sec=ttl,
            inline_env_var="APPLE_JWKS_JSON",
        )
    return _apple_jwks_client


def _jwk_to_public_key(jwk: Dict[str, Any]):
    kty = str(jwk.get("kty", ""))
    # PyJWT's RSAAlgorithm/ECAlgorithm expect a JSON string for from_jwk.
    jwk_json = json.dumps(jwk)
    if kty == "RSA":
        return RSAAlgorithm.from_jwk(jwk_json)
    if kty == "EC":
        return ECAlgorithm.from_jwk(jwk_json)
    raise ValueError(f"unsupported kty: {kty}")


def verify_apple_signed_jws(raw: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """Verify Apple JWS signature if present in raw.

    Accepts common keys:
      - signedTransactionJws
      - signedPayload
      - jws / token

    We only guarantee signature verification + decode.
    (Claims such as aud/iss differ by Apple JWS type, so we don't enforce them here.)
    """
    token = (
        raw.get("signedTransactionJws")
        or raw.get("signedPayload")
        or raw.get("jws")
        or raw.get("token")
    )
    if not token or not isinstance(token, str):
        return False, "verified_stub", {"reason": "no jws in raw"}

    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        alg = header.get("alg")
        if not kid:
            raise ValueError("missing kid")

        client = _get_apple_jwks_client()
        jwk = client.find_jwk(str(kid))
        if jwk is None:
            # Key rotation: refresh once
            client.get_jwks(force_refresh=True)
            jwk = client.find_jwk(str(kid))
        if jwk is None:
            raise ValueError(f"kid not found in JWKS: {kid}")

        key = _jwk_to_public_key(jwk)

        decoded = jwt.decode(
            token,
            key=key,
            algorithms=[str(alg)] if alg else ["ES256", "RS256"],
            options={
                "verify_aud": False,
                "verify_iss": False,
            },
        )

        return True, "verified", {
            "kid": str(kid),
            "alg": str(alg) if alg else None,
            "claims": decoded,
        }
    except Exception as e:
        return False, "verified_stub", {"reason": str(e)}