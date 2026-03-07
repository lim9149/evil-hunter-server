"""Tier catalog (season-based multipliers).

Design intent
-------------
- Keep inflation controllable via server-owned multipliers.
- Allow future expansion via season_id + tier_id without hardcoding.

This module is used by admin_catalog router and other core systems.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from storage.sqlite_db import get_conn


def tier_exists(season_id: str, tier_id: str) -> bool:
    """tier_defs에 (season_id, tier_id) 존재 여부."""
    conn = get_conn()
    row = conn.execute(
        """
        SELECT 1 FROM tier_defs WHERE season_id=? AND tier_id=? LIMIT 1
        """,
        (str(season_id), str(tier_id)),
    ).fetchone()
    return row is not None


def get_tier_multiplier(season_id: str, tier_id: str) -> float:
    """Returns tier multiplier from `tier_defs`; fallback 1.0."""

    conn = get_conn()
    row = conn.execute(
        """
        SELECT multiplier
        FROM tier_defs
        WHERE season_id=? AND tier_id=?
        """,
        (str(season_id), str(tier_id)),
    ).fetchone()
    if not row:
        return 1.0
    try:
        m = float(row[0])
        return m if m > 0 else 1.0
    except Exception:
        return 1.0


def list_tiers(season_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """List tier definitions.

    Args:
        season_id: if provided, filters tiers by season.
    """

    conn = get_conn()
    if season_id:
        rows = conn.execute(
            """
            SELECT season_id, tier_id, multiplier, updatedAt
            FROM tier_defs
            WHERE season_id=?
            ORDER BY season_id ASC, tier_id ASC;
            """,
            (str(season_id),),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT season_id, tier_id, multiplier, updatedAt
            FROM tier_defs
            ORDER BY season_id ASC, tier_id ASC;
            """,
        ).fetchall()
    return [
        {
            "seasonId": r[0],
            "tierId": r[1],
            "multiplier": float(r[2]),
            "updatedAt": r[3],
        }
        for r in rows
    ]


def upsert_tier(season_id: str, tier_id: str, multiplier: float) -> Dict[str, Any]:
    """Upsert a tier multiplier into `tier_defs`.

    Returns the stored row.
    """

    mul = float(multiplier)
    if mul <= 0:
        raise ValueError("multiplier must be > 0")

    conn = get_conn()
    conn.execute(
        """
        INSERT INTO tier_defs(season_id, tier_id, multiplier, updatedAt)
        VALUES(?,?,?,datetime('now'))
        ON CONFLICT(season_id, tier_id)
        DO UPDATE SET multiplier=excluded.multiplier, updatedAt=datetime('now');
        """,
        (str(season_id), str(tier_id), mul),
    )

    row = conn.execute(
        """
        SELECT season_id, tier_id, multiplier, updatedAt
        FROM tier_defs
        WHERE season_id=? AND tier_id=?;
        """,
        (str(season_id), str(tier_id)),
    ).fetchone()
    return {
        "seasonId": row[0],
        "tierId": row[1],
        "multiplier": float(row[2]),
        "updatedAt": row[3],
    }


def tier_rank(tier_id: str) -> int:
    """Converts tier id like 'T1','T2'.. into comparable integer rank."""

    try:
        t = str(tier_id).strip().upper()
        if t.startswith("T"):
            return int(t[1:])
        return int(t)
    except Exception:
        return 0