# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
"""Tier / Season inflation policy simulator.

Goal
----
Provide a quick, repeatable way to sanity-check how tier multipliers affect
combat time-to-kill (TTK) and reward scaling.

Why this exists
--------------
- Keep core engines stable (damage_engine/tier/promotion)
- Avoid client-side calculations: this is server-side/offline simulation
- Help prevent runaway inflation when adding new tiers/seasons

Usage
-----
python -m scripts.sim_tier_inflation --season S1 --tiers T1,T2,T3 --base-atk 10 --monster-hp 50 --monster-def 0

Notes
-----
- Reads tier multipliers from SQLite `tier_defs` (via core.tier.get_tier_multiplier)
- If a tier is missing, multiplier falls back to 1.0
"""

from __future__ import annotations

import argparse
from typing import Any, Dict, List

from core.combat import fight_time_to_kill
from core.tier import get_tier_multiplier


def _parse_csv(s: str) -> List[str]:
    return [x.strip() for x in (s or "").split(",") if x.strip()]


def run(
    season_id: str,
    tier_ids: List[str],
    base_atk: float,
    monster_hp: float,
    monster_def: float,
    atk_mul: float,
    base_gold: int,
    base_exp: int,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for tid in tier_ids:
        tm = float(get_tier_multiplier(season_id, tid))
        result = fight_time_to_kill(
            hunter_atk=float(base_atk) * tm,
            monster_def=float(monster_def),
            monster_hp=float(monster_hp),
            atk_mul=float(atk_mul),
        )
        rows.append(
            {
                "seasonId": season_id,
                "tierId": tid,
                "tierMultiplier": tm,
                "effectiveAtk": float(base_atk) * tm,
                "damagePerHit": float(result["damagePerHit"]),
                "hitsToKill": int(result["hitsToKill"]),
                "totalSec": float(result["totalSec"]),
                "rewardGold": int(base_gold * tm),
                "rewardExp": int(base_exp * tm),
            }
        )
    return rows


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--season", default="S1")
    p.add_argument("--tiers", default="T1,T2,T3")
    p.add_argument("--base-atk", type=float, default=10.0)
    p.add_argument("--monster-hp", type=float, default=50.0)
    p.add_argument("--monster-def", type=float, default=0.0)
    p.add_argument("--atk-mul", type=float, default=1.0)
    p.add_argument("--base-gold", type=int, default=100)
    p.add_argument("--base-exp", type=int, default=50)
    args = p.parse_args()

    tiers = _parse_csv(args.tiers)
    rows = run(
        season_id=str(args.season),
        tier_ids=tiers,
        base_atk=float(args.base_atk),
        monster_hp=float(args.monster_hp),
        monster_def=float(args.monster_def),
        atk_mul=float(args.atk_mul),
        base_gold=int(args.base_gold),
        base_exp=int(args.base_exp),
    )

    # Pretty print (copy/paste friendly)
    headers = [
        "seasonId",
        "tierId",
        "tierMultiplier",
        "effectiveAtk",
        "damagePerHit",
        "hitsToKill",
        "totalSec",
        "rewardGold",
        "rewardExp",
    ]
    print("\t".join(headers))
    for r in rows:
        print("\t".join(str(r[h]) for h in headers))


if __name__ == "__main__":
    main()