from __future__ import annotations

import time
import uuid
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from core.audit import write_audit
from core.security.deps import require_admin
from storage.repo_registry import hunter_repo
from storage.sqlite_db import (
    upsert_ban,
    clear_ban,
    get_ban,
    insert_currency_ledger_idempotent,
)


router = APIRouter()


class GrantCurrencyReq(BaseModel):
    accountId: str
    currency: Literal["gold", "gems", "exp"]
    amount: int = Field(..., description="can be negative for rollback; must be non-zero")
    hunterId: Optional[str] = Field(
        default=None,
        description="Optional. If provided, directly mutates the hunter snapshot for convenience.",
    )
    reason: str = ""
    idempotencyKey: Optional[str] = Field(
        default=None,
        description="Optional. If omitted, uses Idempotency-Key header or auto-generates (not idempotent).",
    )


@router.post("/grant")
def grant_currency(
    req: GrantCurrencyReq,
    admin_id: str = Depends(require_admin),
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
):
    if int(req.amount) == 0:
        raise HTTPException(status_code=400, detail="amount must be non-zero")
    if abs(int(req.amount)) > 1_000_000_000:
        raise HTTPException(status_code=400, detail="amount too large")

    key = (req.idempotencyKey or idempotency_key or "").strip() or None
    source_id = key or str(uuid.uuid4())

    inserted = insert_currency_ledger_idempotent(
        account_id=req.accountId,
        currency=req.currency,
        amount=int(req.amount),
        source_kind="admin_grant",
        source_id=source_id,
    )

    # Convenience: mutate hunter snapshot so gameplay endpoints immediately reflect admin change.
    # IMPORTANT: Only mutate when ledger row is newly inserted (idempotent semantics).
    updated_hunter = None
    if req.hunterId and inserted:
        h = hunter_repo.get(req.hunterId)
        if not h:
            raise HTTPException(status_code=404, detail="hunter not found")
        if h.accountId != req.accountId:
            raise HTTPException(status_code=409, detail="hunter.accountId mismatch")

        if req.currency == "gold":
            h.gold = int(h.gold) + int(req.amount)
        elif req.currency == "gems":
            h.gems = int(h.gems) + int(req.amount)
        elif req.currency == "exp":
            h.exp = int(h.exp) + int(req.amount)
        hunter_repo.upsert(h)
        updated_hunter = h

    write_audit(
        kind="admin:grant_currency",
        actor=admin_id,
        target=req.accountId,
        payload={
            "currency": req.currency,
            "amount": int(req.amount),
            "hunterId": req.hunterId,
            "reason": req.reason,
            "idempotencyKey": key,
            "ledgerInserted": inserted,
        },
    )

    return {
        "ok": True,
        "ledgerInserted": inserted,
        "idempotencyKey": key,
        "sourceId": source_id,
        "hunter": updated_hunter,
    }


class BanReq(BaseModel):
    accountId: str
    reason: str = ""
    durationSec: Optional[int] = Field(
        default=None,
        description="If omitted -> permanent. If provided -> seconds from now.",
    )


@router.post("/ban")
def ban_account(req: BanReq, admin_id: str = Depends(require_admin)):
    now = int(time.time())
    banned_until = None
    if req.durationSec is not None:
        if int(req.durationSec) <= 0:
            raise HTTPException(status_code=400, detail="durationSec must be > 0")
        banned_until = now + int(req.durationSec)

    row = upsert_ban(req.accountId, req.reason, banned_until)
    write_audit(
        kind="admin:ban",
        actor=admin_id,
        target=req.accountId,
        payload={"reason": req.reason, "bannedUntil": banned_until},
    )
    return {"ok": True, "ban": row}


@router.post("/unban")
def unban_account(accountId: str, admin_id: str = Depends(require_admin)):
    existed = clear_ban(accountId)
    write_audit(kind="admin:unban", actor=admin_id, target=accountId, payload={"existed": existed})
    return {"ok": True, "existed": existed}


@router.get("/ban/{account_id}")
def get_ban_status(account_id: str, admin_id: str = Depends(require_admin)):
    return {"adminId": admin_id, "ban": get_ban(account_id)}