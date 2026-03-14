# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
from __future__ import annotations

TOWN_WORLD_DEFINITION = {
    "worldId": "murim_inn_town_001",
    "worldName": "무림객잔 마을",
    "sceneName": "TownWorldScene",
    "cameraMode": "isometric",
    "facilities": [
        {"facilityId": "inn", "label": "객잔", "kind": "rest", "x": -4.0, "y": 0.0, "z": 2.2},
        {"facilityId": "tavern", "label": "주점", "kind": "food", "x": -2.0, "y": 0.0, "z": 1.8},
        {"facilityId": "clinic", "label": "의원", "kind": "heal", "x": 1.5, "y": 0.0, "z": 2.0},
        {"facilityId": "forge", "label": "대장간", "kind": "forge", "x": 3.5, "y": 0.0, "z": 1.2},
        {"facilityId": "training", "label": "수련장", "kind": "training", "x": 4.8, "y": 0.0, "z": -0.6},
        {"facilityId": "ad_shrine", "label": "광고 신전", "kind": "rewarded_ads", "x": 0.4, "y": 0.0, "z": 3.6},
        {"facilityId": "community_board", "label": "게시판", "kind": "notice", "x": -5.0, "y": 0.0, "z": -0.8},
        {"facilityId": "story_gate", "label": "기록석", "kind": "story", "x": 5.5, "y": 0.0, "z": 2.8},
    ],
    "monsterZones": [
        {"zoneId": "south_field", "label": "남문 들판", "difficulty": 1, "spawnCount": 4, "x": 9.0, "y": 0.0, "z": -1.5, "radius": 3.0},
        {"zoneId": "east_forest", "label": "동쪽 숲", "difficulty": 2, "spawnCount": 5, "x": 12.0, "y": 0.0, "z": 2.5, "radius": 4.0},
    ],
    "hudRules": {
        "useOverlayPanels": True,
        "battleSceneAllowed": False,
        "optionalAdsOnlyAtBreaks": True,
        "mailboxButton": True,
        "announcementButton": True,
        "storyButton": True,
    },
}

def build_town_world_snapshot(account_id: str) -> dict:
    return {
        "accountId": account_id,
        "worldId": TOWN_WORLD_DEFINITION["worldId"],
        "recommendedFlow": [
            "recruit_hunter",
            "watch_hunters_patrol",
            "hunt_monsters",
            "return_to_facility",
            "open_overlay_ui",
        ],
        "townState": {
            "residentHunterCount": 8,
            "activeMonsterCount": 9,
            "restingHunterCount": 2,
            "overlayPanels": ["story", "mailbox", "announcement", "probability"],
        },
    }
