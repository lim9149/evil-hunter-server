# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
import json
import jwt
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def _guest_token():
    r = client.post("/auth/guest", json={"deviceId": "device-iap-apple"})
    return r.json()["accessToken"]


def test_apple_iap_verify_accepts_signed_jws_when_jwks_inline(monkeypatch):
    # Generate an EC key and publish as JWKS via env for offline tests.
    priv = ec.generate_private_key(ec.SECP256R1())
    pub = priv.public_key()

    kid = "test-kid-1"
    jwk = {
        "kty": "EC",
        "crv": "P-256",
        "x": jwt.utils.base64url_encode(pub.public_numbers().x.to_bytes(32, "big")).decode(),
        "y": jwt.utils.base64url_encode(pub.public_numbers().y.to_bytes(32, "big")).decode(),
        "use": "sig",
        "kid": kid,
        "alg": "ES256",
    }

    jwks = {"keys": [jwk]}
    monkeypatch.setenv("APPLE_JWKS_JSON", json.dumps(jwks))
    monkeypatch.setenv("ALLOW_STUB_VERIFY", "0")

    private_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    token = jwt.encode(
        {"bundleId": "com.test.game", "tx": "t1"},
        private_pem,
        algorithm="ES256",
        headers={"kid": kid},
    )

    access = _guest_token()
    headers = {"Authorization": f"Bearer {access}"}

    payload = {"productId": "gems_100", "txId": "apple-order-1", "raw": {"signedTransactionJws": token}}
    r = client.post("/iap/apple/verify", json=payload, headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "verified"
    assert "verify" in body