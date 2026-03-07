from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_guest_login_returns_tokens():
    r = client.post("/auth/guest", json={"deviceId": "device-abc"})
    assert r.status_code == 200
    data = r.json()
    assert "accessToken" in data
    assert "refreshToken" in data