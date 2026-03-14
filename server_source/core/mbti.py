# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
import os
import random
from typing import Any, Dict, List, Optional

from storage.sqlite_db import get_conn


_DEFAULT_MBTI_16 = [
    "INTJ", "INTP", "ENTJ", "ENTP",
    "INFJ", "INFP", "ENFJ", "ENFP",
    "ISTJ", "ISFJ", "ESTJ", "ESFJ",
    "ISTP", "ISFP", "ESTP", "ESFP",
]


def list_mbti_types() -> List[str]:
    """
    Returns available MBTI types from DB (mbti_traits).
    Always excludes 'NONE' for random assignment.
    Falls back to default 16 types when DB not ready.
    """
    try:
        conn = get_conn()
        rows = conn.execute("SELECT mbti FROM mbti_traits;").fetchall()
        mbtis = [str(r[0]) for r in rows if r and str(r[0]).strip()]
        mbtis = [m for m in mbtis if m.upper() != "NONE"]
        # If DB has presets, use them; otherwise fallback.
        return mbtis if mbtis else list(_DEFAULT_MBTI_16)
    except Exception:
        return list(_DEFAULT_MBTI_16)


def random_mbti() -> str:
    """
    Random MBTI assignment for recruit.
    In pytest environment, can be made deterministic by setting MBTI_TEST_SEED.
    """
    seed = os.getenv("MBTI_TEST_SEED")
    if os.getenv("PYTEST_CURRENT_TEST") and seed is None:
        seed = "12345"

    rng = random.Random(seed) if seed is not None else random
    candidates = list_mbti_types()
    return rng.choice(candidates) if candidates else "INTJ"


# -------------------------
# Catalog APIs (admin)
# -------------------------
def list_mbti_traits() -> List[Dict[str, Any]]:
    """List MBTI trait multipliers.

    Includes 'NONE' which represents neutral multipliers.
    """

    conn = get_conn()
    rows = conn.execute(
        """
        SELECT mbti, atk_mul, hp_mul, def_mul, gold_mul, exp_mul, updatedAt
        FROM mbti_traits
        ORDER BY mbti ASC;
        """
    ).fetchall()
    return [
        {
            "mbti": r[0],
            "atkMul": float(r[1]),
            "hpMul": float(r[2]),
            "defMul": float(r[3]),
            "goldMul": float(r[4]),
            "expMul": float(r[5]),
            "updatedAt": r[6],
        }
        for r in rows
    ]


def upsert_mbti_trait(
    mbti: str,
    atk_mul: float,
    hp_mul: float,
    def_mul: float,
    gold_mul: float,
    exp_mul: float,
) -> Dict[str, Any]:
    """Upsert a MBTI trait row into `mbti_traits`."""

    m = str(mbti).upper().strip()
    if not m:
        raise ValueError("mbti is required")

    conn = get_conn()
    conn.execute(
        """
        INSERT INTO mbti_traits(mbti, atk_mul, hp_mul, def_mul, gold_mul, exp_mul, updatedAt)
        VALUES(?,?,?,?,?,?,datetime('now'))
        ON CONFLICT(mbti)
        DO UPDATE SET
          atk_mul=excluded.atk_mul,
          hp_mul=excluded.hp_mul,
          def_mul=excluded.def_mul,
          gold_mul=excluded.gold_mul,
          exp_mul=excluded.exp_mul,
          updatedAt=datetime('now');
        """,
        (
            m,
            float(atk_mul),
            float(hp_mul),
            float(def_mul),
            float(gold_mul),
            float(exp_mul),
        ),
    )

    row = conn.execute(
        """
        SELECT mbti, atk_mul, hp_mul, def_mul, gold_mul, exp_mul, updatedAt
        FROM mbti_traits
        WHERE mbti=?;
        """,
        (m,),
    ).fetchone()
    return {
        "mbti": row[0],
        "atkMul": float(row[1]),
        "hpMul": float(row[2]),
        "defMul": float(row[3]),
        "goldMul": float(row[4]),
        "expMul": float(row[5]),
        "updatedAt": row[6],
    }