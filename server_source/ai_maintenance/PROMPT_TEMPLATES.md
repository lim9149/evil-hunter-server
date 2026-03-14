> DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only. See `DEV_DIRECTION_UI_LOCK_2026_03.md`.

# PROMPT TEMPLATES

## Fix bug
Read PROJECT_STATE.md and ARCHITECTURE_MAP.md first. Then run the easy checks and fix the smallest failing unit without breaking passing tests.

## Add feature
Keep the spreadsheet as reference only. Update server code and tests first, then update docs and the spreadsheet progress tabs.

## Prepare Unity integration
Generate C# models and API call examples for guest login, hunter CRUD, combat, and offline rewards using the current OpenAPI schema.

## UI 방향 추가 고정
- 기준 문서: `DEV_DIRECTION_UI_LOCK_2026_03.md`
- 앞으로의 UI/HUD/씬 설계는 세로형 TownWorld 운영형 구조를 우선한다.
- 핵심 뼈대는 `상단 자원바 + 좌측 미션 + 중앙 월드 + 우측 숏컷 + 하단 고정 메뉴`다.
- 패널은 씬 전환보다 오버레이 우선으로 설계한다.
- 참고 이미지는 감성 참고만 가능하며, 직접 복제는 금지한다.
