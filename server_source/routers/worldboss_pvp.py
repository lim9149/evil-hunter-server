# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
from fastapi import APIRouter, HTTPException

from core.admin_mode import (
    get_multiplier,
    WORLD_BOSS_REWARD_MULTIPLIER_KEY,
    PVP_REWARD_MULTIPLIER_KEY,
)
from core.rewards import apply_reward_multiplier
from core.schemas import (
    WorldBoss,
    PvPSeason,
    WorldBossClaimRequest,
    PvPClaimRequest,
    RewardClaimResponse,
    RewardTier,
    RewardTierUpsertRequest,
)
from storage.repo_registry import hunter_repo as hunters
from storage.sqlite_db import (
    get_worldboss_claim,
    insert_worldboss_claim,
    get_pvp_claim,
    insert_pvp_claim,
    get_rank_multiplier,
    list_reward_tiers,
    upsert_reward_tier,
    upsert_worldboss_db,
    list_worldbosses_db,
    get_worldboss_db,
    upsert_pvp_season_db,
    list_pvp_seasons_db,
    get_pvp_season_db,
)

router = APIRouter()


@router.get("/rewards/tiers/{kind}")
def get_reward_tiers(kind: str):
    if kind not in ("worldboss", "pvp"):
        raise HTTPException(status_code=400, detail="kind must be 'worldboss' or 'pvp'")
    return list_reward_tiers(kind)


@router.post("/rewards/tiers", response_model=RewardTier)
def post_reward_tier(req: RewardTierUpsertRequest):
    if req.kind not in ("worldboss", "pvp"):
        raise HTTPException(status_code=400, detail="kind must be 'worldboss' or 'pvp'")
    if req.rankMax is not None and req.rankMax < req.rankMin:
        raise HTTPException(status_code=400, detail="rankMax must be >= rankMin")
    if req.multiplier <= 0:
        raise HTTPException(status_code=400, detail="multiplier must be > 0")
    return upsert_reward_tier(req.kind, req.rankMin, req.rankMax, req.multiplier)


# -------------------------
# worldboss catalog (persisted)
# -------------------------
@router.post("/worldbosses")
def upsert_worldboss(boss: WorldBoss):
    # Persist to SQLite
    return upsert_worldboss_db(boss.model_dump())


@router.get("/worldbosses")
def list_worldbosses():
    return list_worldbosses_db()


# -------------------------
# pvp season catalog (persisted)
# -------------------------
@router.post("/pvp/seasons")
def upsert_pvp_season(season: PvPSeason):
    # Persist to SQLite
    return upsert_pvp_season_db(season.model_dump())


@router.get("/pvp/seasons")
def list_pvp_seasons():
    return list_pvp_seasons_db()


# -------------------------
# claims (idempotent + admin multiplier + rank tier)
# -------------------------
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

    boss = get_worldboss_db(req.bossId)
    if not boss:
        raise HTTPException(status_code=404, detail="WorldBoss not found")

    base = {
        "gold": int(boss["baseGold"]),
        "exp": int(boss["baseExp"]),
        "gems": int(boss.get("baseGems", 0)),
    }

    rm = get_rank_multiplier("worldboss", req.rank)  # DB reward_tier
    admin_mul = get_multiplier(WORLD_BOSS_REWARD_MULTIPLIER_KEY)

    reward = apply_reward_multiplier(base, rm * admin_mul)

    inserted = insert_worldboss_claim(
        req.hunterId, req.bossId, req.seasonId,
        reward["gold"], reward["exp"], reward["gems"]
    )
    if not inserted:
        # race-safe: fetch persisted
        existing = get_worldboss_claim(req.hunterId, req.bossId, req.seasonId)
        if existing:
            reward = {"gold": existing["gold"], "exp": existing["exp"], "gems": existing["gems"]}

    # apply to hunter snapshot (memory repo)
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

    season = get_pvp_season_db(req.seasonId)
    if not season:
        raise HTTPException(status_code=404, detail="PvP season not found")

    base = {
        "gold": int(season["baseGold"]),
        "exp": int(season["baseExp"]),
        "gems": int(season.get("baseGems", 0)),
    }

    rm = get_rank_multiplier("pvp", req.rank)  # DB reward_tier
    admin_mul = get_multiplier(PVP_REWARD_MULTIPLIER_KEY)

    reward = apply_reward_multiplier(base, rm * admin_mul)

    inserted = insert_pvp_claim(
        req.hunterId, req.seasonId,
        reward["gold"], reward["exp"], reward["gems"]
    )
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