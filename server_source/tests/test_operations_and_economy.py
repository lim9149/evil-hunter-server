from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _create_hunter(hunter_id: str, account_id: str = "acc_ops"):
    payload = {
        "hunterId": hunter_id, "accountId": account_id, "slotIndex": 0 if hunter_id.endswith("1") else 1,
        "name": hunter_id, "jobId": "novice", "level": 1, "exp": 0, "powerScore": 64,
        "hp": 120, "atk": 18, "defense": 4
    }
    assert client.post("/hunters", json=payload).status_code == 200


def test_hunter_operation_plan_and_config():
    _create_hunter("ops_1")
    res = client.post("/hunters/ops_1/configure-operations", json={
        "operationStyle": "shadow",
        "restDiscipline": "lavish",
        "trainingFocus": "footwork",
        "morale": 71,
        "fatigue": 14,
        "bondFacilityId": "moon_spring",
    })
    assert res.status_code == 200
    body = res.json()
    assert body["operationStyle"] == "shadow"
    assert body["recommendedFacilityId"] == "moon_spring"
    assert body["combatProfile"]["tempoMultiplier"] > 1.0


def test_world_economy_simulation():
    _create_hunter("ops_2")
    client.post("/hunters/ops_2/configure-operations", json={"operationStyle": "support", "restDiscipline": "measured"})
    res = client.post("/world/economy/simulate", json={
        "accountId": "acc_ops",
        "simulatedHours": 12,
        "battleMinutesPerLoop": 4.5,
        "restMinutesPerLoop": 2.5,
        "crowdingFactor": 0.2,
    })
    assert res.status_code == 200
    body = res.json()
    assert body["hunterCount"] >= 2
    assert body["summary"]["totalEstimatedGold"] > 0
    assert len(body["designHooks"]) >= 1
