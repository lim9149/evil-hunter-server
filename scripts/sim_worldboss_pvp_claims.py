"""Quick simulation for worldboss/pvp idempotent claims + admin mode multipliers.

Run:
  python scripts/sim_worldboss_pvp_claims.py
"""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def seed():
    client.post(
        "/hunters",
        json={
            "hunterId": "h1",
            "accountId": "a1",
            "slotIndex": 0,
            "name": "SimHunter",
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


def main():
    seed()

    # enable admin multipliers
    client.post("/admin/modes", json={"key": "WORLD_BOSS_REWARD_MULTIPLIER", "enabled": True, "multiplier": 2.0})
    client.post("/admin/modes", json={"key": "PVP_REWARD_MULTIPLIER", "enabled": True, "multiplier": 1.5})

    wb_payload = {"hunterId": "h1", "bossId": "wb1", "seasonId": "s1", "rank": 2}
    pvp_payload = {"hunterId": "h1", "seasonId": "p1", "rank": 11}

    wb1 = client.post("/worldboss/claim", json=wb_payload).json()
    wb2 = client.post("/worldboss/claim", json=wb_payload).json()

    p1 = client.post("/pvp/claim", json=pvp_payload).json()
    p2 = client.post("/pvp/claim", json=pvp_payload).json()

    hunter = client.get("/hunters/h1").json()

    print("WB claim #1:", wb1)
    print("WB claim #2 (dup):", wb2)
    print("PVP claim #1:", p1)
    print("PVP claim #2 (dup):", p2)
    print("Hunter:", hunter)


if __name__ == "__main__":
    main()