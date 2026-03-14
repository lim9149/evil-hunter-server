# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
from __future__ import annotations

PROBABILITY_DISCLOSURES = [
    {
        "tableId": "ad_chest_common",
        "displayName": "광고 보물상자 - 일반",
        "isPaid": False,
        "lastUpdated": "2026-03-10",
        "entries": [
            {"itemId": "gold_small", "itemName": "소량 골드", "probabilityPercent": 60.0},
            {"itemId": "exp_note", "itemName": "수련 비급 조각", "probabilityPercent": 25.0},
            {"itemId": "repair_kit", "itemName": "수리 도구", "probabilityPercent": 10.0},
            {"itemId": "rare_mat", "itemName": "희귀 제작 재료", "probabilityPercent": 4.0},
            {"itemId": "hero_talisman", "itemName": "문파 부적", "probabilityPercent": 1.0},
        ],
    },
    {
        "tableId": "dungeon_relic_box",
        "displayName": "던전 유물 상자",
        "isPaid": False,
        "lastUpdated": "2026-03-10",
        "entries": [
            {"itemId": "relic_shard", "itemName": "유물 파편", "probabilityPercent": 52.0},
            {"itemId": "weapon_piece", "itemName": "무기 조각", "probabilityPercent": 28.0},
            {"itemId": "armor_piece", "itemName": "방어구 조각", "probabilityPercent": 15.0},
            {"itemId": "secret_manual", "itemName": "비전 수련서", "probabilityPercent": 4.5},
            {"itemId": "sealed_fragment", "itemName": "봉인 조각", "probabilityPercent": 0.5},
        ],
    },
]

LOOTBOX_RULES = {
    "notice": "확률형 보상은 게임 내 버튼에서 항상 열람 가능해야 하며, 변경 시 변경일을 함께 표기한다.",
    "koreaReadyChecklist": [
        "확률표기 시트와 서버 응답이 일치하는가",
        "클라이언트에서 동일 비율을 보여주는가",
        "변경 이력이 기록되는가",
        "유상/무상 여부와 별개로 오해 가능성이 있는 랜덤 보상을 함께 관리하는가",
    ],
}
