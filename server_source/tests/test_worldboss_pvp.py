# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
import os
from fastapi.testclient import TestClient

# Isolate SQLite for test run (in-memory)
os.environ.setdefault("SQLITE_PATH", ":memory:")

from main import app

client = TestClient(app)


def _upsert_hunter(hunter_id: str = "h1"):
    client.post(
        "/hunters",
        json={
            "hunterId": hunter_id,
            "accountId": f"a_{hunter_id}",
            "slotIndex": 0,
            "name": f"BossHunter_{hunter_id}",
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


def _upsert_worldboss(boss_id: str = "wb1"):
    client.post(
        "/worldbosses",
        json={
            "bossId": boss_id,
            "name": f"Ancient_{boss_id}",
            "maxHp": 1000000,
            "difficulty": 5,
            "baseGold": 1000,
            "baseExp": 500,
            "baseGems": 10,
        },
    )


def _upsert_pvp_season(season_id: str = "p1"):
    client.post(
        "/pvp/seasons",
        json={
            "seasonId": season_id,
            "name": f"Season_{season_id}",
            "baseGold": 500,
            "baseExp": 250,
            "baseGems": 5,
        },
    )


def _set_admin_mode(key: str, enabled: bool, multiplier: float):
    client.post(
        "/admin/modes",
        json={"key": key, "enabled": enabled, "multiplier": multiplier},
    )


def test_worldboss_claim_idempotent_and_admin_multiplier():
    hunter_id = "h_wb_idem"
    boss_id = "wb_idem"
    season_id = "s_wb_idem"

    _upsert_hunter(hunter_id)
    _upsert_worldboss(boss_id)

    _set_admin_mode("WORLD_BOSS_REWARD_MULTIPLIER", True, 2.0)

    payload = {"hunterId": hunter_id, "bossId": boss_id, "seasonId": season_id, "rank": 1}
    r1 = client.post("/worldboss/claim", json=payload)
    assert r1.status_code == 200
    body1 = r1.json()

    assert body1["granted"]["gold"] == 2000
    assert body1["granted"]["exp"] == 1000
    assert body1["granted"]["gems"] == 20

    r2 = client.post("/worldboss/claim", json=payload)
    assert r2.status_code == 200
    body2 = r2.json()
    assert "already_claimed" in body2["note"]
    assert body2["granted"] == body1["granted"]

    h = client.get(f"/hunters/{hunter_id}").json()
    assert h["gold"] == 2000
    assert h["exp"] == 1000
    assert h["gems"] == 20


def test_worldboss_claim_override_fields_are_ignored():
    hunter_id = "h_wb_override"
    boss_id = "wb_override"
    season_id = "s_wb_override"

    _upsert_hunter(hunter_id)
    _upsert_worldboss(boss_id)

    _set_admin_mode("WORLD_BOSS_REWARD_MULTIPLIER", True, 2.0)

    # attempt to spoof multipliers via extra JSON keys (must not change result)
    payload = {
        "hunterId": hunter_id,
        "bossId": boss_id,
        "seasonId": season_id,
        "rank": 1,
        "adminMultiplier": 9999,
        "rankMultiplier": 9999,
        "overrideMultiplier": 9999,
        "multiplier": 9999,
    }
    r = client.post("/worldboss/claim", json=payload)
    assert r.status_code == 200
    body = r.json()

    assert body["granted"]["gold"] == 2000
    assert body["granted"]["exp"] == 1000
    assert body["granted"]["gems"] == 20


def test_pvp_claim_idempotent_and_override_ignored_admin_disabled():
    hunter_id = "h_pvp"
    season_id = "p_override"

    _upsert_hunter(hunter_id)
    _upsert_pvp_season(season_id)

    _set_admin_mode("PVP_REWARD_MULTIPLIER", False, 3.0)

    payload = {
        "hunterId": hunter_id,
        "seasonId": season_id,
        "rank": 11,
        "adminMultiplier": 9999,
        "overrideMultiplier": 9999,
    }
    r1 = client.post("/pvp/claim", json=payload)
    assert r1.status_code == 200
    body1 = r1.json()

    assert body1["granted"]["gold"] == 200
    assert body1["granted"]["exp"] == 100
    assert body1["granted"]["gems"] == 2

    r2 = client.post("/pvp/claim", json={"hunterId": hunter_id, "seasonId": season_id, "rank": 11})
    assert r2.status_code == 200
    assert "already_claimed" in r2.json()["note"]

    h = client.get(f"/hunters/{hunter_id}").json()
    assert h["gold"] == 200
    assert h["exp"] == 100
    assert h["gems"] == 2


def test_reward_tier_override_server_side_affects_claim():
    hunter_id = "h_tier_override"
    boss_id = "wb_tier_override"
    season_id = "s_tier_override"

    _upsert_hunter(hunter_id)
    _upsert_worldboss(boss_id)

    _set_admin_mode("WORLD_BOSS_REWARD_MULTIPLIER", True, 2.0)

    # Override rank 1 multiplier (server-side)
    r = client.post(
        "/rewards/tiers",
        json={"kind": "worldboss", "rankMin": 1, "rankMax": 1, "multiplier": 3.0},
    )
    assert r.status_code == 200

    payload = {"hunterId": hunter_id, "bossId": boss_id, "seasonId": season_id, "rank": 1}
    res = client.post("/worldboss/claim", json=payload)
    assert res.status_code == 200
    body = res.json()

    # base(1000/500/10) * rank(3.0) * admin(2.0)
    assert body["granted"]["gold"] == 6000
    assert body["granted"]["exp"] == 3000
    assert body["granted"]["gems"] == 60