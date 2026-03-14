> DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only. See `DEV_DIRECTION_UI_LOCK_2026_03.md`.

# MurimInnRebuild Hunter & TownWorld System

## Locked direction
- Genre: 객잔 운영 무협 타이쿤
- Camera/flow: Evil Hunter Tycoon 스타일
- Core scene: `TownWorldScene` 하나에서 모든 것이 돌아간다.
- Combat is visible in world. 별도 BattleScene을 기본 전제로 두지 않는다.

## Added scope
- Population cap: 20 resident hunters
- Random generation: gender 50:50, hair 5 variants, skin tone 3 variants
- 4 positions x 4 steps(견습 포함) = 16 job entries
- Village loop: patrol -> hunt -> check HP/Hunger/Stamina -> return -> facility recover -> redeploy
- Facility anchors: Inn / Tavern / Clinic / Forge / Training / AdShrine / CommunityBoard / StoryGate
- Monster zones live inside the same world map
- Story UI / tutorial progress / optional ad presenter / probability panel sample scripts added
- 선택형 광고는 자연스러운 구간에서만 노출되고, 전투 도중 자동 노출 금지

## New/important files
- `TownWorldDefinitionCatalog.cs`
- `TownWorldBootstrap.cs`
- `TownWorldDirector.cs`
- `TownWorldHudController.cs`
- `WorldMonsterSpawnController.cs`
- `HunterWorldAgent.cs`
- `StoryChapterCatalog.cs`
- `GuideQuestCatalog.cs`
- `OptionalAdOfferSystem.cs`
- `ProbabilityDisclosureCatalog.cs`

## Unity build order
1. TownWorldScene 생성
2. Facility anchor 빈 오브젝트 배치
3. Hunter prefab / Monster prefab 연결
4. TownWorldBootstrap에 앵커와 스폰존 연결
5. Overlay HUD 연결(스토리/우편/공지/광고 신전)
6. 실제 서버 API 연결 마감

## UI 방향 추가 고정
- 기준 문서: `DEV_DIRECTION_UI_LOCK_2026_03.md`
- 앞으로의 UI/HUD/씬 설계는 세로형 TownWorld 운영형 구조를 우선한다.
- 핵심 뼈대는 `상단 자원바 + 좌측 미션 + 중앙 월드 + 우측 숏컷 + 하단 고정 메뉴`다.
- 패널은 씬 전환보다 오버레이 우선으로 설계한다.
- 참고 이미지는 감성 참고만 가능하며, 직접 복제는 금지한다.
