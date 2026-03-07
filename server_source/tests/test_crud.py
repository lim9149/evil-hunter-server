from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_monster_crud():
    m = {
        "monsterId": "m1", "name": "Slime", "level": 1,
        "hp": 100, "atk": 10, "defense": 0,
        "goldPerMin": 2, "expPerMin": 1
    }
    r = client.post("/monsters", json=m)
    assert r.status_code == 200

    r = client.get("/monsters/m1")
    assert r.status_code == 200
    assert r.json()["name"] == "Slime"

    r = client.get("/monsters")
    assert r.status_code == 200
    assert len(r.json()) >= 1

    r = client.delete("/monsters/m1")
    assert r.status_code == 200

def test_map_and_village_crud():
    mp = {"mapId":"map1","name":"Forest","recommendedLevel":1,"monsterPool":["m1"],"offlineMultiplier":1.2}
    v = {"villageId":"v1","name":"StarterTown","taxRate":0.05,"offlineStorageBonus":0.2}

    assert client.post("/maps", json=mp).status_code == 200
    assert client.get("/maps/map1").status_code == 200

    assert client.post("/villages", json=v).status_code == 200
    assert client.get("/villages/v1").status_code == 200