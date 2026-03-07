from storage.repo_registry import hunter_repo as repo
from fastapi import APIRouter, HTTPException, Query
from core.schemas import Hunter, HunterPromoteRequest, HunterPromoteResponse, HunterEquipRequest, HunterEquipResponse, HunterTierUpRequest, HunterTierUpResponse
from core.mbti import random_mbti
from core.promotion import get_promotion_node, compute_promotion_effect
from core.items import get_item_def, compute_item_multipliers
from core.tier import tier_rank

router = APIRouter()

@router.get("")
def list_hunters(accountId: str | None = Query(default=None)):
    items = list(repo.list().values())
    if accountId:
        items = [h for h in items if h.accountId == accountId]
    return items

@router.get("/{hunter_id}")
def get_hunter(hunter_id: str):
    h = repo.get(hunter_id)
    if not h:
        raise HTTPException(status_code=404, detail="Hunter not found")
    return h

@router.post("")
def upsert_hunter(hunter: Hunter):
    # Backward compatible default: if not provided, keep neutral.
    # (Random assignment is done via /hunters/{id}/recruit endpoint.)
    if not hunter.mbti:
        hunter.mbti = "NONE"

    # 계정 내 slotIndex 중복 방지(기본 정책)
    # 같은 accountId + slotIndex에 다른 hunterId가 이미 있으면 에러
    for existing in repo.list().values():
        if existing.accountId == hunter.accountId and existing.slotIndex == hunter.slotIndex:
            if existing.hunterId != hunter.hunterId:
                raise HTTPException(status_code=409, detail="Slot already occupied for this accountId")
    return repo.upsert(hunter)


@router.post("/{hunter_id}/recruit")
def recruit_hunter(hunter_id: str):
    """Assign random MBTI on recruit (server-side) if hunter exists and MBTI is NONE/empty."""
    h = repo.get(hunter_id)
    if not h:
        raise HTTPException(status_code=404, detail="Hunter not found")
    if not getattr(h, "mbti", None) or str(h.mbti).upper() == "NONE":
        h.mbti = random_mbti()
        repo.upsert(h)
    return h


@router.post("/{hunter_id}/promote", response_model=HunterPromoteResponse)
def promote_hunter(hunter_id: str, req: HunterPromoteRequest):
    """Apply a promotion node to a hunter.

    Rules:
    - Node must exist.
    - Node parent must match the last node in hunter.promotionPath (or be None for root).
    - choiceGroup can only be taken once.
    - statBonus is applied cumulatively to hunter base stats (hp/atk/defense).
    - jobId is updated to node.jobId.
    """
    h = repo.get(hunter_id)
    if not h:
        raise HTTPException(status_code=404, detail="Hunter not found")

    node = get_promotion_node(req.nodeId)
    if not node:
        raise HTTPException(status_code=404, detail="Promotion node not found")

    path = list(getattr(h, "promotionPath", []) or [])

    # prevent duplicates
    if req.nodeId in path:
        raise HTTPException(status_code=409, detail="Promotion node already applied")

    expected_parent = path[-1] if path else None
    node_parent = node.get("parentNodeId")
    if expected_parent is None:
        # root: allow only if node has no parent
        if node_parent not in (None, "", "null"):
            raise HTTPException(status_code=400, detail="Invalid promotion order (root node must have no parent)")
    else:
        if str(node_parent) != str(expected_parent):
            raise HTTPException(status_code=400, detail="Invalid promotion order (parent mismatch)")

    # choice group uniqueness
    node_group = node.get("choiceGroup")
    if node_group:
        for prev_id in path:
            prev = get_promotion_node(prev_id)
            if prev and prev.get("choiceGroup") == node_group:
                raise HTTPException(status_code=409, detail=f"choiceGroup already chosen: {node_group}")

    # apply
    path.append(req.nodeId)
    h.promotionPath = path
    h.jobId = str(node.get("jobId") or h.jobId)

    stat_bonus = node.get("statBonus") or {}
    # Apply stat bonus to base stats (cumulative, permanent)
    if "hp" in stat_bonus:
        h.hp = float(getattr(h, "hp", 0.0)) + float(stat_bonus["hp"])
    if "atk" in stat_bonus:
        h.atk = float(getattr(h, "atk", 0.0)) + float(stat_bonus["atk"])
    if "def" in stat_bonus:
        h.defense = float(getattr(h, "defense", 0.0)) + float(stat_bonus["def"])
    if "defense" in stat_bonus:
        h.defense = float(getattr(h, "defense", 0.0)) + float(stat_bonus["defense"])

    # Refresh unlocked skills cache
    eff = compute_promotion_effect(h.promotionPath)
    h.skillsUnlocked = list(eff.get("skillsUnlocked") or [])

    repo.upsert(h)

    return HunterPromoteResponse(
        hunter=h,
        appliedStatBonus={k: float(v) for k, v in (stat_bonus or {}).items()},
        unlockedSkills=list(eff.get("skillsUnlocked") or []),
        promotionMultiplier=float(eff.get("promotionMultiplier") or 1.0),
    )


@router.post("/{hunter_id}/equip", response_model=HunterEquipResponse)
def equip_items(hunter_id: str, req: HunterEquipRequest):
    """Equip item ids for a hunter with validation.

    Validation:
    - All itemIds must exist.
    - Only one item per slot.
    - Item seasonId must match hunter.seasonId.
    - Item tierId must be <= hunter.tierId (T1 <= T2 ...).
    """
    h = repo.get(hunter_id)
    if not h:
        raise HTTPException(status_code=404, detail="Hunter not found")

    item_ids = list(req.equippedItemIds or [])
    seen_slots: dict[str, str] = {}
    hunter_season = str(getattr(h, "seasonId", "S1"))
    hunter_tier = str(getattr(h, "tierId", "T1"))
    hunter_tier_rank = tier_rank(hunter_tier)

    for item_id in item_ids:
        d = get_item_def(item_id)
        if not d:
            raise HTTPException(status_code=404, detail=f"Item not found: {item_id}")
        if str(d.get("seasonId")) != hunter_season:
            raise HTTPException(status_code=400, detail=f"Item season mismatch: {item_id}")
        if tier_rank(str(d.get("tierId"))) > hunter_tier_rank:
            raise HTTPException(status_code=400, detail=f"Item tier too high for hunter: {item_id}")

        slot = str(d.get("slot") or "")
        if not slot:
            raise HTTPException(status_code=400, detail=f"Item slot missing: {item_id}")
        if slot in seen_slots:
            raise HTTPException(status_code=409, detail=f"Slot already occupied: {slot}")
        seen_slots[slot] = item_id

    h.equippedItemIds = item_ids
    mul = compute_item_multipliers(item_ids)
    repo.upsert(h)
    return HunterEquipResponse(hunter=h, itemMultipliers={k: float(v) for k, v in mul.items()}, note="equipped")


@router.post("/{hunter_id}/tier-up", response_model=HunterTierUpResponse)
def tier_up_hunter(hunter_id: str, req: HunterTierUpRequest):
    """영웅 티어 상승 (T1 -> T2 -> ...). tier_defs에 정의된 티어만 허용."""
    h = repo.get(hunter_id)
    if not h:
        raise HTTPException(status_code=404, detail="Hunter not found")

    new_tier = str(req.tierId).strip().upper()
    if not new_tier:
        raise HTTPException(status_code=400, detail="tierId required")

    current_tier = str(getattr(h, "tierId", "T1"))
    current_rank = tier_rank(current_tier)
    new_rank = tier_rank(new_tier)

    if new_rank <= current_rank:
        return HunterTierUpResponse(hunter=h, changed=False, note="tier unchanged or lower")

    # 해당 시즌에 정의된 티어인지 확인
    from core.tier import tier_exists
    season = str(getattr(h, "seasonId", "S1"))
    if not tier_exists(season, new_tier):
        raise HTTPException(status_code=400, detail=f"Tier {new_tier} not defined for season {season}")

    h.tierId = new_tier
    repo.upsert(h)
    return HunterTierUpResponse(hunter=h, changed=True, note=f"tier upgraded to {new_tier}")


@router.delete("/{hunter_id}")
def delete_hunter(hunter_id: str):
    ok = repo.delete(hunter_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Hunter not found")
    return {"deleted": True}