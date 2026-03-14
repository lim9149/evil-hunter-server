# MASTER_PROJECT_INDEX

## 1. 지금 이 패키지의 진짜 기준 문서
가장 먼저 아래 5개만 보면 됩니다.

1. `DEV_DIRECTION_UI_LOCK_2026_03.md`
2. `PROJECT_STATE.md`
3. `AI_TASK_ROADMAP.md`
4. `ai_context/GAME_CONCEPT.md`
5. `design_sheet/PROJECT_CLEAN_MASTER_SUMMARY.xlsx`

## 2. 현재 프로젝트 핵심 방향
- 장르: 무림 문파 운영 + 자율 헌터 육성
- 화면 구조: 세로형 TownWorld 단일 Scene 중심
- UI 원칙: 오버레이 패널 우선, 하단 고정 메뉴, 상단 자원바
- 플레이어 역할: 헌터 직접 조작자가 아니라 문파 운영자
- 헌터 행동: 기본은 자율 AI, 필요 시 직접 명령 오버레이
- 월드 구조: 문파와 주변 사냥권역이 함께 있는 확장형 허브

## 3. 지금 당장 Unity에서 먼저 해야 하는 1단계
현재 사용자의 실제 Unity 진행 상태 기준으로 제일 먼저 해야 하는 일은 아래입니다.

- `VillageScene`에서 `GET /hunters` JSON 배열 파싱 수정
- 헌터 목록이 `HunterListText`에 정상 출력되게 만들기

이 단계는 현재 막힌 부분을 가장 작게 해결하는 작업입니다.
이걸 먼저 끝낸 뒤, 다음부터는 `TownWorldScene` 중심 구조로 옮겨가면 됩니다.

## 4. 패키지 안에서 헷갈릴 수 있는 자료 정리
### 지금 기준으로 살아 있는 자료
- `PROJECT_STATE.md`
- `AI_TASK_ROADMAP.md`
- `ai_context/GAME_CONCEPT.md`
- `DEV_DIRECTION_UI_LOCK_2026_03.md`
- `design_sheet/EHT_AI_Maintenance_Master.xlsx`

### 참고용으로만 봐야 하는 자료
- `design_sheet/EvilHunterTycoon_complete_reference_master.xlsx`
  - 직접 복제용이 아니라 참고용입니다.
  - 구조, 감성, 루프 참고만 허용됩니다.
  - 코드, 데이터, UI, 이름, 밸런스 복제는 금지입니다.

### 이번 정리본에서 추가한 자료
- `00_CLEAN_START_HERE/CURRENT_DEVELOPMENT_STATUS_CLEAN.md`
- `00_CLEAN_START_HERE/UNITY_APPLY_GUIDE_VILLAGE_HUNTER_LIST.md`
- `design_sheet/PROJECT_CLEAN_MASTER_SUMMARY.xlsx`
- `deliverables/unity_patch_village_hunter_list/`

## 5. 추천 작업 순서
1. `CURRENT_DEVELOPMENT_STATUS_CLEAN.md` 읽기
2. `deliverables/unity_patch_village_hunter_list/` 안의 코드 확인
3. `UNITY_APPLY_GUIDE_VILLAGE_HUNTER_LIST.md`대로 Unity에 적용
4. 테스트 결과를 다시 AI에게 전달
5. 그다음 `TownWorldScene` 초기 골격 단계로 이동
