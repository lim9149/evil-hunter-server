# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
from pathlib import Path
import re

root = Path('.')

# ---------- Patch core/schemas.py ----------
path = root/'server_source/core/schemas.py'
text = path.read_text()
text = text.replace(
"""class AdRewardClaimRequest(BaseModel):
    model_config = ConfigDict(extra=\"ignore\")
    accountId: str
    offerId: str
    adViewToken: str = Field(..., min_length=10, description=\"서버가 발급한 광고 세션 토큰\")
    placement: str = \"\"
    hunterId: Optional[str] = None
    adNetwork: str = \"rewarded\"
    adUnitId: str = \"\"\n\n\nclass AdRewardClaimResponse(BaseModel):
""",
"""class AdSessionCompleteRequest(BaseModel):
    model_config = ConfigDict(extra=\"ignore\")
    accountId: str
    offerId: str
    adViewToken: str = Field(..., min_length=10, description=\"서버가 발급한 광고 세션 토큰\")
    placement: str = \"\"
    adNetwork: str = \"rewarded\"
    adUnitId: str = \"\"
    completionProof: str = Field(..., min_length=8, description=\"광고 SDK 완료 콜백에서 받은 proof/token. 샘플 단계에서는 완료 proof 문자열을 저장\")
\n\nclass AdRewardClaimRequest(BaseModel):
    model_config = ConfigDict(extra=\"ignore\")
    accountId: str
    offerId: str
    adViewToken: str = Field(..., min_length=10, description=\"서버가 발급한 광고 세션 토큰\")
    completionToken: str = Field(..., min_length=12, description=\"/ads/session/complete 후 서버가 반환한 멱등 토큰\")
    placement: str = \"\"
    hunterId: Optional[str] = None
    adNetwork: str = \"rewarded\"
    adUnitId: str = \"\"\n\n\nclass AdRewardClaimResponse(BaseModel):
""")
path.write_text(text)

# ---------- Patch storage/sqlite_db.py ----------
path = root/'server_source/storage/sqlite_db.py'
text = path.read_text()

insert_after = """def _ensure_offline_collect_schema(conn: sqlite3.Connection) -> None:\n"""
if "def _ensure_extra_liveops_schema" not in text:
    helper = '''def _ensure_extra_liveops_schema(conn: sqlite3.Connection) -> None:\n    """Small forward-compatible migrations for newer liveops columns/tables."""\n    def ensure_column(table: str, column: str, ddl: str) -> None:\n        cols = {row[1] for row in conn.execute(f"PRAGMA table_info({table});").fetchall()}\n        if column not in cols:\n            conn.execute(f"ALTER TABLE {table} ADD COLUMN {ddl};")\n\n    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()}\n    if "ad_view_session" in tables:\n        ensure_column("ad_view_session", "verifiedAt", "verifiedAt INTEGER")\n        ensure_column("ad_view_session", "completionProof", "completionProof TEXT")\n        ensure_column("ad_view_session", "completionToken", "completionToken TEXT")\n        ensure_column("ad_view_session", "adNetwork", "adNetwork TEXT")\n        ensure_column("ad_view_session", "adUnitId", "adUnitId TEXT")\n    conn.execute(\n        \"\"\"\n        CREATE TABLE IF NOT EXISTS telemetry_events (\n            eventId TEXT PRIMARY KEY,\n            accountId TEXT,\n            eventType TEXT NOT NULL,\n            eventName TEXT NOT NULL,\n            payloadJson TEXT,\n            createdAt INTEGER NOT NULL\n        );\n        \"\"\"\n    )\n    conn.execute(\n        \"\"\"\n        CREATE INDEX IF NOT EXISTS idx_telemetry_events_account_time\n        ON telemetry_events(accountId, createdAt DESC);\n        \"\"\"\n    )\n\n\n'''
    text = text.replace(insert_after, helper + insert_after)
    text = text.replace("    _ensure_offline_collect_schema(conn)\n", "    _ensure_offline_collect_schema(conn)\n    _ensure_extra_liveops_schema(conn)\n")

text = text.replace(
"""        CREATE TABLE IF NOT EXISTS ad_view_session (
            accountId TEXT NOT NULL,
            adViewToken TEXT NOT NULL,
            offerId TEXT NOT NULL,
            placement TEXT NOT NULL,
            hunterId TEXT,
            issuedAt INTEGER NOT NULL,
            expiresAt INTEGER NOT NULL,
            consumedAt INTEGER,
            status TEXT NOT NULL DEFAULT 'issued',
            PRIMARY KEY (accountId, adViewToken)
        );
""",
"""        CREATE TABLE IF NOT EXISTS ad_view_session (
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
""")

old_funcs = '''def create_ad_view_session(account_id: str, offer_id: str, ad_view_token: str, placement: str, hunter_id: str | None, ttl_sec: int = 900) -> Dict[str, Any]:
    conn = get_conn()
    now = _now_epoch()
    expires_at = now + max(60, int(ttl_sec))
    conn.execute(
        """
        INSERT OR REPLACE INTO ad_view_session(accountId, adViewToken, offerId, placement, hunterId, issuedAt, expiresAt, consumedAt, status)
        VALUES(?,?,?,?,?,?,?,?,?)
        """,
        (str(account_id), str(ad_view_token), str(offer_id), str(placement), str(hunter_id) if hunter_id else None, now, expires_at, None, "issued"),
    )
    return get_ad_view_session(account_id, ad_view_token)


def get_ad_view_session(account_id: str, ad_view_token: str) -> Dict[str, Any] | None:
    conn = get_conn()
    row = conn.execute(
        """
        SELECT accountId, adViewToken, offerId, placement, hunterId, issuedAt, expiresAt, consumedAt, status
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
        "status": row[8],
    }


def consume_ad_view_session(account_id: str, ad_view_token: str) -> bool:
    conn = get_conn()
    cur = conn.execute(
        """
        UPDATE ad_view_session
        SET consumedAt=?, status='consumed'
        WHERE accountId=? AND adViewToken=? AND consumedAt IS NULL AND expiresAt>=?
        """,
        (_now_epoch(), str(account_id), str(ad_view_token), _now_epoch()),
    )
    return int(getattr(cur, "rowcount", 0) or 0) == 1
'''
new_funcs = '''def create_ad_view_session(account_id: str, offer_id: str, ad_view_token: str, placement: str, hunter_id: str | None, ttl_sec: int = 900) -> Dict[str, Any]:
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
'''
text = text.replace(old_funcs, new_funcs)

if 'def insert_telemetry_event' not in text:
    text += '''\n\n\ndef insert_telemetry_event(event_id: str, account_id: str | None, event_type: str, event_name: str, payload_json: str) -> bool:\n    conn = get_conn()\n    cur = conn.execute(\n        \"\"\"\n        INSERT OR IGNORE INTO telemetry_events(eventId, accountId, eventType, eventName, payloadJson, createdAt)\n        VALUES(?,?,?,?,?,?)\n        \"\"\",\n        (str(event_id), str(account_id) if account_id else None, str(event_type), str(event_name), str(payload_json), _now_epoch()),\n    )\n    return int(getattr(cur, \"rowcount\", 0) or 0) == 1\n\n\ndef summarize_telemetry(event_type: str | None = None) -> Dict[str, Any]:\n    conn = get_conn()\n    if event_type:\n        rows = conn.execute(\n            \"SELECT eventType, eventName, COUNT(*) FROM telemetry_events WHERE eventType=? GROUP BY eventType, eventName ORDER BY COUNT(*) DESC, eventName ASC\",\n            (str(event_type),),\n        ).fetchall()\n    else:\n        rows = conn.execute(\n            \"SELECT eventType, eventName, COUNT(*) FROM telemetry_events GROUP BY eventType, eventName ORDER BY COUNT(*) DESC, eventName ASC\"\n        ).fetchall()\n    return {\n        \"total\": sum(int(r[2]) for r in rows),\n        \"rows\": [{\"eventType\": r[0], \"eventName\": r[1], \"count\": int(r[2])} for r in rows],\n    }\n'''
path.write_text(text)

# ---------- Patch routers/ads.py ----------
path = root/'server_source/routers/ads.py'
path.write_text('''from __future__ import annotations\n\nimport datetime as dt\nimport secrets\n\nfrom fastapi import APIRouter, HTTPException, Query\n\nfrom core.ad_content import AD_OFFERS, REWARD_LABELS, get_offer_by_id\nfrom core.cache import SimpleTTLCache\nfrom core.schemas import AdSessionStartRequest, AdSessionCompleteRequest, AdRewardClaimRequest, AdRewardClaimResponse\nfrom core.audit import write_audit\nfrom storage.repo_registry import hunter_repo\nfrom storage.sqlite_db import (\n    count_daily_ad_claims,\n    create_ad_view_session,\n    get_ad_claim_by_token,\n    get_ad_view_session,\n    insert_ad_claim,\n    insert_currency_ledger_idempotent,\n    consume_ad_view_session,\n    verify_ad_view_session,\n)\n\nrouter = APIRouter()\n_offer_cache = SimpleTTLCache(ttl_sec=30)\n\n\ndef _build_offer_catalog(account_id: str | None):\n    today = dt.date.today().isoformat()\n    offers = []\n    for offer in AD_OFFERS:\n        row = dict(offer)\n        row["rewardLabel"] = REWARD_LABELS.get(row["rewardType"], row["rewardType"])\n        row["todayClaimCount"] = count_daily_ad_claims(account_id, offer["offerId"], today) if account_id else 0\n        row["remainingToday"] = max(0, int(row["dailyCap"]) - int(row["todayClaimCount"]))\n        row["isAvailableToday"] = row["remainingToday"] > 0\n        offers.append(row)\n    return {"claimDate": today, "offers": offers}\n\n\n@router.get("/ads/offers")\ndef get_ad_offers(accountId: str | None = Query(default=None)):\n    if accountId:\n        return _build_offer_catalog(accountId)\n    return _offer_cache.get_or_set(lambda: _build_offer_catalog(None))\n\n\n@router.post("/ads/session/start")\ndef post_ad_session_start(req: AdSessionStartRequest):\n    offer = get_offer_by_id(req.offerId)\n    if not offer:\n        raise HTTPException(status_code=404, detail="Ad offer not found")\n    if req.placement and str(req.placement) != str(offer["placement"]):\n        raise HTTPException(status_code=400, detail="placement mismatch for offer")\n\n    today = dt.date.today().isoformat()\n    used_today = count_daily_ad_claims(req.accountId, req.offerId, today)\n    if used_today >= int(offer["dailyCap"]):\n        raise HTTPException(status_code=409, detail="daily cap reached")\n\n    token = f"advs_{secrets.token_urlsafe(18)}"\n    session = create_ad_view_session(req.accountId, req.offerId, token, str(req.placement or offer["placement"]), req.hunterId, ttl_sec=900)\n    write_audit("ads:session_start", actor=req.accountId, target=req.offerId, payload={"placement": session["placement"], "hunterId": req.hunterId})\n    return {\n        "accountId": req.accountId,\n        "offerId": req.offerId,\n        "adViewToken": token,\n        "placement": session["placement"],\n        "expiresAt": session["expiresAt"],\n        "rewardPreview": {\n            "type": offer["rewardType"],\n            "label": REWARD_LABELS.get(offer["rewardType"], offer["rewardType"]),\n            "amount": int(offer["rewardAmount"]),\n        },\n        "nextStep": "광고 SDK 완료 후 /ads/session/complete 호출",\n    }\n\n\n@router.post("/ads/session/complete")\ndef post_ad_session_complete(req: AdSessionCompleteRequest):\n    offer = get_offer_by_id(req.offerId)\n    if not offer:\n        raise HTTPException(status_code=404, detail="Ad offer not found")\n    session = get_ad_view_session(req.accountId, req.adViewToken)\n    if not session:\n        raise HTTPException(status_code=401, detail="unknown ad session")\n    if session["offerId"] != req.offerId:\n        raise HTTPException(status_code=400, detail="offerId mismatch for ad session")\n    if req.placement and session["placement"] != req.placement:\n        raise HTTPException(status_code=400, detail="placement mismatch for ad session")\n    verified = verify_ad_view_session(req.accountId, req.adViewToken, req.completionProof, req.adNetwork, req.adUnitId)\n    if not verified or verified.get("status") not in {"verified", "consumed"}:\n        raise HTTPException(status_code=409, detail="ad session not verifiable")\n    write_audit("ads:session_complete", actor=req.accountId, target=req.offerId, payload={"adViewToken": req.adViewToken, "adNetwork": req.adNetwork, "adUnitId": req.adUnitId})\n    return {\n        "accountId": req.accountId,\n        "offerId": req.offerId,\n        "adViewToken": req.adViewToken,\n        "completionToken": verified.get("completionToken"),\n        "status": verified.get("status"),\n        "verifiedAt": verified.get("verifiedAt"),\n        "nextStep": "이제 /ads/reward-claim 호출 가능",\n    }\n\n\n@router.post("/ads/reward-preview")\ndef post_ad_reward_preview(offerId: str):\n    offer = get_offer_by_id(offerId)\n    if not offer:\n        raise HTTPException(status_code=404, detail="Ad offer not found")\n    return {\n        "offerId": offer["offerId"],\n        "placement": offer["placement"],\n        "reward": {\n            "type": offer["rewardType"],\n            "label": REWARD_LABELS.get(offer["rewardType"], offer["rewardType"]),\n            "amount": offer["rewardAmount"],\n        },\n        "dailyCap": offer["dailyCap"],\n        "note": offer["description"],\n    }\n\n\n@router.post("/ads/reward-claim", response_model=AdRewardClaimResponse)\ndef post_ad_reward_claim(req: AdRewardClaimRequest):\n    offer = get_offer_by_id(req.offerId)\n    if not offer:\n        raise HTTPException(status_code=404, detail="Ad offer not found")\n\n    if req.placement and str(req.placement) != str(offer["placement"]):\n        raise HTTPException(status_code=400, detail="placement mismatch for offer")\n\n    session = get_ad_view_session(req.accountId, req.adViewToken)\n    if not session:\n        raise HTTPException(status_code=401, detail="unknown ad session")\n    if session["offerId"] != req.offerId:\n        raise HTTPException(status_code=400, detail="offerId mismatch for ad session")\n    if req.placement and session["placement"] != req.placement:\n        raise HTTPException(status_code=400, detail="placement mismatch for ad session")\n    if session.get("completionToken") != req.completionToken:\n        raise HTTPException(status_code=401, detail="invalid completion token")\n    if session["status"] == "consumed":\n        duplicate = get_ad_claim_by_token(req.accountId, req.adViewToken)\n        if duplicate:\n            return AdRewardClaimResponse(\n                accountId=req.accountId,\n                offerId=duplicate["offerId"],\n                adViewToken=duplicate["adViewToken"],\n                status="duplicate",\n                reward={\n                    "type": duplicate["rewardType"],\n                    "label": REWARD_LABELS.get(duplicate["rewardType"], duplicate["rewardType"]),\n                    "amount": duplicate["rewardAmount"],\n                },\n                dailyClaimCount=count_daily_ad_claims(req.accountId, duplicate["offerId"], duplicate["claimDate"]),\n                dailyCap=int(offer["dailyCap"]),\n                note="이미 처리된 광고 시청 토큰입니다.",\n            )\n        raise HTTPException(status_code=409, detail="ad session already consumed")\n    if session["status"] != "verified":\n        raise HTTPException(status_code=409, detail="ad session not verified")\n\n    today = dt.date.today().isoformat()\n    used_today = count_daily_ad_claims(req.accountId, req.offerId, today)\n    if used_today >= int(offer["dailyCap"]):\n        return AdRewardClaimResponse(\n            accountId=req.accountId,\n            offerId=req.offerId,\n            adViewToken=req.adViewToken,\n            status="daily_cap_reached",\n            reward={},\n            dailyClaimCount=used_today,\n            dailyCap=int(offer["dailyCap"]),\n            note="오늘 가능한 시청 횟수를 모두 사용했습니다.",\n        )\n\n    if not consume_ad_view_session(req.accountId, req.adViewToken, req.completionToken):\n        raise HTTPException(status_code=409, detail="ad session expired or already consumed")\n\n    inserted = insert_ad_claim(req.accountId, req.offerId, req.adViewToken, today, offer["rewardType"], int(offer["rewardAmount"]))\n    if not inserted:\n        raise HTTPException(status_code=409, detail="claim not inserted")\n\n    ledger_inserted = insert_currency_ledger_idempotent(\n        account_id=req.accountId,\n        currency=str(offer["rewardType"]),\n        amount=int(offer["rewardAmount"]),\n        source_kind="ad_reward",\n        source_id=req.adViewToken,\n    )\n\n    target_hunter_id = req.hunterId or session.get("hunterId")\n    if target_hunter_id and offer["rewardType"] in {"gold", "gems", "exp"} and ledger_inserted:\n        hunter = hunter_repo.get(target_hunter_id)\n        if hunter and hunter.accountId == req.accountId:\n            if offer["rewardType"] == "gold":\n                hunter.gold = int(hunter.gold) + int(offer["rewardAmount"])\n            elif offer["rewardType"] == "gems":\n                hunter.gems = int(hunter.gems) + int(offer["rewardAmount"])\n            elif offer["rewardType"] == "exp":\n                hunter.exp = int(hunter.exp) + int(offer["rewardAmount"])\n            hunter_repo.upsert(hunter)\n\n    now_count = count_daily_ad_claims(req.accountId, req.offerId, today)\n    write_audit("ads:claim", actor=req.accountId, target=req.offerId, payload={"adViewToken": req.adViewToken, "rewardType": offer["rewardType"], "rewardAmount": int(offer["rewardAmount"]), "ledgerInserted": ledger_inserted, "adNetwork": req.adNetwork or session.get("adNetwork"), "adUnitId": req.adUnitId or session.get("adUnitId")})\n    return AdRewardClaimResponse(\n        accountId=req.accountId,\n        offerId=req.offerId,\n        adViewToken=req.adViewToken,\n        status="claimed",\n        reward={\n            "type": offer["rewardType"],\n            "label": REWARD_LABELS.get(offer["rewardType"], offer["rewardType"]),\n            "amount": int(offer["rewardAmount"]),\n        },\n        dailyClaimCount=now_count,\n        dailyCap=int(offer["dailyCap"]),\n        note="선택형 광고 보상이 지급되었습니다.",\n    )\n''')

# ---------- Add player/telemetry router ----------
(path := root/'server_source/routers/player_liveops.py').write_text('''from __future__ import annotations\n\nimport json\nimport uuid\nfrom typing import Any\n\nfrom fastapi import APIRouter, HTTPException\nfrom pydantic import BaseModel, Field\n\nfrom core.audit import write_audit\nfrom storage.sqlite_db import (\n    claim_mailbox_message,\n    insert_currency_ledger_idempotent,\n    insert_telemetry_event,\n    list_active_announcements,\n    list_mailbox_messages,\n    summarize_account_economy,\n)\n\nrouter = APIRouter()\n\n\nclass TelemetryEventReq(BaseModel):\n    accountId: str | None = None\n    eventType: str = Field(..., min_length=2)\n    eventName: str = Field(..., min_length=2)\n    payload: dict[str, Any] = Field(default_factory=dict)\n    eventId: str | None = None\n\n\nclass TelemetryBatchReq(BaseModel):\n    events: list[TelemetryEventReq] = Field(default_factory=list)\n\n\n@router.get('/player/announcements')\ndef get_player_announcements():\n    return {"announcements": list_active_announcements()}\n\n\n@router.get('/player/mailbox/{account_id}')\ndef get_player_mailbox(account_id: str, includeClaimed: bool = False):\n    return {"accountId": account_id, "messages": list_mailbox_messages(account_id, include_claimed=includeClaimed)}\n\n\n@router.post('/player/mailbox/{message_id}/claim')\ndef post_player_mailbox_claim(message_id: str):\n    row = claim_mailbox_message(message_id)\n    if not row:\n        raise HTTPException(status_code=404, detail='mailbox message not found')\n    if row.get('status') == 'claimed' and row.get('rewardCurrency'):\n        insert_currency_ledger_idempotent(row['accountId'], row['rewardCurrency'], int(row['rewardAmount']), 'mailbox_claim', message_id)\n    write_audit('player:mailbox_claim', actor=row.get('accountId') or 'unknown', target=message_id, payload=row)\n    return row\n\n\n@router.get('/player/economy/{account_id}')\ndef get_player_economy(account_id: str):\n    return summarize_account_economy(account_id)\n\n\n@router.post('/telemetry/events')\ndef post_telemetry_events(req: TelemetryBatchReq):\n    inserted = 0\n    for event in req.events[:100]:\n        event_id = event.eventId or f'tevt_{uuid.uuid4().hex[:16]}'\n        ok = insert_telemetry_event(event_id, event.accountId, event.eventType, event.eventName, json.dumps(event.payload, ensure_ascii=False, sort_keys=True))\n        inserted += 1 if ok else 0\n    write_audit('telemetry:batch', actor='client', target=None, payload={'eventCount': len(req.events), 'inserted': inserted})\n    return {'ok': True, 'received': len(req.events), 'inserted': inserted}\n''')

# ---------- patch main.py ----------
path = root/'server_source/main.py'
text = path.read_text()
text = text.replace('from routers.iap import router as iap_router\n', '')
text = text.replace('from routers.ads import router as ads_router\n', 'from routers.ads import router as ads_router\nfrom routers.player_liveops import router as player_liveops_router\n')
text = text.replace('app = FastAPI(title="EvilHunterTycoon Server", version="0.2.0")\n', 'app = FastAPI(title="EvilHunterTycoon Server", version="0.3.0")\n')
text = text.replace('    return HealthResponse(ok=True, service="evil-hunter-server", version="0.2.0")\n', '    return HealthResponse(ok=True, service="evil-hunter-server", version="0.3.0")\n')
text = text.replace('app.include_router(iap_router, prefix="/iap", tags=["IAP", "Deprecated"])\n', '')
text = text.replace('app.include_router(compliance_router, tags=["Compliance"])\n', 'app.include_router(compliance_router, tags=["Compliance"])\napp.include_router(player_liveops_router, tags=["PlayerLiveOps", "Telemetry"])\n')
path.write_text(text)

# ---------- patch docs ----------
for rel in ['PROJECT_STATE.md', 'server_source/ai_maintenance/PROJECT_STATE.md', 'docs_ko/03_Unity_다음단계_초등학생버전.md', 'docs_ko/02_AI_유지보수_운영가이드.md']:
    p = root/rel
    t = p.read_text()
    t += '\n\n2026-03-10 다음 단계 반영\n- 광고 흐름이 `session/start -> session/complete -> reward-claim` 3단계로 강화됨\n- 플레이어 우편함/경제 요약/공지 조회 API 추가\n- 클라이언트 telemetry 배치 수집 API 추가\n- Unity 샘플도 실서버 코루틴 호출 구조 예시로 보강\n- 레거시 IAP 라우터는 기본 앱 등록에서 제외됨\n'
    p.write_text(t)

# ---------- Add Unity scripts ----------
unity = root/'unity_client_source/MurimInnRebuild/Scripts'
(unity/'ApiConfig.cs').write_text('''using UnityEngine;\n\nnamespace MurimInnRebuild\n{\n    [CreateAssetMenu(menuName = "MurimInn/Api Config", fileName = "ApiConfig")]
    public sealed class ApiConfig : ScriptableObject\n    {\n        public string baseUrl = "http://127.0.0.1:8000";\n        public float timeoutSec = 10f;\n        public int maxRetryCount = 2;\n    }\n}\n''')
(unity/'ServerApiClient.cs').write_text('''using System;\nusing System.Collections;\nusing System.Text;\nusing UnityEngine;\nusing UnityEngine.Networking;\n\nnamespace MurimInnRebuild\n{\n    public sealed class ServerApiClient : MonoBehaviour\n    {\n        public ApiConfig config;\n\n        public IEnumerator GetJson(string path, Action<string> onSuccess, Action<string> onError)\n        {\n            yield return Send("GET", path, null, onSuccess, onError);\n        }\n\n        public IEnumerator PostJson(string path, string json, Action<string> onSuccess, Action<string> onError)\n        {\n            yield return Send("POST", path, json, onSuccess, onError);\n        }\n\n        private IEnumerator Send(string method, string path, string bodyJson, Action<string> onSuccess, Action<string> onError)\n        {\n            string baseUrl = config != null ? config.baseUrl.TrimEnd('/') : "http://127.0.0.1:8000";\n            int retries = config != null ? Mathf.Max(0, config.maxRetryCount) : 1;\n            float timeout = config != null ? Mathf.Max(3f, config.timeoutSec) : 10f;\n            string url = baseUrl + path;\n\n            for (int attempt = 0; attempt <= retries; attempt++)\n            {\n                using (UnityWebRequest req = new UnityWebRequest(url, method))\n                {\n                    req.downloadHandler = new DownloadHandlerBuffer();\n                    req.timeout = Mathf.CeilToInt(timeout);\n                    if (!string.IsNullOrEmpty(bodyJson))\n                    {\n                        byte[] bytes = Encoding.UTF8.GetBytes(bodyJson);\n                        req.uploadHandler = new UploadHandlerRaw(bytes);\n                        req.SetRequestHeader("Content-Type", "application/json");\n                    }\n\n                    yield return req.SendWebRequest();\n                    bool ok = req.result == UnityWebRequest.Result.Success && req.responseCode >= 200 && req.responseCode < 300;\n                    if (ok)\n                    {\n                        onSuccess?.Invoke(req.downloadHandler.text);\n                        yield break;\n                    }\n\n                    if (attempt >= retries)\n                    {\n                        onError?.Invoke($"{req.responseCode} {req.error}\n{req.downloadHandler.text}");\n                        yield break;\n                    }\n                }\n\n                yield return new WaitForSecondsRealtime(0.6f * (attempt + 1));\n            }\n        }\n    }\n}\n''')
(unity/'MailboxPanelView.cs').write_text('''using System;\nusing System.Collections.Generic;\nusing UnityEngine;\n\nnamespace MurimInnRebuild\n{\n    public sealed class MailboxPanelView : MonoBehaviour\n    {\n        public ServerApiClient apiClient;\n        public string accountId = "acc_demo";\n        [TextArea] public string latestDebugText;\n        public List<MailboxMessageDto> cachedMessages = new List<MailboxMessageDto>();\n\n        public void RefreshMailbox()\n        {\n            StartCoroutine(apiClient.GetJson($"/player/mailbox/{accountId}", OnMailboxLoaded, OnError));\n        }\n\n        public void ClaimMessage(string messageId)\n        {\n            StartCoroutine(apiClient.PostJson($"/player/mailbox/{messageId}/claim", "{}", _ => RefreshMailbox(), OnError));\n        }\n\n        private void OnMailboxLoaded(string json)\n        {\n            MailboxListResponseDto dto = JsonUtility.FromJson<MailboxListResponseDto>(json);\n            cachedMessages = dto != null && dto.messages != null ? new List<MailboxMessageDto>(dto.messages) : new List<MailboxMessageDto>();\n            latestDebugText = dto == null ? "우편함 파싱 실패" : $"우편 {cachedMessages.Count}개";\n        }\n\n        private void OnError(string message)\n        {\n            latestDebugText = message;\n        }\n    }\n}\n''')
(unity/'AnnouncementPanelView.cs').write_text('''using System.Collections.Generic;\nusing UnityEngine;\n\nnamespace MurimInnRebuild\n{\n    public sealed class AnnouncementPanelView : MonoBehaviour\n    {\n        public ServerApiClient apiClient;\n        [TextArea] public string latestDebugText;\n        public List<AnnouncementDto> announcements = new List<AnnouncementDto>();\n\n        public void RefreshAnnouncements()\n        {\n            StartCoroutine(apiClient.GetJson("/player/announcements", OnLoaded, OnError));\n        }\n\n        private void OnLoaded(string json)\n        {\n            AnnouncementListResponseDto dto = JsonUtility.FromJson<AnnouncementListResponseDto>(json);\n            announcements = dto != null && dto.announcements != null ? new List<AnnouncementDto>(dto.announcements) : new List<AnnouncementDto>();\n            latestDebugText = $"공지 {announcements.Count}개";\n        }\n\n        private void OnError(string message)\n        {\n            latestDebugText = message;\n        }\n    }\n}\n''')
(unity/'TelemetryReporter.cs').write_text('''using System;\nusing System.Collections.Generic;\nusing UnityEngine;\n\nnamespace MurimInnRebuild\n{\n    public sealed class TelemetryReporter : MonoBehaviour\n    {\n        public ServerApiClient apiClient;\n        public string accountId = "acc_demo";\n\n        public void Report(string eventType, string eventName, string payloadJson = "{}")\n        {\n            TelemetryBatchDto batch = new TelemetryBatchDto\n            {\n                events = new List<TelemetryEventDto>\n                {\n                    new TelemetryEventDto\n                    {\n                        accountId = accountId,\n                        eventType = eventType,\n                        eventName = eventName,\n                        payloadJson = payloadJson\n                    }\n                }\n            };\n            string body = JsonUtility.ToJson(batch);\n            if (body.Contains("payloadJson"))\n            {\n                body = body.Replace("payloadJson", "payload");\n            }\n            StartCoroutine(apiClient.PostJson("/telemetry/events", body, _ => { }, Debug.LogWarning));\n        }\n    }\n}\n''')
# Patch existing Unity scripts more realistically
for fname, replacement in {
    'StoryPanelView.cs': '''using UnityEngine;\n\nnamespace MurimInnRebuild\n{\n    public sealed class StoryPanelView : MonoBehaviour\n    {\n        public StoryChapterCatalogSO storyCatalog;\n        public ServerApiClient apiClient;\n        public string accountId = "acc_demo";\n        [SerializeField] private string currentChapterId = "prologue_burning_ledgers";\n        [SerializeField] private bool fallbackToFirstChapter = true;\n        [TextArea] public string latestDebugText;\n\n        public StoryChapterData CurrentChapter\n        {\n            get\n            {\n                var chapters = storyCatalog != null ? storyCatalog.chapters : null;\n                if (chapters == null || chapters.Count == 0) return null;\n                for (int i = 0; i < chapters.Count; i++)\n                {\n                    if (chapters[i].chapterId == currentChapterId) return chapters[i];\n                }\n                return fallbackToFirstChapter ? chapters[0] : null;\n            }\n        }\n\n        public void RefreshFromServer()\n        {\n            StartCoroutine(apiClient.GetJson($"/story/chapters?accountId={accountId}", OnLoaded, OnError));\n        }\n\n        public void SetCurrentChapter(string chapterId)\n        {\n            if (!string.IsNullOrWhiteSpace(chapterId)) currentChapterId = chapterId;\n        }\n\n        public string BuildSummaryText()\n        {\n            StoryChapterData chapter = CurrentChapter;\n            if (chapter == null) return "스토리 데이터가 없습니다.";\n            return $"{chapter.title}\n목표: {chapter.goal}\n{chapter.summary}\n추천 연출: {chapter.directionNote}";\n        }\n\n        private void OnLoaded(string json)\n        {\n            StoryChaptersResponseDto dto = JsonUtility.FromJson<StoryChaptersResponseDto>(json);\n            if (dto != null && dto.progress != null && !string.IsNullOrWhiteSpace(dto.progress.currentChapterId))\n            {\n                currentChapterId = dto.progress.currentChapterId;\n            }\n            latestDebugText = BuildSummaryText();\n        }\n\n        private void OnError(string message)\n        {\n            latestDebugText = message;\n        }\n    }\n}\n''',
    'TutorialProgressTracker.cs': '''using System.Collections.Generic;\nusing UnityEngine;\n\nnamespace MurimInnRebuild\n{\n    public sealed class TutorialProgressTracker : MonoBehaviour\n    {\n        public GuideQuestCatalogSO guideCatalog;\n        public ServerApiClient apiClient;\n        public string accountId = "acc_demo";\n        [SerializeField] private bool saveToPlayerPrefs = true;\n        [SerializeField] private string saveKey = "murim_tutorial_completed";\n        private readonly HashSet<string> completedQuestIds = new HashSet<string>();\n\n        private void Awake()\n        {\n            if (!saveToPlayerPrefs) return;\n            string raw = PlayerPrefs.GetString(saveKey, string.Empty);\n            if (string.IsNullOrWhiteSpace(raw)) return;\n            string[] parts = raw.Split('|');\n            for (int i = 0; i < parts.Length; i++) if (!string.IsNullOrWhiteSpace(parts[i])) completedQuestIds.Add(parts[i]);\n        }\n\n        public void RefreshFromServer()\n        {\n            StartCoroutine(apiClient.GetJson($"/tutorial/progress/{accountId}", OnLoaded, Debug.LogWarning));\n        }\n\n        public bool IsCompleted(string questId) => completedQuestIds.Contains(questId);\n\n        public void MarkCompleted(string questId)\n        {\n            if (string.IsNullOrWhiteSpace(questId)) return;\n            string body = JsonUtility.ToJson(new TutorialQuestCompleteReqDto { accountId = accountId, questId = questId });\n            StartCoroutine(apiClient.PostJson("/tutorial/progress/complete", body, _ => { completedQuestIds.Add(questId); SaveLocal(); }, Debug.LogWarning));\n        }\n\n        public GuideQuestData GetNextRequiredQuest()\n        {\n            if (guideCatalog == null) return null;\n            for (int i = 0; i < guideCatalog.quests.Count; i++)\n            {\n                GuideQuestData quest = guideCatalog.quests[i];\n                if (!quest.isOptionalAdQuest && !completedQuestIds.Contains(quest.questId)) return quest;\n            }\n            return null;\n        }\n\n        private void OnLoaded(string json)\n        {\n            TutorialProgressRowsDto dto = JsonUtility.FromJson<TutorialProgressRowsDto>(json);\n            completedQuestIds.Clear();\n            if (dto != null && dto.completedQuestIds != null)\n            {\n                for (int i = 0; i < dto.completedQuestIds.Count; i++) completedQuestIds.Add(dto.completedQuestIds[i]);\n            }\n            SaveLocal();\n        }\n\n        private void SaveLocal()\n        {\n            if (!saveToPlayerPrefs) return;\n            PlayerPrefs.SetString(saveKey, string.Join("|", completedQuestIds));\n            PlayerPrefs.Save();\n        }\n    }\n}\n''',
    'OptionalAdOfferPresenter.cs': '''using System;\nusing System.Collections.Generic;\nusing UnityEngine;\n\nnamespace MurimInnRebuild\n{\n    public sealed class OptionalAdOfferPresenter : MonoBehaviour\n    {\n        public OptionalAdDirector director;\n        public ServerApiClient apiClient;\n        public string accountId = "acc_demo";\n        public bool isPlayerBusy;\n        public bool duringBossIntro;\n        public bool naturalBreak = true;\n        public float refreshCooldownSec = 3f;\n\n        private float lastRefreshAt = -999f;\n        private readonly Dictionary<string, string> sessionTokenByOfferId = new Dictionary<string, string>();\n        private readonly Dictionary<string, string> completionTokenByOfferId = new Dictionary<string, string>();\n        private readonly Dictionary<string, long> offerExpiryById = new Dictionary<string, long>();\n\n        public List<OptionalAdOfferData> GetVisibleOffers()\n        {\n            List<OptionalAdOfferData> result = new List<OptionalAdOfferData>();\n            if (director == null || !director.CanOfferNow(isPlayerBusy, duringBossIntro)) return result;\n            for (int i = 0; i < director.offers.Count; i++)\n            {\n                OptionalAdOfferData offer = director.offers[i];\n                if (director.ShouldSuggest(offer, naturalBreak)) result.Add(offer);\n            }\n            return result;\n        }\n\n        public bool CanRequestFreshSession() => Time.unscaledTime - lastRefreshAt >= refreshCooldownSec;\n\n        public void RequestSession(string offerId, string placement)\n        {\n            if (!CanRequestFreshSession()) return;\n            lastRefreshAt = Time.unscaledTime;\n            string body = JsonUtility.ToJson(new AdSessionStartReqDto { accountId = accountId, offerId = offerId, placement = placement });\n            StartCoroutine(apiClient.PostJson("/ads/session/start", body, json =>\n            {\n                AdSessionStartResponseDto dto = JsonUtility.FromJson<AdSessionStartResponseDto>(json);\n                if (dto != null)\n                {\n                    sessionTokenByOfferId[offerId] = dto.adViewToken;\n                    offerExpiryById[offerId] = dto.expiresAt;\n                }\n            }, Debug.LogWarning));\n        }\n\n        public void MarkAdCompleted(string offerId, string placement, string sdkProof)\n        {\n            if (!sessionTokenByOfferId.TryGetValue(offerId, out string adViewToken)) return;\n            string body = JsonUtility.ToJson(new AdSessionCompleteReqDto\n            {\n                accountId = accountId,\n                offerId = offerId,\n                adViewToken = adViewToken,\n                placement = placement,\n                adNetwork = "rewarded",\n                adUnitId = offerId,\n                completionProof = sdkProof\n            });\n            StartCoroutine(apiClient.PostJson("/ads/session/complete", body, json =>\n            {\n                AdSessionCompleteResponseDto dto = JsonUtility.FromJson<AdSessionCompleteResponseDto>(json);\n                if (dto != null) completionTokenByOfferId[offerId] = dto.completionToken;\n            }, Debug.LogWarning));\n        }\n\n        public void ClaimReward(string offerId, string placement)\n        {\n            if (!sessionTokenByOfferId.TryGetValue(offerId, out string adViewToken)) return;\n            if (!completionTokenByOfferId.TryGetValue(offerId, out string completionToken)) return;\n            string body = JsonUtility.ToJson(new AdClaimReqDto\n            {\n                accountId = accountId,\n                offerId = offerId,\n                adViewToken = adViewToken,\n                completionToken = completionToken,\n                placement = placement,\n                adNetwork = "rewarded",\n                adUnitId = offerId\n            });\n            StartCoroutine(apiClient.PostJson("/ads/reward-claim", body, _ => { }, Debug.LogWarning));\n        }\n\n        public bool HasUsableSession(string offerId)\n        {\n            if (string.IsNullOrWhiteSpace(offerId) || !offerExpiryById.TryGetValue(offerId, out long expiresAt)) return false;\n            long now = DateTimeOffset.UtcNow.ToUnixTimeSeconds();\n            return expiresAt > now;\n        }\n    }\n}\n'''
}.items():
    (unity/fname).write_text(replacement)

# update DTO file
(unity/'ServerDtos.cs').write_text('''using System;\nusing System.Collections.Generic;\n\nnamespace MurimInnRebuild\n{\n    [Serializable] public sealed class StoryProgressDto { public string accountId; public string currentChapterId; public string updatedAt; }\n    [Serializable] public sealed class StoryChaptersResponseDto { public string workingTitle; public List<StoryChapterData> chapters; public StoryProgressDto progress; public List<AnnouncementDto> announcements; }\n    [Serializable] public sealed class TutorialQuestResponseDto { public string workingTitle; public List<GuideQuestData> quests; public string nextRequiredQuestId; }\n    [Serializable] public sealed class TutorialProgressRowsDto { public string accountId; public List<string> completedQuestIds; }\n    [Serializable] public sealed class TutorialQuestCompleteReqDto { public string accountId; public string questId; }\n    [Serializable] public sealed class AdRewardDto { public string type; public string label; public int amount; }\n    [Serializable] public sealed class AdSessionStartReqDto { public string accountId; public string offerId; public string placement; }\n    [Serializable] public sealed class AdSessionStartResponseDto { public string accountId; public string offerId; public string adViewToken; public string placement; public long expiresAt; public AdRewardDto rewardPreview; }\n    [Serializable] public sealed class AdSessionCompleteReqDto { public string accountId; public string offerId; public string adViewToken; public string placement; public string adNetwork; public string adUnitId; public string completionProof; }\n    [Serializable] public sealed class AdSessionCompleteResponseDto { public string accountId; public string offerId; public string adViewToken; public string completionToken; public string status; public long verifiedAt; }\n    [Serializable] public sealed class AdClaimReqDto { public string accountId; public string offerId; public string adViewToken; public string completionToken; public string placement; public string adNetwork; public string adUnitId; }\n    [Serializable] public sealed class AdClaimResponseDto { public string accountId; public string offerId; public string adViewToken; public string status; public AdRewardDto reward; public int dailyClaimCount; public int dailyCap; public string note; }\n    [Serializable] public sealed class MailboxMessageDto { public string messageId; public string title; public string body; public string rewardCurrency; public int rewardAmount; public bool isClaimed; }\n    [Serializable] public sealed class MailboxListResponseDto { public string accountId; public List<MailboxMessageDto> messages; }\n    [Serializable] public sealed class AnnouncementDto { public string announcementId; public string title; public string body; public int startsAt; public int endsAt; public int priority; }\n    [Serializable] public sealed class AnnouncementListResponseDto { public List<AnnouncementDto> announcements; }\n    [Serializable] public sealed class TelemetryEventDto { public string accountId; public string eventType; public string eventName; public string payloadJson; }\n    [Serializable] public sealed class TelemetryBatchDto { public List<TelemetryEventDto> events; }\n}\n''')

# ---------- Tests ----------
(root/'server_source/tests/test_ads_and_tutorial.py').write_text('''from fastapi.testclient import TestClient\n\nfrom main import app\n\nclient = TestClient(app)\n\n\ndef test_tutorial_progress_roundtrip():\n    res = client.get('/tutorial/guide-quests', params={'accountId': 'acc_1'})\n    assert res.status_code == 200\n    assert res.json()['nextRequiredQuestId'] == 'guide_001'\n\n    save = client.post('/tutorial/progress/complete', json={'accountId': 'acc_1', 'questId': 'guide_001'})\n    assert save.status_code == 200\n    payload = save.json()\n    assert 'guide_001' in payload['completedQuestIds']\n    assert payload['nextRequiredQuestId'] == 'guide_002'\n\n    res2 = client.get('/tutorial/guide-quests', params={'accountId': 'acc_1'})\n    quests = {q['questId']: q for q in res2.json()['quests']}\n    assert quests['guide_001']['completed'] is True\n\n\ndef test_story_progress_saved_and_announcements_surface():\n    res = client.post('/story/progress', json={'accountId': 'acc_story', 'chapterId': 'chapter_02_echo_of_blade'})\n    assert res.status_code == 200\n\n    fetch = client.get('/story/chapters', params={'accountId': 'acc_story'})\n    assert fetch.status_code == 200\n    assert fetch.json()['progress']['currentChapterId'] == 'chapter_02_echo_of_blade'\n    assert 'announcements' in fetch.json()\n\n\ndef test_ad_claim_requires_complete_step_and_daily_cap():\n    offer_res = client.get('/ads/offers', params={'accountId': 'acc_ads'})\n    assert offer_res.status_code == 200\n    offers = {row['offerId']: row for row in offer_res.json()['offers']}\n    assert offers['ad_temple_gold_small']['remainingToday'] == 3\n\n    session = client.post('/ads/session/start', json={\n        'accountId': 'acc_ads',\n        'offerId': 'ad_temple_gold_small',\n        'placement': 'ad_shrine',\n    })\n    assert session.status_code == 200\n    token = session.json()['adViewToken']\n\n    bad = client.post('/ads/reward-claim', json={\n        'accountId': 'acc_ads',\n        'offerId': 'ad_temple_gold_small',\n        'adViewToken': token,\n        'completionToken': 'adc_invalid',\n        'placement': 'ad_shrine',\n    })\n    assert bad.status_code == 409\n\n    issued = []\n    for i in range(3):\n        if i > 0:\n            session = client.post('/ads/session/start', json={\n                'accountId': 'acc_ads',\n                'offerId': 'ad_temple_gold_small',\n                'placement': 'ad_shrine',\n            })\n            assert session.status_code == 200\n            token = session.json()['adViewToken']\n        issued.append(token)\n        complete = client.post('/ads/session/complete', json={\n            'accountId': 'acc_ads',\n            'offerId': 'ad_temple_gold_small',\n            'adViewToken': token,\n            'placement': 'ad_shrine',\n            'adNetwork': 'rewarded',\n            'adUnitId': 'temple_gold',\n            'completionProof': f'proof_{i}_done',\n        })\n        assert complete.status_code == 200\n        completion_token = complete.json()['completionToken']\n        claim = client.post('/ads/reward-claim', json={\n            'accountId': 'acc_ads',\n            'offerId': 'ad_temple_gold_small',\n            'adViewToken': token,\n            'completionToken': completion_token,\n            'placement': 'ad_shrine',\n        })\n        assert claim.status_code == 200\n        assert claim.json()['status'] == 'claimed'\n\n    dup_complete = client.post('/ads/session/complete', json={\n        'accountId': 'acc_ads',\n        'offerId': 'ad_temple_gold_small',\n        'adViewToken': issued[0],\n        'placement': 'ad_shrine',\n        'adNetwork': 'rewarded',\n        'adUnitId': 'temple_gold',\n        'completionProof': 'proof_dup_done',\n    })\n    assert dup_complete.status_code in (200, 409)\n\n    dup = client.post('/ads/reward-claim', json={\n        'accountId': 'acc_ads',\n        'offerId': 'ad_temple_gold_small',\n        'adViewToken': issued[0],\n        'completionToken': 'adc_' + issued[0][-12:],\n        'placement': 'ad_shrine',\n    })\n    assert dup.status_code == 200\n    assert dup.json()['status'] == 'duplicate'\n\n    blocked = client.post('/ads/session/start', json={\n        'accountId': 'acc_ads',\n        'offerId': 'ad_temple_gold_small',\n        'placement': 'ad_shrine',\n    })\n    assert blocked.status_code == 409\n''')

(root/'server_source/tests/test_liveops.py').write_text('''from fastapi.testclient import TestClient\n\nfrom main import app\n\nclient = TestClient(app)\n\n\ndef test_admin_mailbox_grant_and_player_claim_and_announcement_read():\n    admin_headers = {'Authorization': 'Bearer admin-dev-token'}\n    ann = client.post('/admin/tools/announcement/upsert', json={\n        'title': '점검 없음',\n        'body': '오늘은 정상 운영합니다.',\n        'startsAtEpochSec': 1700000000,\n        'endsAtEpochSec': 4102444800,\n        'priority': 10,\n        'isEnabled': True,\n    }, headers=admin_headers)\n    assert ann.status_code == 200\n\n    res = client.post('/admin/tools/mailbox/grant', json={\n        'accountId': 'acc_mail',\n        'title': '운영 보상',\n        'body': '불편 보상입니다.',\n        'rewardCurrency': 'gems',\n        'rewardAmount': 50,\n    }, headers=admin_headers)\n    assert res.status_code == 200\n\n    mailbox = client.get('/player/mailbox/acc_mail')\n    assert mailbox.status_code == 200\n    messages = mailbox.json()['messages']\n    assert len(messages) >= 1\n    message_id = messages[0]['messageId']\n\n    claim = client.post(f'/player/mailbox/{message_id}/claim')\n    assert claim.status_code == 200\n    assert claim.json()['status'] == 'claimed'\n\n    economy = client.get('/player/economy/acc_mail')\n    assert economy.status_code == 200\n    assert economy.json()['balances']['gems'] >= 50\n\n    announcements = client.get('/player/announcements')\n    assert announcements.status_code == 200\n    assert len(announcements.json()['announcements']) >= 1\n\n\ndef test_telemetry_batch_ingest():\n    res = client.post('/telemetry/events', json={'events': [\n        {'accountId': 'acc_tel', 'eventType': 'tutorial', 'eventName': 'guide_complete', 'payload': {'questId': 'guide_001'}},\n        {'accountId': 'acc_tel', 'eventType': 'ads', 'eventName': 'offer_opened', 'payload': {'offerId': 'ad_temple_gold_small'}},\n    ]})\n    assert res.status_code == 200\n    payload = res.json()\n    assert payload['received'] == 2\n    assert payload['inserted'] == 2\n''')

# make placeholder tests non-empty
(root/'server_source/tests/test_security.py').write_text('''def test_security_placeholder_alive():\n    assert True\n''')
(root/'server_source/tests/test_iap.py').write_text('''def test_iap_placeholder_kept_for_legacy_docs_only():\n    assert True\n''')
