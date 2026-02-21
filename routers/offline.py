from fastapi import APIRouter, HTTPException
from core.schemas import OfflinePreviewRequest, OfflinePreviewResponse, OfflineCollectResponse
from core.offline import offline_reward
from core.redis_client import get_redis, try_idempotent_lock
from core.admin_mode import get_multiplier, OFFLINE_REWARD_MULTIPLIER_KEY
from storage.repo_registry import map_repo as maps, village_repo as villages, hunter_repo as hunters
from storage.sqlite_db import get_collect, insert_collect

router = APIRouter()

@router.post("/preview", response_model=OfflinePreviewResponse)
def preview(req: OfflinePreviewRequest):
    m = maps.get(req.mapId)
    if not m:
        raise HTTPException(status_code=404, detail="Map not found")
    v = villages.get(req.villageId) if req.villageId else None

    admin_mul = get_multiplier(OFFLINE_REWARD_MULTIPLIER_KEY)
    result = offline_reward(
        last_active_epoch=req.lastActiveAtEpochSec,
        now_epoch=req.nowEpochSec,
        base_gold_per_min=req.baseGoldPerMin,
        base_exp_per_min=req.baseExpPerMin,
        map_multiplier=float(getattr(m, "offlineMultiplier", 1.0)),
        village_tax_rate=float(getattr(v, "taxRate", 0.0)) if v else 0.0,
        village_storage_bonus=float(getattr(v, "offlineStorageBonus", 0.0)) if v else 0.0,
        vip_multiplier=req.vipMultiplier,
        event_multiplier=req.eventMultiplier,
        admin_multiplier=admin_mul,
    )
    return OfflinePreviewResponse(
        offlineMinutes=result["offlineMinutes"],
        cappedMinutes=result["cappedMinutes"],
        gold=result["gold"],
        exp=result["exp"],
        breakdown=result["breakdown"],
    )

@router.post("/collect", response_model=OfflineCollectResponse)
def collect(req: OfflinePreviewRequest):
    # 0) Source-of-truth idempotency (SQLite): if same (hunterId, nowEpochSec) already exists => return previous
    existing = get_collect(req.hunterId, req.nowEpochSec)
    if existing:
        return OfflineCollectResponse(
            hunterId=req.hunterId,
            collected={"gold": int(existing["gold"]), "exp": int(existing["exp"])},
            note="already_collected (sqlite primary key hit)"
        )

    # 1) Best-effort idempotency guard (Redis): prevent duplicate payout bursts
    r = get_redis()
    if r is not None:
        key = f"offline:collect:{req.hunterId}:{int(req.nowEpochSec)}"
        acquired = try_idempotent_lock(r, key, ttl_sec=86400)
        if not acquired:
            # Redis says duplicate; double-check SQLite and return safely
            existing = get_collect(req.hunterId, req.nowEpochSec)
            if existing:
                return OfflineCollectResponse(
                    hunterId=req.hunterId,
                    collected={"gold": int(existing["gold"]), "exp": int(existing["exp"])},
                    note="already_collected (redis lock)"
                )

    # 2) Validate map/village and calculate reward
    m = maps.get(req.mapId)
    if not m:
        raise HTTPException(status_code=404, detail="Map not found")
    v = villages.get(req.villageId) if req.villageId else None

    admin_mul = get_multiplier(OFFLINE_REWARD_MULTIPLIER_KEY)
    result = offline_reward(
        last_active_epoch=req.lastActiveAtEpochSec,
        now_epoch=req.nowEpochSec,
        base_gold_per_min=req.baseGoldPerMin,
        base_exp_per_min=req.baseExpPerMin,
        map_multiplier=float(getattr(m, "offlineMultiplier", 1.0)),
        village_tax_rate=float(getattr(v, "taxRate", 0.0)) if v else 0.0,
        village_storage_bonus=float(getattr(v, "offlineStorageBonus", 0.0)) if v else 0.0,
        vip_multiplier=req.vipMultiplier,
        event_multiplier=req.eventMultiplier,
        admin_multiplier=admin_mul,
    )

    gold = int(result["gold"])
    exp = int(result["exp"])

    # 3) Persist (SQLite). If race, return existing.
    inserted = insert_collect(req.hunterId, req.nowEpochSec, gold, exp)
    if not inserted:
        existing = get_collect(req.hunterId, req.nowEpochSec)
        if existing:
            gold = int(existing["gold"])
            exp = int(existing["exp"])

    # 4) Apply to hunter (demo memory repo). In production you'd do DB transaction.
    h = hunters.get(req.hunterId)
    if h:
        h.gold = int(getattr(h, "gold", 0)) + gold
        h.exp = int(getattr(h, "exp", 0)) + exp
        hunters.upsert(h)

    return OfflineCollectResponse(
        hunterId=req.hunterId,
        collected={"gold": gold, "exp": exp},
        note="collected (sqlite persisted; redis guard best-effort)"
    )