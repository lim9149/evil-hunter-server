from fastapi.testclient import TestClient
from main import app
import google.oauth2.id_token as google_id_token

client = TestClient(app)


def test_oauth_google_creates_account(monkeypatch):
    def fake_verify(token, req, aud=None):
        return {"sub": "google-sub-1", "email": "g1@example.com"}

    monkeypatch.setattr(google_id_token, "verify_oauth2_token", fake_verify)
    r = client.post("/auth/oauth/google", json={"idToken": "fake-token", "deviceId": "device-1"})
    assert r.status_code == 200
    data = r.json()
    assert "accessToken" in data
    assert "refreshToken" in data
    assert "accountId" in data


def test_link_google_links_identity(monkeypatch):
    def fake_verify(token, req, aud=None):
        return {"sub": "google-sub-2", "email": "g2@example.com"}

    monkeypatch.setattr(google_id_token, "verify_oauth2_token", fake_verify)
    r = client.post("/auth/guest", json={"deviceId": "dev-link"})
    assert r.status_code == 200
    guest = r.json()
    access = guest["accessToken"]
    headers = {"Authorization": f"Bearer {access}"}
    r2 = client.post("/auth/link/google", json={"idToken": "some-token"}, headers=headers)
    assert r2.status_code == 200
    assert r2.json() == {"ok": True}
