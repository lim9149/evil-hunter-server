from __future__ import annotations

from typing import Dict


def apply_reward_multiplier(base: Dict[str, int], mul: float) -> Dict[str, int]:
    """
    Pure function: base reward dict -> multiplied reward dict.

    Safety rules:
      - multiplier <= 0 is treated as 1.0
      - result is rounded to nearest int
      - missing keys default to 0
    """
    m = float(mul)
    if m <= 0:
        m = 1.0
    return {
        "gold": int(round(int(base.get("gold", 0)) * m)),
        "exp": int(round(int(base.get("exp", 0)) * m)),
        "gems": int(round(int(base.get("gems", 0)) * m)),
    }