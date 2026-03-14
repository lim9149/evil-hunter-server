# 11. AI 연속개발 핵심현황 — 자율 헌터 AI / 무협 차별화 / 직접 명령 공존

## 현재 개발 기준선
- 세로형 모바일
- 심시티식 대각선 하늘 시점
- TownWorld 단일 씬 중심
- 헌터는 마을과 사냥터를 실제로 오간다
- 플레이어는 헌터를 선택하고 직접 개입할 수 있다

## 현재 살아 있는 핵심 시스템
### 관찰 재미
- 헌터가 자율적으로 행동을 고른다
- 다른 헌터는 다른 루틴을 가진다
- 사냥/훈련/순찰/회복이 월드에서 보인다

### 개입 재미
- 특정 헌터를 선택
- 직접 사냥/훈련/휴식/치료/순찰/귀환 지시
- 명령 종료 후 자율 루프로 복귀

### 수익화 방향
- 광고 누적 기반 VIP 유지 가능
- 단, 세계관 명칭은 후원/명망/객잔 명성 등으로 치환 가능

## 현재 코드 기준 파일
### Unity
- `HunterProfile.cs`
- `HunterBrain.cs`
- `HunterSystemManager.cs`
- `HunterTrafficCoordinator.cs`
- `TownWorldInputFlowController.cs`
- `HunterCommandConsole.cs`

### Server
- `routers/hunter.py`
- `core/hunter_ai.py`
- `core/hunter_operations.py`
- `core/economy.py`
- `core/schemas.py`

## 절대 바꾸면 안 되는 해석
- 차별화 = 헌터 AI 제거  (X)
- 차별화 = 헌터 AI 유지 + 무협풍 개성/생활/훈련/풍문/기강 강화  (O)

## 추천 다음 구현
## 2026-03-12 상태머신 기준선
- NeedCheck
- IntentSelect
- MoveToTarget
- Combat / FacilityAction / TrainingAction / PromotionRite
- Settlement
- ResumeAutonomy

## 운영자 개입 포인트
- 사냥터 지정
- 장비/물약 제작 및 판매
- 교육 배정
- 전직 승인
- 환골탈태 자원 투입
- 수수료 정책 조정
- 시설별 대기열 UI
- 헌터별 친분/문파성향/평판
- 게시판 의뢰 난이도와 귀환 리포트
- AI 루틴 로그 패널
- 마을이 혼잡할 때 다른 루트를 선택하는 시각 연출
