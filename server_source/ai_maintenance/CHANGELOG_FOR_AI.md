> DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only. See `DEV_DIRECTION_UI_LOCK_2026_03.md`.

# CHANGELOG FOR AI

## 2026-03-07
## 2026-03-12
- Added `core/hunter_state_machine.py`
- Added `core/operator_progression.py`
- Extended `/ads/vip-status` to use lifetime claims and richer milestone preview
- Added `/hunters/{hunter_id}/assign-hunt-zone` and `/hunters/{hunter_id}/state-machine`
- Added tests for state machine and patron progression
- Added AI maintainer package docs.
- Added one-command easy check script and reports output.
- Added OpenAPI export helper.
- Added AI-focused spreadsheet tabs for continuity.

## UI 방향 추가 고정
- 기준 문서: `DEV_DIRECTION_UI_LOCK_2026_03.md`
- 앞으로의 UI/HUD/씬 설계는 세로형 TownWorld 운영형 구조를 우선한다.
- 핵심 뼈대는 `상단 자원바 + 좌측 미션 + 중앙 월드 + 우측 숏컷 + 하단 고정 메뉴`다.
- 패널은 씬 전환보다 오버레이 우선으로 설계한다.
- 참고 이미지는 감성 참고만 가능하며, 직접 복제는 금지한다.
