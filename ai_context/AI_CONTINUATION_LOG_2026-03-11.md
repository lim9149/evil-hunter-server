# AI Continuation Log — 2026-03-11 (Autonomous Hunter Town Loop Revision)

## 이번 리비전의 핵심 방향
사용자 의도는 **헌터가 마을 안에서 AI로 자유롭게 돌아다니고, 사냥/훈련/회복/제작/무공 수련을 실시간으로 관찰할 수 있어야 한다**는 것이다.
차별화는 이 루프를 없애는 것이 아니라, **무협 객잔 운영 + 생활형 AI + 수동 개입 포인트**로 더 깊게 만드는 방향으로 진행해야 한다.

## 절대 되돌리면 안 되는 기준선
1. 헌터는 기본적으로 **자율 AI**로 행동한다.
2. 플레이어는 필요할 때만 **헌터를 눌러 명령**한다.
3. 마을은 커질 수 있으며, 카메라는 **드래그/이동**해서 넓게 보는 구조를 허용한다.
4. 건물은 마을 내부에서 **이동/재배치** 가능해야 하며, 헌터 동선은 새 위치를 반영해야 한다.
5. 마을과 사냥터는 분리된 추상 UI가 아니라 **실시간 월드 공간**에서 이어져 보여야 한다.
6. 헌터는 상태에 따라 **말풍선/짧은 대사**를 내뱉어야 한다.

## 이번에 실제 코드로 반영한 것
### Unity — 헌터 AI 확장
- `HunterState` 확장
  - `Socializing`
  - `BrowsingShop`
  - `LearningSkill`
  - `Crafting`
  - `Wandering`
- `HunterCommandType` 확장
  - `LearnSkill`
  - `Craft`
  - `ChangeClass`
- `HunterProfile` 확장
  - 자율 AI 성향값: `bravery / discipline / sociability / curiosity`
  - `autonomousBehaviorEnabled`
  - `autonomyCooldown`
  - 대사용 필드: `lastSpokenLine / speechRemaining / speechCooldown`
  - 마을 포인트: `villageCenter / patrolPoint / socialPoint / craftPoint / skillPoint`
- `HunterBrain`
  - 명령이 없을 때도 **자율 행동을 고르는 루프** 추가
  - 필요 수치(HP/Hunger/Stamina) 우선 판단
  - 자율 선택 후보: `Hunt / Train / Patrol / LearnSkill / Craft / Rest`
  - 회복 중/사냥 중/수련 중 상태별 대사 생성

### Unity — 수동 개입 유지
- `TownWorldInputFlowController`
  - 마우스 클릭으로 근처 헌터 선택 가능
  - 선택 시 카메라 포커스
- `HunterCommandConsole`
  - 기존 명령 유지
  - 추가 단축키
    - `K`: 무공 수련
    - `F`: 제작
    - `V`: 전직 준비

### Unity — 큰 마을 대응
- `TownCameraDragController.cs`
  - 우클릭 드래그/키보드 팬 이동
  - 큰 TownWorld를 스크롤하며 볼 수 있게 준비
- `TownBuildingPlacementSystem.cs`
  - 건물 루트를 격자 단위로 이동/스냅 가능
  - 시설 위치가 바뀌면 `HunterSystemManager.ResolveFacility()`가 최신 Transform 위치를 읽는다

### Unity — 시설/동선 확장
- `FacilityType` 확장
  - `TrainingHall`
  - `Forge`
  - `SkillHall`
- `HunterSystemManager`
  - 새 시설 포인트 참조 추가
  - 헌터별 마을 생활 포인트 초기화
  - 시설 위치를 매 프레임 해석 가능한 구조로 변경

### Unity — 말풍선 준비
- `HunterSpeechBubblePresenter.cs`
  - 현재는 프로토타입 디버그 바인딩용
  - 다음 AI가 TMP/TextMeshPro 말풍선 프리팹에 바로 연결하면 된다

## 현재 플레이 판타지 정의
플레이어가 해야 할 일:
- 헌터를 관찰한다
- 필요할 때 선택해서 명령한다
- 건물을 옮기고 동선을 설계한다
- 객잔 운영 효율과 헌터 생활 품질을 함께 관리한다

월드가 스스로 보여줘야 할 것:
- 사냥 출정
- 귀환
- 의원/객잔/주점 방문
- 훈련장 이용
- 무공 수련
- 제작/수리
- 순찰/산책/담소
- 상태 기반 짧은 대사

## 이블헌터타이쿤과의 차별화 포인트 (삭제 금지)
차별화는 “헌터가 안 돌아다니게 만들기”가 아니다. 유지하면서 다음을 강화한다.

1. **무협 객잔 운영 중심성**
   - 중심 시설이 객잔/무공당/의원/대장간이다.
   - 마을은 생활/수련/회복/정보 획득의 공간이다.

2. **생활형 AI**
   - 헌터가 전투만 하는 것이 아니라 담소, 산책, 제작, 수련을 한다.

3. **수동 개입 포인트**
   - 제작, 스킬 습득, 전직, 특정 의뢰 파견 시 유저가 개입한다.

4. **광고 VIP의 세계관 재해석**
   - 단순 과금 VIP보다 `객잔 명망/후원 등급/신뢰도`처럼 해석 가능하다.

5. **건물 재배치와 동선 설계**
   - 시설 간 거리가 체감 동선과 회복 효율에 영향을 준다.

## 다음 AI가 바로 이어서 할 일 (우선순위)
1. 헌터 말풍선 프리팹/TMP 바인딩
2. 건물 탭-드래그 배치 UI 연결
3. 선택된 헌터의 커맨드 플로팅 패널 UI 연결
4. 몬스터 개체와 실제 타겟팅/피격 애니메이션 연결
5. 시설별 상호작용 애니메이션 연결
6. 선택 헌터 상세 패널에 다음 항목 표기
   - 현재 상태
   - 다음 의도 행동
   - HP/Hunger/Stamina
   - Morale/Fatigue
   - 최근 대사
7. 카메라가 큰 마을에서 가장자리까지 자연스럽게 이동하도록 bounds 조정

## 다음 AI가 절대 오해하면 안 되는 문장
## 2026-03-12 추가 보강 - 운영자 중심 / 상태머신 명문화
### 새 기준선
1. 플레이어는 개별 헌터를 직접 조종하는 액션 주체가 아니라 문파 운영자다.
2. 사냥의 미시 조작(공격/스킬/루팅/복귀)은 헌터 AI가 책임진다.
3. 운영자의 핵심 재미는 제작, 판매, 교육, 전직, 환골탈태, 수수료 정책, 시설 해금 순서다.
4. 기능은 단계적으로 열린다. 처음부터 복잡하면 안 되며, 익숙해질수록 운영 항목이 늘어난다.

### 헌터 상태머신 기준
- NeedCheck: 생존/효율/장비/가방/명령 상태 확인
- IntentSelect: Hunt / Return / Rest / Eat / Heal / Train / PromoteReady / ReforgeBody 선택
- RouteMove: 지정 사냥터 또는 시설까지 이동
- PerformAction: 전투 / 회복 / 수련 / 전직 의식 / 환골탈태 의식 수행
- Settlement: 골드/재료 수집, 문파 수수료 차감, 장비 소모 반영, 다음 루프 판단
- ResumeAutonomy: 개입 종료 후 자율 루프로 복귀

### 운영자 시스템 기준
- 제작은 헌터가 자동 수행하지 못하며 운영자 승인/배정이 있어야 한다.
- 판매 가격과 제작 우선순위는 운영자가 조정한다.
- 교육과 전직/환골탈태는 개별 헌터의 성장 단계를 밀어주는 핵심 레버다.
- 문파 수수료는 헌터별 사냥 수익 비례형으로 걷고, 과도하면 충성/기분 저하 패널티가 붙는다.
- 자동전투를 없애라는 뜻이 아니다.
- 실시간 월드 루프를 유지하면서 차별화하라는 뜻이다.
- 개별 헌터를 선택해서 명령할 수 있어야 하지만, 기본은 자율 생활 AI다.
