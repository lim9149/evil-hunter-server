from typing import Any, Dict, List, Optional

from storage.sqlite_db import get_conn


def get_item_def(item_id: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    row = conn.execute(
        """
        SELECT item_id, season_id, tier_id, slot, atk_mul, hp_mul, def_mul, skill_mul
        FROM item_defs
        WHERE item_id=?
        """,
        (str(item_id),),
    ).fetchone()
    if not row:
        return None
    return {
        "itemId": row[0],
        "seasonId": row[1],
        "tierId": row[2],
        "slot": row[3],
        "atkMul": float(row[4]),
        "hpMul": float(row[5]),
        "defMul": float(row[6]),
        "skillMul": float(row[7]),
    }


def compute_item_multiplier(equipped_item_ids: List[str]) -> Dict[str, Any]:
    """
    Returns combined multipliers for equipped items.
    Multipliers are multiplied (product).
    """
    atk = 1.0
    hp = 1.0
    df = 1.0
    skill = 1.0

    for iid in equipped_item_ids or []:
        item = get_item_def(iid)
        if not item:
            continue
        atk *= float(item.get("atkMul", 1.0))
        hp *= float(item.get("hpMul", 1.0))
        df *= float(item.get("defMul", 1.0))
        skill *= float(item.get("skillMul", 1.0))

    return {"atkMul": atk, "hpMul": hp, "defMul": df, "skillMul": skill}


def validate_equip(
    hunter_season_id: str,
    hunter_tier_id: str,
    equipped_item_ids: List[str],
) -> Optional[str]:
    """
    Validate equip rules:
      - item exists
      - slot unique
      - seasonId matches hunter seasonId
      - item tier <= hunter tier (lexicographic for 'T1','T2'.. safe if consistent)
    Returns error string or None if ok.
    """
    seen_slots = set()

    for iid in equipped_item_ids or []:
        item = get_item_def(iid)
        if not item:
            return f"item not found: {iid}"

        if str(item["seasonId"]) != str(hunter_season_id):
            return f"season mismatch for item: {iid}"

        # tier check: expects 'T1','T2'... convert to int
        if _tier_num(item["tierId"]) > _tier_num(hunter_tier_id):
            return f"tier too high for item: {iid}"

        slot = str(item["slot"])
        if slot in seen_slots:
            return f"duplicate slot: {slot}"
        seen_slots.add(slot)

    return None


def compute_item_multipliers(equipped_item_ids):
    """
    Backward-compatible alias.
    routers/hunter.py expects compute_item_multipliers (plural).
    """
    return compute_item_multiplier(equipped_item_ids)


def _tier_num(tier_id: str) -> int:
    try:
        t = str(tier_id).upper().strip()
        if t.startswith("T"):
            return int(t[1:])
        return int(t)
    except Exception:
        return 0


# -------------------------
# Catalog APIs (admin)
# -------------------------
def list_item_defs(season_id: str | None = None, tier_id: str | None = None) -> List[Dict[str, Any]]:
    conn = get_conn()
    q = [
        "SELECT item_id, season_id, tier_id, slot, atk_mul, hp_mul, def_mul, skill_mul FROM item_defs",
    ]
    params: list[Any] = []
    where = []
    if season_id:
        where.append("season_id=?")
        params.append(str(season_id))
    if tier_id:
        where.append("tier_id=?")
        params.append(str(tier_id))
    if where:
        q.append("WHERE " + " AND ".join(where))
    q.append("ORDER BY season_id ASC, tier_id ASC, item_id ASC;")

    rows = conn.execute("\n".join(q), tuple(params)).fetchall()
    return [
        {
            "itemId": r[0],
            "seasonId": r[1],
            "tierId": r[2],
            "slot": r[3],
            "atkMul": float(r[4]),
            "hpMul": float(r[5]),
            "defMul": float(r[6]),
            "skillMul": float(r[7]),
        }
        for r in rows
    ]


def upsert_item_def(
    *,
    item_id: str,
    season_id: str,
    tier_id: str,
    slot: str,
    atk_mul: float,
    hp_mul: float,
    def_mul: float,
    skill_mul: float,
) -> Dict[str, Any]:
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO item_defs(item_id, season_id, tier_id, slot, atk_mul, hp_mul, def_mul, skill_mul)
        VALUES(?,?,?,?,?,?,?,?)
        ON CONFLICT(item_id)
        DO UPDATE SET
          season_id=excluded.season_id,
          tier_id=excluded.tier_id,
          slot=excluded.slot,
          atk_mul=excluded.atk_mul,
          hp_mul=excluded.hp_mul,
          def_mul=excluded.def_mul,
          skill_mul=excluded.skill_mul;
        """,
        (
            str(item_id),
            str(season_id),
            str(tier_id),
            str(slot),
            float(atk_mul),
            float(hp_mul),
            float(def_mul),
            float(skill_mul),
        ),
    )
    return get_item_def(str(item_id)) or {
        "itemId": str(item_id),
        "seasonId": str(season_id),
        "tierId": str(tier_id),
        "slot": str(slot),
        "atkMul": float(atk_mul),
        "hpMul": float(hp_mul),
        "defMul": float(def_mul),
        "skillMul": float(skill_mul),
    }