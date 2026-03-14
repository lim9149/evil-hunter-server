# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
from __future__ import annotations

JOB_CLASS_BALANCE = {
    "novice": {"role": "balanced", "hpScale": 1.0, "atkScale": 1.0, "defScale": 1.0},
    "swordsman": {"role": "burst", "hpScale": 0.95, "atkScale": 1.18, "defScale": 0.92},
    "guardian": {"role": "tank", "hpScale": 1.2, "atkScale": 0.9, "defScale": 1.25},
    "archer": {"role": "ranged", "hpScale": 0.9, "atkScale": 1.12, "defScale": 0.9},
    "healer": {"role": "support", "hpScale": 0.98, "atkScale": 0.88, "defScale": 1.02},
}


def get_job_balance(job_id: str) -> dict:
    return dict(JOB_CLASS_BALANCE.get(str(job_id or "novice"), JOB_CLASS_BALANCE["novice"]))
