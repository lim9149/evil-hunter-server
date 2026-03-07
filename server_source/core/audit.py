import json
import time
from typing import Any, Dict, Optional

from storage.sqlite_db import get_conn


def write_audit(kind: str, actor: str, target: Optional[str] = None, payload: Optional[Dict[str, Any]] = None) -> None:
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