from __future__ import annotations

from typing import Any, Dict, List, Tuple

from storage.sqlite_db import has_operator_mission_claim, insert_operator_mission_claim

MISSION_DEFS: List[Dict[str, Any]] = [
    {
        "missionId": "daily_settle_3",
        "scope": "daily",
        "title": "오늘의 정산 3회",
        "description": "헌터 귀환 정산을 3회 완료하세요.",
        "target": 3,
        "metric": "settle_count",
        "reward": {"operatorGold": 220, "operatorExp": 18, "patronPoint": 1},
    },
    {
        "missionId": "daily_craft_2",
        "scope": "daily",
        "title": "소모품 보급",
        "description": "제작을 2회 완료하세요.",
        "target": 2,
        "metric": "craft_count",
        "reward": {"operatorGold": 180, "operatorExp": 14},
    },
    {
        "missionId": "daily_train_2",
        "scope": "daily",
        "title": "훈련 감독",
        "description": "교육을 2회 완료하세요.",
        "target": 2,
        "metric": "train_count",
        "reward": {"operatorGold": 160, "operatorExp": 16},
    },
    {
        "missionId": "daily_material_25",
        "scope": "daily",
        "title": "재료 비축",
        "description": "재료를 합계 25개 확보하세요.",
        "target": 25,
        "metric": "material_total",
        "reward": {"operatorGold": 260, "operatorExp": 20, "inventory": {"herb": 3}},
    },
    {
        "missionId": "weekly_sell_10",
        "scope": "weekly",
        "title": "주간 상단 거래",
        "description": "판매를 10회 완료하세요.",
        "target": 10,
        "metric": "sell_count",
        "reward": {"operatorGold": 900, "operatorExp": 55, "inventory": {"sect_token": 1}},
    },
    {
        "missionId": "weekly_reforge_1",
        "scope": "weekly",
        "title": "주간 환골 의식",
        "description": "환골탈태를 1회 성공시키세요.",
        "target": 1,
        "metric": "reforge_count",
        "reward": {"operatorGold": 1200, "operatorExp": 80, "inventory": {"rebirth_pill": 1, "discipline_seal": 1}},
    },
]


def _safe_payload(log: Dict[str, Any]) -> Dict[str, Any]:
    payload = log.get("payloadJson")
    if isinstance(payload, dict):
        return payload
    return {}


def summarize_operator_metrics(logs: List[Dict[str, Any]]) -> Dict[str, int]:
    metrics = {
        "settle_count": 0,
        "craft_count": 0,
        "sell_count": 0,
        "train_count": 0,
        "reforge_count": 0,
        "material_total": 0,
    }
    for log in logs:
        rc = str(log.get("resultCode") or "")
        action = str(log.get("actionType") or "")
        payload = _safe_payload(log)
        if action == "settle_return" and rc == "OK_SETTLED":
            metrics["settle_count"] += 1
            mats = payload.get("materialsAdded") or {}
            metrics["material_total"] += sum(max(0, int(v)) for v in mats.values())
        elif action == "craft" and rc == "OK_CRAFTED":
            metrics["craft_count"] += max(1, int(payload.get("quantity", 1) or 1))
        elif action == "sell" and rc == "OK_SOLD":
            metrics["sell_count"] += max(1, int(payload.get("quantity", 1) or 1))
        elif action == "train" and rc == "OK_TRAINED":
            metrics["train_count"] += 1
        elif action == "body_reforge" and rc == "OK_REFORGED":
            metrics["reforge_count"] += 1
    return metrics


def build_operator_mission_snapshot(account_id: str, logs: List[Dict[str, Any]], treasury: Dict[str, Any] | None = None, hunters: List[Any] | None = None) -> Dict[str, Any]:
    metrics = summarize_operator_metrics(logs)
    missions = []
    claimable = 0
    for md in MISSION_DEFS:
        progress = int(metrics.get(md["metric"], 0))
        target = int(md["target"])
        completed = progress >= target
        claimed = has_operator_mission_claim(account_id, md["missionId"], md["scope"])
        if completed and not claimed:
            claimable += 1
        missions.append({
            "missionId": md["missionId"],
            "scope": md["scope"],
            "title": md["title"],
            "description": md["description"],
            "metric": md["metric"],
            "target": target,
            "progress": progress,
            "completed": completed,
            "claimed": claimed,
            "reward": dict(md["reward"]),
        })
    return {
        "accountId": account_id,
        "claimableCount": claimable,
        "metrics": metrics,
        "missions": missions,
        "designIntent": "정산/제작/교육/환골 같은 운영 행동 자체를 짧은 목표로 잘게 쪼개 중간 재미를 자주 느끼게 한다.",
    }


def claim_operator_mission(account_id: str, mission_id: str, scope: str, snapshot: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    mission = next((m for m in snapshot.get("missions", []) if m["missionId"] == mission_id and m["scope"] == scope), None)
    if not mission:
        return False, "ERR_INVALID_INPUT", {"missionId": mission_id, "scope": scope}
    if mission.get("claimed"):
        return False, "ERR_ALREADY_CLAIMED", {"missionId": mission_id, "scope": scope}
    if not mission.get("completed"):
        return False, "ERR_MISSION_NOT_COMPLETE", {"missionId": mission_id, "scope": scope, "progress": mission.get("progress", 0), "target": mission.get("target", 0)}
    reward = dict(mission.get("reward") or {})
    if not insert_operator_mission_claim(account_id, mission_id, scope, reward_json=str(reward)):
        return False, "ERR_ALREADY_CLAIMED", {"missionId": mission_id, "scope": scope}
    return True, "OK_MISSION_CLAIMED", {"missionId": mission_id, "scope": scope, "reward": reward}
