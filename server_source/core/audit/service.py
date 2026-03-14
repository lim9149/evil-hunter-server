# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
"""Audit log service.

All audit events are persisted in the unified SQLite table `audit_logs`
(created by `storage.sqlite_db.ensure_schema`).

Early prototypes used a separate `admin_audit_logs` table. That table is now deprecated;
we keep a small compatibility helper (`write_admin_audit`) for older call sites.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, Optional

from storage.sqlite_db import get_conn


def write_audit(
    kind: str,
    actor: str,
    target: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> None:
    """Persist a single audit event."""
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO audit_logs(kind, actor, target, payload_json, created_at)
        VALUES(?,?,?,?,?)
        """,
        (
            str(kind),
            str(actor),
            None if target is None else str(target),
            None if payload is None else json.dumps(payload, ensure_ascii=False),
            int(time.time()),
        ),
    )
    conn.commit()


def write_admin_audit(admin_id: str, action: str, target: str | None = None, payload: str | None = None) -> None:
    """Legacy helper kept for compatibility with older code paths."""
    try:
        payload_obj = None
        if payload is not None:
            payload_obj = {"payload": payload}
        write_audit(kind=f"admin:{action}", actor=admin_id, target=target, payload=payload_obj)
    except Exception:
        # Never break core flows because of audit write failure.
        return