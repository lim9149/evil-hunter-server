# EvilHunter Tycoon Server

EvilHunter Tycoon 기반 방치형 모바일 게임 백엔드 (FastAPI).

## 요구 사항

- Python 3.10+
- SQLite (기본: `storage/evil_hunter.db`)
- (선택) Redis — rate limit 등

## 설치 및 실행

```bash
pip install -r requirements.txt
# 개발 서버
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

환경 변수:

- `SQLITE_PATH`: DB 경로 (기본: `storage/evil_hunter.db`, 테스트 시 `:memory:`)
- (선택) Admin JWT 시크릿, Google/Apple IAP 설정 등
 - (선택) `GOOGLE_CLIENT_ID`: Google OAuth client ID (audience) — 설정 시 ID 토큰의 audience 검증에 사용

## 헬스 체크

```bash
curl http://localhost:8000/health
# {"ok":true,"service":"evil-hunter-server","version":"0.1.0"}
```

## 테스트

```bash
# SQLITE_PATH 생략 시 pytest가 :memory: 사용
pytest tests/ -v
```

## 주요 API 그룹

| prefix | 설명 |
|--------|------|
| /health | 헬스 체크 |
| /monsters, /maps, /villages | 코어 CRUD |
| /hunters | 영웅 CRUD, recruit, promote, equip, tier-up |
| /offline | 오프라인 보상 preview/collect |
| /combat | 전투 fight |
| /rewards/tiers, /worldbosses, /pvp/seasons | 월드보스·PvP 카탈로그 |
| /worldboss/claim, /pvp/claim | 보상 수령 (멱등) |
| /admin | 운영자 모드 (배율) |
| /auth | 게스트/OAuth/리프레시/연동 |
| /iap | Google/Apple 결제 검증 |
| /admin/auth, /admin/tools, /admin/audit, /admin/catalog | 관리자 전용 |

## 구글 시트 연동

- **reward tier 동기화:** 시트 `월드보스_PvP` 탭의 테이블(kind, rankMin, rankMax, multiplier)을 DB에 반영  
  `python scripts/sync_reward_tiers_from_sheet.py --xlsx <xlsx 경로>`
- **진행도·API 명세:** `docs/GOOGLE_SHEET_SYNC.md` 내용을 시트에 복사하여 반영

시트 URL: https://docs.google.com/spreadsheets/d/1upkVvuiedU7Xrm37dg1gHXQaGL-C8JyL/edit?gid=174422199

## 라이선스

프로젝트 정책에 따릅니다.


## AI 유지보수 우선 문서

다음 AI 또는 다음 작업자는 아래 순서로 읽으면 됩니다.
1. `../README_FIRST.txt`
2. `ai_maintenance/PROJECT_STATE.md`
3. `ai_maintenance/ARCHITECTURE_MAP.md`
4. `ai_maintenance/UNITY_CLIENT_FLOW.md`
5. `ai_maintenance/PROMPT_TEMPLATES.md`

## 가장 쉬운 전체 점검

```bash
python scripts/run_easy_checks.py
```

위 명령은 pytest + 핵심 API 스모크 테스트 + OpenAPI 스냅샷 저장까지 한 번에 수행합니다.
결과 파일은 `reports/easy_check_report.json` 에 저장됩니다.

## Unity 연결 순서

1. `/health`
2. `/auth/guest`
3. `/hunters`
4. `/combat/fight`
5. `/offline/preview`
6. `/offline/collect`

이 순서로 붙이면 가장 빠르게 플레이 가능한 프로토타입을 만들 수 있습니다.
