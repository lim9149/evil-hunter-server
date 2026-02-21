from __future__ import annotations

from typing import Dict


def rank_multiplier(rank: int) -> float:
    """Simple rank-to-multiplier curve.

    This is an MVP curve that can later be replaced with Sheet-driven tables.
    """
    r = int(rank)
    if r <= 1:
        return 1.0
    if 2 <= r <= 10:
        return 0.7
    if 11 <= r <= 50:
        return 0.4
    if 51 <= r <= 200:
        return 0.25
    return 0.15


def apply_reward_multiplier(base: Dict[str, int], mul: float) -> Dict[str, int]:
    m = float(mul)
    if m <= 0:
        m = 1.0
    return {
        "gold": int(round(int(base.get("gold", 0)) * m)),
        "exp": int(round(int(base.get("exp", 0)) * m)),
        "gems": int(round(int(base.get("gems", 0)) * m)),
    }