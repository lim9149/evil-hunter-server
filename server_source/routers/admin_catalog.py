# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from core.security.deps import require_admin
from core.audit import write_audit

from core.tier import list_tiers, upsert_tier
from core.mbti import list_mbti_traits, upsert_mbti_trait
from core.items import list_item_defs, upsert_item_def
from core.promotion import list_promotion_nodes, upsert_promotion_node
from storage.sqlite_db import get_conn

router = APIRouter()


# -------------------------
# IAP product catalog
# -------------------------
class IapProductUpsertReq(BaseModel):
    productId: str
    currency: str = Field(pattern=r"^(gold|gems|exp)$")
    amount: int = Field(ge=0)


@router.get("/iap-products")
def get_iap_products(admin_id: str = Depends(require_admin)):
    conn = get_conn()
    rows = conn.execute(
        "SELECT product_id, currency, amount, updatedAt FROM iap_products ORDER BY product_id ASC;"
    ).fetchall()
    return [
        {"productId": r[0], "currency": r[1], "amount": int(r[2]), "updatedAt": r[3]} for r in rows
    ]


@router.post("/iap-products")
def upsert_iap_product(req: IapProductUpsertReq, admin_id: str = Depends(require_admin)):
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO iap_products(product_id, currency, amount, updatedAt)
        VALUES(?,?,?,datetime('now'))
        ON CONFLICT(product_id)
        DO UPDATE SET currency=excluded.currency, amount=excluded.amount, updatedAt=datetime('now');
        """,
        (req.productId, req.currency, int(req.amount)),
    )
    write_audit(
        kind="admin:catalog:iap_product_upsert",
        actor=admin_id,
        target=req.productId,
        payload=req.model_dump(),
    )
    return {"ok": True, **req.model_dump()}


# -------------------------
# Tier definitions
# -------------------------
class TierUpsertReq(BaseModel):
    seasonId: str
    tierId: str
    multiplier: float = Field(gt=0)


@router.get("/tiers")
def get_tiers(seasonId: str | None = None, admin_id: str = Depends(require_admin)):
    return list_tiers(seasonId)


@router.post("/tiers")
def post_tier(req: TierUpsertReq, admin_id: str = Depends(require_admin)):
    row = upsert_tier(req.seasonId, req.tierId, req.multiplier)
    write_audit("admin:catalog:tier_upsert", actor=admin_id, target=f"{req.seasonId}:{req.tierId}", payload=row)
    return row


# -------------------------
# MBTI traits
# -------------------------
class MbtiUpsertReq(BaseModel):
    mbti: str
    atkMul: float = Field(gt=0)
    hpMul: float = Field(gt=0)
    defMul: float = Field(gt=0)
    goldMul: float = Field(gt=0)
    expMul: float = Field(gt=0)


@router.get("/mbti")
def get_mbti(admin_id: str = Depends(require_admin)):
    return list_mbti_traits()


@router.post("/mbti")
def post_mbti(req: MbtiUpsertReq, admin_id: str = Depends(require_admin)):
    row = upsert_mbti_trait(
        mbti=req.mbti,
        atk_mul=req.atkMul,
        hp_mul=req.hpMul,
        def_mul=req.defMul,
        gold_mul=req.goldMul,
        exp_mul=req.expMul,
    )
    write_audit("admin:catalog:mbti_upsert", actor=admin_id, target=req.mbti, payload=row)
    return row


# -------------------------
# Item definitions
# -------------------------
class ItemUpsertReq(BaseModel):
    itemId: str
    seasonId: str
    tierId: str
    slot: str
    atkMul: float = Field(gt=0)
    hpMul: float = Field(gt=0)
    defMul: float = Field(gt=0)
    skillMul: float = Field(gt=0)


@router.get("/items")
def get_items(seasonId: str | None = None, tierId: str | None = None, admin_id: str = Depends(require_admin)):
    return list_item_defs(seasonId, tierId)


@router.post("/items")
def post_item(req: ItemUpsertReq, admin_id: str = Depends(require_admin)):
    row = upsert_item_def(
        item_id=req.itemId,
        season_id=req.seasonId,
        tier_id=req.tierId,
        slot=req.slot,
        atk_mul=req.atkMul,
        hp_mul=req.hpMul,
        def_mul=req.defMul,
        skill_mul=req.skillMul,
    )
    write_audit("admin:catalog:item_upsert", actor=admin_id, target=req.itemId, payload=row)
    return row


# -------------------------
# Promotion nodes
# -------------------------
class PromotionNodeUpsertReq(BaseModel):
    nodeId: str
    parentNodeId: str | None = None
    jobId: str
    choiceGroup: str | None = None
    promotionMultiplier: float = Field(gt=0)
    statBonus: dict[str, float] = Field(default_factory=dict)
    skillUnlock: list[str] = Field(default_factory=list)


@router.get("/promotions")
def get_promotions(admin_id: str = Depends(require_admin)):
    return list_promotion_nodes()


@router.post("/promotions")
def post_promotions(req: PromotionNodeUpsertReq, admin_id: str = Depends(require_admin)):
    row = upsert_promotion_node(
        node_id=req.nodeId,
        parent_node_id=req.parentNodeId,
        job_id=req.jobId,
        choice_group=req.choiceGroup,
        promotion_multiplier=req.promotionMultiplier,
        stat_bonus=req.statBonus,
        skill_unlock=req.skillUnlock,
    )
    write_audit("admin:catalog:promotion_upsert", actor=admin_id, target=req.nodeId, payload=row)
    return row