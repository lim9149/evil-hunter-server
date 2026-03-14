# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
#!/usr/bin/env python3
"""Update the project Google Sheet with progress, API spec, and docs.

Respects existing sheet format:
- 프로젝트 요약본: A=버전, B=내용, C=날짜 → appends one version row (v0.1.0).
- 진행도: 구분, 항목, 상태, 비고 → appends rows (or sets if empty).
- API 명세: Method, Path, 설명 → appends rows (or sets if empty).
- 02_Server_Structure: A1 = server folder structure text.
- DB_SCHEMA: 테이블, 용도 → appends rows (or sets if empty).

Requirements:
  1. Google Cloud: enable Sheets API + Drive API, create Service Account, download JSON key.
  2. Share the spreadsheet with the service account email (Editor).
  3. Set credentials path:
       GOOGLE_APPLICATION_CREDENTIALS=path/to/service_account.json
     or: --credentials path/to/service_account.json

Usage:
  python scripts/update_google_sheet.py
  python scripts/update_google_sheet.py --credentials ./my-key.json
  python scripts/update_google_sheet.py --dry-run   # print only, no API calls
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Default Spreadsheet ID from URL: .../d/SPREADSHEET_ID/edit
# If you get "This operation is not supported for this document", the file may be
# an uploaded .xlsx: use File → Save as Google Sheets, then use the new sheet's ID with --spreadsheet-id.
DEFAULT_SPREADSHEET_ID = "1upkVvuiedU7Xrm37dg1gHXQaGL-C8JyL"


def _progress_rows():
    headers = ["구분", "항목", "상태", "비고"]
    data = [
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
    return [headers] + data


def _api_rows():
    headers = ["Method", "Path", "설명"]
    data = [
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
    return [headers] + data


def _db_schema_rows():
    headers = ["테이블", "용도"]
    data = [
        ["offline_collect", "오프라인 수령 멱등 (hunterId, collectedAtEpoch)"],
        ["bans", "계정 밴"],
        ["admin_mode", "운영자 배율 키-값"],
        ["worldboss_claim", "월드보스 보상 멱등 (hunterId, bossId, seasonId)"],
        ["pvp_claim", "PvP 보상 멱등 (hunterId, seasonId)"],
        ["reward_tier", "랭크 구간별 배율 (kind, rankMin, rankMax, multiplier)"],
        ["accounts, account_identities", "계정·OAuth 연동"],
        ["refresh_tokens", "리프레시 토큰"],
        ["purchases", "IAP 결제 (멱등: provider+provider_tx_id)"],
        ["currency_ledger", "재화 입출금 (source_kind+source_id 멱등)"],
        ["audit_logs", "감사 로그"],
        ["iap_products", "IAP 상품 카탈로그"],
        ["tier_defs", "시즌별 티어 배율"],
        ["mbti_traits", "MBTI별 스탯 배율"],
        ["promotion_nodes", "승급 노드"],
        ["item_defs", "아이템 정의"],
    ]
    return [headers] + data


def _server_structure_text():
    return """evil-hunter-server/
├── main.py                 # FastAPI 앱, 라우터 등록, /health
├── requirements.txt
├── core/
│   ├── schemas.py          # Pydantic 모델 (Monster, Hunter, Offline, Combat, Reward 등)
│   ├── admin_mode.py       # 운영자 배율 (worldboss/pvp 등)
│   ├── rewards.py          # 랭크→배율 적용
│   ├── tier.py             # tier_defs 조회, tier_rank, tier_exists
│   ├── mbti.py             # MBTI 랜덤/특성
│   ├── promotion.py        # 승급 노드/효과
│   ├── items.py            # 아이템 정의/장착 배율
│   ├── offline.py          # 오프라인 보상 계산
│   ├── combat.py           # 전투 데미지 계산
│   ├── auth/               # 게스트/OAuth/리프레시
│   ├── iap/                # Google/Apple 검증
│   ├── audit/              # 감사 로그
│   └── security/           # JWT, rate limit, replay guard
├── routers/
│   ├── monster, map, village, hunter, offline, combat
│   ├── worldboss_pvp.py    # 보상 tier, claim
│   ├── admin_mode.py, admin_auth, admin_audit, admin_tools, admin_catalog
│   ├── auth.py, iap.py
│   └── (rewards.py: 구 스키마, 미등록)
├── storage/
│   ├── sqlite_db.py        # 스키마·CRUD·claim·reward_tier·auth·iap·audit
│   ├── repo_registry.py    # 메모리/DB 레포
│   └── memory_repo.py
├── scripts/
│   ├── sync_reward_tiers_from_sheet.py  # xlsx 월드보스_PvP → reward_tier
│   ├── update_google_sheet.py           # 시트 자동 반영
│   └── sim_*.py            # 시뮬레이션
└── tests/                  # pytest 15개"""


def _version_row():
    return [
        "v0.1.0",
        "서버: 헬스 엔드포인트 추가, Hunter tier-up API 추가, 테스트 15개 통과, 구글 시트 동기화 스크립트(update_google_sheet.py) 추가",
        "2026-03-07",
    ]


def _find_worksheet(sh, title_candidates: list[str]):
    for name in title_candidates:
        try:
            return sh.worksheet(name)
        except Exception:
            continue
    return None


def update_sheet(credentials_path: str | None, spreadsheet_id: str | None, dry_run: bool) -> None:
    sid = spreadsheet_id or DEFAULT_SPREADSHEET_ID
    if dry_run:
        print("[DRY-RUN] Would update spreadsheet", sid)
        print("  프로젝트 요약본: append row", _version_row())
        print("  진행도: set/append", len(_progress_rows()), "rows")
        print("  API 명세: set/append", len(_api_rows()), "rows")
        print("  02_Server_Structure: set A1 text")
        print("  DB_SCHEMA: set/append", len(_db_schema_rows()), "rows")
        return

    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError as e:
        raise SystemExit("Install gspread and google-auth: pip install gspread google-auth") from e

    path = credentials_path or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not path or not os.path.isfile(path):
        raise SystemExit(
            "Set GOOGLE_APPLICATION_CREDENTIALS or --credentials to a service account JSON key file. "
            "Share the spreadsheet with the service account email (Editor)."
        )

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(path, scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(sid)

    # 1) 프로젝트 요약본: 기존 양식 A=버전, B=내용, C=날짜 → 맨 아래에 버전 행 추가
    ws_summary = _find_worksheet(sh, ["프로젝트 요약본", "요약본", "Sheet1"])
    if ws_summary:
        all_ = ws_summary.get_all_values()
        next_row = len(all_) + 1
        ws_summary.append_row(_version_row(), value_input_option="USER_ENTERED")
        print("Updated 프로젝트 요약본: appended version row at", next_row)
    else:
        print("Sheet '프로젝트 요약본' not found; skip.")

    # 2) 진행도: 구분, 항목, 상태, 비고
    ws_progress = _find_worksheet(sh, ["진행도"])
    if ws_progress:
        progress = _progress_rows()
        existing = ws_progress.get_all_values()
        if not existing:
            ws_progress.update(progress, value_input_option="USER_ENTERED")
            print("Updated 진행도: set", len(progress), "rows (header + data)")
        else:
            # 기존 양식 존중: 헤더가 맞고 아직 서버 진행도 데이터가 없을 때만 추가
            has_header = existing and len(existing[0]) >= 2 and existing[0][0] == "구분" and existing[0][1] == "항목"
            already_has_data = any(
                len(r) > 1 and "FastAPI" in str(r[1]) for r in (existing or [])[1:4]
            )
            if has_header and not already_has_data:
                ws_progress.append_rows(progress[1:], value_input_option="USER_ENTERED")
                print("Updated 진행도: appended", len(progress) - 1, "data rows")
            elif not has_header:
                ws_progress.update(progress, value_input_option="USER_ENTERED")
                print("Updated 진행도: set", len(progress), "rows")
            else:
                print("진행도: already has server progress data; skip append.")
    else:
        print("Sheet '진행도' not found; skip.")

    # 3) API 명세: Method, Path, 설명
    ws_api = _find_worksheet(sh, ["API 명세", "API명세"])
    if ws_api:
        api = _api_rows()
        existing = ws_api.get_all_values()
        if not existing:
            ws_api.update(api, value_input_option="USER_ENTERED")
            print("Updated API 명세: set", len(api), "rows")
        else:
            has_header = existing and len(existing[0]) >= 2 and existing[0][0] == "Method" and existing[0][1] == "Path"
            already_has_data = any(
                len(r) > 1 and r[1] == "/health" for r in (existing or [])[1:4]
            )
            if has_header and not already_has_data:
                ws_api.append_rows(api[1:], value_input_option="USER_ENTERED")
                print("Updated API 명세: appended", len(api) - 1, "data rows")
            elif not has_header:
                ws_api.update(api, value_input_option="USER_ENTERED")
                print("Updated API 명세: set", len(api), "rows")
            else:
                print("API 명세: already has API data; skip append.")
    else:
        print("Sheet 'API 명세' not found; skip.")

    # 4) 02_Server_Structure: A1에 구조 텍스트
    ws_struct = _find_worksheet(sh, ["02_Server_Structure", "Server_Structure", "서버 구조"])
    if ws_struct:
        ws_struct.update_acell("A1", _server_structure_text())
        print("Updated 02_Server_Structure: set A1")
    else:
        print("Sheet '02_Server_Structure' not found; skip.")

    # 5) DB_SCHEMA: 테이블, 용도
    ws_db = _find_worksheet(sh, ["DB_SCHEMA", "DB SCHEMA"])
    if ws_db:
        schema = _db_schema_rows()
        existing = ws_db.get_all_values()
        if not existing:
            ws_db.update(schema, value_input_option="USER_ENTERED")
            print("Updated DB_SCHEMA: set", len(schema), "rows")
        else:
            has_header = existing and existing[0][0] == "테이블"
            already_has_data = any(
                len(r) > 0 and r[0] == "offline_collect" for r in (existing or [])[1:4]
            )
            if has_header and not already_has_data:
                ws_db.append_rows(schema[1:], value_input_option="USER_ENTERED")
                print("Updated DB_SCHEMA: appended", len(schema) - 1, "data rows")
            elif not has_header:
                ws_db.update(schema, value_input_option="USER_ENTERED")
                print("Updated DB_SCHEMA: set", len(schema), "rows")
            else:
                print("DB_SCHEMA: already has schema data; skip append.")
    else:
        print("Sheet 'DB_SCHEMA' not found; skip.")

    print("Done.")


def main():
    ap = argparse.ArgumentParser(description="Update project Google Sheet with progress and API spec.")
    ap.add_argument("--credentials", "-c", default=None, help="Path to service account JSON key")
    ap.add_argument("--spreadsheet-id", "-s", default=None, help="Spreadsheet ID (from URL .../d/ID/edit). Use if you get 'operation not supported' with xlsx-uploaded docs.")
    ap.add_argument("--dry-run", action="store_true", help="Print what would be done, no API calls")
    args = ap.parse_args()
    update_sheet(args.credentials, args.spreadsheet_id, args.dry_run)


if __name__ == "__main__":
    main()
