"""Quick simulation for /offline/collect idempotency.

Run:
  python scripts/sim_offline_collect_idempotent.py
"""
import time
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def upsert_prereqs():
    client.post("/maps", json={
        "mapId": "map1",
        "name": "Green Fields",
        "recommendedLevel": 1,
        "monsterPool": [],
        "offlineMultiplier": 1.0,
    })
    client.post("/villages", json={
        "villageId": "v1",
        "name": "Starter Village",
        "taxRate": 0.0,
        "offlineStorageBonus": 0.0,
    })
    client.post("/hunters", json={
        "hunterId": "h1",
        "accountId": "a1",
        "slotIndex": 0,
        "name": "SimHunter",
        "gold": 0,
        "exp": 0,
        "level": 1,
        "jobId": "novice",
        "powerScore": 1.0,
        "hp": 100.0,
        "atk": 10.0,
        "defense": 0.0,
    })

if __name__ == "__main__":
    upsert_prereqs()

    now_epoch = int(time.time())
    last_epoch = now_epoch - 60 * 60  # 60분

    payload = {
        "hunterId": "h1",
        "lastActiveAtEpochSec": last_epoch,
        "nowEpochSec": now_epoch,
        "mapId": "map1",
        "villageId": "v1",
        "baseGoldPerMin": 10,
        "baseExpPerMin": 5,
        "vipMultiplier": 1.0,
        "eventMultiplier": 1.0,
        "adminMultiplier": 1.0
    }

    r1 = client.post("/offline/collect", json=payload).json()
    r2 = client.post("/offline/collect", json=payload).json()
    hunter = client.get("/hunters/h1").json()

    print("1st collect:", r1)
    print("2nd collect (duplicate):", r2)
    print("hunter after:", hunter)