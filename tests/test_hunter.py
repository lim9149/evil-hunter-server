from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_hunter_crud_multi_slot():
    h1 = {
        "hunterId": "h1", "accountId": "acc1", "slotIndex": 0, "name": "Alpha",
        "jobId":"novice","level":1,"exp":0,"powerScore":10,"hp":100,"atk":10,"defense":1
    }
    h2 = {
        "hunterId": "h2", "accountId": "acc1", "slotIndex": 1, "name": "Beta",
        "jobId":"novice","level":1,"exp":0,"powerScore":12,"hp":110,"atk":11,"defense":1
    }

    assert client.post("/hunters", json=h1).status_code == 200
    assert client.post("/hunters", json=h2).status_code == 200

    r = client.get("/hunters?accountId=acc1")
    assert r.status_code == 200
    assert len(r.json()) >= 2

    r = client.get("/hunters/h1")
    assert r.status_code == 200
    assert r.json()["name"] == "Alpha"

def test_hunter_slot_conflict():
    h1 = {"hunterId":"h10","accountId":"accX","slotIndex":0,"name":"One","jobId":"novice","level":1,"exp":0,"powerScore":1,"hp":100,"atk":10,"defense":0}
    h2 = {"hunterId":"h11","accountId":"accX","slotIndex":0,"name":"Two","jobId":"novice","level":1,"exp":0,"powerScore":1,"hp":100,"atk":10,"defense":0}
    assert client.post("/hunters", json=h1).status_code == 200
    r = client.post("/hunters", json=h2)
    assert r.status_code == 409