> DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only. See `DEV_DIRECTION_UI_LOCK_2026_03.md`.

# UNITY CLIENT FLOW

## Direction locked
이 프로젝트는 Evil Hunter Tycoon 스타일의 `TownWorld 단일 Scene`을 기준으로 개발한다.
별도 BattleScene 전환보다, 마을 안에서 헌터 이동 / 몬스터 사냥 / 귀환 / 시설 회복이 모두 보이도록 설계한다.

## Minimum playable flow
1. Guest login
2. Load TownWorld definition (`/world/definition`)
3. Spawn or fetch resident hunters
4. Spawn monster zones and facility anchors in a single TownWorldScene
5. Hunters loop automatically: patrol -> hunt -> return -> recover -> redeploy
6. At natural break only, show optional ad affordance near shrine or result overlay
7. Open story / mailbox / announcement panels as overlay UI, not hard scene switch
8. Sync tutorial progress and telemetry
9. Collect offline reward from TownHUD
10. Open probability disclosure panel from reward or draw UI

## Recommended scene order
- BootScene
- TownWorldScene
- Overlay panels only (StoryPanel, MailboxPanel, AnnouncementPanel, ProbabilityPanel)

## DTOs Unity should model first
- health response
- auth token response
- town world definition response
- town world snapshot response
- hunter create/read response
- story chapters response
- tutorial progress response
- ad session/claim response
- mailbox / announcements / economy response

## Rule
Unity should treat server as authority for progression and reward outcomes.
광고는 전투 도중 자동 재생하지 않고, 유저가 직접 선택했을 때만 서버 호출을 한다.

## UI 방향 추가 고정
- 기준 문서: `DEV_DIRECTION_UI_LOCK_2026_03.md`
- 앞으로의 UI/HUD/씬 설계는 세로형 TownWorld 운영형 구조를 우선한다.
- 핵심 뼈대는 `상단 자원바 + 좌측 미션 + 중앙 월드 + 우측 숏컷 + 하단 고정 메뉴`다.
- 패널은 씬 전환보다 오버레이 우선으로 설계한다.
- 참고 이미지는 감성 참고만 가능하며, 직접 복제는 금지한다.
