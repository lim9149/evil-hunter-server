> DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only. See `DEV_DIRECTION_UI_LOCK_2026_03.md`.

현재 패키지 기준 버전: v0.5.0

핵심 반영 상태
- 방향을 `메뉴형 전투 분리`가 아니라 `TownWorld 단일 Scene` 기준으로 재정렬
- TownWorld 정의 API(`/world/definition`, `/world/snapshot`, `/world/hud`) 추가
- Unity 쪽은 `마을 하나에서 모든 것이 돌아가는 구조`를 기준으로 씬/프리팹/앵커/스폰존 설계 문서와 샘플 스크립트 보강
- 광고는 TownWorld에서 쉬는 구간/시설 상호작용 시에만 제안되도록 원칙 강화
- 유지보수 시트와 로드맵도 `객잔 운영 무협 타이쿤` 방향으로 최신화

다음 AI 작업 우선순위
1. Unity TownWorld 씬에서 실제 프리팹/애니메이션/Collider/NavMesh 연결
2. 헌터/몬스터 실제 피격 연출과 드롭 연출 연결
3. TownHUD/Facility 패널을 실제 버튼과 연결하고 모바일 해상도 대응
4. 소프트런치 지표(잔존/광고선택률/튜토리얼완료율/귀환율) 수집 강화

방향 고정 원칙
- 씬은 가능한 한 `TownWorldScene` 하나를 중심으로 운용한다.
- 전투, 회복, 광고, 우편, 스토리 진입은 모두 마을 흐름을 끊지 않는 선에서 오버레이 UI로 처리한다.
- 서버는 보상/진행 판정을 담당하고 Unity는 월드 표현과 UX를 담당한다.

## UI 방향 추가 고정
- 기준 문서: `DEV_DIRECTION_UI_LOCK_2026_03.md`
- 앞으로의 UI/HUD/씬 설계는 세로형 TownWorld 운영형 구조를 우선한다.
- 핵심 뼈대는 `상단 자원바 + 좌측 미션 + 중앙 월드 + 우측 숏컷 + 하단 고정 메뉴`다.
- 패널은 씬 전환보다 오버레이 우선으로 설계한다.
- 참고 이미지는 감성 참고만 가능하며, 직접 복제는 금지한다.


## 2026-03-11 direction correction (highest priority)
- Prior temporary drift toward "manual-only command game" is superseded.
- Correct direction: autonomous hunter life-sim stays alive, with direct orders layered on top.
- Differentiation target is not removing hunter roaming; it is making roaming more murim-specific and more personality-driven.
- Future AI should treat current baseline as: "living town + living hunters + direct command override + murim originality."


## 2026-03-11 추가 기준선
## 2026-03-12 운영자 중심 방향 보강
## 2026-03-12 서버 구현 추가
- Unity UI가 아니라도 이어서 개발할 수 있도록 서버 쪽 상태머신 계산 로직을 추가했다.
- 신규 백엔드 기준: `core/hunter_state_machine.py`, `core/operator_progression.py`
- `/hunters/{hunter_id}/state-machine` 엔드포인트로 현재 상태/다음 상태/운영자 TODO를 확인할 수 있다.
- `/hunters/{hunter_id}/assign-hunt-zone` 엔드포인트로 사냥터 지정과 루프 횟수를 서버에 반영한다.
- `/ads/vip-status`는 이제 일일 카운트가 아니라 누적 광고 보상 수령 기록 기반의 다단계 후원/명망 단계로 계산된다.
- 중간 성장 체감을 늘리기 위해 후원 단계는 10단계로 확장했고, 각 단계에 작은 보너스를 붙였다.
- 입력 정규화/클램프 범위를 늘려 상태 수치가 깨지지 않도록 안정성을 보강했다.
- 플레이어의 기본 역할은 `헌터 1인 조작`이 아니라 `문파/마을 운영자`다.
- 플레이어는 사냥터만 지정하고, 전투/스킬/타깃 전환/루팅/귀환 판단은 헌터 AI가 수행한다.
- 플레이어의 주된 개입은 제작, 판매, 교육, 전직, 환골탈태, 시설 운영, 수수료율 조정, 해금 순서 설계다.
- 문파 수수료는 `고정 세금`보다 `헌터별 사냥 수익 비례`가 기준선이다. 초반 8%, 중반 12%, 후반 15% 안에서 해금/시설 효과로 조정한다.
- 신규 기능은 한 번에 전부 열지 않고 `운영 메뉴 -> 교육 -> 전직 -> 환골탈태 -> 특수 운영규율` 순서로 단계 해금한다.
- 헌터 상태머신은 `NeedCheck -> IntentSelect -> MoveToTarget -> PerformAction -> Settlement -> ResumeAutonomy`의 반복 구조를 기본으로 한다.
- 헌터는 기본적으로 자율 AI로 생활/사냥/회복/수련/제작을 반복한다.
- 플레이어는 필요 시 개별 헌터를 선택해 직접 명령한다.
- 건물 재배치와 카메라 이동을 전제로 큰 TownWorld를 허용한다.
- 차별화는 월드 루프 제거가 아니라 `무협 객잔 운영 + 생활형 AI` 강화다.

- 운영 배포 시 JWT/HMAC 비밀키는 32바이트 이상으로 유지해 약한 키 경고를 피한다.

## 2026-03-12 서버 구현 추가 2 (v0.5.0)
- 기준 버전을 `v0.5.0`으로 상향했다.
- 서버에 운영자 루프 API를 실제 추가했다.
  - `GET /world/operator/summary`
  - `POST /hunters/{hunter_id}/settle-return`
  - `POST /world/operator/craft`
  - `POST /world/operator/sell`
  - `POST /hunters/{hunter_id}/train`
  - `POST /hunters/{hunter_id}/body-reforge`
- 단순 성공/실패 문자열 대신 `resultCode` 기반 표준 응답을 추가했다.
  - 예: `OK_SETTLED`, `OK_CRAFTED`, `OK_SOLD`, `OK_TRAINED`, `OK_REFORGED`
  - 예: `ERR_NOT_ENOUGH_GOLD`, `ERR_NOT_ENOUGH_MATERIAL`, `ERR_LOW_LOYALTY`, `ERR_TRAINING_LOCKED`
- SQLite에 운영 지속개발용 저장 구조를 확장했다.
  - `operator_treasury`: 운영자 골드/운영 경험치
  - `operator_inventory`: 재료/제작품 재고
  - `operator_action_log`: 정산/제작/판매/교육/환골탈태 로그
  - `hunter_state_snapshot`: 상태머신 스냅샷 이력
- 헌터 엔티티에 `insight`, `safetyStockPreference`, `lastFailureCode`, `lastFailureDetail`를 추가했다.
- 이제 다음 AI는 UI 없이도 서버 응답/로그/DB 기준으로 운영 루프를 이어서 개발할 수 있다.

다음 AI 작업 우선순위(서버 중심 재정렬)
1. operator_action_log 를 기반으로 일일/주간 운영 퀘스트와 LiveOps 미션 추가
2. 재료 소비처와 제작 레시피 수를 늘려 중반 루프 밀도 강화
3. 전직 조건과 body-reforge 조건을 직업/증표/문파 규율과 연결
4. SQLite 저장 구조를 실제 배포용 repo abstraction 으로 확장
5. Unity는 UI 표현만 하고 서버 resultCode 를 그대로 바인딩하도록 유지


[2026-03-12 final update]
- v6에서 문서상 예고되었던 운영 랭크 12단계 축을 실제 코드/요약 응답 기준으로 재확인하고 유지했다.
- 다음 이어가기 항목도 선반영: 일일/주간 운영 미션, 레시피 확장, 전직/환골탈태의 증표/문파 규율 연동, 레시피 카탈로그 API, 성장 조건 조회 API.
- 새 API: GET /world/operator/missions, POST /world/operator/missions/claim, GET /world/operator/recipes, GET /hunters/{hunter_id}/growth-rules
