"""Test/dev compatibility shims for optional Google auth dependencies.

If google-auth is not installed, provide minimal modules used by the app/tests:
- google.oauth2.id_token.verify_oauth2_token
- google.auth.transport.requests.Request

When google-auth is installed, this file stays out of the way.
"""
from __future__ import annotations

import importlib
import sys
import types


def _ensure_module(name: str) -> types.ModuleType:
    mod = sys.modules.get(name)
    if mod is None:
        mod = types.ModuleType(name)
        sys.modules[name] = mod
    return mod


try:
    importlib.import_module("google.oauth2.id_token")
    importlib.import_module("google.auth.transport.requests")
except Exception:
    google = _ensure_module("google")
    oauth2 = _ensure_module("google.oauth2")
    auth = _ensure_module("google.auth")
    transport = _ensure_module("google.auth.transport")

    id_token = _ensure_module("google.oauth2.id_token")
    requests_mod = _ensure_module("google.auth.transport.requests")

    class Request:  # pragma: no cover - trivial shim
        pass

    def verify_oauth2_token(token, request, audience=None):
        raise RuntimeError(
            "google-auth is not installed; verify_oauth2_token is unavailable in this environment"
        )

    id_token.verify_oauth2_token = verify_oauth2_token
    requests_mod.Request = Request

    google.oauth2 = oauth2
    google.auth = auth
    oauth2.id_token = id_token
    auth.transport = transport
    transport.requests = requests_mod
