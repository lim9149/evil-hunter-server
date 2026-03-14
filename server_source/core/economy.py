from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List

from core.hunter_operations import compute_operation_modifiers, normalized_hunter_operation


def _simulate_one(hunter: Any, hours: int, battle_minutes_per_loop: float, rest_minutes_per_loop: float, crowding_factor: float) -> Dict[str, Any]:
    mods = compute_operation_modifiers(hunter)
    op = normalized_hunter_operation(hunter)
    power = max(float(getattr(hunter, "powerScore", 0.0) or 0.0), 1.0)
    loops = (hours * 60.0) / max(1.0, battle_minutes_per_loop + rest_minutes_per_loop / max(mods["recoveryMul"], 0.5))
    tempo_loops = loops * mods["tempoMul"] * max(0.75, 1.0 - crowding_factor * 0.45)
    crowd_penalty = 1.0 - crowding_factor * (0.35 if op["operationStyle"] == "shadow" else 0.55)
    gold_per_loop = math.sqrt(power) * 4.5 * mods["offlineMul"] * crowd_penalty
    exp_per_loop = math.sqrt(power) * 2.8 * mods["offlineMul"] * crowd_penalty
    fatigue_gain = max(2.0, battle_minutes_per_loop * 1.7 * (2.0 - mods["recoveryMul"]))
    net_fatigue = max(0.0, op["fatigue"] + fatigue_gain - (rest_minutes_per_loop * 2.4 * mods["recoveryMul"]))
    morale_shift = ((mods["tempoMul"] - 1.0) * 6.0) - (net_fatigue / 45.0) + ((op["morale"] - 50.0) / 30.0)
    return {
        "hunterId": getattr(hunter, "hunterId", "unknown"),
        "style": op["operationStyle"],
        "rest": op["restDiscipline"],
        "focus": op["trainingFocus"],
        "estimatedLoops": round(tempo_loops, 2),
        "estimatedGold": int(math.floor(max(0.0, tempo_loops * gold_per_loop))),
        "estimatedExp": int(math.floor(max(0.0, tempo_loops * exp_per_loop))),
        "endFatigue": round(min(100.0, net_fatigue), 1),
        "moraleDelta": round(morale_shift, 2),
        "congestionPressure": round(max(0.0, 100.0 * crowding_factor * (1.1 if op["operationStyle"] == "vanguard" else 0.9)), 1),
        "tempoScore": round(tempo_loops / max(hours, 1), 2),
    }


def simulate_long_term_economy(hunters: Iterable[Any], hours: int, battle_minutes_per_loop: float, rest_minutes_per_loop: float, crowding_factor: float) -> Dict[str, Any]:
    per_hunter: List[Dict[str, Any]] = [
        _simulate_one(h, hours, battle_minutes_per_loop, rest_minutes_per_loop, crowding_factor)
        for h in hunters
    ]
    total_gold = sum(item["estimatedGold"] for item in per_hunter)
    total_exp = sum(item["estimatedExp"] for item in per_hunter)
    avg_fatigue = round(sum(item["endFatigue"] for item in per_hunter) / max(len(per_hunter), 1), 2)
    avg_tempo = round(sum(item["tempoScore"] for item in per_hunter) / max(len(per_hunter), 1), 2)
    warnings: List[str] = []
    if avg_fatigue > 65:
        warnings.append("Average fatigue is too high for a long session; increase recovery cadence or reduce battle block length.")
    if avg_tempo < 4.0:
        warnings.append("Hunt loop tempo feels slow; shorten travel/rest windows or add slot-based express routing.")
    if crowding_factor > 0.30:
        warnings.append("Crowding risk is high; facility slotting and lane offset logic should stay enabled in the client.")
    design_hooks = [
        "Different operation styles should unlock distinct inn events and dispatch dialogue to reinforce product identity.",
        "Economy gain is intentionally tied to morale and recovery doctrine so the game does not feel like a direct copy of another auto-hunt tycoon.",
        "Use bonded facilities and lane reservations as visible town-management verbs for longer sessions.",
    ]
    return {
        "summary": {
            "totalEstimatedGold": total_gold,
            "totalEstimatedExp": total_exp,
            "averageEndFatigue": avg_fatigue,
            "averageTempoScore": avg_tempo,
        },
        "perHunter": per_hunter,
        "balanceWarnings": warnings,
        "designHooks": design_hooks,
    }
