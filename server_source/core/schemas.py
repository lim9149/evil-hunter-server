from __future__ import annotations

"""Pydantic schemas used by routers and storage repos.

IMPORTANT
- Tests in this repository expect "flat" fields (hp/atk/defense, monsterId, ...)
- Routers also rely on catalog/extension fields (tierId/mbti/promotionPath/items)

So this module provides a backward-compatible superset schema set.

Design principles
- Server-authoritative: requests ignore unknown fields (extra="ignore") to prevent spoofing.
- Data-driven: ids are strings, extensible lists/dicts where needed.
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# -------------------------
# Common
# -------------------------


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    error: str
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ok: bool = True
    service: str = "evil-hunter-server"
    version: str = "0.1.0"


# -------------------------
# Core CRUD entities
# -------------------------


class Monster(BaseModel):
    model_config = ConfigDict(extra="ignore")

    monsterId: str
    name: str = ""
    level: int = 1

    hp: float = 0
    atk: float = 0
    defense: float = 0

    # offline reward baseline (server uses request values, but kept for catalog)
    goldPerMin: int = 0
    expPerMin: int = 0

    tags: List[str] = Field(default_factory=list)


class Map(BaseModel):
    model_config = ConfigDict(extra="ignore")

    mapId: str
    name: str = ""
    recommendedLevel: int = 1
    monsterPool: List[str] = Field(default_factory=list)
    offlineMultiplier: float = 1.0


class Village(BaseModel):
    model_config = ConfigDict(extra="ignore")

    villageId: str
    name: str = ""
    taxRate: float = 0.0
    offlineStorageBonus: float = 0.0


class Hunter(BaseModel):
    model_config = ConfigDict(extra="ignore")

    # identity / slots
    hunterId: str
    accountId: str
    slotIndex: int = Field(0, ge=0)
    name: str = ""

    # progression (legacy)
    jobId: str = "novice"
    level: int = Field(1, ge=1)
    exp: int = Field(0, ge=0)
    powerScore: float = 0.0

    # combat stats
    hp: float = 0.0
    atk: float = 0.0
    defense: float = 0.0

    # currencies (legacy fields kept for tests)
    gold: int = Field(0, ge=0)
    gems: int = Field(0, ge=0)

    # extension fields (today goal: catalog 기반)
    mbti: str = "NONE"  # server-side assigned on recruit
    tierId: str = "T1"
    seasonId: str = "S1"
    promotionPath: List[str] = Field(default_factory=list)
    equippedItemIds: List[str] = Field(default_factory=list)
    skillsUnlocked: List[str] = Field(default_factory=list)


# -------------------------
# Offline
# -------------------------


class OfflinePreviewRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    hunterId: str
    lastActiveAtEpochSec: int
    nowEpochSec: int
    mapId: str
    villageId: str
    baseGoldPerMin: int
    baseExpPerMin: int

    # client-sent multipliers are ignored by server engine;
    # kept for compatibility / debugging
    vipMultiplier: float = 1.0
    eventMultiplier: float = 1.0
    adminMultiplier: float = 1.0


class OfflinePreviewResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    offlineMinutes: int
    cappedMinutes: int
    gold: int
    exp: int
    breakdown: Dict[str, Any] = Field(default_factory=dict)
    note: str = ""


class OfflineCollectResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    hunterId: str
    collected: Dict[str, int]
    note: str = ""


# -------------------------
# Combat
# -------------------------


class CombatFightRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    hunterId: str
    monsterId: str
    # server-side engine may use deterministic seed in future
    seed: Optional[int] = None
    buffs: Dict[str, Any] = Field(default_factory=dict)


class CombatFightResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    hunterId: str
    monsterId: str
    damagePerHit: float
    hitsToKill: int
    totalSec: float
    fightSucceed: bool
    breakdown: Dict[str, Any] = Field(default_factory=dict)


# -------------------------
# Admin / Operator
# -------------------------


class AdminModeUpsertRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    key: str
    enabled: bool = True
    multiplier: float = Field(1.0, gt=0)


# -------------------------
# Promotion / Tier / Items (catalog-driven)
# -------------------------


class HunterPromoteRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    nodeId: str = Field(..., description="Promotion node id to apply")


class HunterPromoteResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    hunter: Hunter
    appliedStatBonus: Dict[str, float] = Field(default_factory=dict)
    unlockedSkills: List[str] = Field(default_factory=list)
    promotionMultiplier: float = 1.0


class HunterEquipRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    equippedItemIds: List[str] = Field(default_factory=list, description="List of equipped item ids")


class HunterEquipResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    hunter: Hunter
    itemMultipliers: Dict[str, float] = Field(default_factory=dict)
    note: str = ""


class HunterTierUpRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    tierId: str


class HunterTierUpResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    hunter: Hunter
    changed: bool = True
    note: str = ""


# -------------------------
# WorldBoss / PvP (persisted catalogs + idempotent claims)
# -------------------------


class WorldBoss(BaseModel):
    model_config = ConfigDict(extra="ignore")

    bossId: str
    name: str = ""
    maxHp: int = Field(1, ge=1)
    difficulty: int = Field(1, ge=1)

    baseGold: int = 0
    baseExp: int = 0
    baseGems: int = 0


class PvPSeason(BaseModel):
    model_config = ConfigDict(extra="ignore")

    seasonId: str
    name: str = ""
    baseGold: int = 0
    baseExp: int = 0
    baseGems: int = 0


class RewardTier(BaseModel):
    model_config = ConfigDict(extra="ignore")

    kind: Literal["worldboss", "pvp"]
    rankMin: int = Field(..., ge=1)
    rankMax: Optional[int] = Field(default=None, ge=1)
    multiplier: float = Field(1.0, gt=0)


class RewardTierUpsertRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    kind: Literal["worldboss", "pvp"]
    rankMin: int = Field(..., ge=1)
    rankMax: Optional[int] = Field(default=None, ge=1)
    multiplier: float = Field(1.0, gt=0)


class WorldBossClaimRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    hunterId: str
    bossId: str
    seasonId: str
    rank: int = Field(..., ge=1)


class PvPClaimRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    hunterId: str
    seasonId: str
    rank: int = Field(..., ge=1)


class RewardClaimResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    hunterId: str
    seasonId: str
    source: Literal["worldboss", "pvp"]
    granted: Dict[str, int]
    note: str = ""