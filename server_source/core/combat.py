# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
from dataclasses import dataclass
from typing import Dict, Any
import math


@dataclass(frozen=True)
class CombatConfig:
    hit_interval_sec: float = 0.5  # 0.5초에 1타(임시)
    min_damage: int = 1


def calculate_damage_per_hit(hunter_atk: float, monster_def: float, atk_mul: float = 1.0) -> int:
    # 매우 단순한 MVP: max(min_damage, atk*mul - def)
    raw = hunter_atk * atk_mul - monster_def
    return max(1, int(math.floor(raw)))

def fight_time_to_kill(
    *,
    hunter_atk: float,
    monster_def: float,
    monster_hp: float,
    atk_mul: float = 1.0,
    tempo_mul: float = 1.0,
    morale: float = 50.0,
    fatigue: float = 0.0,
    config: CombatConfig = CombatConfig(),
) -> Dict[str, Any]:
    dmg = calculate_damage_per_hit(hunter_atk, monster_def, atk_mul=atk_mul)
    hits = int(math.ceil(max(monster_hp, 0.0) / max(dmg, 1)))
    tempo = max(0.7, float(tempo_mul))
    morale_factor = max(0.9, 1.0 - max(0.0, 50.0 - morale) / 500.0)
    fatigue_factor = min(1.35, 1.0 + max(0.0, fatigue) / 180.0)
    total_sec = hits * config.hit_interval_sec / tempo * morale_factor * fatigue_factor
    succeed = monster_hp <= 0 or dmg > 0  # MVP는 dmg>0이면 결국 잡는다고 가정

    return {
        "damagePerHit": dmg,
        "hitsToKill": hits,
        "totalSec": float(total_sec),
        "fightSucceed": bool(succeed),
        "breakdown": {
            "hunterAtk": hunter_atk,
            "monsterDef": monster_def,
            "monsterHp": monster_hp,
            "atkMul": atk_mul,
            "tempoMul": tempo_mul,
            "morale": morale,
            "fatigue": fatigue,
            "hitIntervalSec": config.hit_interval_sec,
        },
    }