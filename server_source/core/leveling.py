# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
from __future__ import annotations


def exp_to_next_level(level: int) -> int:
    lvl = max(1, int(level))
    return 100 + ((lvl - 1) * 35) + ((lvl - 1) ** 2 * 5)


def estimate_level_from_total_exp(total_exp: int, start_level: int = 1) -> int:
    remaining = max(0, int(total_exp))
    level = max(1, int(start_level))
    while remaining >= exp_to_next_level(level):
        remaining -= exp_to_next_level(level)
        level += 1
    return level
