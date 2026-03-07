"""Minimal fallback for tests/dev when google-auth is unavailable."""

def verify_oauth2_token(token, request, audience=None):
    raise RuntimeError("google-auth is not installed in this environment")
