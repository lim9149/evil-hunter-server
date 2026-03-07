from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def _guest_token():
    r = client.post("/auth/guest", json={"deviceId": "device-iap"})
    return r.json()["accessToken"]

def test_iap_verify_idempotent_grant_once():
    access = _guest_token()
    headers={"Authorization": f"Bearer {access}"}

    payload={"productId":"gems_100","purchaseToken":"ptok","txId":"order-1","raw":{"x":1}}
    r1 = client.post("/iap/google/verify", json=payload, headers=headers)
    assert r1.status_code == 200
    assert r1.json()["granted"] is True

    r2 = client.post("/iap/google/verify", json=payload, headers=headers)
    assert r2.status_code == 200
    assert r2.json()["granted"] is False