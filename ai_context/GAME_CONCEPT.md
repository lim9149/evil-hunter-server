> DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only. See `DEV_DIRECTION_UI_LOCK_2026_03.md`.

# GAME_CONCEPT

Title:
- Working title: 무림객잔: 문파 재건기

Genre:
- Mobile idle / management RPG

Core loop:
- 객잔 운영 -> 헌터 모집 -> 사냥/귀환 -> 시설 회복 -> 전직 -> 문파 재건 반복

Story premise:
- 주인공은 몰락한 객잔 겸 문파의 마지막 장부지기다.
- 어느 날 객잔 지하 금고에서 `청심비록`과 `잔향패`를 발견하고, 무기와 방의 흔적을 읽어 과거 사건을 추적하는 재능을 얻게 된다.
- 객잔은 단순한 휴식처가 아니라 사라진 문파의 지부를 이어주는 비밀 거점이었다.
- 플레이어는 철갑/검객/신궁/도사 출신의 떠돌이 무인들을 다시 모아 문파를 재건하고, 혈야맹과 흑시회가 노리는 봉인 조각을 먼저 확보해야 한다.

Hunter rules:
- 마을 상주 헌터 최대 20명
- 생성 시 성별 50:50, 헤어 5종, 피부색 3종 랜덤
- 4대 포지션: 철갑 / 검객 / 신궁 / 도사
- 전직 흐름: 견습(내부 시작단계) -> 입문 -> 등봉 -> 화경

Village facilities:
- 주점: 허기 회복
- 숙소: 기력 회복
- 의원: 체력 회복
- 광고 신전: 플레이어가 원할 때만 선택형 보상광고를 열 수 있는 시설
- 교역 게시판: 커뮤니티 홍보 / 제휴형 보상 슬롯 확인용 시설

Visual identity:
- 화려한 FX 대신 작은 픽셀 포인트(증표)로 직업 정체성 표현
- Tier 2: 머리띠 / 견장 / 깃털 / 비녀 등
- Tier 3: 갈기 / 작은 깃발 / 눈가 문양 / 부적 등
- 마을에서 많은 헌터가 모여도 색상과 부위만으로 전직 단계를 읽을 수 있게 설계

Monetization identity:
- 사업자등록 없는 운영 전제를 우선 고려
- 수익화는 **선택형 보상광고 + 커뮤니티 홍보 슬롯 + 제휴형 이벤트 보상** 중심
- 배너 광고, 중간 강제 광고, 플레이 방해형 팝업 광고는 사용하지 않음
- 광고 보상은 유저가 직접 원할 때만 수령 가능하며, 게임 루프와 자연스럽게 연결

Important rule:
## Operator fantasy
- 플레이어는 전장의 주인공이 아니라 객잔과 문파를 다시 일으키는 운영자다.
- 헌터는 자동으로 사냥하고, 운영자는 제작/판매/교육/전직/환골탈태/수수료 정책으로 성장을 설계한다.
- 운영의 손맛은 `누구를 먼저 키울지`, `어떤 시설을 먼저 열지`, `수수료를 얼마나 걷고 얼마나 재투자할지`에서 나온다.

## Hunter state machine baseline
- ObserveNeed: HP, 허기, 기력, 장비 내구도, 가방 상태, 퀘스트 상태 확인
- ChooseIntent: 사냥 / 복귀 / 치료 / 식사 / 휴식 / 수련 / 전직 대기 / 환골탈태 준비 중 하나 선택
- ExecuteIntent: 월드에서 직접 이동하고 행동 수행
- ResolveResult: 전리품 정산, 수수료 계산, 재배치 필요 여부 판정
- ReturnToLoop: 다시 필요 체크로 복귀

## Unlock philosophy
## Backend hooks now prepared
- Hunter state machine snapshot API exists for non-UI integration and debugging.
- Patron/VIP ladder now has more granular milestone rewards so the player feels progress between large unlocks.
- Server-side numeric clamping is expanded for satiety/stamina/bag/durability/loyalty/body-reforge stage fields.
- 초반: 모집, 사냥터 지정, 회복 시설, 기초 제작
- 중반: 교육, 장비 제작/판매, 전직, 수수료 세부 설정
- 후반: 환골탈태, 고급 제련, 문파 규율, 특수 훈련
- Game must be original and not replicate Evil Hunter Tycoon content or any recent murim IP directly.
- Data-driven design and low-end mobile optimization are first priority.
- Monetization must not rely on forced interruptions.

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
