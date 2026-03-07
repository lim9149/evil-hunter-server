#!/usr/bin/env python3
"""Export progress and API summary as tab-separated rows for pasting into Google Sheet.

Usage:
  python scripts/export_sheet_rows.py progress   # 진행도 탭용
  python scripts/export_sheet_rows.py api        # API 명세 탭용
  python scripts/export_sheet_rows.py            # both to stdout
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def progress_rows():
    """진행도 탭에 붙여넣을 행 (탭 구분)."""
    headers = ["구분", "항목", "상태", "비고"]
    rows = [
        ["서버", "FastAPI 앱 (v0.1.0)", "완료", "main.py, /health 포함"],
        ["서버", "Monster/Map/Village CRUD", "완료", "GET/POST/DELETE"],
        ["서버", "Hunter CRUD + recruit/promote/equip/tier-up", "완료", "slot 중복 방지, MBTI 랜덤 배정"],
        ["서버", "Offline preview & collect (멱등)", "완료", "offline_collect PK (hunterId, collectedAtEpoch)"],
        ["서버", "Combat fight", "완료", "damage/hitsToKill/totalSec"],
        ["서버", "WorldBoss/PvP 시즌·보스 카탈로그", "완료", "POST/GET worldbosses, pvp/seasons"],
        ["서버", "WorldBoss/PvP 랭크 보상 tier (배율)", "완료", "reward_tier DB, 시트 동기화 스크립트"],
        ["서버", "WorldBoss/PvP claim (멱등)", "완료", "worldboss_claim, pvp_claim PK"],
        ["서버", "운영자 모드 (admin modes)", "완료", "/admin/modes, 골드/경험치 배율"],
        ["서버", "Auth (게스트/리프레시/OAuth/연동)", "완료", "guest, refresh, logout, oauth, link"],
        ["서버", "IAP (Google/Apple 검증·재화 지급)", "완료", "/iap/google/verify, /iap/apple/verify"],
        ["서버", "Admin Auth/Tools/Audit/Catalog", "완료", "JWT 보호, grant/ban, audit, catalog"],
        ["서버", "헬스 체크", "완료", "GET /health"],
        ["서버", "Hunter 티어 상승 API", "완료", "POST /hunters/{id}/tier-up (tier_defs 기반)"],
        ["테스트", "pytest 15개", "완료", "auth, refresh, combat, crud, hunter, iap, offline, worldboss_pvp"],
        ["시트 연동", "월드보스_PvP → reward_tier", "완료", "sync_reward_tiers_from_sheet.py (xlsx)"],
        ["클라이언트", "Unity 연동", "미진행", "API 명세 참고"],
        ["QA", "통합/부하 테스트", "미진행", ""],
    ]
    return [headers] + rows


def api_rows():
    """API 명세 탭에 붙여넣을 행 (Method, Path, 설명)."""
    headers = ["Method", "Path", "설명"]
    rows = [
        ["GET", "/health", "서비스 상태·버전 (배포 헬스체크)"],
        ["GET", "/monsters", "몬스터 목록"],
        ["GET", "/monsters/{id}", "몬스터 조회"],
        ["POST", "/monsters", "몬스터 생성/수정"],
        ["DELETE", "/monsters/{id}", "몬스터 삭제"],
        ["GET", "/maps", "맵 목록"],
        ["GET", "/maps/{id}", "맵 조회"],
        ["POST", "/maps", "맵 생성/수정"],
        ["DELETE", "/maps/{id}", "맵 삭제"],
        ["GET", "/villages", "마을 목록"],
        ["GET", "/villages/{id}", "마을 조회"],
        ["POST", "/villages", "마을 생성/수정"],
        ["DELETE", "/villages/{id}", "마을 삭제"],
        ["GET", "/hunters?accountId=", "영웅 목록 (accountId 필터)"],
        ["GET", "/hunters/{id}", "영웅 조회"],
        ["POST", "/hunters", "영웅 생성/수정"],
        ["POST", "/hunters/{id}/recruit", "MBTI 랜덤 배정"],
        ["POST", "/hunters/{id}/promote", "승급 노드 적용"],
        ["POST", "/hunters/{id}/equip", "장비 장착"],
        ["POST", "/hunters/{id}/tier-up", "티어 상승 (T1→T2…)"],
        ["DELETE", "/hunters/{id}", "영웅 삭제"],
        ["POST", "/offline/preview", "오프라인 보상 미리보기"],
        ["POST", "/offline/collect", "오프라인 보상 수령 (멱등)"],
        ["POST", "/combat/fight", "전투 1회 (damage/hitsToKill 등)"],
        ["GET", "/rewards/tiers/{kind}", "보상 tier 목록 (kind=worldboss|pvp)"],
        ["POST", "/rewards/tiers", "보상 tier UPSERT"],
        ["POST", "/worldbosses", "보스 카탈로그 UPSERT"],
        ["GET", "/worldbosses", "보스 목록"],
        ["POST", "/pvp/seasons", "시즌 UPSERT"],
        ["GET", "/pvp/seasons", "시즌 목록"],
        ["POST", "/worldboss/claim", "월드보스 보상 수령 (멱등)"],
        ["POST", "/pvp/claim", "PvP 보상 수령 (멱등)"],
        ["GET", "/admin/modes", "모드 목록"],
        ["GET", "/admin/modes/{key}", "모드 조회"],
        ["POST", "/admin/modes", "모드 UPSERT"],
        ["POST", "/auth/guest", "게스트 로그인"],
        ["POST", "/auth/refresh", "리프레시 토큰 갱신"],
        ["POST", "/auth/logout", "로그아웃"],
        ["POST", "/auth/oauth/google", "Google OAuth"],
        ["POST", "/auth/oauth/apple", "Apple OAuth"],
        ["POST", "/auth/link/google", "Google 연동"],
        ["POST", "/auth/link/apple", "Apple 연동"],
        ["POST", "/iap/google/verify", "Google 결제 검증·재화 지급"],
        ["POST", "/iap/apple/verify", "Apple 결제 검증·재화 지급"],
        ["POST", "/admin/auth/login", "관리자 로그인"],
        ["GET", "/admin/audit/logs", "감사 로그"],
        ["POST", "/admin/tools/grant", "재화 지급"],
        ["POST", "/admin/tools/ban", "밴"],
        ["POST", "/admin/tools/unban", "밴 해제"],
        ["GET", "/admin/tools/ban/{account_id}", "밴 조회"],
        ["GET", "/admin/catalog/iap-products", "IAP 상품 목록"],
        ["POST", "/admin/catalog/iap-products", "IAP 상품 등록"],
        ["GET", "/admin/catalog/tiers", "티어 정의 목록"],
        ["POST", "/admin/catalog/tiers", "티어 정의 등록"],
        ["GET", "/admin/catalog/mbti", "MBTI 특성 목록"],
        ["POST", "/admin/catalog/mbti", "MBTI 특성 등록"],
        ["GET", "/admin/catalog/items", "아이템 정의 목록"],
        ["POST", "/admin/catalog/items", "아이템 정의 등록"],
        ["GET", "/admin/catalog/promotions", "승급 노드 목록"],
        ["POST", "/admin/catalog/promotions", "승급 노드 등록"],
    ]
    return [headers] + rows


def to_tsv(rows):
    return "\n".join("\t".join(str(c) for c in row) for row in rows)


def main():
    mode = (sys.argv[1:] or ["all"])[0].lower()
    if mode == "progress":
        print(to_tsv(progress_rows()))
    elif mode == "api":
        print(to_tsv(api_rows()))
    else:
        print("=== 진행도 (탭에 붙여넣기) ===")
        print(to_tsv(progress_rows()))
        print()
        print("=== API 명세 (탭에 붙여넣기) ===")
        print(to_tsv(api_rows()))


if __name__ == "__main__":
    main()
