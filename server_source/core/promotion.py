import json
from typing import Any, Dict, List, Optional, Tuple

from storage.sqlite_db import get_conn


def get_promotion_node(node_id: str) -> Optional[Dict[str, Any]]:
    """
    Returns a promotion node row from DB (promotion_nodes).
    """
    conn = get_conn()
    row = conn.execute(
        """
        SELECT node_id, parent_node_id, job_id, choice_group, promotion_multiplier,
               stat_bonus_json, skill_unlock_json
        FROM promotion_nodes
        WHERE node_id=?
        """,
        (str(node_id),),
    ).fetchone()
    if not row:
        return None

    return {
        "nodeId": row[0],
        "parentNodeId": row[1],
        "jobId": row[2],
        "choiceGroup": row[3],
        "promotionMultiplier": float(row[4]) if row[4] is not None else 1.0,
        "statBonus": _safe_json_obj(row[5], default={}),
        "skillUnlock": _safe_json_list(row[6], default=[]),
    }


def compute_promotion_effect(promotion_path: List[str]) -> Dict[str, Any]:
    """
    Computes cumulative effect from a promotion path:
      - promotionMultiplier: product of node multipliers
      - statBonus: sum of numeric bonuses
      - skillsUnlocked: concatenation unique
    """
    mul = 1.0
    stat_bonus: Dict[str, float] = {}
    skills: List[str] = []

    for nid in promotion_path or []:
        node = get_promotion_node(nid)
        if not node:
            continue
        mul *= float(node.get("promotionMultiplier", 1.0))

        sb = node.get("statBonus") or {}
        if isinstance(sb, dict):
            for k, v in sb.items():
                try:
                    stat_bonus[k] = float(stat_bonus.get(k, 0.0)) + float(v)
                except Exception:
                    # ignore non-numeric
                    continue

        su = node.get("skillUnlock") or []
        if isinstance(su, list):
            for s in su:
                ss = str(s)
                if ss and ss not in skills:
                    skills.append(ss)

    return {
        "promotionMultiplier": float(mul),
        "statBonus": stat_bonus,
        "skillsUnlocked": skills,
    }


def validate_next_promotion(current_path: List[str], next_node_id: str) -> Tuple[bool, str]:
    """
    Validates promotion step:
      - next node exists
      - parentNodeId matches current last node (or None for first)
      - choiceGroup not already chosen in path
    """
    next_node = get_promotion_node(next_node_id)
    if not next_node:
        return False, "promotion node not found"

    parent = next_node.get("parentNodeId")
    last = (current_path[-1] if current_path else None)
    if parent != last:
        return False, "parentNodeId mismatch"

    next_group = next_node.get("choiceGroup")
    if next_group:
        for nid in current_path or []:
            n = get_promotion_node(nid)
            if n and n.get("choiceGroup") == next_group:
                return False, "choiceGroup already chosen"
    return True, "ok"


def _safe_json_obj(v: Any, default: Dict[str, Any]) -> Dict[str, Any]:
    try:
        if v is None:
            return dict(default)
        if isinstance(v, dict):
            return v
        return json.loads(v)
    except Exception:
        return dict(default)


def _safe_json_list(v: Any, default: List[Any]) -> List[Any]:
    try:
        if v is None:
            return list(default)
        if isinstance(v, list):
            return v
        return json.loads(v)
    except Exception:
        return list(default)


# -------------------------
# Catalog APIs (admin)
# -------------------------
def list_promotion_nodes() -> List[Dict[str, Any]]:
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT node_id, parent_node_id, job_id, choice_group, promotion_multiplier,
               stat_bonus_json, skill_unlock_json
        FROM promotion_nodes
        ORDER BY node_id ASC;
        """
    ).fetchall()
    out: List[Dict[str, Any]] = []
    for r in rows:
        out.append(
            {
                "nodeId": r[0],
                "parentNodeId": r[1],
                "jobId": r[2],
                "choiceGroup": r[3],
                "promotionMultiplier": float(r[4]) if r[4] is not None else 1.0,
                "statBonus": _safe_json_obj(r[5], default={}),
                "skillUnlock": _safe_json_list(r[6], default=[]),
            }
        )
    return out


def upsert_promotion_node(
    *,
    node_id: str,
    parent_node_id: Optional[str],
    job_id: str,
    choice_group: Optional[str],
    promotion_multiplier: float,
    stat_bonus: Dict[str, Any],
    skill_unlock: List[Any],
) -> Dict[str, Any]:
    conn = get_conn()

    payload_stat = json.dumps(stat_bonus or {}, ensure_ascii=False)
    payload_skill = json.dumps(skill_unlock or [], ensure_ascii=False)

    conn.execute(
        """
        INSERT INTO promotion_nodes(
          node_id, parent_node_id, job_id, choice_group, promotion_multiplier,
          stat_bonus_json, skill_unlock_json
        ) VALUES(?,?,?,?,?,?,?)
        ON CONFLICT(node_id)
        DO UPDATE SET
          parent_node_id=excluded.parent_node_id,
          job_id=excluded.job_id,
          choice_group=excluded.choice_group,
          promotion_multiplier=excluded.promotion_multiplier,
          stat_bonus_json=excluded.stat_bonus_json,
          skill_unlock_json=excluded.skill_unlock_json;
        """,
        (
            str(node_id),
            None if parent_node_id is None else str(parent_node_id),
            str(job_id),
            None if choice_group is None else str(choice_group),
            float(promotion_multiplier),
            payload_stat,
            payload_skill,
        ),
    )

    return get_promotion_node(str(node_id)) or {
        "nodeId": str(node_id),
        "parentNodeId": parent_node_id,
        "jobId": str(job_id),
        "choiceGroup": choice_group,
        "promotionMultiplier": float(promotion_multiplier),
        "statBonus": stat_bonus or {},
        "skillUnlock": skill_unlock or [],
    }