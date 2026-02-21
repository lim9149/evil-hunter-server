import os
import sqlite3
from typing import Optional, Dict, Any

_conn: Optional[sqlite3.Connection] = None

def _resolve_db_path() -> str:
    # In production: persist to file storage/evil_hunter.db (or SQLITE_PATH).
    # In tests(pytest): default to in-memory to keep runs isolated.
    default_path = ":memory:" if os.getenv("PYTEST_CURRENT_TEST") else os.path.join(os.path.dirname(__file__), "evil_hunter.db")
    return os.getenv("SQLITE_PATH", default_path)

def get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        db_path = _resolve_db_path()
        _conn = sqlite3.connect(db_path, check_same_thread=False)
        _conn.execute("PRAGMA journal_mode=WAL;")
        _conn.execute("PRAGMA foreign_keys=ON;")
        _init_schema(_conn)
    return _conn

def _init_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS offline_collect (
            hunterId TEXT NOT NULL,
            collectedAtEpochSec INTEGER NOT NULL,
            gold INTEGER NOT NULL,
            exp INTEGER NOT NULL,
            createdAt TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (hunterId, collectedAtEpochSec)
        );
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_offline_collect_hunter_time
        ON offline_collect(hunterId, collectedAtEpochSec);
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS admin_mode (
            key TEXT NOT NULL PRIMARY KEY,
            enabled INTEGER NOT NULL,
            multiplier REAL NOT NULL,
            updatedAt TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS worldboss_reward_claim (
            hunterId TEXT NOT NULL,
            bossId TEXT NOT NULL,
            seasonId TEXT NOT NULL,
            gold INTEGER NOT NULL,
            exp INTEGER NOT NULL,
            gems INTEGER NOT NULL,
            createdAt TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (hunterId, bossId, seasonId)
        );
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pvp_reward_claim (
            hunterId TEXT NOT NULL,
            seasonId TEXT NOT NULL,
            gold INTEGER NOT NULL,
            exp INTEGER NOT NULL,
            gems INTEGER NOT NULL,
            createdAt TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (hunterId, seasonId)
        );
        """
    )
    conn.commit()

def get_collect(hunter_id: str, now_epoch: int) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.execute(
        "SELECT hunterId, collectedAtEpochSec, gold, exp, createdAt FROM offline_collect WHERE hunterId=? AND collectedAtEpochSec=?",
        (hunter_id, int(now_epoch)),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {
        "hunterId": row[0],
        "collectedAtEpochSec": row[1],
        "gold": row[2],
        "exp": row[3],
        "createdAt": row[4],
    }

def insert_collect(hunter_id: str, now_epoch: int, gold: int, exp: int) -> bool:
    """Insert a collect record. Returns True if inserted, False if already exists."""
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO offline_collect(hunterId, collectedAtEpochSec, gold, exp) VALUES(?,?,?,?)",
            (hunter_id, int(now_epoch), int(gold), int(exp)),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def upsert_admin_mode(key: str, enabled: bool, multiplier: float) -> Dict[str, Any]:
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO admin_mode(key, enabled, multiplier, updatedAt)
        VALUES(?,?,?, datetime('now'))
        ON CONFLICT(key) DO UPDATE SET
            enabled=excluded.enabled,
            multiplier=excluded.multiplier,
            updatedAt=datetime('now');
        """,
        (str(key), 1 if enabled else 0, float(multiplier)),
    )
    conn.commit()
    row = get_admin_mode(key)
    return row if row else {"key": key, "enabled": enabled, "multiplier": float(multiplier)}


def get_admin_mode(key: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.execute(
        "SELECT key, enabled, multiplier, updatedAt FROM admin_mode WHERE key=?",
        (str(key),),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {
        "key": row[0],
        "enabled": bool(row[1]),
        "multiplier": float(row[2]),
        "updatedAt": row[3],
    }


def list_admin_modes() -> list[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.execute("SELECT key, enabled, multiplier, updatedAt FROM admin_mode ORDER BY key ASC")
    rows = cur.fetchall()
    return [
        {"key": r[0], "enabled": bool(r[1]), "multiplier": float(r[2]), "updatedAt": r[3]}
        for r in rows
    ]


def get_worldboss_claim(hunter_id: str, boss_id: str, season_id: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.execute(
        """
        SELECT hunterId, bossId, seasonId, gold, exp, gems, createdAt
        FROM worldboss_reward_claim
        WHERE hunterId=? AND bossId=? AND seasonId=?
        """,
        (str(hunter_id), str(boss_id), str(season_id)),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {
        "hunterId": row[0],
        "bossId": row[1],
        "seasonId": row[2],
        "gold": int(row[3]),
        "exp": int(row[4]),
        "gems": int(row[5]),
        "createdAt": row[6],
    }


def insert_worldboss_claim(hunter_id: str, boss_id: str, season_id: str, gold: int, exp: int, gems: int) -> bool:
    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO worldboss_reward_claim(hunterId,bossId,seasonId,gold,exp,gems)
            VALUES(?,?,?,?,?,?)
            """,
            (str(hunter_id), str(boss_id), str(season_id), int(gold), int(exp), int(gems)),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def get_pvp_claim(hunter_id: str, season_id: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.execute(
        """
        SELECT hunterId, seasonId, gold, exp, gems, createdAt
        FROM pvp_reward_claim
        WHERE hunterId=? AND seasonId=?
        """,
        (str(hunter_id), str(season_id)),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {
        "hunterId": row[0],
        "seasonId": row[1],
        "gold": int(row[2]),
        "exp": int(row[3]),
        "gems": int(row[4]),
        "createdAt": row[5],
    }


def insert_pvp_claim(hunter_id: str, season_id: str, gold: int, exp: int, gems: int) -> bool:
    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO pvp_reward_claim(hunterId,seasonId,gold,exp,gems)
            VALUES(?,?,?,?,?)
            """,
            (str(hunter_id), str(season_id), int(gold), int(exp), int(gems)),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False