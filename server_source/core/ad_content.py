# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
from __future__ import annotations

from typing import Dict, List


AD_OFFERS: List[Dict] = [
    {
        "offerId": "ad_temple_gold_small",
        "placement": "ad_shrine",
        "title": "객잔 운영비 보충",
        "buttonLabel": "광고 보고 골드 받기",
        "rewardType": "gold",
        "rewardAmount": 1200,
        "dailyCap": 3,
        "weight": 100,
        "isFlowSafe": True,
        "naturalBreakOnly": True,
        "description": "마을 화면에서만 노출. 전투 흐름을 끊지 않음.",
    },
    {
        "offerId": "ad_boost_hunt_ticket",
        "placement": "result_screen",
        "title": "사냥 재정비 지원",
        "buttonLabel": "광고 보고 재정비권 받기",
        "rewardType": "ticket",
        "rewardAmount": 1,
        "dailyCap": 2,
        "weight": 80,
        "isFlowSafe": True,
        "naturalBreakOnly": True,
        "description": "전투 종료 후 결과창 하단에서만 선택적으로 노출.",
    },
    {
        "offerId": "ad_pass_point",
        "placement": "daily_pass",
        "title": "광고 패스 포인트",
        "buttonLabel": "광고 보고 패스 포인트 +1",
        "rewardType": "passPoint",
        "rewardAmount": 1,
        "dailyCap": 5,
        "weight": 120,
        "isFlowSafe": True,
        "naturalBreakOnly": True,
        "description": "일일 목표와 합쳐서 제공. 핵심 진행 차단 없음.",
    },
]

REWARD_LABELS = {
    "gold": "골드",
    "ticket": "재정비권",
    "passPoint": "광고 패스 포인트",
}


def get_offer_by_id(offer_id: str) -> Dict | None:
    for offer in AD_OFFERS:
        if str(offer.get("offerId")) == str(offer_id):
            return offer
    return None
