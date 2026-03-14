# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
from __future__ import annotations

import json
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.audit import write_audit
from storage.sqlite_db import (
    claim_mailbox_message,
    insert_currency_ledger_idempotent,
    insert_telemetry_event,
    list_active_announcements,
    list_mailbox_messages,
    summarize_account_economy,
)

router = APIRouter()


class TelemetryEventReq(BaseModel):
    accountId: str | None = None
    eventType: str = Field(..., min_length=2)
    eventName: str = Field(..., min_length=2)
    payload: dict[str, Any] = Field(default_factory=dict)
    eventId: str | None = None


class TelemetryBatchReq(BaseModel):
    events: list[TelemetryEventReq] = Field(default_factory=list)


@router.get('/player/announcements')
def get_player_announcements():
    return {"announcements": list_active_announcements()}


@router.get('/player/mailbox/{account_id}')
def get_player_mailbox(account_id: str, includeClaimed: bool = False):
    return {"accountId": account_id, "messages": list_mailbox_messages(account_id, include_claimed=includeClaimed)}


@router.post('/player/mailbox/{message_id}/claim')
def post_player_mailbox_claim(message_id: str):
    row = claim_mailbox_message(message_id)
    if not row:
        raise HTTPException(status_code=404, detail='mailbox message not found')
    if row.get('status') == 'claimed' and row.get('rewardCurrency'):
        insert_currency_ledger_idempotent(row['accountId'], row['rewardCurrency'], int(row['rewardAmount']), 'mailbox_claim', message_id)
    write_audit('player:mailbox_claim', actor=row.get('accountId') or 'unknown', target=message_id, payload=row)
    return row


@router.get('/player/economy/{account_id}')
def get_player_economy(account_id: str):
    return summarize_account_economy(account_id)


@router.post('/telemetry/events')
def post_telemetry_events(req: TelemetryBatchReq):
    inserted = 0
    for event in req.events[:100]:
        event_id = event.eventId or f'tevt_{uuid.uuid4().hex[:16]}'
        ok = insert_telemetry_event(event_id, event.accountId, event.eventType, event.eventName, json.dumps(event.payload, ensure_ascii=False, sort_keys=True))
        inserted += 1 if ok else 0
    write_audit('telemetry:batch', actor='client', target=None, payload={'eventCount': len(req.events), 'inserted': inserted})
    return {'ok': True, 'received': len(req.events), 'inserted': inserted}
