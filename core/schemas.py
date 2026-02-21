from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class Monster(BaseModel):
    monsterId: str = Field(..., min_length=1)
    name: str
    level: int = Field(1, ge=1)
    hp: float = Field(100.0, ge=0)
    atk: float = Field(10.0, ge=0)
    defense: float = Field(0.0, ge=0)
    goldPerMin: float = Field(1.0, ge=0)
    expPerMin: float = Field(1.0, ge=0)

class Map(BaseModel):
    mapId: str = Field(..., min_length=1)
    name: str
    recommendedLevel: int = Field(1, ge=1)
    monsterPool: List[str] = Field(default_factory=list)
    offlineMultiplier: float = Field(1.0, gt=0)

class Village(BaseModel):
    villageId: str = Field(..., min_length=1)
    name: str
    taxRate: float = Field(0.0, ge=0.0, le=1.0)
    offlineStorageBonus: float = Field(0.0, ge=0.0)

class OfflinePreviewRequest(BaseModel):
    hunterId: str
    lastActiveAtEpochSec: int
    nowEpochSec: int
    mapId: str
    villageId: Optional[str] = None
    baseGoldPerMin: float = Field(..., ge=0)
    baseExpPerMin: float = Field(..., ge=0)
    vipMultiplier: float = Field(1.0, gt=0)
    eventMultiplier: float = Field(1.0, gt=0)
    adminMultiplier: float = Field(1.0, gt=0)

class OfflinePreviewResponse(BaseModel):
    offlineMinutes: int
    cappedMinutes: int
    gold: int
    exp: int
    breakdown: Dict[str, Any]

class OfflineCollectResponse(BaseModel):
    hunterId: str
    collected: Dict[str, int]
    note: str

class Hunter(BaseModel):
    hunterId: str = Field(..., min_length=1)
    accountId: str = Field(..., min_length=1)
    slotIndex: int = Field(..., ge=0)
    name: str = Field(..., min_length=1)

    jobId: str = Field("novice", min_length=1)
    level: int = Field(1, ge=1)
    exp: int = Field(0, ge=0)
    gold: int = Field(0, ge=0)
    gems: int = Field(0, ge=0)

    powerScore: float = Field(1.0, ge=0)
    hp: float = Field(100.0, ge=0)
    atk: float = Field(10.0, ge=0)
    defense: float = Field(0.0, ge=0)

class CombatFightRequest(BaseModel):
    hunterId: str
    monsterId: str
    mapId: Optional[str] = None
    buffs: Dict[str, float] = Field(default_factory=dict)

class CombatFightResponse(BaseModel):
    hunterId: str
    monsterId: str
    damagePerHit: int
    hitsToKill: int
    totalSec: float
    fightSucceed: bool
    breakdown: Dict[str, Any]


class AdminMode(BaseModel):
    """Operator(Admin) mode toggle + multiplier.

    key examples:
      - OFFLINE_REWARD_MULTIPLIER
      - WORLD_BOSS_REWARD_MULTIPLIER
      - PVP_REWARD_MULTIPLIER
    """
    key: str = Field(..., min_length=1)
    enabled: bool = False
    multiplier: float = Field(1.0, gt=0)


class AdminModeUpsertRequest(BaseModel):
    key: str = Field(..., min_length=1)
    enabled: bool
    multiplier: float = Field(1.0, gt=0)


class WorldBoss(BaseModel):
    bossId: str = Field(..., min_length=1)
    name: str
    maxHp: int = Field(100000, ge=1)
    difficulty: int = Field(1, ge=1)
    baseGold: int = Field(1000, ge=0)
    baseExp: int = Field(500, ge=0)
    baseGems: int = Field(0, ge=0)


class PvPSeason(BaseModel):
    seasonId: str = Field(..., min_length=1)
    name: str
    baseGold: int = Field(500, ge=0)
    baseExp: int = Field(250, ge=0)
    baseGems: int = Field(0, ge=0)


class WorldBossClaimRequest(BaseModel):
    hunterId: str
    bossId: str
    seasonId: str
    rank: int = Field(..., ge=1)


class PvPClaimRequest(BaseModel):
    hunterId: str
    seasonId: str
    rank: int = Field(..., ge=1)


class RewardClaimResponse(BaseModel):
    hunterId: str
    seasonId: str
    source: str
    granted: Dict[str, int]
    note: str