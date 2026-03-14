# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
from storage.repo_registry import hunter_repo as repo
from fastapi import APIRouter, HTTPException, Query
import json, uuid
from core.schemas import Hunter, HunterPromoteRequest, HunterPromoteResponse, HunterEquipRequest, HunterEquipResponse, HunterTierUpRequest, HunterTierUpResponse, HunterOperationConfigRequest, HunterOperationPlanResponse, HunterCommandRequest, HunterCommandResponse, HunterAiConfigRequest, HunterAiProfileResponse, HunterAssignHuntZoneRequest, HunterAssignHuntZoneResponse, HunterStateMachineResponse, HunterSettleReturnRequest, HunterTrainingRequest, HunterBodyReforgeRequest, OperatorActionResult, HunterGrowthRuleResponse
from core.mbti import random_mbti
from core.promotion import get_promotion_node, compute_promotion_effect
from core.items import get_item_def, compute_item_multipliers
from core.tier import tier_rank
from core.hunter_operations import build_operation_plan
from core.hunter_ai import build_ai_profile
from core.hunter_state_machine import build_state_machine_snapshot
from core.operator_loop import settle_hunt_return, apply_training, try_body_reforge, evaluate_growth_requirements, FAILURE_CODES
from storage.sqlite_db import add_operator_inventory, upsert_operator_treasury, insert_operator_action_log, insert_hunter_state_snapshot

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
    hunter.operationStyle = (hunter.operationStyle or "steady").lower()
    hunter.restDiscipline = (hunter.restDiscipline or "measured").lower()
    hunter.trainingFocus = (hunter.trainingFocus or "body").lower()
    hunter.morale = max(0.0, min(100.0, float(getattr(hunter, "morale", 50.0))))
    hunter.fatigue = max(0.0, min(100.0, float(getattr(hunter, "fatigue", 0.0))))
    if not getattr(hunter, "bondFacilityId", ""):
        hunter.bondFacilityId = "inn_main"
    hunter.aiMode = str(getattr(hunter, "aiMode", "autonomous") or "autonomous").lower()
    hunter.preferredActivity = str(getattr(hunter, "preferredActivity", "hunt") or "hunt").lower()
    hunter.socialDrive = max(0.0, min(100.0, float(getattr(hunter, "socialDrive", 50.0))))
    hunter.disciplineDrive = max(0.0, min(100.0, float(getattr(hunter, "disciplineDrive", 50.0))))
    hunter.braveryDrive = max(0.0, min(100.0, float(getattr(hunter, "braveryDrive", 50.0))))
    hunter.assignedHuntZoneId = str(getattr(hunter, "assignedHuntZoneId", "south_field") or "south_field")[:64]
    hunter.desiredLoopCount = max(1, min(12, int(getattr(hunter, "desiredLoopCount", 2) or 2)))
    hunter.satiety = max(0.0, min(100.0, float(getattr(hunter, "satiety", 75.0))))
    hunter.stamina = max(0.0, min(100.0, float(getattr(hunter, "stamina", 75.0))))
    hunter.bagLoad = max(0.0, min(100.0, float(getattr(hunter, "bagLoad", 0.0))))
    hunter.durability = max(0.0, min(100.0, float(getattr(hunter, "durability", 100.0))))
    hunter.loyalty = max(0.0, min(100.0, float(getattr(hunter, "loyalty", 50.0))))
    hunter.bodyReforgeStage = max(0, min(9, int(getattr(hunter, "bodyReforgeStage", 0) or 0)))
    hunter.insight = max(0.0, min(100.0, float(getattr(hunter, "insight", 0.0))))
    hunter.safetyStockPreference = max(0, min(99, int(getattr(hunter, "safetyStockPreference", 3) or 3)))

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

@router.get("/{hunter_id}/operation-plan", response_model=HunterOperationPlanResponse)
def get_hunter_operation_plan(hunter_id: str):
    h = repo.get(hunter_id)
    if not h:
        raise HTTPException(status_code=404, detail="Hunter not found")
    return HunterOperationPlanResponse(hunterId=hunter_id, **build_operation_plan(h))


@router.post("/{hunter_id}/configure-operations", response_model=HunterOperationPlanResponse)
def configure_hunter_operations(hunter_id: str, req: HunterOperationConfigRequest):
    h = repo.get(hunter_id)
    if not h:
        raise HTTPException(status_code=404, detail="Hunter not found")

    if req.operationStyle is not None:
        h.operationStyle = req.operationStyle
    if req.restDiscipline is not None:
        h.restDiscipline = req.restDiscipline
    if req.trainingFocus is not None:
        h.trainingFocus = req.trainingFocus
    if req.morale is not None:
        h.morale = req.morale
    if req.fatigue is not None:
        h.fatigue = req.fatigue
    if req.bondFacilityId is not None:
        h.bondFacilityId = req.bondFacilityId
    repo.upsert(h)
    return HunterOperationPlanResponse(hunterId=hunter_id, **build_operation_plan(h))




@router.get("/{hunter_id}/ai-profile", response_model=HunterAiProfileResponse)
def get_hunter_ai_profile(hunter_id: str):
    h = repo.get(hunter_id)
    if not h:
        raise HTTPException(status_code=404, detail="Hunter not found")
    return HunterAiProfileResponse(**build_ai_profile(h))


@router.post("/{hunter_id}/configure-ai", response_model=HunterAiProfileResponse)
def configure_hunter_ai(hunter_id: str, req: HunterAiConfigRequest):
    h = repo.get(hunter_id)
    if not h:
        raise HTTPException(status_code=404, detail="Hunter not found")

    if req.aiMode is not None:
        h.aiMode = req.aiMode
    if req.preferredActivity is not None:
        h.preferredActivity = req.preferredActivity
    if req.socialDrive is not None:
        h.socialDrive = req.socialDrive
    if req.disciplineDrive is not None:
        h.disciplineDrive = req.disciplineDrive
    if req.braveryDrive is not None:
        h.braveryDrive = req.braveryDrive
    repo.upsert(h)
    return HunterAiProfileResponse(**build_ai_profile(h))


@router.post("/{hunter_id}/assign-hunt-zone", response_model=HunterAssignHuntZoneResponse)
def assign_hunt_zone(hunter_id: str, req: HunterAssignHuntZoneRequest):
    h = repo.get(hunter_id)
    if not h:
        raise HTTPException(status_code=404, detail="Hunter not found")
    h.assignedHuntZoneId = str(req.huntZoneId or "south_field")[:64]
    h.desiredLoopCount = max(1, min(12, int(req.desiredLoopCount or 2)))
    h.manualControl = False
    if str(getattr(h, "activeCommand", "hold") or "hold").lower() == "hunt":
        h.activeCommand = "hold"
    repo.upsert(h)
    return HunterAssignHuntZoneResponse(
        hunterId=hunter_id,
        huntZoneId=h.assignedHuntZoneId,
        desiredLoopCount=h.desiredLoopCount,
        note="사냥터 지정이 반영되었습니다. 이후 전투/스킬/루팅/귀환은 헌터 AI가 처리합니다.",
    )


@router.get("/{hunter_id}/state-machine", response_model=HunterStateMachineResponse)
def get_hunter_state_machine(hunter_id: str):
    h = repo.get(hunter_id)
    if not h:
        raise HTTPException(status_code=404, detail="Hunter not found")
    snapshot = build_state_machine_snapshot(h)
    insert_hunter_state_snapshot(
        snapshot_id=f"sm_{uuid.uuid4().hex}",
        hunter_id=h.hunterId,
        account_id=h.accountId,
        state_code=snapshot["currentState"],
        next_state_code=snapshot["nextState"],
        payload_json=json.dumps(snapshot, ensure_ascii=False),
    )
    return HunterStateMachineResponse(**snapshot)

@router.get("/{hunter_id}/growth-rules", response_model=HunterGrowthRuleResponse)
def get_hunter_growth_rules(hunter_id: str):
    h = repo.get(hunter_id)
    if not h:
        raise HTTPException(status_code=404, detail=FAILURE_CODES["ERR_NOT_FOUND"])
    return HunterGrowthRuleResponse(**evaluate_growth_requirements(h))


@router.post("/{hunter_id}/command", response_model=HunterCommandResponse)
def command_hunter(hunter_id: str, req: HunterCommandRequest):
    h = repo.get(hunter_id)
    if not h:
        raise HTTPException(status_code=404, detail="Hunter not found")

    h.activeCommand = req.command
    h.desiredMonsterCount = req.desiredMonsterCount
    h.manualControl = req.command != "hold"
    if req.command == "hunt":
        h.huntStreak = int(getattr(h, "huntStreak", 0)) + 1
    repo.upsert(h)
    notes = {
        "hunt": "예외 사냥 명령이 들어갔습니다. 현재 루틴을 잠시 끊고 목표 수만큼 사냥한 뒤 다시 자율 AI 운영 루프로 복귀하세요.",
        "train": "훈련 명령이 들어갔습니다. 무공 수련 애니메이션/훈련장 이동과 연결하세요.",
        "rest": "객잔 휴식 명령이 들어갔습니다.",
        "eat": "식사 명령이 들어갔습니다.",
        "heal": "치료 명령이 들어갔습니다.",
        "patrol": "마을 순찰 명령이 들어갔습니다.",
        "return": "즉시 귀환 명령이 들어갔습니다.",
        "hold": "현재 행동을 멈추고 대기합니다. 이후 필요/성향 기반 AI 루틴으로 자연 복귀할 수 있습니다.",
    }
    return HunterCommandResponse(hunterId=hunter_id, command=req.command, desiredMonsterCount=req.desiredMonsterCount, note=notes.get(req.command, "명령 반영됨"))


@router.post("/{hunter_id}/settle-return", response_model=OperatorActionResult)
def settle_hunter_return(hunter_id: str, req: HunterSettleReturnRequest):
    h = repo.get(hunter_id)
    if not h:
        raise HTTPException(status_code=404, detail=FAILURE_CODES["ERR_NOT_FOUND"])
    h, payload = settle_hunt_return(
        h,
        found_gold=req.foundGold,
        found_materials=req.foundMaterials,
        tax_rate=req.taxRate,
        loops_completed=req.loopsCompleted,
        fatigue_delta=req.fatigueDelta,
        satiety_delta=req.satietyDelta,
        durability_delta=req.durabilityDelta,
    )
    repo.upsert(h)
    upsert_operator_treasury(h.accountId, gold_delta=int(payload["operatorShareGold"]), exp_delta=max(4, int(req.loopsCompleted) * 2))
    for item_id, quantity in (payload.get("materialsAdded") or {}).items():
        add_operator_inventory(h.accountId, item_id, int(quantity))
    insert_operator_action_log(
        log_id=f"log_{uuid.uuid4().hex}",
        account_id=h.accountId,
        hunter_id=h.hunterId,
        action_type="settle_return",
        result_code="OK_SETTLED",
        detail=FAILURE_CODES["OK_SETTLED"],
        payload_json=json.dumps(payload, ensure_ascii=False),
    )
    return OperatorActionResult(
        ok=True,
        resultCode="OK_SETTLED",
        detail=FAILURE_CODES["OK_SETTLED"],
        hunterId=h.hunterId,
        accountId=h.accountId,
        payload=payload,
    )


@router.post("/{hunter_id}/train", response_model=OperatorActionResult)
def train_hunter(hunter_id: str, req: HunterTrainingRequest):
    h = repo.get(hunter_id)
    if not h:
        raise HTTPException(status_code=404, detail=FAILURE_CODES["ERR_NOT_FOUND"])
    ok, result_code, payload = apply_training(h, req.packageId, req.intensity)
    if not ok:
        h.lastFailureCode = result_code
        h.lastFailureDetail = FAILURE_CODES.get(result_code, result_code)
        repo.upsert(h)
        insert_operator_action_log(
            log_id=f"log_{uuid.uuid4().hex}",
            account_id=h.accountId,
            hunter_id=h.hunterId,
            action_type="train",
            result_code=result_code,
            detail=FAILURE_CODES.get(result_code, result_code),
            payload_json=json.dumps(payload, ensure_ascii=False),
        )
        return OperatorActionResult(ok=False, resultCode=result_code, detail=FAILURE_CODES.get(result_code, result_code), hunterId=h.hunterId, accountId=h.accountId, payload=payload)
    repo.upsert(h)
    upsert_operator_treasury(h.accountId, exp_delta=12)
    insert_operator_action_log(
        log_id=f"log_{uuid.uuid4().hex}",
        account_id=h.accountId,
        hunter_id=h.hunterId,
        action_type="train",
        result_code=result_code,
        detail=FAILURE_CODES.get(result_code, result_code),
        payload_json=json.dumps(payload, ensure_ascii=False),
    )
    return OperatorActionResult(ok=True, resultCode=result_code, detail=FAILURE_CODES[result_code], hunterId=h.hunterId, accountId=h.accountId, payload=payload)


@router.post("/{hunter_id}/body-reforge", response_model=OperatorActionResult)
def body_reforge_hunter(hunter_id: str, req: HunterBodyReforgeRequest):
    h = repo.get(hunter_id)
    if not h:
        raise HTTPException(status_code=404, detail=FAILURE_CODES["ERR_NOT_FOUND"])
    ok, result_code, payload = try_body_reforge(h, req.consumeGold, req.consumeMaterials)
    if not ok:
        h.lastFailureCode = result_code
        h.lastFailureDetail = FAILURE_CODES.get(result_code, result_code)
        repo.upsert(h)
        insert_operator_action_log(
            log_id=f"log_{uuid.uuid4().hex}",
            account_id=h.accountId,
            hunter_id=h.hunterId,
            action_type="body_reforge",
            result_code=result_code,
            detail=FAILURE_CODES.get(result_code, result_code),
            payload_json=json.dumps(payload, ensure_ascii=False),
        )
        return OperatorActionResult(ok=False, resultCode=result_code, detail=FAILURE_CODES.get(result_code, result_code), hunterId=h.hunterId, accountId=h.accountId, payload=payload)
    repo.upsert(h)
    upsert_operator_treasury(h.accountId, exp_delta=26)
    insert_operator_action_log(
        log_id=f"log_{uuid.uuid4().hex}",
        account_id=h.accountId,
        hunter_id=h.hunterId,
        action_type="body_reforge",
        result_code=result_code,
        detail=FAILURE_CODES.get(result_code, result_code),
        payload_json=json.dumps(payload, ensure_ascii=False),
    )
    return OperatorActionResult(ok=True, resultCode=result_code, detail=FAILURE_CODES[result_code], hunterId=h.hunterId, accountId=h.accountId, payload=payload)
