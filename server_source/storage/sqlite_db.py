# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
import os
import sqlite3
import threading
import time
from typing import Optional, Dict, Any, List, Tuple


_conn: Optional[sqlite3.Connection] = None
_conn_path: Optional[str] = None
_lock = threading.RLock()


def _resolve_db_path() -> str:
    """
    우선순위:
    1) SQLITE_PATH 환경변수
    2) pytest 실행 중이면 :memory:
    3) 기본: storage/evil_hunter.db
    """
    env_path = os.getenv("SQLITE_PATH")
    if env_path and env_path.strip():
        return env_path.strip()

    if os.getenv("PYTEST_CURRENT_TEST"):
        return ":memory:"

    return os.path.join(os.path.dirname(__file__), "evil_hunter.db")


def close_conn() -> None:
    """현재 커넥션을 안전하게 닫습니다."""
    global _conn, _conn_path
    with _lock:
        if _conn is not None:
            try:
                _conn.close()
            finally:
                _conn = None
                _conn_path = None


def reset_conn() -> None:
    """테스트 격리/재초기화용: 커넥션 리셋."""
    close_conn()


def get_conn() -> sqlite3.Connection:
    global _conn, _conn_path

    with _lock:
        db_path = _resolve_db_path()

        # 경로가 바뀌었으면 재연결
        if _conn is not None and _conn_path != db_path:
            close_conn()

        if _conn is None:
            _conn_path = db_path
            _conn = sqlite3.connect(
                db_path,
                check_same_thread=False,
                isolation_level=None,  # autocommit; 명시적 BEGIN/COMMIT 사용
            )

            _conn.execute("PRAGMA foreign_keys=ON;")
            _conn.execute("PRAGMA busy_timeout=3000;")  # 3s

            # 파일 기반일 때만 WAL 시도
            if db_path != ":memory:" and not db_path.startswith("file::memory:"):
                try:
                    _conn.execute("PRAGMA journal_mode=WAL;")
                except Exception:
                    pass

            _init_schema(_conn)

        return _conn


def _ensure_extra_liveops_schema(conn: sqlite3.Connection) -> None:
    """Small forward-compatible migrations for newer liveops columns/tables."""
    def ensure_column(table: str, column: str, ddl: str) -> None:
        cols = {row[1] for row in conn.execute(f"PRAGMA table_info({table});").fetchall()}
        if column not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {ddl};")

    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()}
    if "ad_view_session" in tables:
        ensure_column("ad_view_session", "verifiedAt", "verifiedAt INTEGER")
        ensure_column("ad_view_session", "completionProof", "completionProof TEXT")
        ensure_column("ad_view_session", "completionToken", "completionToken TEXT")
        ensure_column("ad_view_session", "adNetwork", "adNetwork TEXT")
        ensure_column("ad_view_session", "adUnitId", "adUnitId TEXT")

    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS operator_treasury (
            accountId TEXT PRIMARY KEY,
            operatorGold INTEGER NOT NULL DEFAULT 0,
            operatorExp INTEGER NOT NULL DEFAULT 0,
            updatedAt INTEGER NOT NULL
        );
        '''
    )
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS operator_inventory (
            accountId TEXT NOT NULL,
            itemId TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0,
            updatedAt INTEGER NOT NULL,
            PRIMARY KEY (accountId, itemId)
        );
        '''
    )
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS operator_action_log (
            logId TEXT PRIMARY KEY,
            accountId TEXT NOT NULL,
            hunterId TEXT,
            actionType TEXT NOT NULL,
            resultCode TEXT NOT NULL,
            detail TEXT,
            payloadJson TEXT,
            createdAt INTEGER NOT NULL
        );
        '''
    )
    conn.execute(
        '''
        CREATE INDEX IF NOT EXISTS idx_operator_action_log_account_time
        ON operator_action_log(accountId, createdAt DESC);
        '''
    )
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS hunter_state_snapshot (
            snapshotId TEXT PRIMARY KEY,
            hunterId TEXT NOT NULL,
            accountId TEXT NOT NULL,
            stateCode TEXT NOT NULL,
            nextStateCode TEXT NOT NULL,
            payloadJson TEXT,
            createdAt INTEGER NOT NULL
        );
        '''
    )
    conn.execute(
        '''
        CREATE INDEX IF NOT EXISTS idx_hunter_state_snapshot_hunter_time
        ON hunter_state_snapshot(hunterId, createdAt DESC);
        '''
    )

    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS operator_mission_claim (
            accountId TEXT NOT NULL,
            missionId TEXT NOT NULL,
            missionScope TEXT NOT NULL,
            rewardJson TEXT,
            createdAt INTEGER NOT NULL,
            PRIMARY KEY (accountId, missionId, missionScope)
        );
        '''
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS telemetry_events (
            eventId TEXT PRIMARY KEY,
            accountId TEXT,
            eventType TEXT NOT NULL,
            eventName TEXT NOT NULL,
            payloadJson TEXT,
            createdAt INTEGER NOT NULL
        );
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_telemetry_events_account_time
        ON telemetry_events(accountId, createdAt DESC);
        """
    )


def _ensure_offline_collect_schema(conn: sqlite3.Connection) -> None:
    """Ensure offline_collect has (hunterId, collectedAtEpoch) idempotency key.

    Legacy schema (hunterId PK, lastCollectedAt TEXT) is renamed to offline_collect_legacy,
    then a new table is created.
    """
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='offline_collect';")
    exists = cur.fetchone() is not None
    if not exists:
        return

    info = conn.execute("PRAGMA table_info(offline_collect);").fetchall()
    cols = {row[1] for row in info}  # row[1] = name
    # expected new schema columns
    if {"hunterId", "collectedAtEpoch", "gold", "exp", "gems"}.issubset(cols):
        # already new enough
        return

    # Legacy detected -> rename
    conn.execute("ALTER TABLE offline_collect RENAME TO offline_collect_legacy;")


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.execute("BEGIN;")

    _ensure_offline_collect_schema(conn)
    _ensure_extra_liveops_schema(conn)

    # -------------------------
    # offline_collect (idempotent offline reward)
    # -------------------------
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS offline_collect (
            hunterId TEXT NOT NULL,
            collectedAtEpoch INTEGER NOT NULL,
            gold INTEGER NOT NULL,
            exp INTEGER NOT NULL,
            gems INTEGER NOT NULL DEFAULT 0,
            createdAt TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (hunterId, collectedAtEpoch)
        );
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_offline_collect_hunter_time
        ON offline_collect(hunterId, collectedAtEpoch);
        """
    )

    # -------------------------
    # bans (account moderation)
    # -------------------------
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS bans(
            account_id TEXT PRIMARY KEY,
            reason TEXT,
            banned_until INTEGER,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        );
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_bans_until
        ON bans(banned_until);
        """
    )

    # -------------------------
    # admin_mode
    # -------------------------
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS admin_mode (
            key TEXT PRIMARY KEY,
            enabled INTEGER NOT NULL DEFAULT 0,
            multiplier REAL NOT NULL DEFAULT 1.0,
            updatedAt TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )

    # -------------------------
    # claims (idempotent)  ✅ 표준 컬럼: hunterId/bossId/seasonId
    # -------------------------
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS worldboss_claim (
            hunterId TEXT NOT NULL,
            bossId TEXT NOT NULL,
            seasonId TEXT NOT NULL,
            gold INTEGER NOT NULL,
            exp INTEGER NOT NULL,
            gems INTEGER NOT NULL DEFAULT 0,
            createdAt TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (hunterId, bossId, seasonId)
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pvp_claim (
            hunterId TEXT NOT NULL,
            seasonId TEXT NOT NULL,
            gold INTEGER NOT NULL,
            exp INTEGER NOT NULL,
            gems INTEGER NOT NULL DEFAULT 0,
            createdAt TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (hunterId, seasonId)
        );
        """
    )

    # -------------------------
    # reward_tier (rank -> multiplier)
    # -------------------------
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reward_tier (
            kind TEXT NOT NULL,
            rankMin INTEGER NOT NULL,
            rankMax INTEGER,
            multiplier REAL NOT NULL,
            updatedAt TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (kind, rankMin, rankMax)
        );
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_reward_tier_kind_min
        ON reward_tier(kind, rankMin);
        """
    )

    # -------------------------
    # Auth / IAP / Audit (commercial baseline)
    # -------------------------
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS accounts(
            account_id TEXT PRIMARY KEY,
            created_at INTEGER NOT NULL
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS account_identities(
            provider TEXT NOT NULL,
            provider_sub TEXT NOT NULL,
            account_id TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            PRIMARY KEY(provider, provider_sub)
        );
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_account_identities_account
        ON account_identities(account_id);
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS refresh_tokens(
            refresh_id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL,
            device_id TEXT NOT NULL,
            token_hash TEXT NOT NULL,
            expires_at INTEGER NOT NULL,
            revoked_at INTEGER,
            created_at INTEGER NOT NULL
        );
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_refresh_tokens_account_device
        ON refresh_tokens(account_id, device_id);
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS purchases(
            purchase_id TEXT PRIMARY KEY,
            provider TEXT NOT NULL,
            provider_tx_id TEXT NOT NULL,
            account_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            status TEXT NOT NULL,
            raw_json TEXT,
            created_at INTEGER NOT NULL
        );
        """
    )
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_purchases_provider_tx
        ON purchases(provider, provider_tx_id);
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS currency_ledger(
            ledger_id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL,
            currency TEXT NOT NULL,
            amount INTEGER NOT NULL,
            source_kind TEXT NOT NULL,
            source_id TEXT NOT NULL,
            created_at INTEGER NOT NULL
        );
        """
    )
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_currency_ledger_source
        ON currency_ledger(source_kind, source_id);
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_currency_ledger_account_time
        ON currency_ledger(account_id, created_at DESC);
        """
    )


    # -------------------------
    # tutorial / story / ads claim persistence
    # -------------------------
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tutorial_progress (
            accountId TEXT NOT NULL,
            questId TEXT NOT NULL,
            completedAt TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (accountId, questId)
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS story_progress (
            accountId TEXT PRIMARY KEY,
            currentChapterId TEXT NOT NULL,
            updatedAt TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ad_offer_claim (
            accountId TEXT NOT NULL,
            offerId TEXT NOT NULL,
            adViewToken TEXT NOT NULL,
            claimDate TEXT NOT NULL,
            rewardType TEXT NOT NULL,
            rewardAmount INTEGER NOT NULL,
            createdAt TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (accountId, adViewToken)
        );
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ad_offer_claim_daily
        ON ad_offer_claim(accountId, offerId, claimDate);
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ad_view_session (
            accountId TEXT NOT NULL,
            adViewToken TEXT NOT NULL,
            offerId TEXT NOT NULL,
            placement TEXT NOT NULL,
            hunterId TEXT,
            issuedAt INTEGER NOT NULL,
            expiresAt INTEGER NOT NULL,
            consumedAt INTEGER,
            verifiedAt INTEGER,
            completionProof TEXT,
            completionToken TEXT,
            adNetwork TEXT,
            adUnitId TEXT,
            status TEXT NOT NULL DEFAULT 'issued',
            PRIMARY KEY (accountId, adViewToken)
        );
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ad_view_session_account_offer
        ON ad_view_session(accountId, offerId, expiresAt DESC);
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS mailbox_messages (
            messageId TEXT PRIMARY KEY,
            accountId TEXT NOT NULL,
            messageType TEXT NOT NULL,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            rewardCurrency TEXT,
            rewardAmount INTEGER NOT NULL DEFAULT 0,
            sourceKind TEXT NOT NULL,
            sourceId TEXT NOT NULL,
            isClaimed INTEGER NOT NULL DEFAULT 0,
            createdAt INTEGER NOT NULL,
            claimedAt INTEGER
        );
        """
    )
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_mailbox_source
        ON mailbox_messages(sourceKind, sourceId);
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS announcements (
            announcementId TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            startsAt INTEGER NOT NULL,
            endsAt INTEGER NOT NULL,
            priority INTEGER NOT NULL DEFAULT 100,
            isEnabled INTEGER NOT NULL DEFAULT 1,
            createdAt INTEGER NOT NULL,
            updatedAt INTEGER NOT NULL
        );
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_logs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,
            actor TEXT NOT NULL,
            target TEXT,
            payload_json TEXT,
            created_at INTEGER NOT NULL
        );
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_audit_logs_time
        ON audit_logs(created_at DESC);
        """
    )

    # -------------------------
    # IAP product catalog
    # -------------------------
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS iap_products(
            product_id TEXT PRIMARY KEY,
            currency TEXT NOT NULL,
            amount INTEGER NOT NULL,
            updatedAt TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )

    # -------------------------
    # Tier definitions (season-based expansion)
    # -------------------------
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tier_defs(
            season_id TEXT NOT NULL,
            tier_id TEXT NOT NULL,
            multiplier REAL NOT NULL,
            updatedAt TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY(season_id, tier_id)
        );
        """
    )

    # -------------------------
    # MBTI traits
    # -------------------------
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS mbti_traits(
            mbti TEXT PRIMARY KEY,
            atk_mul REAL NOT NULL DEFAULT 1.0,
            hp_mul REAL NOT NULL DEFAULT 1.0,
            def_mul REAL NOT NULL DEFAULT 1.0,
            gold_mul REAL NOT NULL DEFAULT 1.0,
            exp_mul REAL NOT NULL DEFAULT 1.0,
            updatedAt TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )

    # -------------------------
    # Promotion nodes
    # -------------------------
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS promotion_nodes(
            node_id TEXT PRIMARY KEY,
            parent_node_id TEXT,
            job_id TEXT NOT NULL,
            choice_group TEXT,
            promotion_multiplier REAL NOT NULL DEFAULT 1.0,
            stat_bonus_json TEXT NOT NULL DEFAULT '{}',
            skill_unlock_json TEXT NOT NULL DEFAULT '[]',
            updatedAt TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )

    # -------------------------
    # Item definitions
    # -------------------------
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS item_defs(
            item_id TEXT PRIMARY KEY,
            season_id TEXT NOT NULL,
            tier_id TEXT NOT NULL,
            slot TEXT NOT NULL,
            atk_mul REAL NOT NULL DEFAULT 1.0,
            hp_mul REAL NOT NULL DEFAULT 1.0,
            def_mul REAL NOT NULL DEFAULT 1.0,
            skill_mul REAL NOT NULL DEFAULT 1.0,
            updatedAt TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )

    # -------------------------
    # worldboss / pvp seasons (persisted catalog)
    # -------------------------
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS worldbosses(
            boss_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            max_hp INTEGER NOT NULL,
            difficulty INTEGER NOT NULL,
            base_gold INTEGER NOT NULL,
            base_exp INTEGER NOT NULL,
            base_gems INTEGER NOT NULL DEFAULT 0,
            updatedAt TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pvp_seasons(
            season_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            base_gold INTEGER NOT NULL,
            base_exp INTEGER NOT NULL,
            base_gems INTEGER NOT NULL DEFAULT 0,
            updatedAt TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )

    conn.execute("COMMIT;")

    # --- seed (idempotent) ---
    _ensure_default_reward_tiers(conn)
    _ensure_default_iap_products(conn)
    _ensure_default_tiers(conn)
    _ensure_default_mbti_traits(conn)
    _seed_defaults(conn)


def _seed_defaults(conn: sqlite3.Connection) -> None:
    """Insert small sensible defaults when tables are empty."""
    # worldbosses
    try:
        cnt = conn.execute("SELECT COUNT(1) FROM worldbosses;").fetchone()[0]
        if int(cnt) == 0:
            conn.execute(
                """
                INSERT INTO worldbosses(boss_id,name,max_hp,difficulty,base_gold,base_exp,base_gems,updatedAt)
                VALUES('wb_s1_1','Ancient Demon',1000000,5,1000,500,10,datetime('now'));
                """
            )
    except Exception:
        pass

    # pvp seasons
    try:
        cnt = conn.execute("SELECT COUNT(1) FROM pvp_seasons;").fetchone()[0]
        if int(cnt) == 0:
            conn.execute(
                """
                INSERT INTO pvp_seasons(season_id,name,base_gold,base_exp,base_gems,updatedAt)
                VALUES('pvp_s1','Arena Season S1',500,250,5,datetime('now'));
                """
            )
    except Exception:
        pass


def _ensure_default_reward_tiers(conn: sqlite3.Connection) -> None:
    """테이블이 비어있을 때만 기본 곡선 삽입."""
    cur = conn.execute("SELECT COUNT(1) FROM reward_tier;")
    n = cur.fetchone()[0]
    if n and int(n) > 0:
        return

    defaults = [
        ("worldboss", 1, 1, 1.0),
        ("worldboss", 2, 10, 0.7),
        ("worldboss", 11, 50, 0.4),
        ("worldboss", 51, 200, 0.25),
        ("worldboss", 201, None, 0.15),
        ("pvp", 1, 1, 1.0),
        ("pvp", 2, 10, 0.7),
        ("pvp", 11, 50, 0.4),
        ("pvp", 51, 200, 0.25),
        ("pvp", 201, None, 0.15),
    ]

    for kind, rmin, rmax, mul in defaults:
        conn.execute(
            """
            INSERT OR IGNORE INTO reward_tier(kind, rankMin, rankMax, multiplier)
            VALUES (?, ?, ?, ?);
            """,
            (kind, rmin, rmax, mul),
        )


def _ensure_default_iap_products(conn: sqlite3.Connection) -> None:
    """Keep minimal demo products.

    Production should overwrite via admin tooling (or migration scripts).
    """
    # Insert only when empty
    cur = conn.execute("SELECT COUNT(1) FROM iap_products;")
    n = int(cur.fetchone()[0])
    if n > 0:
        return

    defaults = [
        ("gems_pack_small", "gems", 100),
        ("gems_pack_medium", "gems", 550),
        ("gems_pack_large", "gems", 1200),
    ]
    for pid, curcy, amt in defaults:
        conn.execute(
            """
            INSERT OR IGNORE INTO iap_products(product_id, currency, amount)
            VALUES(?,?,?);
            """,
            (pid, curcy, int(amt)),
        )


def _ensure_default_tiers(conn: sqlite3.Connection) -> None:
    """Season-based tier multipliers.

    Tiers are designed to control inflation while keeping old content valid.
    """
    cur = conn.execute("SELECT COUNT(1) FROM tier_defs;")
    n = int(cur.fetchone()[0])
    if n > 0:
        return

    defaults = [
        ("S1", "T1", 1.0),
        ("S1", "T2", 3.0),
        ("S1", "T3", 9.0),
    ]
    for season_id, tier_id, mul in defaults:
        conn.execute(
            """
            INSERT OR IGNORE INTO tier_defs(season_id, tier_id, multiplier)
            VALUES(?,?,?);
            """,
            (season_id, tier_id, float(mul)),
        )


def _ensure_default_mbti_traits(conn: sqlite3.Connection) -> None:
    """Insert balanced 16-type MBTI modifiers.

    Rule of thumb:
      - Each type has small pros/cons within ±10%.
      - No absolute dominance: sum of (atk,hp,def,gold,exp) stays around 5.0.
    """
    # Always ensure neutral type exists for backward compatibility / deterministic tests.
    conn.execute(
        """
        INSERT OR IGNORE INTO mbti_traits(mbti, atk_mul, hp_mul, def_mul, gold_mul, exp_mul)
        VALUES('NONE', 1.0, 1.0, 1.0, 1.0, 1.0);
        """
    )

    cur = conn.execute("SELECT COUNT(1) FROM mbti_traits;")
    n = int(cur.fetchone()[0])
    if n > 1:
        # already has presets (and maybe NONE)
        return

    # Balanced preset (can be tuned later in DB)
    presets = {
        "INTJ": (1.08, 0.95, 0.97, 1.00, 1.02),
        "INTP": (1.06, 0.96, 0.98, 1.00, 1.02),
        "ENTJ": (1.07, 0.97, 0.96, 1.01, 0.99),
        "ENTP": (1.05, 0.97, 0.97, 1.02, 0.99),
        "INFJ": (1.03, 1.02, 0.97, 0.99, 0.99),
        "INFP": (1.02, 1.03, 0.97, 0.99, 0.99),
        "ENFJ": (1.04, 1.01, 0.97, 1.00, 0.98),
        "ENFP": (1.03, 1.01, 0.97, 1.01, 0.98),
        "ISTJ": (0.98, 1.05, 1.05, 0.97, 0.95),
        "ISFJ": (0.99, 1.06, 1.03, 0.97, 0.95),
        "ESTJ": (1.02, 1.04, 1.02, 0.96, 0.96),
        "ESFJ": (1.01, 1.05, 1.02, 0.96, 0.96),
        "ISTP": (1.04, 0.98, 1.03, 0.98, 0.97),
        "ISFP": (1.03, 0.99, 1.02, 0.98, 0.98),
        "ESTP": (1.06, 0.97, 1.00, 0.99, 0.98),
        "ESFP": (1.05, 0.98, 1.00, 1.00, 0.97),
    }
    for mbti, (atk, hp, df, gold, exp) in presets.items():
        conn.execute(
            """
            INSERT OR IGNORE INTO mbti_traits(mbti, atk_mul, hp_mul, def_mul, gold_mul, exp_mul)
            VALUES(?,?,?,?,?,?);
            """,
            (mbti, float(atk), float(hp), float(df), float(gold), float(exp)),
        )


# -------------------------
# admin_mode
# -------------------------
def upsert_admin_mode(key: str, enabled: bool, multiplier: float) -> Dict[str, Any]:
    conn = get_conn()
    k = str(key).strip()
    en = 1 if bool(enabled) else 0
    try:
        mul = float(multiplier)
    except Exception:
        mul = 1.0

    if mul <= 0:
        mul = 1.0

    conn.execute(
        """
        INSERT INTO admin_mode(key, enabled, multiplier, updatedAt)
        VALUES (?, ?, ?, datetime('now'))
        ON CONFLICT(key)
        DO UPDATE SET enabled=excluded.enabled, multiplier=excluded.multiplier, updatedAt=datetime('now');
        """,
        (k, en, mul),
    )
    return {"key": k, "enabled": bool(en), "multiplier": float(mul)}


def get_admin_mode(key: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.execute("SELECT key, enabled, multiplier, updatedAt FROM admin_mode WHERE key=?;", (str(key),))
    row = cur.fetchone()
    if not row:
        return None
    return {"key": row[0], "enabled": bool(row[1]), "multiplier": float(row[2]), "updatedAt": row[3]}


def list_admin_modes():
    conn = get_conn()
    cur = conn.execute("SELECT key, enabled, multiplier, updatedAt FROM admin_mode ORDER BY key ASC;")
    out = []
    for row in cur.fetchall():
        out.append({"key": row[0], "enabled": bool(row[1]), "multiplier": float(row[2]), "updatedAt": row[3]})
    return out


# -------------------------
# offline_collect (idempotent offline reward)
# -------------------------
def get_collect(hunterId: str, collectedAtEpoch: int) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.execute(
        """
        SELECT hunterId, collectedAtEpoch, gold, exp, gems, createdAt
        FROM offline_collect
        WHERE hunterId=? AND collectedAtEpoch=?;
        """,
        (str(hunterId), int(collectedAtEpoch)),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {
        "hunterId": row[0],
        "collectedAtEpoch": int(row[1]),
        "gold": int(row[2]),
        "exp": int(row[3]),
        "gems": int(row[4]),
        "createdAt": row[5],
    }


def insert_collect(hunterId: str, collectedAtEpoch: int, gold: int, exp: int, gems: int = 0) -> bool:
    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO offline_collect(hunterId, collectedAtEpoch, gold, exp, gems, createdAt)
            VALUES (?, ?, ?, ?, ?, datetime('now'));
            """,
            (str(hunterId), int(collectedAtEpoch), int(gold), int(exp), int(gems)),
        )
        return True
    except sqlite3.IntegrityError:
        return False


# -------------------------
# claims (idempotent)
# -------------------------
def get_worldboss_claim(hunterId: str, bossId: str, seasonId: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.execute(
        """
        SELECT hunterId, bossId, seasonId, gold, exp, gems, createdAt
        FROM worldboss_claim
        WHERE hunterId=? AND bossId=? AND seasonId=?;
        """,
        (str(hunterId), str(bossId), str(seasonId)),
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


def insert_worldboss_claim(hunterId: str, bossId: str, seasonId: str, gold: int, exp: int, gems: int) -> bool:
    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO worldboss_claim(hunterId, bossId, seasonId, gold, exp, gems, createdAt)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'));
            """,
            (str(hunterId), str(bossId), str(seasonId), int(gold), int(exp), int(gems)),
        )
        return True
    except sqlite3.IntegrityError:
        return False


def get_pvp_claim(hunterId: str, seasonId: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.execute(
        """
        SELECT hunterId, seasonId, gold, exp, gems, createdAt
        FROM pvp_claim
        WHERE hunterId=? AND seasonId=?;
        """,
        (str(hunterId), str(seasonId)),
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


def insert_pvp_claim(hunterId: str, seasonId: str, gold: int, exp: int, gems: int) -> bool:
    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO pvp_claim(hunterId, seasonId, gold, exp, gems, createdAt)
            VALUES (?, ?, ?, ?, ?, datetime('now'));
            """,
            (str(hunterId), str(seasonId), int(gold), int(exp), int(gems)),
        )
        return True
    except sqlite3.IntegrityError:
        return False


# -------------------------
# reward_tier (rank -> multiplier)
# -------------------------
def list_reward_tiers(kind: str):
    conn = get_conn()
    cur = conn.execute(
        """
        SELECT kind, rankMin, rankMax, multiplier, updatedAt
        FROM reward_tier
        WHERE kind=?
        ORDER BY rankMin ASC, COALESCE(rankMax, 2147483647) ASC;
        """,
        (str(kind),),
    )
    out = []
    for row in cur.fetchall():
        out.append(
            {
                "kind": row[0],
                "rankMin": int(row[1]),
                "rankMax": None if row[2] is None else int(row[2]),
                "multiplier": float(row[3]),
                "updatedAt": row[4],
            }
        )
    return out


def upsert_reward_tier(kind: str, rankMin: int, rankMax: Optional[int], multiplier: float) -> Dict[str, Any]:
    conn = get_conn()
    k = str(kind).strip().lower()
    if k not in ("worldboss", "pvp"):
        raise ValueError("kind must be 'worldboss' or 'pvp'")

    rmin = int(rankMin)
    rmax = None if rankMax is None else int(rankMax)
    mul = float(multiplier)

    if rmin <= 0:
        raise ValueError("rankMin must be >= 1")
    if rmax is not None and rmax < rmin:
        raise ValueError("rankMax must be >= rankMin")
    if mul <= 0:
        raise ValueError("multiplier must be > 0")

    conn.execute(
        """
        INSERT INTO reward_tier(kind, rankMin, rankMax, multiplier, updatedAt)
        VALUES (?, ?, ?, ?, datetime('now'))
        ON CONFLICT(kind, rankMin, rankMax)
        DO UPDATE SET multiplier=excluded.multiplier, updatedAt=datetime('now');
        """,
        (k, rmin, rmax, mul),
    )

    return {"kind": k, "rankMin": rmin, "rankMax": rmax, "multiplier": mul}




def bulk_replace_reward_tiers(kind: str, rows: List[Tuple[int, Optional[int], float]]) -> Dict[str, Any]:
    """Replace all reward_tier rows for a kind with the supplied sorted list.

    Args:
        kind: worldboss or pvp
        rows: iterable of (rankMin, rankMax, multiplier)

    Returns:
        summary dict with count
    """
    conn = get_conn()
    k = str(kind).strip().lower()
    if k not in ("worldboss", "pvp"):
        raise ValueError("kind must be 'worldboss' or 'pvp'")

    normalized: List[Tuple[int, Optional[int], float]] = []
    for rankMin, rankMax, multiplier in rows:
        rmin = int(rankMin)
        rmax = None if rankMax is None else int(rankMax)
        mul = float(multiplier)
        if rmin <= 0:
            raise ValueError("rankMin must be >= 1")
        if rmax is not None and rmax < rmin:
            raise ValueError("rankMax must be >= rankMin")
        if mul <= 0:
            raise ValueError("multiplier must be > 0")
        normalized.append((rmin, rmax, mul))

    normalized.sort(key=lambda x: (x[0], 2147483647 if x[1] is None else x[1]))

    with conn:
        conn.execute("DELETE FROM reward_tier WHERE kind=?", (k,))
        for rmin, rmax, mul in normalized:
            conn.execute(
                """
                INSERT INTO reward_tier(kind, rankMin, rankMax, multiplier, updatedAt)
                VALUES (?, ?, ?, ?, datetime('now'))
                """,
                (k, rmin, rmax, mul),
            )

    return {"kind": k, "count": len(normalized)}


def get_rank_multiplier(kind: str, rank: int) -> float:
    """
    DB의 reward_tier로 rank->multiplier 매핑.
    매칭이 없거나 이상값이면 안전하게 1.0.
    """
    r = int(rank)
    conn = get_conn()
    cur = conn.execute(
        """
        SELECT multiplier
        FROM reward_tier
        WHERE kind=?
          AND rankMin <= ?
          AND (rankMax IS NULL OR rankMax >= ?)
        ORDER BY rankMin DESC, COALESCE(rankMax, 2147483647) ASC
        LIMIT 1
        """,
        (str(kind), r, r),
    )
    row = cur.fetchone()
    if not row:
        return 1.0
    try:
        m = float(row[0])
        return m if m > 0 else 1.0
    except Exception:
        return 1.0


def _now_epoch() -> int:
    return int(time.time())


# -------------------------
# bans
# -------------------------
def upsert_ban(account_id: str, reason: str = "", banned_until: Optional[int] = None) -> Dict[str, Any]:
    conn = get_conn()
    now = _now_epoch()
    conn.execute(
        """
        INSERT INTO bans(account_id, reason, banned_until, created_at, updated_at)
        VALUES(?,?,?,?,?)
        ON CONFLICT(account_id)
        DO UPDATE SET reason=excluded.reason, banned_until=excluded.banned_until, updated_at=excluded.updated_at;
        """,
        (str(account_id), str(reason), None if banned_until is None else int(banned_until), now, now),
    )
    return get_ban(account_id) or {"account_id": str(account_id), "reason": str(reason), "banned_until": banned_until}


def clear_ban(account_id: str) -> bool:
    conn = get_conn()
    cur = conn.execute("DELETE FROM bans WHERE account_id=?;", (str(account_id),))
    return cur.rowcount == 1


def get_ban(account_id: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    row = conn.execute(
        "SELECT account_id, reason, banned_until, created_at, updated_at FROM bans WHERE account_id=?;",
        (str(account_id),),
    ).fetchone()
    if not row:
        return None
    return {
        "account_id": row[0],
        "reason": row[1],
        "banned_until": row[2],  # None이면 영구 밴
        "created_at": int(row[3]),
        "updated_at": int(row[4]),
    }


def is_banned(account_id: str, now: Optional[int] = None) -> bool:
    ban = get_ban(account_id)
    if not ban:
        return False
    # banned_until None => permanent
    if ban["banned_until"] is None:
        return True
    now_ts = int(now if now is not None else _now_epoch())
    return now_ts < int(ban["banned_until"])


# -------------------------
# currency_ledger (idempotent)
# -------------------------
def insert_currency_ledger_idempotent(
    account_id: str,
    currency: str,
    amount: int,
    source_kind: str,
    source_id: str,
) -> bool:
    """
    Insert currency_ledger with unique (source_kind, source_id) semantics.
    Returns True if inserted; False if already existed.
    """
    conn = get_conn()
    cur = conn.execute(
        """
        INSERT OR IGNORE INTO currency_ledger(
          ledger_id, account_id, currency, amount, source_kind, source_id, created_at
        ) VALUES(?,?,?,?,?,?,?)
        """,
        (
            f"ldg_{source_kind}:{source_id}",
            str(account_id),
            str(currency),
            int(amount),
            str(source_kind),
            str(source_id),
            _now_epoch(),
        ),
    )
    return cur.rowcount == 1


# -------------------------
# worldbosses / pvp_seasons (persisted catalog)
# -------------------------
def upsert_worldboss_db(boss: Dict[str, Any]) -> Dict[str, Any]:
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO worldbosses(boss_id,name,max_hp,difficulty,base_gold,base_exp,base_gems,updatedAt)
        VALUES(?,?,?,?,?,?,?,datetime('now'))
        ON CONFLICT(boss_id) DO UPDATE SET
          name=excluded.name,
          max_hp=excluded.max_hp,
          difficulty=excluded.difficulty,
          base_gold=excluded.base_gold,
          base_exp=excluded.base_exp,
          base_gems=excluded.base_gems,
          updatedAt=datetime('now');
        """,
        (
            str(boss.get("bossId") or boss.get("boss_id")),
            str(boss.get("name")),
            int(boss.get("maxHp") or boss.get("max_hp")),
            int(boss.get("difficulty")),
            int(boss.get("baseGold") or boss.get("base_gold")),
            int(boss.get("baseExp") or boss.get("base_exp")),
            int(boss.get("baseGems") or boss.get("base_gems") or 0),
        ),
    )
    return get_worldboss_db(str(boss.get("bossId") or boss.get("boss_id"))) or boss


def get_worldboss_db(boss_id: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    row = conn.execute(
        """
        SELECT boss_id,name,max_hp,difficulty,base_gold,base_exp,base_gems,updatedAt
        FROM worldbosses
        WHERE boss_id=?
        """,
        (str(boss_id),),
    ).fetchone()
    if not row:
        return None
    return {
        "bossId": row[0],
        "name": row[1],
        "maxHp": int(row[2]),
        "difficulty": int(row[3]),
        "baseGold": int(row[4]),
        "baseExp": int(row[5]),
        "baseGems": int(row[6]),
        "updatedAt": row[7],
    }


def list_worldbosses_db() -> list[Dict[str, Any]]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT boss_id,name,max_hp,difficulty,base_gold,base_exp,base_gems,updatedAt FROM worldbosses ORDER BY boss_id ASC"
    ).fetchall()
    return [
        {
            "bossId": r[0],
            "name": r[1],
            "maxHp": int(r[2]),
            "difficulty": int(r[3]),
            "baseGold": int(r[4]),
            "baseExp": int(r[5]),
            "baseGems": int(r[6]),
            "updatedAt": r[7],
        }
        for r in rows
    ]


def upsert_pvp_season_db(season: Dict[str, Any]) -> Dict[str, Any]:
    conn = get_conn()
    sid = str(season.get("seasonId") or season.get("season_id"))
    conn.execute(
        """
        INSERT INTO pvp_seasons(season_id,name,base_gold,base_exp,base_gems,updatedAt)
        VALUES(?,?,?,?,?,datetime('now'))
        ON CONFLICT(season_id) DO UPDATE SET
          name=excluded.name,
          base_gold=excluded.base_gold,
          base_exp=excluded.base_exp,
          base_gems=excluded.base_gems,
          updatedAt=datetime('now');
        """,
        (
            sid,
            str(season.get("name")),
            int(season.get("baseGold") or season.get("base_gold")),
            int(season.get("baseExp") or season.get("base_exp")),
            int(season.get("baseGems") or season.get("base_gems") or 0),
        ),
    )
    return get_pvp_season_db(sid) or season


def get_pvp_season_db(season_id: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    row = conn.execute(
        """
        SELECT season_id,name,base_gold,base_exp,base_gems,updatedAt
        FROM pvp_seasons
        WHERE season_id=?
        """,
        (str(season_id),),
    ).fetchone()
    if not row:
        return None
    return {
        "seasonId": row[0],
        "name": row[1],
        "baseGold": int(row[2]),
        "baseExp": int(row[3]),
        "baseGems": int(row[4]),
        "updatedAt": row[5],
    }


def list_pvp_seasons_db() -> list[Dict[str, Any]]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT season_id,name,base_gold,base_exp,base_gems,updatedAt FROM pvp_seasons ORDER BY season_id ASC"
    ).fetchall()
    return [
        {
            "seasonId": r[0],
            "name": r[1],
            "baseGold": int(r[2]),
            "baseExp": int(r[3]),
            "baseGems": int(r[4]),
            "updatedAt": r[5],
        }
        for r in rows
    ]




# -------------------------
# tutorial / story / ads claim
# -------------------------


def complete_tutorial_quest(account_id: str, quest_id: str) -> List[Dict[str, Any]]:
    conn = get_conn()
    conn.execute(
        """
        INSERT OR IGNORE INTO tutorial_progress(accountId, questId, completedAt)
        VALUES(?, ?, datetime('now'));
        """,
        (str(account_id), str(quest_id)),
    )
    cur = conn.execute(
        "SELECT accountId, questId, completedAt FROM tutorial_progress WHERE accountId=? AND questId=?;",
        (str(account_id), str(quest_id)),
    )
    row = cur.fetchone()
    return {"accountId": row[0], "questId": row[1], "completedAt": row[2]}


def list_tutorial_progress(account_id: str) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.execute(
        "SELECT accountId, questId, completedAt FROM tutorial_progress WHERE accountId=? ORDER BY completedAt ASC, questId ASC;",
        (str(account_id),),
    )
    rows = cur.fetchall()
    return [{"accountId": r[0], "questId": r[1], "completedAt": r[2]} for r in rows]


def upsert_story_progress(account_id: str, chapter_id: str) -> Dict[str, Any]:
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO story_progress(accountId, currentChapterId, updatedAt)
        VALUES(?, ?, datetime('now'))
        ON CONFLICT(accountId) DO UPDATE SET currentChapterId=excluded.currentChapterId, updatedAt=datetime('now');
        """,
        (str(account_id), str(chapter_id)),
    )
    cur = conn.execute(
        "SELECT accountId, currentChapterId, updatedAt FROM story_progress WHERE accountId=?;",
        (str(account_id),),
    )
    row = cur.fetchone()
    return {"accountId": row[0], "currentChapterId": row[1], "updatedAt": row[2]}


def get_story_progress(account_id: str) -> Dict[str, Any] | None:
    conn = get_conn()
    cur = conn.execute(
        "SELECT accountId, currentChapterId, updatedAt FROM story_progress WHERE accountId=?;",
        (str(account_id),),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {"accountId": row[0], "currentChapterId": row[1], "updatedAt": row[2]}


def count_daily_ad_claims(account_id: str, offer_id: str, claim_date: str) -> int:
    conn = get_conn()
    cur = conn.execute(
        "SELECT COUNT(*) FROM ad_offer_claim WHERE accountId=? AND offerId=? AND claimDate=?;",
        (str(account_id), str(offer_id), str(claim_date)),
    )
    row = cur.fetchone()
    return int(row[0] if row else 0)


def count_lifetime_ad_claims(account_id: str) -> int:
    conn = get_conn()
    cur = conn.execute(
        "SELECT COUNT(*) FROM ad_offer_claim WHERE accountId=?;",
        (str(account_id),),
    )
    row = cur.fetchone()
    return int(row[0] if row else 0)


def get_ad_claim_by_token(account_id: str, ad_view_token: str) -> Dict[str, Any] | None:
    conn = get_conn()
    cur = conn.execute(
        """
        SELECT accountId, offerId, adViewToken, claimDate, rewardType, rewardAmount, createdAt
        FROM ad_offer_claim
        WHERE accountId=? AND adViewToken=?;
        """,
        (str(account_id), str(ad_view_token)),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {
        "accountId": row[0],
        "offerId": row[1],
        "adViewToken": row[2],
        "claimDate": row[3],
        "rewardType": row[4],
        "rewardAmount": row[5],
        "createdAt": row[6],
    }


def insert_ad_claim(account_id: str, offer_id: str, ad_view_token: str, claim_date: str, reward_type: str, reward_amount: int) -> bool:
    conn = get_conn()
    cur = conn.execute(
        """
        INSERT OR IGNORE INTO ad_offer_claim(accountId, offerId, adViewToken, claimDate, rewardType, rewardAmount)
        VALUES(?, ?, ?, ?, ?, ?);
        """,
        (str(account_id), str(offer_id), str(ad_view_token), str(claim_date), str(reward_type), int(reward_amount)),
    )
    return int(getattr(cur, "rowcount", 0) or 0) > 0

# -------------------------
# ad sessions / liveops / account summary helpers
# -------------------------

def create_ad_view_session(account_id: str, offer_id: str, ad_view_token: str, placement: str, hunter_id: str | None, ttl_sec: int = 900) -> Dict[str, Any]:
    conn = get_conn()
    now = _now_epoch()
    expires_at = now + max(60, int(ttl_sec))
    conn.execute(
        """
        INSERT OR REPLACE INTO ad_view_session(accountId, adViewToken, offerId, placement, hunterId, issuedAt, expiresAt, consumedAt, verifiedAt, completionProof, completionToken, adNetwork, adUnitId, status)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (str(account_id), str(ad_view_token), str(offer_id), str(placement), str(hunter_id) if hunter_id else None, now, expires_at, None, None, None, None, None, None, "issued"),
    )
    return get_ad_view_session(account_id, ad_view_token)


def get_ad_view_session(account_id: str, ad_view_token: str) -> Dict[str, Any] | None:
    conn = get_conn()
    row = conn.execute(
        """
        SELECT accountId, adViewToken, offerId, placement, hunterId, issuedAt, expiresAt, consumedAt, verifiedAt, completionProof, completionToken, adNetwork, adUnitId, status
        FROM ad_view_session WHERE accountId=? AND adViewToken=?
        """,
        (str(account_id), str(ad_view_token)),
    ).fetchone()
    if not row:
        return None
    return {
        "accountId": row[0],
        "adViewToken": row[1],
        "offerId": row[2],
        "placement": row[3],
        "hunterId": row[4],
        "issuedAt": int(row[5]),
        "expiresAt": int(row[6]),
        "consumedAt": int(row[7]) if row[7] is not None else None,
        "verifiedAt": int(row[8]) if row[8] is not None else None,
        "completionProof": row[9],
        "completionToken": row[10],
        "adNetwork": row[11],
        "adUnitId": row[12],
        "status": row[13],
    }


def verify_ad_view_session(account_id: str, ad_view_token: str, completion_proof: str, ad_network: str, ad_unit_id: str) -> Dict[str, Any] | None:
    conn = get_conn()
    session = get_ad_view_session(account_id, ad_view_token)
    if not session:
        return None
    if session["status"] == "verified":
        return session
    if session["status"] != "issued":
        return None
    now = _now_epoch()
    if session["expiresAt"] < now:
        return None
    completion_token = f"adc_{str(ad_view_token)[-12:]}"
    conn.execute(
        """
        UPDATE ad_view_session
        SET verifiedAt=?, completionProof=?, completionToken=?, adNetwork=?, adUnitId=?, status='verified'
        WHERE accountId=? AND adViewToken=? AND status='issued' AND expiresAt>=?
        """,
        (now, str(completion_proof), completion_token, str(ad_network), str(ad_unit_id), str(account_id), str(ad_view_token), now),
    )
    return get_ad_view_session(account_id, ad_view_token)


def consume_ad_view_session(account_id: str, ad_view_token: str, completion_token: str | None = None) -> bool:
    conn = get_conn()
    params = [_now_epoch(), str(account_id), str(ad_view_token), _now_epoch()]
    completion_sql = ""
    if completion_token is not None:
        completion_sql = " AND completionToken=?"
        params.append(str(completion_token))
    cur = conn.execute(
        f"""
        UPDATE ad_view_session
        SET consumedAt=?, status='consumed'
        WHERE accountId=? AND adViewToken=? AND expiresAt>=? AND status='verified'{completion_sql}
        """,
        tuple(params),
    )
    return int(getattr(cur, "rowcount", 0) or 0) == 1


def insert_mailbox_message(message_id: str, account_id: str, title: str, body: str, reward_currency: str | None, reward_amount: int, source_kind: str, source_id: str, message_type: str = "reward") -> bool:
    conn = get_conn()
    cur = conn.execute(
        """
        INSERT OR IGNORE INTO mailbox_messages(messageId, accountId, messageType, title, body, rewardCurrency, rewardAmount, sourceKind, sourceId, isClaimed, createdAt, claimedAt)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (str(message_id), str(account_id), str(message_type), str(title), str(body), str(reward_currency) if reward_currency else None, int(reward_amount), str(source_kind), str(source_id), 0, _now_epoch(), None),
    )
    return int(getattr(cur, "rowcount", 0) or 0) == 1


def list_mailbox_messages(account_id: str, include_claimed: bool = False) -> List[Dict[str, Any]]:
    conn = get_conn()
    query = "SELECT messageId, accountId, messageType, title, body, rewardCurrency, rewardAmount, sourceKind, sourceId, isClaimed, createdAt, claimedAt FROM mailbox_messages WHERE accountId=?"
    if not include_claimed:
        query += " AND isClaimed=0"
    query += " ORDER BY createdAt DESC, messageId DESC"
    rows = conn.execute(query, (str(account_id),)).fetchall()
    return [{
        "messageId": r[0], "accountId": r[1], "messageType": r[2], "title": r[3], "body": r[4], "rewardCurrency": r[5], "rewardAmount": int(r[6]), "sourceKind": r[7], "sourceId": r[8], "isClaimed": bool(r[9]), "createdAt": int(r[10]), "claimedAt": int(r[11]) if r[11] is not None else None,
    } for r in rows]


def claim_mailbox_message(message_id: str) -> Dict[str, Any] | None:
    conn = get_conn()
    row = conn.execute("SELECT messageId, accountId, rewardCurrency, rewardAmount, isClaimed FROM mailbox_messages WHERE messageId=?", (str(message_id),)).fetchone()
    if not row:
        return None
    if int(row[4]) == 1:
        return {"messageId": row[0], "accountId": row[1], "rewardCurrency": row[2], "rewardAmount": int(row[3]), "status": "already_claimed"}
    conn.execute("UPDATE mailbox_messages SET isClaimed=1, claimedAt=? WHERE messageId=?", (_now_epoch(), str(message_id)))
    return {"messageId": row[0], "accountId": row[1], "rewardCurrency": row[2], "rewardAmount": int(row[3]), "status": "claimed"}


def upsert_announcement(announcement_id: str, title: str, body: str, starts_at: int, ends_at: int, priority: int = 100, is_enabled: bool = True) -> Dict[str, Any]:
    conn = get_conn()
    now = _now_epoch()
    conn.execute(
        """
        INSERT INTO announcements(announcementId, title, body, startsAt, endsAt, priority, isEnabled, createdAt, updatedAt)
        VALUES(?,?,?,?,?,?,?,?,?)
        ON CONFLICT(announcementId) DO UPDATE SET
          title=excluded.title, body=excluded.body, startsAt=excluded.startsAt, endsAt=excluded.endsAt,
          priority=excluded.priority, isEnabled=excluded.isEnabled, updatedAt=excluded.updatedAt
        """,
        (str(announcement_id), str(title), str(body), int(starts_at), int(ends_at), int(priority), 1 if is_enabled else 0, now, now),
    )
    return get_announcement(announcement_id)


def get_announcement(announcement_id: str) -> Dict[str, Any] | None:
    conn = get_conn()
    row = conn.execute("SELECT announcementId, title, body, startsAt, endsAt, priority, isEnabled, createdAt, updatedAt FROM announcements WHERE announcementId=?", (str(announcement_id),)).fetchone()
    if not row:
        return None
    return {"announcementId": row[0], "title": row[1], "body": row[2], "startsAt": int(row[3]), "endsAt": int(row[4]), "priority": int(row[5]), "isEnabled": bool(row[6]), "createdAt": int(row[7]), "updatedAt": int(row[8])}


def list_active_announcements(now: int | None = None) -> List[Dict[str, Any]]:
    current = int(now if now is not None else _now_epoch())
    conn = get_conn()
    rows = conn.execute(
        "SELECT announcementId, title, body, startsAt, endsAt, priority, isEnabled, createdAt, updatedAt FROM announcements WHERE isEnabled=1 AND startsAt<=? AND endsAt>=? ORDER BY priority ASC, startsAt DESC",
        (current, current),
    ).fetchall()
    return [{"announcementId": r[0], "title": r[1], "body": r[2], "startsAt": int(r[3]), "endsAt": int(r[4]), "priority": int(r[5]), "isEnabled": bool(r[6]), "createdAt": int(r[7]), "updatedAt": int(r[8])} for r in rows]


def summarize_account_economy(account_id: str) -> Dict[str, Any]:
    conn = get_conn()
    rows = conn.execute("SELECT currency, COALESCE(SUM(amount),0) FROM currency_ledger WHERE account_id=? GROUP BY currency ORDER BY currency ASC", (str(account_id),)).fetchall()
    balances = {str(r[0]): int(r[1]) for r in rows}
    pending_mail = list_mailbox_messages(account_id, include_claimed=False)
    return {"accountId": str(account_id), "balances": balances, "pendingMailboxCount": len(pending_mail), "pendingMailboxRewards": pending_mail[:20]}



def insert_telemetry_event(event_id: str, account_id: str | None, event_type: str, event_name: str, payload_json: str) -> bool:
    conn = get_conn()
    cur = conn.execute(
        """
        INSERT OR IGNORE INTO telemetry_events(eventId, accountId, eventType, eventName, payloadJson, createdAt)
        VALUES(?,?,?,?,?,?)
        """,
        (str(event_id), str(account_id) if account_id else None, str(event_type), str(event_name), str(payload_json), _now_epoch()),
    )
    return int(getattr(cur, "rowcount", 0) or 0) == 1


def summarize_telemetry(event_type: str | None = None) -> Dict[str, Any]:
    conn = get_conn()
    if event_type:
        rows = conn.execute(
            "SELECT eventType, eventName, COUNT(*) FROM telemetry_events WHERE eventType=? GROUP BY eventType, eventName ORDER BY COUNT(*) DESC, eventName ASC",
            (str(event_type),),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT eventType, eventName, COUNT(*) FROM telemetry_events GROUP BY eventType, eventName ORDER BY COUNT(*) DESC, eventName ASC"
        ).fetchall()
    return {
        "total": sum(int(r[2]) for r in rows),
        "rows": [{"eventType": r[0], "eventName": r[1], "count": int(r[2])} for r in rows],
    }


def upsert_operator_treasury(account_id: str, gold_delta: int = 0, exp_delta: int = 0) -> Dict[str, Any]:
    conn = get_conn()
    now = _now_epoch()
    existing = conn.execute("SELECT operatorGold, operatorExp FROM operator_treasury WHERE accountId=?", (str(account_id),)).fetchone()
    gold = int(existing[0]) if existing else 0
    exp = int(existing[1]) if existing else 0
    gold = max(0, gold + int(gold_delta))
    exp = max(0, exp + int(exp_delta))
    conn.execute(
        """
        INSERT INTO operator_treasury(accountId, operatorGold, operatorExp, updatedAt)
        VALUES(?,?,?,?)
        ON CONFLICT(accountId) DO UPDATE SET
          operatorGold=excluded.operatorGold,
          operatorExp=excluded.operatorExp,
          updatedAt=excluded.updatedAt
        """,
        (str(account_id), gold, exp, now),
    )
    return {"accountId": str(account_id), "operatorGold": gold, "operatorExp": exp, "updatedAt": now}


def get_operator_inventory(account_id: str) -> Dict[str, int]:
    conn = get_conn()
    rows = conn.execute("SELECT itemId, quantity FROM operator_inventory WHERE accountId=? ORDER BY itemId ASC", (str(account_id),)).fetchall()
    return {str(r[0]): int(r[1]) for r in rows if int(r[1]) > 0}


def set_operator_inventory(account_id: str, item_id: str, quantity: int) -> Dict[str, Any]:
    conn = get_conn()
    now = _now_epoch()
    quantity = max(0, int(quantity))
    conn.execute(
        """
        INSERT INTO operator_inventory(accountId, itemId, quantity, updatedAt)
        VALUES(?,?,?,?)
        ON CONFLICT(accountId, itemId) DO UPDATE SET
          quantity=excluded.quantity,
          updatedAt=excluded.updatedAt
        """,
        (str(account_id), str(item_id), quantity, now),
    )
    return {"accountId": str(account_id), "itemId": str(item_id), "quantity": quantity, "updatedAt": now}


def add_operator_inventory(account_id: str, item_id: str, quantity_delta: int) -> Dict[str, Any]:
    current = get_operator_inventory(account_id).get(str(item_id), 0)
    return set_operator_inventory(account_id, item_id, current + int(quantity_delta))


def insert_operator_action_log(log_id: str, account_id: str, action_type: str, result_code: str, detail: str = "", payload_json: str = "{}", hunter_id: str | None = None) -> bool:
    conn = get_conn()
    cur = conn.execute(
        """
        INSERT OR IGNORE INTO operator_action_log(logId, accountId, hunterId, actionType, resultCode, detail, payloadJson, createdAt)
        VALUES(?,?,?,?,?,?,?,?)
        """,
        (str(log_id), str(account_id), str(hunter_id) if hunter_id else None, str(action_type), str(result_code), str(detail), str(payload_json), _now_epoch()),
    )
    return int(getattr(cur, "rowcount", 0) or 0) == 1


def list_operator_action_logs(account_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT logId, accountId, hunterId, actionType, resultCode, detail, payloadJson, createdAt FROM operator_action_log WHERE accountId=? ORDER BY createdAt DESC LIMIT ?",
        (str(account_id), max(1, int(limit))),
    ).fetchall()
    return [
        {
            "logId": r[0],
            "accountId": r[1],
            "hunterId": r[2],
            "actionType": r[3],
            "resultCode": r[4],
            "detail": r[5] or "",
            "payloadJson": r[6] or "{}",
            "createdAt": int(r[7]),
        }
        for r in rows
    ]


def insert_hunter_state_snapshot(snapshot_id: str, hunter_id: str, account_id: str, state_code: str, next_state_code: str, payload_json: str = "{}") -> bool:
    conn = get_conn()
    cur = conn.execute(
        """
        INSERT OR IGNORE INTO hunter_state_snapshot(snapshotId, hunterId, accountId, stateCode, nextStateCode, payloadJson, createdAt)
        VALUES(?,?,?,?,?,?,?)
        """,
        (str(snapshot_id), str(hunter_id), str(account_id), str(state_code), str(next_state_code), str(payload_json), _now_epoch()),
    )
    return int(getattr(cur, "rowcount", 0) or 0) == 1


def list_hunter_state_snapshots(hunter_id: str, limit: int = 12) -> List[Dict[str, Any]]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT snapshotId, hunterId, accountId, stateCode, nextStateCode, payloadJson, createdAt FROM hunter_state_snapshot WHERE hunterId=? ORDER BY createdAt DESC LIMIT ?",
        (str(hunter_id), max(1, int(limit))),
    ).fetchall()
    return [
        {
            "snapshotId": r[0],
            "hunterId": r[1],
            "accountId": r[2],
            "stateCode": r[3],
            "nextStateCode": r[4],
            "payloadJson": r[5] or "{}",
            "createdAt": int(r[6]),
        }
        for r in rows
    ]


def has_operator_mission_claim(account_id: str, mission_id: str, mission_scope: str) -> bool:
    conn = get_conn()
    row = conn.execute(
        "SELECT 1 FROM operator_mission_claim WHERE accountId=? AND missionId=? AND missionScope=?",
        (str(account_id), str(mission_id), str(mission_scope)),
    ).fetchone()
    return row is not None


def insert_operator_mission_claim(account_id: str, mission_id: str, mission_scope: str, reward_json: str = "{}") -> bool:
    conn = get_conn()
    cur = conn.execute(
        "INSERT OR IGNORE INTO operator_mission_claim(accountId, missionId, missionScope, rewardJson, createdAt) VALUES(?,?,?,?,?)",
        (str(account_id), str(mission_id), str(mission_scope), str(reward_json), _now_epoch()),
    )
    return int(getattr(cur, "rowcount", 0) or 0) == 1
