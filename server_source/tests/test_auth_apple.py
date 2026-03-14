# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
import time

import jwt
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _apple_token(sub='apple-user-1', aud='com.murim.inn'):
    payload = {
        'iss': 'https://appleid.apple.com',
        'sub': sub,
        'aud': aud,
        'exp': int(time.time()) + 3600,
        'email': 'apple@example.com',
    }
    return jwt.encode(payload, 'unused', algorithm='HS256')


def test_oauth_apple_accepts_claims_valid_token(monkeypatch):
    monkeypatch.setenv('APPLE_CLIENT_ID', 'com.murim.inn')
    r = client.post('/auth/oauth/apple', json={'identityToken': _apple_token(), 'deviceId': 'apple-device-1'})
    assert r.status_code == 200
    data = r.json()
    assert 'accountId' in data
    assert 'accessToken' in data


def test_link_apple_requires_valid_claims(monkeypatch):
    monkeypatch.setenv('APPLE_CLIENT_ID', 'com.murim.inn')
    guest = client.post('/auth/guest', json={'deviceId': 'apple-link-dev'}).json()
    headers = {'Authorization': f"Bearer {guest['accessToken']}"}
    bad = client.post('/auth/link/apple', json={'identityToken': _apple_token(aud='wrong.aud')}, headers=headers)
    assert bad.status_code == 401
