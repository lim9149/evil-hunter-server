
from fastapi.testclient import TestClient

from main import app
from storage.repo_registry import hunter_repo


client = TestClient(app)


def setup_function():
    hunter_repo.items.clear()


def _make_hunter(hunter_id: str = "loop_1", account_id: str = "acc_loop"):
    payload = {
        "hunterId": hunter_id,
        "accountId": account_id,
        "slotIndex": 0 if hunter_id.endswith("1") else 1,
        "name": "운영헌터",
        "jobId": "novice",
        "level": 30,
        "exp": 0,
        "powerScore": 80,
        "hp": 100,
        "atk": 20,
        "defense": 8,
        "gold": 500,
        "loyalty": 40,
        "stamina": 80,
        "satiety": 80,
        "insight": 30,
    }
    assert client.post("/hunters", json=payload).status_code == 200


def test_settle_return_updates_operator_summary_and_logs():
    _make_hunter("loop_1")
    r = client.post("/hunters/loop_1/settle-return", json={
        "foundGold": 1000,
        "foundMaterials": {"herb": 4, "iron_ore": 3},
        "taxRate": 0.12,
        "loopsCompleted": 3,
        "fatigueDelta": 9,
        "satietyDelta": -12,
        "durabilityDelta": -7,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["resultCode"] == "OK_SETTLED"
    assert body["payload"]["operatorShareGold"] == 120

    s = client.get("/world/operator/summary", params={"accountId": "acc_loop"})
    assert s.status_code == 200
    summary = s.json()
    assert summary["treasury"]["operatorGold"] >= 120
    assert summary["inventories"]["herb"] == 4
    assert len(summary["recentLogs"]) >= 1


def test_craft_sell_train_and_reforge_flow():
    _make_hunter("loop_2")
    assert client.post("/hunters/loop_2/settle-return", json={
        "foundGold": 5000,
        "foundMaterials": {"herb": 10, "iron_ore": 10, "wood": 3},
        "taxRate": 0.2,
        "loopsCompleted": 5,
        "fatigueDelta": 8,
        "satietyDelta": -10,
        "durabilityDelta": -6,
    }).status_code == 200

    craft = client.post("/world/operator/craft", json={"accountId": "acc_loop", "recipeId": "potion_basic", "quantity": 3})
    assert craft.status_code == 200
    assert craft.json()["resultCode"] == "OK_CRAFTED"

    sell = client.post("/world/operator/sell", json={"accountId": "acc_loop", "itemId": "potion_basic", "quantity": 2, "unitPrice": 44})
    assert sell.status_code == 200
    assert sell.json()["resultCode"] == "OK_SOLD"

    train = client.post("/hunters/loop_2/train", json={"packageId": "mind", "intensity": "standard"})
    assert train.status_code == 200
    assert train.json()["resultCode"] == "OK_TRAINED"

    reforge_fail = client.post("/hunters/loop_2/body-reforge", json={"consumeGold": 100, "consumeMaterials": {"rebirth_pill": 1}})
    assert reforge_fail.status_code == 200
    assert reforge_fail.json()["ok"] is False
    assert reforge_fail.json()["resultCode"] in {"ERR_TRAINING_LOCKED", "ERR_LOW_LEVEL", "ERR_LOW_LOYALTY"}

    # make eligible
    client.post("/hunters", json={
        "hunterId": "loop_2",
        "accountId": "acc_loop",
        "slotIndex": 1,
        "name": "운영헌터",
        "jobId": "novice",
        "level": 40,
        "exp": 0,
        "powerScore": 120,
        "hp": 100,
        "atk": 20,
        "defense": 8,
        "gold": 1000,
        "loyalty": 80,
        "stamina": 80,
        "satiety": 80,
        "insight": 45,
        "bodyReforgeStage": 0,
    })
    reforge_ok = client.post("/hunters/loop_2/body-reforge", json={"consumeGold": 100, "consumeMaterials": {"rebirth_pill": 1}})
    assert reforge_ok.status_code == 200
    assert reforge_ok.json()["resultCode"] == "OK_REFORGED"
