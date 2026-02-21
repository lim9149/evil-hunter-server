"""Operator(Admin) mode state.

Design goals:
  - Server-determined multipliers (client cannot spoof multipliers)
  - SQLite is the source of truth
  - Safe defaults: if no row exists -> disabled, multiplier 1.0
"""

from __future__ import annotations

from typing import Dict

from storage.sqlite_db import get_admin_mode, list_admin_modes


OFFLINE_REWARD_MULTIPLIER_KEY = "OFFLINE_REWARD_MULTIPLIER"
WORLD_BOSS_REWARD_MULTIPLIER_KEY = "WORLD_BOSS_REWARD_MULTIPLIER"
PVP_REWARD_MULTIPLIER_KEY = "PVP_REWARD_MULTIPLIER"


def get_multiplier(key: str) -> float:
    row = get_admin_mode(key)
    if not row:
        return 1.0
    if not bool(row.get("enabled", False)):
        return 1.0
    try:
        m = float(row.get("multiplier", 1.0))
    except Exception:
        return 1.0
    return m if m > 0 else 1.0


def snapshot() -> Dict[str, Dict]:
    """Convenience for debugging/admin UI."""
    items = list_admin_modes()
    return {i["key"]: i for i in items}