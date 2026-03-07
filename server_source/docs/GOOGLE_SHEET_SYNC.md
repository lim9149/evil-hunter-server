# 구글 시트 동기화용 문서 (EvilHunterTycoon Server)

**문서 기준일:** 2026-03-07  
**시트 URL:** https://docs.google.com/spreadsheets/d/1upkVvuiedU7Xrm37dg1gHXQaGL-C8JyL/edit?gid=174422199

---

## 시트 직접 편집에 대해

AI는 Google 계정으로 로그인하거나 시트를 **직접** 수정할 수 없습니다. Edit 권한을 주셔도 제가 브라우저/API로 접속하는 것은 불가능합니다.  
대신 **아래 두 가지 방법**으로 반영할 수 있습니다.

1. **자동 반영 (권장):** 서비스 계정을 설정한 뒤 `scripts/update_google_sheet.py`를 실행하면 시트가 자동으로 갱신됩니다. (기존 양식 존중, 중복 방지)
2. **수동 반영:** 이 문서의 표를 복사해 해당 시트 탭에 붙여넣기합니다.

### 자동 반영 설정 (서비스 계정)

1. [Google Cloud Console](https://console.cloud.google.com/) → 프로젝트 선택 → **API 및 서비스** → **라이브러리**에서 **Google Sheets API**, **Google Drive API** 사용 설정.
2. **API 및 서비스** → **사용자 인증 정보** → **사용자 인증 정보 만들기** → **서비스 계정** 생성 후, **키** 추가 → JSON 키 파일 다운로드.
3. 해당 구글 시트에서 **공유** → 서비스 계정 이메일(예: `xxx@프로젝트.iam.gserviceaccount.com`)을 **편집자**로 추가.
4. 터미널에서 (PowerShell 예시):
   ```powershell
   python scripts/update_google_sheet.py --credentials "C:\경로\서비스계정키.json"
   ```

**"This operation is not supported for this document" (400) 에러가 나는 경우**  
문서가 **엑셀(.xlsx)을 업로드해서 연 것**일 수 있습니다. 이럴 때는 API로 편집이 안 됩니다.

- Google 시트에서 **파일 → Google 스프레드시트로 사본 저장** (또는 **사본 만들기** 후 형식을 Google 스프레드시트로 선택) 하면 **진짜 Google 스프레드시트**가 새로 만들어집니다.
- 그 **새 시트**를 서비스 계정과 **공유(편집자)** 한 뒤, 주소창에서 **새 시트 ID**를 복사합니다. (주소에서 `/d/` 다음부터 `/edit` 전까지가 ID입니다.)
- 아래처럼 **새 ID**를 넣어 실행합니다:
  ```powershell
  python scripts/update_google_sheet.py --credentials "경로\키.json" --spreadsheet-id "새시트ID"
  ```

실행 시 **프로젝트 요약본**에 버전 행이 추가되고, **진행도**, **API 명세**, **02_Server_Structure**, **DB_SCHEMA** 탭이 비어 있으면 채워지며, 이미 같은 데이터가 있으면 추가하지 않습니다.

---

아래 내용은 수동으로 복사·붙여넣기할 때 참고용입니다.

---

## 1. 진행도 (탭: 진행도)

| 구분 | 항목 | 상태 | 비고 |
|------|------|------|------|
| 서버 | FastAPI 앱 (v0.1.0) | 완료 | main.py, /health 포함 |
| 서버 | Monster/Map/Village CRUD | 완료 | GET/POST/DELETE |
| 서버 | Hunter CRUD + recruit/promote/equip/tier-up | 완료 | slot 중복 방지, MBTI 랜덤 배정 |
| 서버 | Offline preview & collect (멱등) | 완료 | offline_collect PK (hunterId, collectedAtEpoch) |
| 서버 | Combat fight | 완료 | damage/hitsToKill/totalSec |
| 서버 | WorldBoss/PvP 시즌·보스 카탈로그 | 완료 | POST/GET worldbosses, pvp/seasons |
| 서버 | WorldBoss/PvP 랭크 보상 tier (배율) | 완료 | reward_tier DB, 시트 동기화 스크립트 |
| 서버 | WorldBoss/PvP claim (멱등) | 완료 | worldboss_claim, pvp_claim PK |
| 서버 | 운영자 모드 (admin modes) | 완료 | /admin/modes, 골드/경험치 배율 |
| 서버 | Auth (게스트/리프레시/OAuth/연동) | 완료 | guest, refresh, logout, oauth, link |
| 서버 | IAP (Google/Apple 검증·재화 지급) | 완료 | /iap/google/verify, /iap/apple/verify |
| 서버 | Admin Auth/Tools/Audit/Catalog | 완료 | JWT 보호, grant/ban, audit logs, tier/mbti/items/promotion/iap-products |
| 서버 | 헬스 체크 | 완료 | GET /health |
| 서버 | Hunter 티어 상승 API | 완료 | POST /hunters/{id}/tier-up (tier_defs 기반) |
| 테스트 | pytest 15개 | 완료 | auth, refresh, combat, crud, hunter, iap, offline, worldboss_pvp |
| 시트 연동 | 월드보스_PvP → reward_tier | 완료 | sync_reward_tiers_from_sheet.py (xlsx) |
| 클라이언트 | Unity 연동 | 미진행 | API 명세 참고 |
| QA | 통합/부하 테스트 | 미진행 | |

---

## 2. API 명세 (탭: API 명세)

### 공통
- **Base URL:** (배포 주소)
- **인증(플레이어):** Bearer {access_token} (Auth 발급)
- **인증(관리자):** Bearer {admin_access_token} (Admin Auth 로그인)

### 헬스
| Method | Path | 설명 |
|--------|------|------|
| GET | /health | 서비스 상태·버전 (배포 헬스체크) |

### 코어 CRUD
| Method | Path | 설명 |
|--------|------|------|
| GET | /monsters | 몬스터 목록 |
| GET | /monsters/{id} | 몬스터 조회 |
| POST | /monsters | 몬스터 생성/수정 |
| DELETE | /monsters/{id} | 몬스터 삭제 |
| GET | /maps | 맵 목록 |
| GET | /maps/{id} | 맵 조회 |
| POST | /maps | 맵 생성/수정 |
| DELETE | /maps/{id} | 맵 삭제 |
| GET | /villages | 마을 목록 |
| GET | /villages/{id} | 마을 조회 |
| POST | /villages | 마을 생성/수정 |
| DELETE | /villages/{id} | 마을 삭제 |
| GET | /hunters?accountId= | 영웅 목록 (accountId 필터) |
| GET | /hunters/{id} | 영웅 조회 |
| POST | /hunters | 영웅 생성/수정 |
| POST | /hunters/{id}/recruit | MBTI 랜덤 배정 |
| POST | /hunters/{id}/promote | 승급 노드 적용 |
| POST | /hunters/{id}/equip | 장비 장착 |
| POST | /hunters/{id}/tier-up | 티어 상승 (T1→T2…) |
| DELETE | /hunters/{id} | 영웅 삭제 |

### 오프라인/전투
| Method | Path | 설명 |
|--------|------|------|
| POST | /offline/preview | 오프라인 보상 미리보기 |
| POST | /offline/collect | 오프라인 보상 수령 (멱등) |
| POST | /combat/fight | 전투 1회 (damage/hitsToKill 등) |

### 월드보스/PvP
| Method | Path | 설명 |
|--------|------|------|
| GET | /rewards/tiers/{kind} | 보상 tier 목록 (kind=worldboss|pvp) |
| POST | /rewards/tiers | 보상 tier UPSERT |
| POST | /worldbosses | 보스 카탈로그 UPSERT |
| GET | /worldbosses | 보스 목록 |
| POST | /pvp/seasons | 시즌 UPSERT |
| GET | /pvp/seasons | 시즌 목록 |
| POST | /worldboss/claim | 월드보스 보상 수령 (멱등) |
| POST | /pvp/claim | PvP 보상 수령 (멱등) |

### 운영자 모드
| Method | Path | 설명 |
|--------|------|------|
| GET | /admin/modes | 모드 목록 |
| GET | /admin/modes/{key} | 모드 조회 |
| POST | /admin/modes | 모드 UPSERT (multiplier 등) |

### Auth
| Method | Path | 설명 |
|--------|------|------|
| POST | /auth/guest | 게스트 로그인 |
| POST | /auth/refresh | 리프레시 토큰 갱신 |
| POST | /auth/logout | 로그아웃 |
| POST | /auth/oauth/google | Google OAuth |
| POST | /auth/oauth/apple | Apple OAuth |
| POST | /auth/link/google | Google 연동 |
| POST | /auth/link/apple | Apple 연동 |

### IAP
| Method | Path | 설명 |
|--------|------|------|
| POST | /iap/google/verify | Google 결제 검증·재화 지급 |
| POST | /iap/apple/verify | Apple 결제 검증·재화 지급 |

### Admin (관리자 토큰 필요)
| Method | Path | 설명 |
|--------|------|------|
| POST | /admin/auth/login | 관리자 로그인 |
| GET | /admin/audit/logs | 감사 로그 |
| POST | /admin/tools/grant | 재화 지급 |
| POST | /admin/tools/ban | 밴 |
| POST | /admin/tools/unban | 밴 해제 |
| GET | /admin/tools/ban/{account_id} | 밴 조회 |
| GET/POST | /admin/catalog/iap-products | IAP 상품 목록/등록 |
| GET/POST | /admin/catalog/tiers | 티어 정의 |
| GET/POST | /admin/catalog/mbti | MBTI 특성 |
| GET/POST | /admin/catalog/items | 아이템 정의 |
| GET/POST | /admin/catalog/promotions | 승급 노드 |

---

## 3. 서버 구조 (탭: 02_Server_Structure)

```
evil-hunter-server/
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
│   └── sim_*.py            # 시뮬레이션
└── tests/                  # pytest 15개
```

---

## 4. DB 스키마 요약 (탭: DB_SCHEMA)

| 테이블 | 용도 |
|--------|------|
| offline_collect | 오프라인 수령 멱등 (hunterId, collectedAtEpoch) |
| bans | 계정 밴 |
| admin_mode | 운영자 배율 키-값 |
| worldboss_claim | 월드보스 보상 멱등 (hunterId, bossId, seasonId) |
| pvp_claim | PvP 보상 멱등 (hunterId, seasonId) |
| reward_tier | 랭크 구간별 배율 (kind, rankMin, rankMax, multiplier) |
| accounts, account_identities | 계정·OAuth 연동 |
| refresh_tokens | 리프레시 토큰 |
| purchases | IAP 결제 (멱등: provider+provider_tx_id) |
| currency_ledger | 재화 입출금 (source_kind+source_id 멱등) |
| audit_logs | 감사 로그 |
| iap_products | IAP 상품 카탈로그 |
| tier_defs | 시즌별 티어 배율 |
| mbti_traits | MBTI별 스탯 배율 |
| promotion_nodes | 승급 노드 |
| item_defs | 아이템 정의 |

---

## 5. 월드보스_PvP 시트 연동 (탭: 월드보스_PvP)

- **스크립트:** `scripts/sync_reward_tiers_from_sheet.py`
- **입력:** xlsx 파일 (시트 이름 `월드보스_PvP`)
- **형식:** 헤더 `kind`(또는 종류/구분), `rankMin`(최소랭크), `rankMax`(최대랭크), `multiplier`(배율)
- **실행 예:**  
  `python scripts/sync_reward_tiers_from_sheet.py --xlsx EvilHunterTycoon_CompleteMasterTemplate_withPrompt.xlsx`  
  (옵션: `--replace`, `--kinds worldboss pvp`)
- **환경변수:** `SQLITE_PATH` (기본: storage/evil_hunter.db)

---

## 6. 버전 이력 (프로젝트 요약본 또는 진행도에 추가)

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1 | 2026-02-20 | EvilHunter Tycoon 기반 방치형 RPG 기획 (마을/영웅/장비/오프라인/PvP·월드보스/광고·현질·구독/운영자 모드/MBTI·직업/2.5D/장기 콘텐츠) |
| v0.1.0 | 2026-03-07 | 서버: 헬스 엔드포인트 추가, Hunter tier-up API 추가, 테스트 15개 통과, 구글 시트 동기화 문서 정리 |

---

이 파일을 수정한 뒤 위 시트 탭에 맞춰 복사하여 반영하시면 됩니다.

### 붙여넣기용 TSV 내보내기

```bash
python scripts/export_sheet_rows.py progress   # 진행도 탭용 (탭 구분 텍스트)
python scripts/export_sheet_rows.py api       # API 명세 탭용
python scripts/export_sheet_rows.py           # 둘 다 출력
```

출력된 텍스트를 구글 시트 셀에 붙여넣으면 열이 자동 분리됩니다.
