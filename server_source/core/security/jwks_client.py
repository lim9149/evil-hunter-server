# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx


def _now() -> int:
    return int(time.time())


@dataclass
class JWKSCache:
    jwks: Dict[str, Any]
    fetched_at: int


class JWKSClient:
    """Small JWKS fetcher with in-memory cache.

    - Network fetch uses httpx (timeout, basic hardening).
    - Optional inline JWKS JSON via env var for offline tests.
    """

    def __init__(
        self,
        jwks_url: str,
        cache_ttl_sec: int = 3600,
        inline_env_var: Optional[str] = None,
    ) -> None:
        self.jwks_url = str(jwks_url)
        self.cache_ttl_sec = int(cache_ttl_sec)
        self.inline_env_var = str(inline_env_var) if inline_env_var else None
        self._cache: Optional[JWKSCache] = None

    def _load_inline(self) -> Optional[Dict[str, Any]]:
        if not self.inline_env_var:
            return None
        raw = os.getenv(self.inline_env_var)
        if not raw:
            return None
        try:
            return json.loads(raw)
        except Exception as e:
            raise ValueError(f"invalid inline JWKS JSON in {self.inline_env_var}: {e}")

    def _fetch_remote(self) -> Dict[str, Any]:
        with httpx.Client(timeout=5.0, follow_redirects=True) as client:
            r = client.get(self.jwks_url)
            r.raise_for_status()
            return r.json()

    def get_jwks(self, force_refresh: bool = False) -> Dict[str, Any]:
        inline = self._load_inline()
        if inline is not None:
            self._cache = JWKSCache(jwks=inline, fetched_at=_now())
            return inline

        if not force_refresh and self._cache is not None:
            if (_now() - self._cache.fetched_at) < self.cache_ttl_sec:
                return self._cache.jwks

        jwks = self._fetch_remote()
        self._cache = JWKSCache(jwks=jwks, fetched_at=_now())
        return jwks

    def find_jwk(self, kid: str) -> Optional[Dict[str, Any]]:
        jwks = self.get_jwks()
        keys = jwks.get("keys")
        if not isinstance(keys, list):
            return None
        for k in keys:
            if isinstance(k, dict) and str(k.get("kid")) == str(kid):
                return k
        return None