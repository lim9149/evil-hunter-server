
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from core.operator_progression import compute_patron_stage
from storage.sqlite_db import (
    count_lifetime_ad_claims,
    get_operator_inventory,
    list_operator_action_logs,
    set_operator_inventory,
    upsert_operator_treasury,
)

FAILURE_CODES = {
    "OK_SETTLED": "사냥 귀환 정산 완료",
    "OK_CRAFTED": "제작 완료",
    "OK_SOLD": "판매 완료",
    "OK_TRAINED": "교육 완료",
    "OK_REFORGED": "환골탈태 성공",
    "ERR_NOT_FOUND": "대상을 찾을 수 없음",
    "ERR_INVALID_INPUT": "입력값이 올바르지 않음",
    "ERR_NOT_ENOUGH_GOLD": "골드 부족",
    "ERR_NOT_ENOUGH_MATERIAL": "재료 부족",
    "ERR_BAG_OVERFLOW": "가방이 가득 참",
    "ERR_LOW_LOYALTY": "충성도 부족",
    "ERR_LOW_LEVEL": "레벨 부족",
    "ERR_REFORGE_LIMIT": "환골탈태 최대 단계 도달",
    "ERR_TRAINING_LOCKED": "교육 조건 미충족",
    "ERR_UNSAFE_STATE": "위험 상태로 작업 불가",
    "ERR_ALREADY_CLAIMED": "이미 수령함",
    "ERR_MISSION_NOT_COMPLETE": "미션 미완료",
    "ERR_NOT_ENOUGH_SECT_TOKEN": "증표 부족",
    "ERR_DISCIPLINE_TOO_LOW": "문파 규율 부족",
    "OK_MISSION_CLAIMED": "미션 보상 수령 완료",
}


TRAINING_RULES: Dict[str, Dict[str, float]] = {
    "body": {"gold": 120, "fatigue": 8.0, "loyalty": 2.0, "insight": 4.0, "power": 5.0},
    "weapon": {"gold": 150, "fatigue": 7.0, "loyalty": 1.5, "insight": 5.0, "power": 6.0},
    "mind": {"gold": 110, "fatigue": 4.0, "loyalty": 2.5, "insight": 7.0, "power": 2.0},
    "footwork": {"gold": 135, "fatigue": 6.0, "loyalty": 1.5, "insight": 4.5, "power": 4.0},
}

INTENSITY_TABLE: Dict[str, Dict[str, float]] = {
    "light": {"costMul": 0.8, "gainMul": 0.8},
    "standard": {"costMul": 1.0, "gainMul": 1.0},
    "focused": {"costMul": 1.35, "gainMul": 1.28},
}

CRAFT_RULES: Dict[str, Dict[str, Any]] = {
    "potion_basic": {"costGold": 24, "materials": {"herb": 2}, "output": {"potion_basic": 1}, "unlockRank": 0},
    "weapon_iron": {"costGold": 90, "materials": {"iron_ore": 4, "wood": 1}, "output": {"weapon_iron": 1}, "unlockRank": 1},
    "armor_leather": {"costGold": 78, "materials": {"leather": 4, "fiber": 2}, "output": {"armor_leather": 1}, "unlockRank": 1},
    "charm_lucky": {"costGold": 65, "materials": {"cloth": 2, "bead": 1}, "output": {"charm_lucky": 1}, "unlockRank": 2},
    "pill_focus": {"costGold": 88, "materials": {"herb": 3, "bead": 1}, "output": {"pill_focus": 1}, "unlockRank": 2},
    "weapon_refined": {"costGold": 180, "materials": {"iron_ore": 6, "wood": 2, "sect_token": 1}, "output": {"weapon_refined": 1}, "unlockRank": 4},
    "armor_guardian": {"costGold": 170, "materials": {"leather": 6, "fiber": 4, "discipline_seal": 1}, "output": {"armor_guardian": 1}, "unlockRank": 4},
    "charm_dragon": {"costGold": 210, "materials": {"cloth": 4, "bead": 3, "discipline_seal": 1}, "output": {"charm_dragon": 1}, "unlockRank": 5},
}

SELL_PRICE_HINT = {
    "potion_basic": 40,
    "weapon_iron": 150,
    "armor_leather": 130,
    "charm_lucky": 110,
    "pill_focus": 145,
    "weapon_refined": 290,
    "armor_guardian": 275,
    "charm_dragon": 330,
}

REFORGE_STAGE_RULES: List[Dict[str, Any]] = [
    {"stage": 1, "minLevel": 15, "minLoyalty": 45, "insight": 20, "sectToken": 0, "discipline": 0},
    {"stage": 2, "minLevel": 25, "minLoyalty": 52, "insight": 28, "sectToken": 1, "discipline": 28},
    {"stage": 3, "minLevel": 35, "minLoyalty": 58, "insight": 36, "sectToken": 1, "discipline": 36},
    {"stage": 4, "minLevel": 45, "minLoyalty": 64, "insight": 44, "sectToken": 2, "discipline": 44},
    {"stage": 5, "minLevel": 55, "minLoyalty": 70, "insight": 52, "sectToken": 2, "discipline": 52},
    {"stage": 6, "minLevel": 65, "minLoyalty": 76, "insight": 60, "sectToken": 3, "discipline": 60},
    {"stage": 7, "minLevel": 75, "minLoyalty": 82, "insight": 68, "sectToken": 3, "discipline": 68},
    {"stage": 8, "minLevel": 85, "minLoyalty": 88, "insight": 76, "sectToken": 4, "discipline": 76},
    {"stage": 9, "minLevel": 95, "minLoyalty": 92, "insight": 84, "sectToken": 5, "discipline": 84},
]

OPERATOR_RANKS: List[Dict[str, Any]] = [
    {"level": 0, "title": "나그네 운영자", "requires": 0},
    {"level": 1, "title": "객잔 관리인", "requires": 1_000},
    {"level": 2, "title": "초보 장주", "requires": 3_000},
    {"level": 3, "title": "소문난 장주", "requires": 7_000},
    {"level": 4, "title": "문파 살림꾼", "requires": 12_000},
    {"level": 5, "title": "중견 총관", "requires": 20_000},
    {"level": 6, "title": "상단 제휴관", "requires": 32_000},
    {"level": 7, "title": "객잔 주인장", "requires": 48_000},
    {"level": 8, "title": "문파 안살림 대행수", "requires": 68_000},
    {"level": 9, "title": "명문 장문대리", "requires": 92_000},
    {"level": 10, "title": "강호 재정통", "requires": 122_000},
    {"level": 11, "title": "무림 경영명가", "requires": 160_000},
    {"level": 12, "title": "전설의 장문운영자", "requires": 210_000},
]


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def _operator_rank(exp_value: int) -> Dict[str, Any]:
    current = OPERATOR_RANKS[0]
    next_stage = None
    for stage in OPERATOR_RANKS:
        if exp_value >= int(stage["requires"]):
            current = stage
        elif next_stage is None:
            next_stage = stage
            break
    current_req = int(current["requires"])
    next_req = int(next_stage["requires"]) if next_stage else current_req
    progress = 1.0 if next_stage is None else max(0.0, min(1.0, (exp_value - current_req) / max(1, next_req - current_req)))
    return {
        "level": int(current["level"]),
        "title": str(current["title"]),
        "exp": int(exp_value),
        "currentThreshold": current_req,
        "nextLevel": int(next_stage["level"]) if next_stage else None,
        "nextRequires": int(next_req) if next_stage else None,
        "progressRatio": round(progress, 4),
    }


def build_operator_summary(account_id: str, hunters: List[Any]) -> Dict[str, Any]:
    treasury = upsert_operator_treasury(account_id)
    inventory = get_operator_inventory(account_id)
    patron = compute_patron_stage(count_lifetime_ad_claims(account_id))
    recent_logs = list_operator_action_logs(account_id, limit=12)
    operator_rank = _operator_rank(int(treasury.get("operatorExp", 0)))
    pending: List[str] = []
    for h in hunters:
        if float(getattr(h, "fatigue", 0.0) or 0.0) >= 75:
            pending.append(f"{getattr(h, 'hunterId', 'hunter')} 휴식 또는 회복 필요")
        if float(getattr(h, "durability", 100.0) or 100.0) <= 25:
            pending.append(f"{getattr(h, 'hunterId', 'hunter')} 장비 내구도 낮음")
        if float(getattr(h, "loyalty", 50.0) or 50.0) <= 35:
            pending.append(f"{getattr(h, 'hunterId', 'hunter')} 충성도 관리 필요")
        if bool(getattr(h, "promotionReady", False)):
            pending.append(f"{getattr(h, 'hunterId', 'hunter')} 전직 가능 상태")
    return {
        "accountId": account_id,
        "hunterCount": len(hunters),
        "operatorRank": operator_rank,
        "patronStatus": patron,
        "treasury": treasury,
        "inventories": inventory,
        "pendingTodos": pending[:12],
        "recentLogs": recent_logs,
        "designHooks": [
            "귀환 정산 -> 제작/판매 -> 교육 -> 환골탈태 준비로 이어지는 운영 루프를 서버 기준으로 유지한다.",
            "실패 사유 코드는 UI가 아니라 서버에서 먼저 표준화해 다음 채팅에서도 그대로 재사용한다.",
            "운영 숙련도와 후원 단계는 분리된 성장축으로 유지한다.",
        ],
    }


def settle_hunt_return(hunter: Any, found_gold: int, found_materials: Dict[str, int], tax_rate: float, loops_completed: int, fatigue_delta: float, satiety_delta: float, durability_delta: float) -> Tuple[Any, Dict[str, Any]]:
    tax_rate = _clamp(tax_rate, 0.0, 0.5)
    gross_gold = max(0, int(found_gold))
    operator_cut = int(round(gross_gold * tax_rate))
    hunter_cut = max(0, gross_gold - operator_cut)
    hunter.gold = int(getattr(hunter, "gold", 0) or 0) + hunter_cut
    hunter.bagLoad = _clamp((getattr(hunter, "bagLoad", 0.0) or 0.0) + min(55.0, loops_completed * 7.0), 0.0, 100.0)
    hunter.fatigue = _clamp((getattr(hunter, "fatigue", 0.0) or 0.0) + fatigue_delta, 0.0, 100.0)
    hunter.satiety = _clamp((getattr(hunter, "satiety", 75.0) or 75.0) + satiety_delta, 0.0, 100.0)
    hunter.stamina = _clamp((getattr(hunter, "stamina", 75.0) or 75.0) - max(4.0, fatigue_delta / 1.4), 0.0, 100.0)
    hunter.durability = _clamp((getattr(hunter, "durability", 100.0) or 100.0) + durability_delta, 0.0, 100.0)
    hunter.huntStreak = int(getattr(hunter, "huntStreak", 0) or 0) + max(1, loops_completed)
    hunter.manualControl = False
    hunter.activeCommand = "hold"
    hunter.lastFailureCode = ""
    hunter.lastFailureDetail = ""
    return hunter, {
        "grossGold": gross_gold,
        "hunterShareGold": hunter_cut,
        "operatorShareGold": operator_cut,
        "materialsAdded": {k: max(0, int(v)) for k, v in (found_materials or {}).items()},
        "loopsCompleted": int(loops_completed),
        "updatedHunter": {
            "gold": int(hunter.gold),
            "fatigue": float(hunter.fatigue),
            "satiety": float(hunter.satiety),
            "stamina": float(hunter.stamina),
            "durability": float(hunter.durability),
            "bagLoad": float(hunter.bagLoad),
        },
    }


def apply_training(hunter: Any, package_id: str, intensity: str) -> Tuple[bool, str, Dict[str, Any]]:
    package_id = str(package_id or "").lower()
    intensity = str(intensity or "standard").lower()
    if package_id not in TRAINING_RULES or intensity not in INTENSITY_TABLE:
        return False, "ERR_INVALID_INPUT", {"packageId": package_id, "intensity": intensity}
    if float(getattr(hunter, "stamina", 0.0) or 0.0) < 15 or float(getattr(hunter, "satiety", 0.0) or 0.0) < 20:
        return False, "ERR_UNSAFE_STATE", {"stamina": getattr(hunter, "stamina", 0.0), "satiety": getattr(hunter, "satiety", 0.0)}
    rule = TRAINING_RULES[package_id]
    mul = INTENSITY_TABLE[intensity]
    cost_gold = int(round(rule["gold"] * mul["costMul"]))
    fatigue_gain = float(rule["fatigue"]) * mul["costMul"]
    hunter_gold = int(getattr(hunter, "gold", 0) or 0)
    if hunter_gold < cost_gold:
        return False, "ERR_NOT_ENOUGH_GOLD", {"requiredGold": cost_gold, "gold": hunter_gold}
    hunter.gold = hunter_gold - cost_gold
    hunter.fatigue = _clamp((getattr(hunter, "fatigue", 0.0) or 0.0) + fatigue_gain, 0.0, 100.0)
    hunter.stamina = _clamp((getattr(hunter, "stamina", 75.0) or 75.0) - fatigue_gain * 1.8, 0.0, 100.0)
    hunter.loyalty = _clamp((getattr(hunter, "loyalty", 50.0) or 50.0) + rule["loyalty"] * mul["gainMul"], 0.0, 100.0)
    hunter.insight = _clamp((getattr(hunter, "insight", 0.0) or 0.0) + rule["insight"] * mul["gainMul"], 0.0, 100.0)
    hunter.powerScore = max(0.0, float(getattr(hunter, "powerScore", 0.0) or 0.0) + rule["power"] * mul["gainMul"])
    hunter.lastFailureCode = ""
    hunter.lastFailureDetail = ""
    return True, "OK_TRAINED", {
        "packageId": package_id,
        "intensity": intensity,
        "costGold": cost_gold,
        "insight": round(float(hunter.insight), 2),
        "powerScore": round(float(hunter.powerScore), 2),
        "fatigue": round(float(hunter.fatigue), 2),
    }


def try_body_reforge(hunter: Any, consume_gold: int, consume_materials: Dict[str, int]) -> Tuple[bool, str, Dict[str, Any]]:
    current_stage = int(getattr(hunter, "bodyReforgeStage", 0) or 0)
    if current_stage >= 9:
        return False, "ERR_REFORGE_LIMIT", {"currentStage": current_stage}
    rule = REFORGE_STAGE_RULES[current_stage]
    if int(getattr(hunter, "level", 1) or 1) < int(rule["minLevel"]):
        return False, "ERR_LOW_LEVEL", {"requiredLevel": int(rule["minLevel"]), "level": int(getattr(hunter, "level", 1) or 1)}
    if float(getattr(hunter, "loyalty", 50.0) or 50.0) < float(rule["minLoyalty"]):
        return False, "ERR_LOW_LOYALTY", {"requiredLoyalty": float(rule["minLoyalty"]), "loyalty": float(getattr(hunter, "loyalty", 0.0) or 0.0)}
    if float(getattr(hunter, "insight", 0.0) or 0.0) < float(rule["insight"]):
        return False, "ERR_TRAINING_LOCKED", {"requiredInsight": float(rule["insight"]), "insight": float(getattr(hunter, "insight", 0.0) or 0.0)}
    if int(getattr(hunter, "sectTokenCount", 0) or 0) < int(rule.get("sectToken", 0)):
        return False, "ERR_NOT_ENOUGH_SECT_TOKEN", {"requiredSectToken": int(rule.get("sectToken", 0)), "sectTokenCount": int(getattr(hunter, "sectTokenCount", 0) or 0)}
    if float(getattr(hunter, "sectDiscipline", 0.0) or 0.0) < float(rule.get("discipline", 0.0)):
        return False, "ERR_DISCIPLINE_TOO_LOW", {"requiredDiscipline": float(rule.get("discipline", 0.0)), "sectDiscipline": float(getattr(hunter, "sectDiscipline", 0.0) or 0.0)}
    hunter_gold = int(getattr(hunter, "gold", 0) or 0)
    if hunter_gold < int(consume_gold):
        return False, "ERR_NOT_ENOUGH_GOLD", {"requiredGold": int(consume_gold), "gold": hunter_gold}
    hunter.gold = hunter_gold - int(consume_gold)
    hunter.sectTokenCount = max(0, int(getattr(hunter, "sectTokenCount", 0) or 0) - int(rule.get("sectToken", 0)))
    hunter.bodyReforgeStage = current_stage + 1
    hunter.powerScore = max(0.0, float(getattr(hunter, "powerScore", 0.0) or 0.0) + 18.0 + current_stage * 4.0)
    hunter.loyalty = _clamp((getattr(hunter, "loyalty", 50.0) or 50.0) + 3.0, 0.0, 100.0)
    hunter.insight = _clamp((getattr(hunter, "insight", 0.0) or 0.0) + 2.0, 0.0, 100.0)
    hunter.lastFailureCode = ""
    hunter.lastFailureDetail = ""
    return True, "OK_REFORGED", {
        "newStage": int(hunter.bodyReforgeStage),
        "goldSpent": int(consume_gold),
        "materialsSpent": {k: max(0, int(v)) for k, v in (consume_materials or {}).items()},
        "powerScore": round(float(hunter.powerScore), 2),
        "sectTokenRemaining": int(getattr(hunter, "sectTokenCount", 0) or 0),
    }


def apply_craft(account_id: str, recipe_id: str, quantity: int) -> Tuple[bool, str, Dict[str, Any]]:
    recipe_id = str(recipe_id or "")
    quantity = max(1, int(quantity))
    if recipe_id not in CRAFT_RULES:
        return False, "ERR_INVALID_INPUT", {"recipeId": recipe_id}
    treasury = upsert_operator_treasury(account_id)
    inventory = get_operator_inventory(account_id)
    recipe = CRAFT_RULES[recipe_id]
    total_gold = int(recipe["costGold"]) * quantity
    if int(treasury.get("operatorGold", 0)) < total_gold:
        return False, "ERR_NOT_ENOUGH_GOLD", {"requiredGold": total_gold, "operatorGold": int(treasury.get("operatorGold", 0))}
    for material_id, count in recipe["materials"].items():
        need = int(count) * quantity
        if int(inventory.get(material_id, 0)) < need:
            return False, "ERR_NOT_ENOUGH_MATERIAL", {"materialId": material_id, "required": need, "owned": int(inventory.get(material_id, 0))}
    for material_id, count in recipe["materials"].items():
        set_operator_inventory(account_id, material_id, int(inventory.get(material_id, 0)) - int(count) * quantity)
    for item_id, count in recipe["output"].items():
        set_operator_inventory(account_id, item_id, int(inventory.get(item_id, 0)) + int(count) * quantity)
    treasury = upsert_operator_treasury(account_id, gold_delta=-total_gold, exp_delta=max(8, quantity * 5))
    return True, "OK_CRAFTED", {
        "recipeId": recipe_id,
        "quantity": quantity,
        "spentGold": total_gold,
        "treasury": treasury,
        "inventory": get_operator_inventory(account_id),
    }


def apply_sell(account_id: str, item_id: str, quantity: int, unit_price: int) -> Tuple[bool, str, Dict[str, Any]]:
    item_id = str(item_id or "")
    quantity = max(1, int(quantity))
    unit_price = max(1, int(unit_price))
    inventory = get_operator_inventory(account_id)
    owned = int(inventory.get(item_id, 0))
    if owned < quantity:
        return False, "ERR_NOT_ENOUGH_MATERIAL", {"itemId": item_id, "required": quantity, "owned": owned}
    set_operator_inventory(account_id, item_id, owned - quantity)
    total_revenue = quantity * unit_price
    treasury = upsert_operator_treasury(account_id, gold_delta=total_revenue, exp_delta=max(6, quantity * 4))
    return True, "OK_SOLD", {
        "itemId": item_id,
        "quantity": quantity,
        "unitPrice": unit_price,
        "suggestedUnitPrice": SELL_PRICE_HINT.get(item_id),
        "totalRevenue": total_revenue,
        "treasury": treasury,
        "inventory": get_operator_inventory(account_id),
    }


def list_operator_recipes() -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for recipe_id, recipe in CRAFT_RULES.items():
        out.append({
            "recipeId": recipe_id,
            "costGold": int(recipe["costGold"]),
            "materials": dict(recipe["materials"]),
            "output": dict(recipe["output"]),
            "unlockRank": int(recipe.get("unlockRank", 0)),
            "hintPrice": int(SELL_PRICE_HINT.get(recipe_id, 0)),
        })
    return sorted(out, key=lambda x: (x["unlockRank"], x["recipeId"]))


def evaluate_growth_requirements(hunter: Any) -> Dict[str, Any]:
    current_stage = int(getattr(hunter, "bodyReforgeStage", 0) or 0)
    rule = REFORGE_STAGE_RULES[min(current_stage, len(REFORGE_STAGE_RULES) - 1)]
    sect_tokens = int(getattr(hunter, "sectTokenCount", 0) or 0)
    discipline = float(getattr(hunter, "sectDiscipline", 0.0) or 0.0)
    level = int(getattr(hunter, "level", 1) or 1)
    loyalty = float(getattr(hunter, "loyalty", 0.0) or 0.0)
    insight = float(getattr(hunter, "insight", 0.0) or 0.0)
    promotion = {
        "promotionReadyFlag": bool(getattr(hunter, "promotionReady", False)),
        "recommendedTokenCost": max(1, current_stage + 1),
        "recommendedDiscipline": min(90, 30 + current_stage * 6),
        "ready": bool(getattr(hunter, "promotionReady", False)) and sect_tokens >= max(1, current_stage + 1) and discipline >= min(90, 30 + current_stage * 6),
    }
    return {
        "hunterId": str(getattr(hunter, "hunterId", "hunter")),
        "promotion": promotion,
        "bodyReforge": {
            "currentStage": current_stage,
            "nextStage": current_stage + 1,
            "requirements": dict(rule),
            "hasEnoughLevel": level >= int(rule["minLevel"]),
            "hasEnoughLoyalty": loyalty >= float(rule["minLoyalty"]),
            "hasEnoughInsight": insight >= float(rule["insight"]),
            "hasEnoughSectToken": sect_tokens >= int(rule.get("sectToken", 0)),
            "hasEnoughDiscipline": discipline >= float(rule.get("discipline", 0.0)),
        },
        "advice": [
            "증표와 문파 규율은 전직/환골탈태 개방 리듬을 조절하는 중간 목표로 사용한다.",
            "유니티 UI보다 먼저 서버가 성장 조건/실패 사유를 표준화해 두면 이후 연결이 쉬워진다.",
        ],
    }
