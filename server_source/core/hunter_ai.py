from __future__ import annotations

from typing import Any, Dict


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(v)))


def build_ai_profile(hunter: Any) -> Dict[str, Any]:
    operation = str(getattr(hunter, 'operationStyle', 'steady') or 'steady').lower()
    rest = str(getattr(hunter, 'restDiscipline', 'measured') or 'measured').lower()
    training = str(getattr(hunter, 'trainingFocus', 'body') or 'body').lower()
    preferred = str(getattr(hunter, 'preferredActivity', 'hunt') or 'hunt').lower()
    ai_mode = str(getattr(hunter, 'aiMode', 'autonomous') or 'autonomous').lower()
    manual_override = bool(getattr(hunter, 'manualControl', False))
    morale = _clamp(getattr(hunter, 'morale', 50.0), 0.0, 100.0)
    fatigue = _clamp(getattr(hunter, 'fatigue', 0.0), 0.0, 100.0)
    social = _clamp(getattr(hunter, 'socialDrive', 50.0), 0.0, 100.0)
    discipline = _clamp(getattr(hunter, 'disciplineDrive', 50.0), 0.0, 100.0)
    bravery = _clamp(getattr(hunter, 'braveryDrive', 50.0), 0.0, 100.0)

    weights = {
        'hunt': 1.0 + bravery / 100.0,
        'train': 0.8 + discipline / 100.0,
        'rest': 0.6 + fatigue / 110.0,
        'socialize': 0.5 + social / 100.0,
    }
    if preferred in weights:
        weights[preferred] += 0.35
    if operation == 'vanguard':
        weights['hunt'] += 0.3
    elif operation == 'shadow':
        weights['hunt'] += 0.15
        weights['socialize'] -= 0.1
    elif operation == 'support':
        weights['socialize'] += 0.25
        weights['train'] += 0.1
    if rest == 'lavish':
        weights['rest'] += 0.2
    elif rest == 'frugal':
        weights['rest'] -= 0.1
    if training == 'weapon':
        weights['train'] += 0.2
    elif training == 'mind':
        weights['socialize'] += 0.1
        weights['rest'] += 0.05
    elif training == 'footwork':
        weights['hunt'] += 0.12

    routine = []
    if fatigue >= 65:
        routine.extend(['tea_rest', 'clinic_or_inn', 'light_patrol'])
    elif morale <= 35:
        routine.extend(['tavern_social', 'sparring', 'short_hunt'])
    else:
        routine.extend(['board_check', preferred, 'return_and_report'])

    command_policy = [
        'AI roaming remains active by default.',
        'Direct orders temporarily override the current routine, then the hunter returns to AI life-sim flow.',
        'Different hunters should choose different loops based on needs, bravery, discipline, and social drive.',
    ]
    originality = [
        'Differentiate through murim inn life-sim, sect gossip, discipline, and training culture rather than removing visible hunter AI.',
        'Keep hunters visibly roaming town and field, but make routines personality-driven and facility-linked.',
        'Manual orders are an intervention layer on top of AI routines, not a replacement for the world simulation.',
    ]
    summary = f"{operation} style / {rest} rest / {training} focus / preferred {preferred}"

    return {
        'hunterId': getattr(hunter, 'hunterId', ''),
        'aiMode': ai_mode,
        'manualOverrideActive': manual_override,
        'preferredActivity': preferred,
        'socialDrive': social,
        'disciplineDrive': discipline,
        'braveryDrive': bravery,
        'personalitySummary': summary,
        'dailyRoutineTemplate': routine,
        'decisionWeights': weights,
        'commandPolicy': command_policy,
        'originalityHooks': originality,
    }
