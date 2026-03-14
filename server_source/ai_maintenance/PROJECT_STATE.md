> DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only. See `DEV_DIRECTION_UI_LOCK_2026_03.md`.

현재 패키지 기준 버전: v0.4.0

핵심 반영 상태
- 방향을 `메뉴형 전투 분리`가 아니라 `TownWorld 단일 Scene` 기준으로 재정렬
- TownWorld 정의 API(`/world/definition`, `/world/snapshot`, `/world/hud`) 추가
- Unity 쪽은 `마을 하나에서 모든 것이 돌아가는 구조`를 기준으로 씬/프리팹/앵커/스폰존 설계 문서와 샘플 스크립트 보강
- 광고는 TownWorld에서 쉬는 구간/시설 상호작용 시에만 제안되도록 원칙 강화
- 유지보수 시트와 로드맵도 `객잔 운영 무협 타이쿤` 방향으로 최신화

다음 AI 작업 우선순위
## 2026-03-12 server-side additions
- Hunter state machine snapshot route added.
- Hunt-zone assignment route added.
- Patron/VIP ladder expanded to 10 milestones with lifetime claim counting.
- Expanded hunter numeric normalization for satiety/stamina/bag/durability/loyalty/reforge stage.
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


[2026-03-12 final update]
- v6에서 문서상 예고되었던 운영 랭크 12단계 축을 실제 코드/요약 응답 기준으로 재확인하고 유지했다.
- 다음 이어가기 항목도 선반영: 일일/주간 운영 미션, 레시피 확장, 전직/환골탈태의 증표/문파 규율 연동, 레시피 카탈로그 API, 성장 조건 조회 API.
- 새 API: GET /world/operator/missions, POST /world/operator/missions/claim, GET /world/operator/recipes, GET /hunters/{hunter_id}/growth-rules
