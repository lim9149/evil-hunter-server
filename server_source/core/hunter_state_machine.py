from __future__ import annotations

from typing import Any, Dict, List


def _clamp(v: float, lo: float, hi: float) -> float:
    try:
        return max(lo, min(hi, float(v)))
    except Exception:
        return lo


def _tier_rank(tier_id: str) -> int:
    tier_id = str(tier_id or "T1").upper().strip()
    if tier_id.startswith("T"):
        try:
            return int(tier_id[1:])
        except Exception:
            return 1
    return 1


def build_state_machine_snapshot(hunter: Any) -> Dict[str, Any]:
    hunter_id = str(getattr(hunter, "hunterId", "unknown"))
    assigned_hunt_zone = str(getattr(hunter, "assignedHuntZoneId", "south_field") or "south_field")
    preferred = str(getattr(hunter, "preferredActivity", "hunt") or "hunt").lower()
    active_command = str(getattr(hunter, "activeCommand", "hold") or "hold").lower()
    manual_control = bool(getattr(hunter, "manualControl", False))
    tier_id = str(getattr(hunter, "tierId", "T1") or "T1")
    level = int(getattr(hunter, "level", 1) or 1)
    hunt_streak = int(getattr(hunter, "huntStreak", 0) or 0)

    hp_ratio = _clamp(getattr(hunter, "hp", 100.0), 0.0, 100.0)
    satiety = _clamp(getattr(hunter, "satiety", 75.0), 0.0, 100.0)
    stamina = _clamp(getattr(hunter, "stamina", 75.0), 0.0, 100.0)
    fatigue = _clamp(getattr(hunter, "fatigue", 0.0), 0.0, 100.0)
    morale = _clamp(getattr(hunter, "morale", 50.0), 0.0, 100.0)
    loyalty = _clamp(getattr(hunter, "loyalty", 50.0), 0.0, 100.0)
    bag_load = _clamp(getattr(hunter, "bagLoad", 0.0), 0.0, 100.0)
    durability = _clamp(getattr(hunter, "durability", 100.0), 0.0, 100.0)
    body_reforge_stage = int(getattr(hunter, "bodyReforgeStage", 0) or 0)
    promotion_ready = bool(getattr(hunter, "promotionReady", False))

    risk_flags: List[str] = []
    operator_todos: List[str] = []
    transition_rules = [
        "NeedCheck -> IntentSelect -> MoveToTarget -> PerformAction -> Settlement -> ResumeAutonomy",
        "수동 개입은 예외 레이어이며 종료 후 자율 루프로 복귀",
        "사냥터 지정은 운영자가, 전투/스킬/루팅/복귀는 헌터 AI가 담당",
    ]

    current_state = "NeedCheck"
    next_state = "IntentSelect"
    target_location = assigned_hunt_zone
    target_reason = "운영자가 지정한 사냥터 우선"
    suggested_action_window = "지금은 자동 루프 관찰 구간"
    recovery_priority = "normal"

    if manual_control and active_command not in {"", "hold"}:
        current_state = "OperatorOverride"
        next_state = "ResumeAutonomy"
        target_reason = f"예외 개입 명령({active_command}) 수행 후 자율 루프 복귀"
        suggested_action_window = "명령 수행 직후 정산/회복 체크"
    elif hp_ratio <= 30 or stamina <= 20:
        current_state = "NeedCheck"
        next_state = "EmergencyReturn"
        target_location = "clinic_or_inn"
        target_reason = "생존 수치 저하로 즉시 귀환"
        recovery_priority = "critical"
        risk_flags.append("critical_recovery")
        operator_todos.append("회복 시설 보강 또는 회복약 재고 확인")
    elif fatigue >= 80 or satiety <= 25:
        current_state = "NeedCheck"
        next_state = "Recover"
        target_location = "inn_or_tavern"
        target_reason = "피로/허기 누적으로 회복 필요"
        recovery_priority = "high"
        risk_flags.append("fatigue_pressure")
        operator_todos.append("식사/휴식 투자 또는 파견 간격 조정")
    elif durability <= 20:
        current_state = "NeedCheck"
        next_state = "WaitOperator"
        target_location = "forge"
        target_reason = "장비 내구도 부족으로 운영자 보급 대기"
        operator_todos.append("무기/방어구 수리 또는 교체")
        risk_flags.append("gear_break_risk")
    elif bag_load >= 85:
        current_state = "NeedCheck"
        next_state = "Settlement"
        target_location = "warehouse_or_shop"
        target_reason = "가방이 가득 차 정산 필요"
        operator_todos.append("전리품 판매/분해/창고 정리")
    elif promotion_ready or (level >= 12 and _tier_rank(tier_id) <= 1 and hunt_streak >= 4):
        current_state = "NeedCheck"
        next_state = "WaitOperator"
        target_location = "promotion_hall"
        target_reason = "전직 가능성 확인 및 운영자 승인 대기"
        operator_todos.append("전직 조건 확인 및 승인")
    elif level >= 25 and _tier_rank(tier_id) >= 2 and body_reforge_stage < 1 and hunt_streak >= 8:
        current_state = "NeedCheck"
        next_state = "WaitOperator"
        target_location = "reforge_chamber"
        target_reason = "환골탈태 준비 단계 진입"
        operator_todos.append("환골탈태 재료/비용 확인")
    elif preferred == "train" and morale >= 50 and fatigue <= 45:
        current_state = "IntentSelect"
        next_state = "MoveToTarget"
        target_location = "training_hall"
        target_reason = "훈련 선호와 낮은 피로도 반영"
        suggested_action_window = "다음 사냥 전 교육/훈련 투자 검토"
    else:
        current_state = "IntentSelect"
        next_state = "MoveToTarget"
        target_location = assigned_hunt_zone
        target_reason = "기본 사냥 루프 진입"

    if morale <= 35:
        risk_flags.append("low_morale")
        operator_todos.append("휴식/교육/수수료 완화로 사기 회복")
    if loyalty <= 40:
        risk_flags.append("low_loyalty")
        operator_todos.append("문파 수수료/지원 정책 점검")
    if not operator_todos:
        operator_todos.append("현재는 자동 루프 유지, 정산 후 다음 성장 투자 검토")

    patron_synergy = (
        "후원 단계가 오를수록 회복/교육/희귀재료 등 작은 중간 보상을 자주 체감하게 설계"
    )

    return {
        "hunterId": hunter_id,
        "assignedHuntZoneId": assigned_hunt_zone,
        "currentState": current_state,
        "nextState": next_state,
        "targetLocation": target_location,
        "targetReason": target_reason,
        "recoveryPriority": recovery_priority,
        "suggestedActionWindow": suggested_action_window,
        "operatorTodos": operator_todos,
        "riskFlags": risk_flags,
        "transitionRules": transition_rules,
        "patronSynergy": patron_synergy,
    }
