import os
from fastapi.testclient import TestClient

# Ensure SQLite is isolated per test run (in-memory for pytest by default)
os.environ.setdefault("SQLITE_PATH", ":memory:")

from main import app

client = TestClient(app)

def _ensure_map_village():
    client.post("/maps", json={
        "mapId": "map1",
        "name": "Green Fields",
        "recommendedLevel": 1,
        "monsterPool": [],
        "offlineMultiplier": 1.0
    })
    client.post("/villages", json={
        "villageId": "v1",
        "name": "Starter Village",
        "taxRate": 0.0,
        "offlineStorageBonus": 0.0
    })

def test_offline_preview_basic():
    _ensure_map_village()
    req = {
        "hunterId": "h1",
        "lastActiveAtEpochSec": 0,
        "nowEpochSec": 60 * 60,  # 60분
        "mapId": "map1",
        "villageId": "v1",
        "baseGoldPerMin": 10,
        "baseExpPerMin": 5,
        "vipMultiplier": 1.0,
        "eventMultiplier": 1.0,
        "adminMultiplier": 1.0
    }
    r = client.post("/offline/preview", json=req)
    assert r.status_code == 200
    body = r.json()
    assert body["cappedMinutes"] == 60
    assert body["gold"] == 600
    assert body["exp"] == 300

def test_offline_collect_idempotent_and_applies_to_hunter():
    _ensure_map_village()
    # create hunter
    client.post("/hunters", json={
        "hunterId": "h1",
        "accountId": "a1",
        "slotIndex": 0,
        "name": "TestHunter",
        "jobId": "novice",
        "level": 1,
        "exp": 0,
        "gold": 0,
        "powerScore": 1.0,
        "hp": 100.0,
        "atk": 10.0,
        "defense": 0.0
    })

    req = {
        "hunterId": "h1",
        "lastActiveAtEpochSec": 0,
        "nowEpochSec": 60 * 60,  # 60분
        "mapId": "map1",
        "villageId": "v1",
        "baseGoldPerMin": 10,
        "baseExpPerMin": 5,
        "vipMultiplier": 1.0,
        "eventMultiplier": 1.0,
        "adminMultiplier": 1.0
    }

    r1 = client.post("/offline/collect", json=req)
    assert r1.status_code == 200
    body1 = r1.json()
    assert body1["collected"]["gold"] == 600
    assert body1["collected"]["exp"] == 300

    # duplicate call with same nowEpochSec should not double pay
    r2 = client.post("/offline/collect", json=req)
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["collected"]["gold"] == 600
    assert body2["collected"]["exp"] == 300
    assert "already_collected" in body2["note"]

    # hunter should have received reward only once
    h = client.get("/hunters/h1").json()
    assert h["gold"] == 600
    assert h["exp"] == 300