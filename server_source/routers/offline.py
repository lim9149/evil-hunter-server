# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
from fastapi import APIRouter, HTTPException
from core.schemas import OfflinePreviewRequest, OfflinePreviewResponse, OfflineCollectResponse
from core.offline import offline_reward
from core.hunter_operations import compute_operation_modifiers, normalized_hunter_operation
from core.redis_client import get_redis, try_idempotent_lock
from core.admin_mode import get_multiplier, OFFLINE_REWARD_MULTIPLIER_KEY
from storage.repo_registry import map_repo as maps, village_repo as villages, hunter_repo as hunters
from storage.sqlite_db import get_collect, insert_collect

router = APIRouter()


def _operation_context(hunter_id: str):
    hunter = hunters.get(hunter_id)
    if not hunter:
        return 1.0, {"morale": 50.0, "fatigue": 0.0}
    return compute_operation_modifiers(hunter)["offlineMul"], normalized_hunter_operation(hunter)


@router.post("/preview", response_model=OfflinePreviewResponse)
def preview(req: OfflinePreviewRequest):
    m = maps.get(req.mapId)
    if not m:
        raise HTTPException(status_code=404, detail="Map not found")
    v = villages.get(req.villageId) if req.villageId else None

    op_mul, operation = _operation_context(req.hunterId)
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
        operation_multiplier=op_mul,
        morale=float(operation["morale"]),
        fatigue=float(operation["fatigue"]),
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
    existing = get_collect(req.hunterId, req.nowEpochSec)
    if existing:
        return OfflineCollectResponse(
            hunterId=req.hunterId,
            collected={"gold": int(existing["gold"]), "exp": int(existing["exp"])},
            note="already_collected (sqlite primary key hit)"
        )

    r = get_redis()
    if r is not None:
        key = f"offline:collect:{req.hunterId}:{int(req.nowEpochSec)}"
        acquired = try_idempotent_lock(r, key, ttl_sec=86400)
        if not acquired:
            existing = get_collect(req.hunterId, req.nowEpochSec)
            if existing:
                return OfflineCollectResponse(
                    hunterId=req.hunterId,
                    collected={"gold": int(existing["gold"]), "exp": int(existing["exp"])},
                    note="already_collected (redis lock)"
                )

    m = maps.get(req.mapId)
    if not m:
        raise HTTPException(status_code=404, detail="Map not found")
    v = villages.get(req.villageId) if req.villageId else None

    op_mul, operation = _operation_context(req.hunterId)
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
        operation_multiplier=op_mul,
        morale=float(operation["morale"]),
        fatigue=float(operation["fatigue"]),
    )

    gold = int(result["gold"])
    exp = int(result["exp"])

    inserted = insert_collect(req.hunterId, req.nowEpochSec, gold, exp)
    if not inserted:
        existing = get_collect(req.hunterId, req.nowEpochSec)
        if existing:
            gold = int(existing["gold"])
            exp = int(existing["exp"])

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
