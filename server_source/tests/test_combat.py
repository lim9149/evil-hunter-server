from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_combat_fight_uses_shared_registry_repos():
    """Combat must see hunters/monsters created by CRUD routers (shared repo_registry)."""

    # seed monster
    m = {
        "monsterId": "m_combat",
        "name": "Slime",
        "level": 1,
        "hp": 50,
        "atk": 5,
        "defense": 0,
        "goldPerMin": 2,
        "expPerMin": 1,
    }
    assert client.post("/monsters", json=m).status_code == 200

    # seed hunter
    h = {
        "hunterId": "h_combat",
        "accountId": "acc_combat",
        "slotIndex": 0,
        "name": "Alpha",
        "jobId": "novice",
        "level": 1,
        "exp": 0,
        "powerScore": 10,
        "hp": 100,
        "atk": 10,
        "defense": 1,
    }
    assert client.post("/hunters", json=h).status_code == 200

    # fight
    req = {"hunterId": "h_combat", "monsterId": "m_combat", "buffs": {"atkMul": 1.0}}
    r = client.post("/combat/fight", json=req)
    assert r.status_code == 200

    body = r.json()
    assert body["hunterId"] == "h_combat"
    assert body["monsterId"] == "m_combat"
    assert body["damagePerHit"] >= 1
    assert body["hitsToKill"] >= 1
    assert body["totalSec"] > 0