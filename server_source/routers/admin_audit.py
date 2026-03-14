# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
from fastapi import APIRouter, Depends
from storage.sqlite_db import get_conn
from core.security.deps import require_admin

router = APIRouter()

@router.get("/logs")
def get_logs(limit: int = 200, admin_id: str = Depends(require_admin)):
    # limit 안전 범위
    if limit <= 0:
        limit = 1
    if limit > 500:
        limit = 500

    conn = get_conn()
    rows = conn.execute(
        """
        SELECT id, kind, actor, target, payload_json, created_at
        FROM audit_logs
        ORDER BY id DESC
        LIMIT ?
        """,
        (int(limit),),
    ).fetchall()

    logs = []
    for r in rows:
        logs.append(
            {
                "id": int(r[0]),
                "kind": r[1],
                "actor": r[2],
                "target": r[3],
                "payload_json": r[4],
                "created_at": int(r[5]),
            }
        )

    return {"adminId": admin_id, "logs": logs}