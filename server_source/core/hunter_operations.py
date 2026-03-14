from __future__ import annotations

from typing import Any, Dict

STYLE_TABLE = {
    "steady": {"atkMul": 1.00, "tempoMul": 1.00, "riskMul": 0.95, "offlineMul": 1.00, "moraleDelta": 2.0},
    "vanguard": {"atkMul": 1.12, "tempoMul": 1.12, "riskMul": 1.20, "offlineMul": 1.05, "moraleDelta": -1.0},
    "shadow": {"atkMul": 1.06, "tempoMul": 1.18, "riskMul": 0.92, "offlineMul": 1.02, "moraleDelta": 1.0},
    "support": {"atkMul": 0.96, "tempoMul": 0.95, "riskMul": 0.82, "offlineMul": 1.08, "moraleDelta": 3.0},
}

REST_TABLE = {
    "frugal": {"fatigueRecovery": 0.92, "offlineMul": 1.02, "taxTolerance": 0.96},
    "measured": {"fatigueRecovery": 1.00, "offlineMul": 1.00, "taxTolerance": 1.00},
    "lavish": {"fatigueRecovery": 1.14, "offlineMul": 0.97, "taxTolerance": 1.04},
}

TRAINING_TABLE = {
    "body": {"atkMul": 1.03, "tempoMul": 1.00, "recoveryMul": 1.04},
    "weapon": {"atkMul": 1.07, "tempoMul": 1.02, "recoveryMul": 0.98},
    "mind": {"atkMul": 0.99, "tempoMul": 0.97, "recoveryMul": 1.07},
    "footwork": {"atkMul": 1.01, "tempoMul": 1.10, "recoveryMul": 1.00},
}

DEFAULT_FACILITY_BY_NEED = {
    "frugal": "tavern_corner",
    "measured": "inn_main",
    "lavish": "clinic_spring",
}


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(v)))


def normalized_hunter_operation(hunter: Any) -> Dict[str, Any]:
    style = str(getattr(hunter, "operationStyle", "steady") or "steady").lower()
    rest = str(getattr(hunter, "restDiscipline", "measured") or "measured").lower()
    focus = str(getattr(hunter, "trainingFocus", "body") or "body").lower()
    if style not in STYLE_TABLE:
        style = "steady"
    if rest not in REST_TABLE:
        rest = "measured"
    if focus not in TRAINING_TABLE:
        focus = "body"
    morale = _clamp(getattr(hunter, "morale", 50.0), 0.0, 100.0)
    fatigue = _clamp(getattr(hunter, "fatigue", 0.0), 0.0, 100.0)
    bond = str(getattr(hunter, "bondFacilityId", "") or DEFAULT_FACILITY_BY_NEED[rest])
    return {
        "operationStyle": style,
        "restDiscipline": rest,
        "trainingFocus": focus,
        "morale": morale,
        "fatigue": fatigue,
        "bondFacilityId": bond,
    }


def compute_operation_modifiers(hunter: Any) -> Dict[str, float]:
    op = normalized_hunter_operation(hunter)
    style = STYLE_TABLE[op["operationStyle"]]
    rest = REST_TABLE[op["restDiscipline"]]
    focus = TRAINING_TABLE[op["trainingFocus"]]
    morale_bonus = 1.0 + ((op["morale"] - 50.0) / 250.0)
    fatigue_penalty = max(0.78, 1.0 - (op["fatigue"] / 220.0))
    atk_mul = style["atkMul"] * focus["atkMul"] * morale_bonus * fatigue_penalty
    tempo_mul = style["tempoMul"] * focus["tempoMul"] * max(0.82, 1.0 - (op["fatigue"] / 300.0))
    recovery_mul = rest["fatigueRecovery"] * focus["recoveryMul"] * (1.0 + op["morale"] / 500.0)
    offline_mul = style["offlineMul"] * rest["offlineMul"] * max(0.86, morale_bonus)
    injury_risk = style["riskMul"] * max(0.75, 1.0 + (op["fatigue"] - 35.0) / 180.0)
    return {
        "atkMul": round(atk_mul, 4),
        "tempoMul": round(tempo_mul, 4),
        "recoveryMul": round(recovery_mul, 4),
        "offlineMul": round(offline_mul, 4),
        "injuryRiskMul": round(injury_risk, 4),
        "taxToleranceMul": round(rest["taxTolerance"], 4),
    }


def build_operation_plan(hunter: Any) -> Dict[str, Any]:
    op = normalized_hunter_operation(hunter)
    mod = compute_operation_modifiers(hunter)
    style = op["operationStyle"]
    rest = op["restDiscipline"]
    focus = op["trainingFocus"]
    facility = op["bondFacilityId"] or DEFAULT_FACILITY_BY_NEED[rest]
    daily_plan = [
        f"Warm-up at {facility} before the first dispatch window.",
        f"Use {style} rotation for two hunt cycles, then schedule a {rest} recovery block.",
        f"Reserve one training block with {focus} focus before the final sortie.",
    ]
    originality_notes = [
        "Core loop emphasizes inn discipline, morale, and bonded facilities instead of copying another town-management title verbatim.",
        "Hunter identity is shaped by operation style and recovery doctrine, creating a murim-inn management fantasy rather than a generic hero tavern clone.",
        "Different recovery doctrines change pacing and economy, which supports mechanical differentiation and clearer product identity.",
    ]
    return {
        **op,
        "recommendedFacilityId": facility,
        "combatProfile": {
            "attackMultiplier": mod["atkMul"],
            "tempoMultiplier": mod["tempoMul"],
            "injuryRiskMultiplier": mod["injuryRiskMul"],
        },
        "offlineProfile": {
            "offlineMultiplier": mod["offlineMul"],
            "recoveryMultiplier": mod["recoveryMul"],
            "taxToleranceMultiplier": mod["taxToleranceMul"],
        },
        "dailyPlan": daily_plan,
        "originalityNotes": originality_notes,
    }
