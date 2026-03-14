> DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only. See `DEV_DIRECTION_UI_LOCK_2026_03.md`.

# Unity 다음 단계 - 초등학생 버전

이 게임은 버튼만 많은 메뉴형 RPG가 아니라,
마을 하나에서 헌터가 돌아다니고 몬스터를 잡는 타이쿤 게임으로 만든다.

먼저 해야 할 것
1. TownWorldScene 하나 만든다.
2. 객잔, 주점, 의원, 광고 신전, 게시판 위치를 빈 오브젝트로 찍는다.
3. 헌터 프리팹이 마을에서 사냥터로 걸어가게 만든다.
4. 몬스터가 사냥 구역에서 다시 나오게 만든다.
5. 헌터가 다치면 의원, 배고프면 주점, 피곤하면 객잔으로 돌아오게 만든다.
6. 우편함, 스토리, 광고 버튼은 화면 위 오버레이 UI로 붙인다.

중요
- 전투 화면으로 따로 넘어가지 않는다.
- 광고는 쉬는 구간에만 보여준다.
- 화면에서 헌터가 살아 움직이는 게 제일 중요하다.
