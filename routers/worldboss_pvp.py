from fastapi import APIRouter, HTTPException

from core.admin_mode import (
    get_multiplier,
    WORLD_BOSS_REWARD_MULTIPLIER_KEY,
    PVP_REWARD_MULTIPLIER_KEY,
)
from core.rewards import rank_multiplier, apply_reward_multiplier
from core.schemas import (
    WorldBoss,
    PvPSeason,
    WorldBossClaimRequest,
    PvPClaimRequest,
    RewardClaimResponse,
)
from storage.repo_registry import worldboss_repo as worldbosses, pvp_season_repo as pvp_seasons, hunter_repo as hunters
from storage.sqlite_db import (
    get_worldboss_claim,
    insert_worldboss_claim,
    get_pvp_claim,
    insert_pvp_claim,
)

router = APIRouter()


@router.post("/worldbosses")
def upsert_worldboss(boss: WorldBoss):
    return worldbosses.upsert(boss)


@router.get("/worldbosses")
def list_worldbosses():
    return list(worldbosses.list().values())


@router.post("/pvp/seasons")
def upsert_pvp_season(season: PvPSeason):
    return pvp_seasons.upsert(season)


@router.get("/pvp/seasons")
def list_pvp_seasons():
    return list(pvp_seasons.list().values())


@router.post("/worldboss/claim", response_model=RewardClaimResponse)
def claim_worldboss(req: WorldBossClaimRequest):
    # 0) idempotency: SQLite truth
    existing = get_worldboss_claim(req.hunterId, req.bossId, req.seasonId)
    if existing:
        return RewardClaimResponse(
            hunterId=req.hunterId,
            seasonId=req.seasonId,
            source="worldboss",
            granted={"gold": existing["gold"], "exp": existing["exp"], "gems": existing["gems"]},
            note="already_claimed (sqlite primary key hit)",
        )

    boss = worldbosses.get(req.bossId)
    if not boss:
        raise HTTPException(status_code=404, detail="WorldBoss not found")

    base = {
        "gold": int(boss.baseGold),
        "exp": int(boss.baseExp),
        "gems": int(getattr(boss, "baseGems", 0)),
    }

    rm = rank_multiplier(req.rank)
    admin_mul = get_multiplier(WORLD_BOSS_REWARD_MULTIPLIER_KEY)

    reward = apply_reward_multiplier(base, rm * admin_mul)

    inserted = insert_worldboss_claim(req.hunterId, req.bossId, req.seasonId, reward["gold"], reward["exp"], reward["gems"])
    if not inserted:
        existing = get_worldboss_claim(req.hunterId, req.bossId, req.seasonId)
        if existing:
            reward = {"gold": existing["gold"], "exp": existing["exp"], "gems": existing["gems"]}

    h = hunters.get(req.hunterId)
    if h:
        h.gold = int(getattr(h, "gold", 0)) + int(reward["gold"])
        h.exp = int(getattr(h, "exp", 0)) + int(reward["exp"])
        h.gems = int(getattr(h, "gems", 0)) + int(reward["gems"])
        hunters.upsert(h)

    return RewardClaimResponse(
        hunterId=req.hunterId,
        seasonId=req.seasonId,
        source="worldboss",
        granted=reward,
        note="claimed (sqlite persisted; server-determined multipliers)",
    )


@router.post("/pvp/claim", response_model=RewardClaimResponse)
def claim_pvp(req: PvPClaimRequest):
    existing = get_pvp_claim(req.hunterId, req.seasonId)
    if existing:
        return RewardClaimResponse(
            hunterId=req.hunterId,
            seasonId=req.seasonId,
            source="pvp",
            granted={"gold": existing["gold"], "exp": existing["exp"], "gems": existing["gems"]},
            note="already_claimed (sqlite primary key hit)",
        )

    season = pvp_seasons.get(req.seasonId)
    if not season:
        raise HTTPException(status_code=404, detail="PvP season not found")

    base = {
        "gold": int(season.baseGold),
        "exp": int(season.baseExp),
        "gems": int(getattr(season, "baseGems", 0)),
    }

    rm = rank_multiplier(req.rank)
    admin_mul = get_multiplier(PVP_REWARD_MULTIPLIER_KEY)
    reward = apply_reward_multiplier(base, rm * admin_mul)

    inserted = insert_pvp_claim(req.hunterId, req.seasonId, reward["gold"], reward["exp"], reward["gems"])
    if not inserted:
        existing = get_pvp_claim(req.hunterId, req.seasonId)
        if existing:
            reward = {"gold": existing["gold"], "exp": existing["exp"], "gems": existing["gems"]}

    h = hunters.get(req.hunterId)
    if h:
        h.gold = int(getattr(h, "gold", 0)) + int(reward["gold"])
        h.exp = int(getattr(h, "exp", 0)) + int(reward["exp"])
        h.gems = int(getattr(h, "gems", 0)) + int(reward["gems"])
        hunters.upsert(h)

    return RewardClaimResponse(
        hunterId=req.hunterId,
        seasonId=req.seasonId,
        source="pvp",
        granted=reward,
        note="claimed (sqlite persisted; server-determined multipliers)",
    )