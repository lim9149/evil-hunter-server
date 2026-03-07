from fastapi import APIRouter, HTTPException

from core.schemas import RewardTierUpsertRequest
from storage.sqlite_db import list_reward_tiers, upsert_reward_tier, delete_reward_tier

router = APIRouter(prefix="/rewards", tags=["Rewards"])


def _validate_source(source: str) -> str:
    src = str(source).lower().strip()
    if src not in ("worldboss", "pvp"):
        raise HTTPException(status_code=400, detail="source must be 'worldboss' or 'pvp'")
    return src


@router.get("/{source}")
def list_tiers(source: str):
    src = _validate_source(source)
    return list_reward_tiers(src)


@router.post("/{source}")
def upsert_tier(source: str, req: RewardTierUpsertRequest):
    src = _validate_source(source)
    if int(req.rankTo) < int(req.rankFrom):
        raise HTTPException(status_code=400, detail="rankTo must be >= rankFrom")
    try:
        return upsert_reward_tier(src, req.rankFrom, req.rankTo, req.gold, req.exp, req.gems)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{source}/{rankFrom}/{rankTo}")
def delete_tier(source: str, rankFrom: int, rankTo: int):
    src = _validate_source(source)
    ok = delete_reward_tier(src, int(rankFrom), int(rankTo))
    return {"deleted": ok}