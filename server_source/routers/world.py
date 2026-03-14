# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
from fastapi import APIRouter
import json, uuid

from core.schemas import TownWorldDefinitionResponse, TownWorldSnapshotResponse, TownHudRules, EconomySimulationRequest, EconomySimulationResponse, OperatorCraftRequest, OperatorSellRequest, OperatorSummaryResponse, OperatorActionResult, OperatorMissionSnapshotResponse, OperatorMissionClaimRequest, OperatorRecipeCatalogResponse
from core.world_content import TOWN_WORLD_DEFINITION, build_town_world_snapshot
from core.economy import simulate_long_term_economy
from core.operator_loop import build_operator_summary, apply_craft, apply_sell, list_operator_recipes, FAILURE_CODES
from core.operator_missions import build_operator_mission_snapshot, claim_operator_mission
from storage.repo_registry import hunter_repo
from storage.sqlite_db import insert_operator_action_log, upsert_operator_treasury, add_operator_inventory, list_operator_action_logs

router = APIRouter()


@router.get("/world/definition", response_model=TownWorldDefinitionResponse)
def get_town_world_definition():
    return TOWN_WORLD_DEFINITION


@router.get("/world/snapshot", response_model=TownWorldSnapshotResponse)
def get_town_world_snapshot(accountId: str = "guest"):
    return build_town_world_snapshot(accountId)


@router.get("/world/hud", response_model=TownHudRules)
def get_town_world_hud_rules():
    return TOWN_WORLD_DEFINITION["hudRules"]


@router.post("/world/economy/simulate", response_model=EconomySimulationResponse)
def simulate_economy(req: EconomySimulationRequest):
    hunters = list(hunter_repo.list().values())
    if req.hunterIds:
        wanted = set(req.hunterIds)
        hunters = [h for h in hunters if h.hunterId in wanted]
    else:
        hunters = [h for h in hunters if h.accountId == req.accountId]

    result = simulate_long_term_economy(
        hunters=hunters,
        hours=req.simulatedHours,
        battle_minutes_per_loop=req.battleMinutesPerLoop,
        rest_minutes_per_loop=req.restMinutesPerLoop,
        crowding_factor=req.crowdingFactor,
    )
    return EconomySimulationResponse(
        accountId=req.accountId,
        simulatedHours=req.simulatedHours,
        hunterCount=len(hunters),
        summary=result["summary"],
        perHunter=result["perHunter"],
        balanceWarnings=result["balanceWarnings"],
        designHooks=result["designHooks"],
    )


@router.get("/world/operator/summary", response_model=OperatorSummaryResponse)
def get_operator_summary(accountId: str = "guest"):
    hunters = [h for h in hunter_repo.list().values() if h.accountId == accountId]
    return OperatorSummaryResponse(**build_operator_summary(accountId, hunters))


@router.post("/world/operator/craft", response_model=OperatorActionResult)
def craft_operator_item(req: OperatorCraftRequest):
    ok, result_code, payload = apply_craft(req.accountId, req.recipeId, req.quantity)
    insert_operator_action_log(
        log_id=f"log_{uuid.uuid4().hex}",
        account_id=req.accountId,
        hunter_id=None,
        action_type="craft",
        result_code=result_code,
        detail=FAILURE_CODES.get(result_code, result_code),
        payload_json=json.dumps(payload, ensure_ascii=False),
    )
    return OperatorActionResult(ok=ok, resultCode=result_code, detail=FAILURE_CODES.get(result_code, result_code), accountId=req.accountId, payload=payload)


@router.post("/world/operator/sell", response_model=OperatorActionResult)
def sell_operator_item(req: OperatorSellRequest):
    ok, result_code, payload = apply_sell(req.accountId, req.itemId, req.quantity, req.unitPrice)
    insert_operator_action_log(
        log_id=f"log_{uuid.uuid4().hex}",
        account_id=req.accountId,
        hunter_id=None,
        action_type="sell",
        result_code=result_code,
        detail=FAILURE_CODES.get(result_code, result_code),
        payload_json=json.dumps(payload, ensure_ascii=False),
    )
    return OperatorActionResult(ok=ok, resultCode=result_code, detail=FAILURE_CODES.get(result_code, result_code), accountId=req.accountId, payload=payload)


@router.get("/world/operator/missions", response_model=OperatorMissionSnapshotResponse)
def get_operator_missions(accountId: str = "guest"):
    logs = list_operator_action_logs(accountId, limit=200)
    snapshot = build_operator_mission_snapshot(accountId, logs)
    return OperatorMissionSnapshotResponse(**snapshot)


@router.post("/world/operator/missions/claim", response_model=OperatorActionResult)
def claim_world_operator_mission(req: OperatorMissionClaimRequest):
    logs = list_operator_action_logs(req.accountId, limit=200)
    snapshot = build_operator_mission_snapshot(req.accountId, logs)
    ok, result_code, payload = claim_operator_mission(req.accountId, req.missionId, req.scope, snapshot)
    if ok:
        reward = payload.get("reward") or {}
        upsert_operator_treasury(req.accountId, gold_delta=int(reward.get("operatorGold", 0)), exp_delta=int(reward.get("operatorExp", 0)))
        for item_id, qty in (reward.get("inventory") or {}).items():
            add_operator_inventory(req.accountId, item_id, int(qty))
    insert_operator_action_log(
        log_id=f"log_{uuid.uuid4().hex}",
        account_id=req.accountId,
        hunter_id=None,
        action_type="mission_claim",
        result_code=result_code,
        detail=FAILURE_CODES.get(result_code, result_code),
        payload_json=json.dumps(payload, ensure_ascii=False),
    )
    return OperatorActionResult(ok=ok, resultCode=result_code, detail=FAILURE_CODES.get(result_code, result_code), accountId=req.accountId, payload=payload)


@router.get("/world/operator/recipes", response_model=OperatorRecipeCatalogResponse)
def get_operator_recipes():
    return OperatorRecipeCatalogResponse(recipes=list_operator_recipes(), designIntent="운영자 성장 구간마다 제작 레시피를 조금씩 열어 중간 목표를 촘촘하게 만든다.")
