import os
from fastapi.testclient import TestClient

# Isolate SQLite for test run
os.environ.setdefault("SQLITE_PATH", ":memory:")

from main import app

client = TestClient(app)


def _upsert_hunter():
    client.post(
        "/hunters",
        json={
            "hunterId": "h1",
            "accountId": "a1",
            "slotIndex": 0,
            "name": "BossHunter",
            "jobId": "novice",
            "level": 1,
            "exp": 0,
            "gold": 0,
            "gems": 0,
            "powerScore": 1.0,
            "hp": 100.0,
            "atk": 10.0,
            "defense": 0.0,
        },
    )


def test_worldboss_claim_idempotent_and_admin_multiplier():
    _upsert_hunter()

    # upsert boss
    client.post(
        "/worldbosses",
        json={
            "bossId": "wb1",
            "name": "Ancient Dragon",
            "maxHp": 1000000,
            "difficulty": 5,
            "baseGold": 1000,
            "baseExp": 500,
            "baseGems": 10,
        },
    )

    # enable admin mode for worldboss rewards
    client.post(
        "/admin/modes",
        json={
            "key": "WORLD_BOSS_REWARD_MULTIPLIER",
            "enabled": True,
            "multiplier": 2.0,
        },
    )

    payload = {"hunterId": "h1", "bossId": "wb1", "seasonId": "s1", "rank": 1}
    r1 = client.post("/worldboss/claim", json=payload)
    assert r1.status_code == 200
    body1 = r1.json()
    # rank1 multiplier 1.0, admin 2.0
    assert body1["granted"]["gold"] == 2000
    assert body1["granted"]["exp"] == 1000
    assert body1["granted"]["gems"] == 20

    # duplicate claim should return same and not double-add to hunter
    r2 = client.post("/worldboss/claim", json=payload)
    assert r2.status_code == 200
    body2 = r2.json()
    assert "already_claimed" in body2["note"]
    assert body2["granted"] == body1["granted"]

    h = client.get("/hunters/h1").json()
    assert h["gold"] == 2000
    assert h["exp"] == 1000
    assert h["gems"] == 20


def test_pvp_claim_idempotent_default_admin_disabled():
    _upsert_hunter()

    # upsert season
    client.post(
        "/pvp/seasons",
        json={
            "seasonId": "p1",
            "name": "Preseason",
            "baseGold": 500,
            "baseExp": 250,
            "baseGems": 5,
        },
    )

    # ensure admin mode disabled or absent
    client.post(
        "/admin/modes",
        json={
            "key": "PVP_REWARD_MULTIPLIER",
            "enabled": False,
            "multiplier": 3.0,
        },
    )

    payload = {"hunterId": "h1", "seasonId": "p1", "rank": 11}
    r1 = client.post("/pvp/claim", json=payload)
    assert r1.status_code == 200
    body1 = r1.json()
    # rank 11 -> 0.4 multiplier, admin disabled -> 1.0
    assert body1["granted"]["gold"] == 200
    assert body1["granted"]["exp"] == 100
    assert body1["granted"]["gems"] == 2

    r2 = client.post("/pvp/claim", json=payload)
    assert r2.status_code == 200
    assert "already_claimed" in r2.json()["note"]