from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_refresh_rotation_revokes_old():
    r = client.post("/auth/guest", json={"deviceId": "device-xyz"})
    assert r.status_code == 200
    refresh = r.json()["refreshToken"]

    r2 = client.post("/auth/refresh", json={"refreshToken": refresh, "deviceId": "device-xyz"})
    assert r2.status_code == 200
    new_refresh = r2.json()["refreshToken"]
    assert new_refresh != refresh

    r3 = client.post("/auth/refresh", json={"refreshToken": refresh, "deviceId": "device-xyz"})
    assert r3.status_code == 401