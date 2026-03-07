"""Simple local simulation for the combat loop.

Run:
  python -m scripts.sim_combat

What it does:
  1) Upserts a demo monster + hunter via API routes (shared repo_registry).
  2) Calls /combat/fight and prints the result.
"""

from fastapi.testclient import TestClient
from main import app

def main() -> None:
    client = TestClient(app)

    monster = {
        "monsterId": "m_sim_1",
        "name": "Training Slime",
        "level": 1,
        "hp": 120,
        "atk": 8,
        "defense": 1,
        "goldPerMin": 3,
        "expPerMin": 2,
    }
    hunter = {
        "hunterId": "h_sim_1",
        "accountId": "acc_sim",
        "slotIndex": 0,
        "name": "SimHunter",
        "jobId": "novice",
        "level": 1,
        "exp": 0,
        "powerScore": 15,
        "hp": 100,
        "atk": 12,
        "defense": 2,
    }

    print("[1] upsert monster")
    print(client.post("/monsters", json=monster).json())

    print("[2] upsert hunter")
    print(client.post("/hunters", json=hunter).json())

    print("[3] fight")
    fight_req = {"hunterId": "h_sim_1", "monsterId": "m_sim_1", "buffs": {"atkMul": 1.0}}
    res = client.post("/combat/fight", json=fight_req)
    print(res.status_code)
    print(res.json())

if __name__ == "__main__":
    main()