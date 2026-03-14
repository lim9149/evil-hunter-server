# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
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
    insert_mailbox_message,
    claim_mailbox_message,
    list_mailbox_messages,
    summarize_account_economy,
    upsert_announcement,
)

router = APIRouter()


class GrantCurrencyReq(BaseModel):
    accountId: str
    currency: Literal["gold", "gems", "exp"]
    amount: int = Field(..., description="can be negative for rollback; must be non-zero")
    hunterId: Optional[str] = Field(default=None, description="Optional. If provided, directly mutates the hunter snapshot for convenience.")
    reason: str = ""
    idempotencyKey: Optional[str] = Field(default=None, description="Optional. If omitted, uses Idempotency-Key header or auto-generates (not idempotent).")


class MailGrantReq(BaseModel):
    accountId: str
    title: str
    body: str
    rewardCurrency: Optional[Literal["gold", "gems", "exp"]] = None
    rewardAmount: int = 0
    reason: str = ""
    sourceId: Optional[str] = None


class AnnouncementUpsertReq(BaseModel):
    announcementId: Optional[str] = None
    title: str
    body: str
    startsAtEpochSec: int
    endsAtEpochSec: int
    priority: int = 100
    isEnabled: bool = True


@router.post("/grant")
def grant_currency(req: GrantCurrencyReq, admin_id: str = Depends(require_admin), idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key")):
    if int(req.amount) == 0:
        raise HTTPException(status_code=400, detail="amount must be non-zero")
    if abs(int(req.amount)) > 1_000_000_000:
        raise HTTPException(status_code=400, detail="amount too large")

    key = (req.idempotencyKey or idempotency_key or "").strip() or None
    source_id = key or str(uuid.uuid4())

    inserted = insert_currency_ledger_idempotent(account_id=req.accountId, currency=req.currency, amount=int(req.amount), source_kind="admin_grant", source_id=source_id)

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

    write_audit(kind="admin:grant_currency", actor=admin_id, target=req.accountId, payload={"currency": req.currency, "amount": int(req.amount), "hunterId": req.hunterId, "reason": req.reason, "idempotencyKey": key, "ledgerInserted": inserted})
    return {"ok": True, "ledgerInserted": inserted, "idempotencyKey": key, "sourceId": source_id, "hunter": updated_hunter}


class BanReq(BaseModel):
    accountId: str
    reason: str = ""
    durationSec: Optional[int] = Field(default=None, description="If omitted -> permanent. If provided -> seconds from now.")


@router.post("/ban")
def ban_account(req: BanReq, admin_id: str = Depends(require_admin)):
    now = int(time.time())
    banned_until = None
    if req.durationSec is not None:
        if int(req.durationSec) <= 0:
            raise HTTPException(status_code=400, detail="durationSec must be > 0")
        banned_until = now + int(req.durationSec)

    row = upsert_ban(req.accountId, req.reason, banned_until)
    write_audit(kind="admin:ban", actor=admin_id, target=req.accountId, payload={"reason": req.reason, "bannedUntil": banned_until})
    return {"ok": True, "ban": row}


@router.post("/unban")
def unban_account(accountId: str, admin_id: str = Depends(require_admin)):
    existed = clear_ban(accountId)
    write_audit(kind="admin:unban", actor=admin_id, target=accountId, payload={"existed": existed})
    return {"ok": True, "existed": existed}


@router.get("/ban/{account_id}")
def get_ban_status(account_id: str, admin_id: str = Depends(require_admin)):
    return {"adminId": admin_id, "ban": get_ban(account_id)}


@router.post("/mailbox/grant")
def admin_mailbox_grant(req: MailGrantReq, admin_id: str = Depends(require_admin)):
    source_id = req.sourceId or f"mail_{uuid.uuid4().hex[:16]}"
    ok = insert_mailbox_message(
        message_id=f"msg_{uuid.uuid4().hex[:16]}",
        account_id=req.accountId,
        title=req.title,
        body=req.body,
        reward_currency=req.rewardCurrency,
        reward_amount=int(req.rewardAmount),
        source_kind="admin_mailbox",
        source_id=source_id,
        message_type="reward",
    )
    write_audit(kind="admin:mailbox_grant", actor=admin_id, target=req.accountId, payload={"title": req.title, "rewardCurrency": req.rewardCurrency, "rewardAmount": int(req.rewardAmount), "sourceId": source_id, "inserted": ok, "reason": req.reason})
    return {"ok": ok, "sourceId": source_id}


@router.get("/mailbox/{account_id}")
def admin_list_mailbox(account_id: str, includeClaimed: bool = False, admin_id: str = Depends(require_admin)):
    return {"adminId": admin_id, "accountId": account_id, "messages": list_mailbox_messages(account_id, include_claimed=includeClaimed)}


@router.post("/mailbox/{message_id}/claim")
def admin_claim_mailbox(message_id: str, admin_id: str = Depends(require_admin)):
    row = claim_mailbox_message(message_id)
    if not row:
        raise HTTPException(status_code=404, detail="mailbox message not found")
    if row.get("status") == "claimed" and row.get("rewardCurrency"):
        insert_currency_ledger_idempotent(row["accountId"], row["rewardCurrency"], int(row["rewardAmount"]), "mailbox_claim", message_id)
    write_audit(kind="admin:mailbox_claim", actor=admin_id, target=row.get("accountId"), payload=row)
    return row


@router.get("/account-summary/{account_id}")
def admin_account_summary(account_id: str, admin_id: str = Depends(require_admin)):
    return {"adminId": admin_id, **summarize_account_economy(account_id)}


@router.post("/announcement/upsert")
def admin_upsert_announcement(req: AnnouncementUpsertReq, admin_id: str = Depends(require_admin)):
    if req.endsAtEpochSec <= req.startsAtEpochSec:
        raise HTTPException(status_code=400, detail="endsAtEpochSec must be later than startsAtEpochSec")
    aid = req.announcementId or f"ann_{uuid.uuid4().hex[:12]}"
    row = upsert_announcement(aid, req.title, req.body, req.startsAtEpochSec, req.endsAtEpochSec, req.priority, req.isEnabled)
    write_audit(kind="admin:announcement_upsert", actor=admin_id, target=aid, payload=row)
    return row
