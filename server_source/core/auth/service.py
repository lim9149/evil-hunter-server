# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
import hashlib
import secrets
import time
from typing import Tuple, Dict

from storage.sqlite_db import get_conn
from core.security.jwt import create_access_token

REFRESH_TTL_SEC = 30 * 86400  # 30d

def _now() -> int:
    return int(time.time())

def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()

def _make_refresh() -> Tuple[str, str, str]:
    refresh_id = secrets.token_hex(16)
    raw = secrets.token_urlsafe(48)
    return refresh_id, raw, _hash_token(raw)

def _parse_refresh(refresh_token: str) -> Tuple[str, str]:
    parts = refresh_token.split(".", 1)
    if len(parts) != 2:
        raise ValueError("invalid refresh token format")
    return parts[0], parts[1]

def ensure_account(account_id: str) -> None:
    conn = get_conn()
    conn.execute(
        """INSERT OR IGNORE INTO accounts(account_id, created_at) VALUES(?,?)""",
        (account_id, _now()),
    )

def issue_refresh(account_id: str, device_id: str) -> str:
    conn = get_conn()
    now = _now()
    refresh_id, raw, token_hash = _make_refresh()
    expires_at = now + REFRESH_TTL_SEC
    conn.execute(
        """
        INSERT INTO refresh_tokens(refresh_id, account_id, device_id, token_hash, expires_at, revoked_at, created_at)
        VALUES(?,?,?,?,?,?,?)
        """,
        (refresh_id, account_id, device_id, token_hash, expires_at, None, now),
    )
    return f"{refresh_id}.{raw}"

def guest_login(device_id: str) -> Dict[str, str]:
    account_id = f"guest_{hashlib.sha256(device_id.encode()).hexdigest()[:16]}"
    ensure_account(account_id)
    access = create_access_token(account_id, scope="player")
    refresh_token = issue_refresh(account_id=account_id, device_id=device_id)
    return {"accountId": account_id, "accessToken": access, "refreshToken": refresh_token}

def rotate_refresh(refresh_token: str, device_id: str) -> Dict[str, str]:
    refresh_id, raw = _parse_refresh(refresh_token)
    token_hash = _hash_token(raw)

    conn = get_conn()
    row = conn.execute(
        """
        SELECT account_id, token_hash, expires_at, revoked_at
        FROM refresh_tokens
        WHERE refresh_id=? AND device_id=?
        """,
        (refresh_id, device_id),
    ).fetchone()
    if not row:
        raise ValueError("refresh not found")
    account_id, stored_hash, expires_at, revoked_at = row
    now = _now()
    if revoked_at is not None:
        raise ValueError("refresh revoked")
    if now >= int(expires_at):
        raise ValueError("refresh expired")
    if str(stored_hash) != token_hash:
        conn.execute("""UPDATE refresh_tokens SET revoked_at=? WHERE refresh_id=?""", (now, refresh_id))
        raise ValueError("refresh mismatch")

    # rotate
    conn.execute("""UPDATE refresh_tokens SET revoked_at=? WHERE refresh_id=?""", (now, refresh_id))

    new_refresh = issue_refresh(account_id=str(account_id), device_id=device_id)
    access = create_access_token(str(account_id), scope="player")
    return {"accountId": str(account_id), "accessToken": access, "refreshToken": new_refresh}

def revoke_device_refreshes(account_id: str, device_id: str) -> None:
    conn = get_conn()
    conn.execute(
        """UPDATE refresh_tokens SET revoked_at=? WHERE account_id=? AND device_id=? AND revoked_at IS NULL""",
        (_now(), account_id, device_id),
    )

# --- OAuth skeletons (verify TODO) ---
def oauth_login(provider: str, provider_sub: str, device_id: str) -> Dict[str, str]:
    conn = get_conn()
    row = conn.execute(
        """SELECT account_id FROM account_identities WHERE provider=? AND provider_sub=?""",
        (provider, provider_sub),
    ).fetchone()

    if row:
        account_id = str(row[0])
    else:
        account_id = f"acc_{secrets.token_hex(12)}"
        ensure_account(account_id)
        conn.execute(
            """INSERT INTO account_identities(provider, provider_sub, account_id, created_at) VALUES(?,?,?,?)""",
            (provider, provider_sub, account_id, _now()),
        )

    access = create_access_token(account_id, scope="player")
    refresh = issue_refresh(account_id, device_id)
    return {"accountId": account_id, "accessToken": access, "refreshToken": refresh}

def link_identity(account_id: str, provider: str, provider_sub: str) -> None:
    conn = get_conn()
    row = conn.execute(
        """SELECT account_id FROM account_identities WHERE provider=? AND provider_sub=?""",
        (provider, provider_sub),
    ).fetchone()
    if row and str(row[0]) != str(account_id):
        raise ValueError("identity already linked to another account")

    conn.execute(
        """
        INSERT INTO account_identities(provider, provider_sub, account_id, created_at)
        VALUES(?,?,?,?)
        ON CONFLICT(provider, provider_sub) DO UPDATE SET account_id=excluded.account_id
        """,
        (provider, provider_sub, account_id, _now()),
    )