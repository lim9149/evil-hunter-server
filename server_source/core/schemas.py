# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
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
    service: str = "murim-inn-rebuild-server"
    version: str = "0.4.1"


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

    # operation / originality layer
    operationStyle: str = "steady"
    restDiscipline: str = "measured"
    trainingFocus: str = "body"
    morale: float = 50.0
    fatigue: float = 0.0
    bondFacilityId: str = "inn_main"
    huntStreak: int = 0
    activeCommand: str = "hold"
    manualControl: bool = False
    desiredMonsterCount: int = Field(3, ge=1, le=20)
    aiMode: str = "autonomous"
    preferredActivity: str = "hunt"
    socialDrive: float = 50.0
    disciplineDrive: float = 50.0
    braveryDrive: float = 50.0

    # state machine / operator loop helpers
    assignedHuntZoneId: str = "south_field"
    desiredLoopCount: int = Field(2, ge=1, le=12)
    satiety: float = Field(75.0, ge=0.0, le=100.0)
    stamina: float = Field(75.0, ge=0.0, le=100.0)
    bagLoad: float = Field(0.0, ge=0.0, le=100.0)
    durability: float = Field(100.0, ge=0.0, le=100.0)
    loyalty: float = Field(50.0, ge=0.0, le=100.0)
    promotionReady: bool = False
    bodyReforgeStage: int = Field(0, ge=0, le=9)
    insight: float = Field(0.0, ge=0.0, le=100.0)
    safetyStockPreference: int = Field(3, ge=0, le=99)
    lastFailureCode: str = ""
    lastFailureDetail: str = ""
    sectTokenCount: int = Field(0, ge=0, le=99)
    sectDiscipline: float = Field(0.0, ge=0.0, le=100.0)


class HunterOperationConfigRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    operationStyle: Optional[Literal["steady", "vanguard", "shadow", "support"]] = None
    restDiscipline: Optional[Literal["frugal", "measured", "lavish"]] = None
    trainingFocus: Optional[Literal["body", "weapon", "mind", "footwork"]] = None
    morale: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    fatigue: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    bondFacilityId: Optional[str] = None


class HunterOperationPlanResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    hunterId: str
    operationStyle: str
    restDiscipline: str
    trainingFocus: str
    morale: float
    fatigue: float
    recommendedFacilityId: str
    combatProfile: Dict[str, Any] = Field(default_factory=dict)
    offlineProfile: Dict[str, Any] = Field(default_factory=dict)
    dailyPlan: List[str] = Field(default_factory=list)
    originalityNotes: List[str] = Field(default_factory=list)




class HunterCommandRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    command: Literal["hunt", "train", "rest", "eat", "heal", "patrol", "return", "hold"]
    desiredMonsterCount: int = Field(3, ge=1, le=20)


class HunterCommandResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    hunterId: str
    command: str
    desiredMonsterCount: int
    note: str = ""


class HunterAiConfigRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    aiMode: Optional[Literal["autonomous", "assisted", "manual_only"]] = None
    preferredActivity: Optional[Literal["hunt", "train", "patrol", "rest", "socialize"]] = None
    socialDrive: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    disciplineDrive: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    braveryDrive: Optional[float] = Field(default=None, ge=0.0, le=100.0)


class HunterAiProfileResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    hunterId: str
    aiMode: str
    manualOverrideActive: bool
    preferredActivity: str
    socialDrive: float
    disciplineDrive: float
    braveryDrive: float
    personalitySummary: str = ""
    dailyRoutineTemplate: List[str] = Field(default_factory=list)
    decisionWeights: Dict[str, Any] = Field(default_factory=dict)
    commandPolicy: List[str] = Field(default_factory=list)
    originalityHooks: List[str] = Field(default_factory=list)


class HunterAssignHuntZoneRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    huntZoneId: str = Field(min_length=1, max_length=64)
    desiredLoopCount: int = Field(2, ge=1, le=12)


class HunterAssignHuntZoneResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    hunterId: str
    huntZoneId: str
    desiredLoopCount: int
    note: str = ""


class HunterStateMachineResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    hunterId: str
    assignedHuntZoneId: str
    currentState: str
    nextState: str
    targetLocation: str
    targetReason: str
    recoveryPriority: str = "normal"
    suggestedActionWindow: str = ""
    operatorTodos: List[str] = Field(default_factory=list)
    riskFlags: List[str] = Field(default_factory=list)
    transitionRules: List[str] = Field(default_factory=list)
    patronSynergy: str = ""


class AdVipStatusResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    accountId: str
    adViewsLifetime: int
    vipLevel: int
    nextVipLevel: Optional[int] = None
    nextVipRequires: Optional[int] = None
    perks: List[str] = Field(default_factory=list)
    designIntent: str = ""
    vipTitle: str = ""
    currentThreshold: int = 0
    remainingToNext: Optional[int] = None
    progressToNext: float = 0.0
    milestonePreview: List[Dict[str, Any]] = Field(default_factory=list)


class EconomySimulationRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    accountId: str = "guest"
    hunterIds: List[str] = Field(default_factory=list)
    simulatedHours: int = Field(12, ge=1, le=72)
    battleMinutesPerLoop: float = Field(4.0, gt=0.5, le=20.0)
    restMinutesPerLoop: float = Field(2.0, gt=0.25, le=20.0)
    crowdingFactor: float = Field(0.15, ge=0.0, le=1.0)


class EconomySimulationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    accountId: str
    simulatedHours: int
    hunterCount: int
    summary: Dict[str, Any] = Field(default_factory=dict)
    perHunter: List[Dict[str, Any]] = Field(default_factory=list)
    balanceWarnings: List[str] = Field(default_factory=list)
    designHooks: List[str] = Field(default_factory=list)




class OperatorActionResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    ok: bool = True
    resultCode: str
    detail: str = ""
    hunterId: Optional[str] = None
    accountId: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class HunterSettleReturnRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    foundGold: int = Field(0, ge=0, le=2_000_000_000)
    foundMaterials: Dict[str, int] = Field(default_factory=dict)
    taxRate: float = Field(0.12, ge=0.0, le=0.5)
    loopsCompleted: int = Field(1, ge=1, le=99)
    fatigueDelta: float = Field(8.0, ge=0.0, le=100.0)
    satietyDelta: float = Field(-10.0, ge=-100.0, le=100.0)
    durabilityDelta: float = Field(-5.0, ge=-100.0, le=100.0)
    eventTag: str = "normal_return"


class HunterTrainingRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    packageId: Literal["body", "weapon", "mind", "footwork"]
    intensity: Literal["light", "standard", "focused"] = "standard"


class HunterBodyReforgeRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    catalystId: str = "rebirth_pill"
    consumeGold: int = Field(0, ge=0, le=2_000_000_000)
    consumeMaterials: Dict[str, int] = Field(default_factory=dict)


class OperatorCraftRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    accountId: str
    recipeId: Literal["potion_basic", "weapon_iron", "armor_leather", "charm_lucky", "pill_focus", "weapon_refined", "armor_guardian", "charm_dragon"]
    quantity: int = Field(1, ge=1, le=999)


class OperatorSellRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    accountId: str
    itemId: str = Field(min_length=1, max_length=64)
    quantity: int = Field(1, ge=1, le=999)
    unitPrice: int = Field(1, ge=1, le=2_000_000_000)




class OperatorMissionClaimRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    accountId: str
    missionId: str = Field(min_length=1, max_length=64)
    scope: Literal["daily", "weekly"]


class OperatorMissionSnapshotResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    accountId: str
    claimableCount: int
    metrics: Dict[str, int] = Field(default_factory=dict)
    missions: List[Dict[str, Any]] = Field(default_factory=list)
    designIntent: str = ""


class OperatorRecipeCatalogResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    recipes: List[Dict[str, Any]] = Field(default_factory=list)
    designIntent: str = ""


class HunterGrowthRuleResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    hunterId: str
    promotion: Dict[str, Any] = Field(default_factory=dict)
    bodyReforge: Dict[str, Any] = Field(default_factory=dict)
    advice: List[str] = Field(default_factory=list)

class OperatorSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    accountId: str
    hunterCount: int
    operatorRank: Dict[str, Any] = Field(default_factory=dict)
    patronStatus: Dict[str, Any] = Field(default_factory=dict)
    treasury: Dict[str, Any] = Field(default_factory=dict)
    inventories: Dict[str, int] = Field(default_factory=dict)
    pendingTodos: List[str] = Field(default_factory=list)
    recentLogs: List[Dict[str, Any]] = Field(default_factory=list)
    designHooks: List[str] = Field(default_factory=list)


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

# -------------------------
# Story / Tutorial / Ads / Compliance
# -------------------------


class TutorialQuestCompleteRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    accountId: str
    questId: str


class StoryProgressUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    accountId: str
    chapterId: str


class AdSessionStartRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    accountId: str
    offerId: str
    placement: str = ""
    hunterId: Optional[str] = None


class AdSessionCompleteRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    accountId: str
    offerId: str
    adViewToken: str = Field(..., min_length=10, description="서버가 발급한 광고 세션 토큰")
    placement: str = ""
    adNetwork: str = "rewarded"
    adUnitId: str = ""
    completionProof: str = Field(..., min_length=8, description="광고 SDK 완료 콜백에서 받은 proof/token. 샘플 단계에서는 완료 proof 문자열을 저장")


class AdRewardClaimRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    accountId: str
    offerId: str
    adViewToken: str = Field(..., min_length=10, description="서버가 발급한 광고 세션 토큰")
    completionToken: str = Field(..., min_length=12, description="/ads/session/complete 후 서버가 반환한 멱등 토큰")
    placement: str = ""
    hunterId: Optional[str] = None
    adNetwork: str = "rewarded"
    adUnitId: str = ""


class AdRewardClaimResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    accountId: str
    offerId: str
    adViewToken: str
    status: Literal["claimed", "duplicate", "daily_cap_reached"]
    reward: Dict[str, Any] = Field(default_factory=dict)
    dailyClaimCount: int = 0
    dailyCap: int = 0
    note: str = ""


# -------------------------
# TownWorld (single-scene live town)
# -------------------------


class TownFacilityAnchor(BaseModel):
    model_config = ConfigDict(extra="ignore")

    facilityId: str
    label: str
    kind: str
    x: float
    y: float
    z: float


class TownMonsterZone(BaseModel):
    model_config = ConfigDict(extra="ignore")

    zoneId: str
    label: str
    difficulty: int = 1
    spawnCount: int = 1
    x: float
    y: float
    z: float
    radius: float = 1.0


class TownHudRules(BaseModel):
    model_config = ConfigDict(extra="ignore")

    useOverlayPanels: bool = True
    battleSceneAllowed: bool = False
    optionalAdsOnlyAtBreaks: bool = True
    mailboxButton: bool = True
    announcementButton: bool = True
    storyButton: bool = True


class TownWorldDefinitionResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    worldId: str
    worldName: str
    sceneName: str
    cameraMode: str
    facilities: List[TownFacilityAnchor] = Field(default_factory=list)
    monsterZones: List[TownMonsterZone] = Field(default_factory=list)
    hudRules: TownHudRules


class TownWorldSnapshotResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    accountId: str
    worldId: str
    recommendedFlow: List[str] = Field(default_factory=list)
    townState: Dict[str, Any] = Field(default_factory=dict)
