from __future__ import annotations

from typing import Any, Dict, List, Tuple

# More granular progression ladder so players feel frequent milestones.
# This remains compatible with the existing /ads/vip-status endpoint,
# but is framed as an in-world patron/support track rather than hard paywall VIP.
PATRON_STAGES: List[Dict[str, Any]] = [
    {"level": 0, "title": "객잔 손님", "requires": 0, "perks": ["후원 누적 시 작은 운영 보너스가 열린다."]},
    {"level": 1, "title": "단골 손님", "requires": 5, "perks": ["객잔 회복 속도 +3%"]},
    {"level": 2, "title": "후원 손님", "requires": 12, "perks": ["의뢰 보상 +4%"]},
    {"level": 3, "title": "객잔 지기", "requires": 20, "perks": ["동시 파견 칸 +1"]},
    {"level": 4, "title": "문파 후원인", "requires": 32, "perks": ["교육 완료 속도 +5%"]},
    {"level": 5, "title": "객잔 귀빈", "requires": 48, "perks": ["희귀 재료 발견률 +3%"]},
    {"level": 6, "title": "의형 손님", "requires": 70, "perks": ["회복약 제작 효율 +6%"]},
    {"level": 7, "title": "문파 공로객", "requires": 98, "perks": ["전직 준비 비용 -4%"]},
    {"level": 8, "title": "객잔 수호객", "requires": 135, "perks": ["고급 사냥 귀환 골드 +5%"]},
    {"level": 9, "title": "장문 후원객", "requires": 185, "perks": ["환골탈태 재료 보정 +4%"]},
    {"level": 10, "title": "객잔 전설 후원", "requires": 250, "perks": ["마을 전체 운영 속도 +5%", "특수 풍문 슬롯 +1"]},
]

STAGE_BY_LEVEL = {int(row["level"]): row for row in PATRON_STAGES}


def compute_patron_stage(progress_value: int) -> Dict[str, Any]:
    progress_value = max(0, int(progress_value))
    current = PATRON_STAGES[0]
    next_stage = None
    prev_req = 0
    for stage in PATRON_STAGES:
        if progress_value >= int(stage["requires"]):
            current = stage
            prev_req = int(stage["requires"])
        elif next_stage is None:
            next_stage = stage
            break

    current_req = int(current["requires"])
    if next_stage is None:
        progress_ratio = 1.0
        remaining = 0
        next_req = None
    else:
        next_req = int(next_stage["requires"])
        span = max(1, next_req - current_req)
        progress_ratio = max(0.0, min(1.0, (progress_value - current_req) / span))
        remaining = max(0, next_req - progress_value)

    current_index = next((idx for idx, row in enumerate(PATRON_STAGES) if row["level"] == current["level"]), 0)
    preview = PATRON_STAGES[current_index : min(len(PATRON_STAGES), current_index + 3)]
    return {
        "level": int(current["level"]),
        "title": str(current["title"]),
        "perks": list(current["perks"]),
        "currentThreshold": current_req,
        "nextLevel": int(next_stage["level"]) if next_stage else None,
        "nextRequires": next_req,
        "remainingToNext": remaining,
        "progressRatio": round(progress_ratio, 4),
        "milestonePreview": [
            {
                "level": int(row["level"]),
                "title": str(row["title"]),
                "requires": int(row["requires"]),
                "perks": list(row["perks"]),
            }
            for row in preview
        ],
    }


def patron_design_intent() -> str:
    return (
        "현금 VIP 대신 세계관 내부의 후원 단계/객잔 명망 단계로 자주 작은 보상을 주어, "
        "중간중간 성취감과 운영 선택의 맛을 더합니다."
    )
