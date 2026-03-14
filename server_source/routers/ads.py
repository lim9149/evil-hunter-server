# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
from __future__ import annotations

import datetime as dt
import secrets

from fastapi import APIRouter, HTTPException, Query

from core.ad_content import AD_OFFERS, REWARD_LABELS, get_offer_by_id
from core.cache import SimpleTTLCache
from core.schemas import AdSessionStartRequest, AdSessionCompleteRequest, AdRewardClaimRequest, AdRewardClaimResponse, AdVipStatusResponse
from core.audit import write_audit
from core.operator_progression import compute_patron_stage, patron_design_intent, PATRON_STAGES
from storage.repo_registry import hunter_repo
from storage.sqlite_db import (
    count_daily_ad_claims,
    count_lifetime_ad_claims,
    create_ad_view_session,
    get_ad_claim_by_token,
    get_ad_view_session,
    insert_ad_claim,
    insert_currency_ledger_idempotent,
    consume_ad_view_session,
    verify_ad_view_session,
)

router = APIRouter()
_offer_cache = SimpleTTLCache(ttl_sec=30)
VIP_THRESHOLDS = [(int(stage["level"]), int(stage["requires"])) for stage in PATRON_STAGES if int(stage["level"]) > 0]
VIP_PERKS = {int(stage["level"]): list(stage["perks"]) for stage in PATRON_STAGES}
VIP_TITLES = {int(stage["level"]): str(stage["title"]) for stage in PATRON_STAGES}


def _build_offer_catalog(account_id: str | None):
    today = dt.date.today().isoformat()
    offers = []
    for offer in AD_OFFERS:
        row = dict(offer)
        row["rewardLabel"] = REWARD_LABELS.get(row["rewardType"], row["rewardType"])
        row["todayClaimCount"] = count_daily_ad_claims(account_id, offer["offerId"], today) if account_id else 0
        row["remainingToday"] = max(0, int(row["dailyCap"]) - int(row["todayClaimCount"]))
        row["isAvailableToday"] = row["remainingToday"] > 0
        offers.append(row)
    return {"claimDate": today, "offers": offers}


@router.get("/ads/offers")
def get_ad_offers(accountId: str | None = Query(default=None)):
    if accountId:
        return _build_offer_catalog(accountId)
    return _offer_cache.get_or_set(lambda: _build_offer_catalog(None))


@router.post("/ads/session/start")
def post_ad_session_start(req: AdSessionStartRequest):
    offer = get_offer_by_id(req.offerId)
    if not offer:
        raise HTTPException(status_code=404, detail="Ad offer not found")
    if req.placement and str(req.placement) != str(offer["placement"]):
        raise HTTPException(status_code=400, detail="placement mismatch for offer")

    today = dt.date.today().isoformat()
    used_today = count_daily_ad_claims(req.accountId, req.offerId, today)
    if used_today >= int(offer["dailyCap"]):
        raise HTTPException(status_code=409, detail="daily cap reached")

    token = f"advs_{secrets.token_urlsafe(18)}"
    session = create_ad_view_session(req.accountId, req.offerId, token, str(req.placement or offer["placement"]), req.hunterId, ttl_sec=900)
    write_audit("ads:session_start", actor=req.accountId, target=req.offerId, payload={"placement": session["placement"], "hunterId": req.hunterId})
    return {
        "accountId": req.accountId,
        "offerId": req.offerId,
        "adViewToken": token,
        "placement": session["placement"],
        "expiresAt": session["expiresAt"],
        "rewardPreview": {
            "type": offer["rewardType"],
            "label": REWARD_LABELS.get(offer["rewardType"], offer["rewardType"]),
            "amount": int(offer["rewardAmount"]),
        },
        "nextStep": "광고 SDK 완료 후 /ads/session/complete 호출",
    }


@router.post("/ads/session/complete")
def post_ad_session_complete(req: AdSessionCompleteRequest):
    offer = get_offer_by_id(req.offerId)
    if not offer:
        raise HTTPException(status_code=404, detail="Ad offer not found")
    session = get_ad_view_session(req.accountId, req.adViewToken)
    if not session:
        raise HTTPException(status_code=401, detail="unknown ad session")
    if session["offerId"] != req.offerId:
        raise HTTPException(status_code=400, detail="offerId mismatch for ad session")
    if req.placement and session["placement"] != req.placement:
        raise HTTPException(status_code=400, detail="placement mismatch for ad session")
    verified = verify_ad_view_session(req.accountId, req.adViewToken, req.completionProof, req.adNetwork, req.adUnitId)
    if not verified or verified.get("status") not in {"verified", "consumed"}:
        raise HTTPException(status_code=409, detail="ad session not verifiable")
    write_audit("ads:session_complete", actor=req.accountId, target=req.offerId, payload={"adViewToken": req.adViewToken, "adNetwork": req.adNetwork, "adUnitId": req.adUnitId})
    return {
        "accountId": req.accountId,
        "offerId": req.offerId,
        "adViewToken": req.adViewToken,
        "completionToken": verified.get("completionToken"),
        "status": verified.get("status"),
        "verifiedAt": verified.get("verifiedAt"),
        "nextStep": "이제 /ads/reward-claim 호출 가능",
    }


@router.post("/ads/reward-preview")
def post_ad_reward_preview(offerId: str):
    offer = get_offer_by_id(offerId)
    if not offer:
        raise HTTPException(status_code=404, detail="Ad offer not found")
    return {
        "offerId": offer["offerId"],
        "placement": offer["placement"],
        "reward": {
            "type": offer["rewardType"],
            "label": REWARD_LABELS.get(offer["rewardType"], offer["rewardType"]),
            "amount": offer["rewardAmount"],
        },
        "dailyCap": offer["dailyCap"],
        "note": offer["description"],
    }


@router.post("/ads/reward-claim", response_model=AdRewardClaimResponse)
def post_ad_reward_claim(req: AdRewardClaimRequest):
    offer = get_offer_by_id(req.offerId)
    if not offer:
        raise HTTPException(status_code=404, detail="Ad offer not found")

    if req.placement and str(req.placement) != str(offer["placement"]):
        raise HTTPException(status_code=400, detail="placement mismatch for offer")

    session = get_ad_view_session(req.accountId, req.adViewToken)
    if not session:
        raise HTTPException(status_code=401, detail="unknown ad session")
    if session["offerId"] != req.offerId:
        raise HTTPException(status_code=400, detail="offerId mismatch for ad session")
    if req.placement and session["placement"] != req.placement:
        raise HTTPException(status_code=400, detail="placement mismatch for ad session")
    if session.get("completionToken") != req.completionToken:
        raise HTTPException(status_code=401, detail="invalid completion token")
    if session["status"] == "consumed":
        duplicate = get_ad_claim_by_token(req.accountId, req.adViewToken)
        if duplicate:
            return AdRewardClaimResponse(
                accountId=req.accountId,
                offerId=duplicate["offerId"],
                adViewToken=duplicate["adViewToken"],
                status="duplicate",
                reward={
                    "type": duplicate["rewardType"],
                    "label": REWARD_LABELS.get(duplicate["rewardType"], duplicate["rewardType"]),
                    "amount": duplicate["rewardAmount"],
                },
                dailyClaimCount=count_daily_ad_claims(req.accountId, duplicate["offerId"], duplicate["claimDate"]),
                dailyCap=int(offer["dailyCap"]),
                note="이미 처리된 광고 시청 토큰입니다.",
            )
        raise HTTPException(status_code=409, detail="ad session already consumed")
    if session["status"] != "verified":
        raise HTTPException(status_code=409, detail="ad session not verified")

    today = dt.date.today().isoformat()
    used_today = count_daily_ad_claims(req.accountId, req.offerId, today)
    if used_today >= int(offer["dailyCap"]):
        return AdRewardClaimResponse(
            accountId=req.accountId,
            offerId=req.offerId,
            adViewToken=req.adViewToken,
            status="daily_cap_reached",
            reward={},
            dailyClaimCount=used_today,
            dailyCap=int(offer["dailyCap"]),
            note="오늘 가능한 시청 횟수를 모두 사용했습니다.",
        )

    if not consume_ad_view_session(req.accountId, req.adViewToken, req.completionToken):
        raise HTTPException(status_code=409, detail="ad session expired or already consumed")

    inserted = insert_ad_claim(req.accountId, req.offerId, req.adViewToken, today, offer["rewardType"], int(offer["rewardAmount"]))
    if not inserted:
        raise HTTPException(status_code=409, detail="claim not inserted")

    ledger_inserted = insert_currency_ledger_idempotent(
        account_id=req.accountId,
        currency=str(offer["rewardType"]),
        amount=int(offer["rewardAmount"]),
        source_kind="ad_reward",
        source_id=req.adViewToken,
    )

    target_hunter_id = req.hunterId or session.get("hunterId")
    if target_hunter_id and offer["rewardType"] in {"gold", "gems", "exp"} and ledger_inserted:
        hunter = hunter_repo.get(target_hunter_id)
        if hunter and hunter.accountId == req.accountId:
            if offer["rewardType"] == "gold":
                hunter.gold = int(hunter.gold) + int(offer["rewardAmount"])
            elif offer["rewardType"] == "gems":
                hunter.gems = int(hunter.gems) + int(offer["rewardAmount"])
            elif offer["rewardType"] == "exp":
                hunter.exp = int(hunter.exp) + int(offer["rewardAmount"])
            hunter_repo.upsert(hunter)

    now_count = count_daily_ad_claims(req.accountId, req.offerId, today)
    write_audit("ads:claim", actor=req.accountId, target=req.offerId, payload={"adViewToken": req.adViewToken, "rewardType": offer["rewardType"], "rewardAmount": int(offer["rewardAmount"]), "ledgerInserted": ledger_inserted, "adNetwork": req.adNetwork or session.get("adNetwork"), "adUnitId": req.adUnitId or session.get("adUnitId")})
    return AdRewardClaimResponse(
        accountId=req.accountId,
        offerId=req.offerId,
        adViewToken=req.adViewToken,
        status="claimed",
        reward={
            "type": offer["rewardType"],
            "label": REWARD_LABELS.get(offer["rewardType"], offer["rewardType"]),
            "amount": int(offer["rewardAmount"]),
        },
        dailyClaimCount=now_count,
        dailyCap=int(offer["dailyCap"]),
        note="선택형 광고 보상이 지급되었습니다.",
    )


def _compute_vip_level(ad_views_lifetime: int) -> tuple[int, int | None, int | None]:
    vip_level = 0
    next_level = None
    next_req = None
    for level, threshold in VIP_THRESHOLDS:
        if ad_views_lifetime >= threshold:
            vip_level = level
        elif next_level is None:
            next_level = level
            next_req = threshold
    return vip_level, next_level, next_req


@router.get("/ads/vip-status", response_model=AdVipStatusResponse)
def get_ad_vip_status(accountId: str):
    ad_views_lifetime = count_lifetime_ad_claims(accountId)
    stage = compute_patron_stage(ad_views_lifetime)
    vip_level, next_level, next_req = _compute_vip_level(ad_views_lifetime)
    return AdVipStatusResponse(
        accountId=accountId,
        adViewsLifetime=ad_views_lifetime,
        vipLevel=vip_level,
        nextVipLevel=next_level,
        nextVipRequires=next_req,
        perks=VIP_PERKS.get(vip_level, []),
        designIntent=patron_design_intent(),
        vipTitle=VIP_TITLES.get(vip_level, "객잔 손님"),
        currentThreshold=int(stage.get("currentThreshold") or 0),
        remainingToNext=stage.get("remainingToNext"),
        progressToNext=float(stage.get("progressRatio") or 0.0),
        milestonePreview=list(stage.get("milestonePreview") or []),
    )
