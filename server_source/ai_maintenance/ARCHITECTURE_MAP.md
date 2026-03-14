> DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only. See `DEV_DIRECTION_UI_LOCK_2026_03.md`.

# ARCHITECTURE MAP

##
## 2026-03-12 backend modules
- `core/hunter_state_machine.py`: 헌터 자율 루프 상태 계산과 운영자 TODO 도출
- `core/operator_progression.py`: 후원/명망 단계 계산, 중간 보상 단계화
- `routers/hunter.py`: 사냥터 배정, 상태머신 스냅샷 엔드포인트 추가
- `routers/ads.py`: 누적 후원 단계 및 진행률 확장 Entry
- `main.py` mounts all routers.

##
## 2026-03-12 backend modules
- `core/hunter_state_machine.py`: 헌터 자율 루프 상태 계산과 운영자 TODO 도출
- `core/operator_progression.py`: 후원/명망 단계 계산, 중간 보상 단계화
- `routers/hunter.py`: 사냥터 배정, 상태머신 스냅샷 엔드포인트 추가
- `routers/ads.py`: 누적 후원 단계 및 진행률 확장 Core rules
- `core/` contains combat, rewards, leveling, MBTI, promotion, classes, and schemas.

##
## 2026-03-12 backend modules
- `core/hunter_state_machine.py`: 헌터 자율 루프 상태 계산과 운영자 TODO 도출
- `core/operator_progression.py`: 후원/명망 단계 계산, 중간 보상 단계화
- `routers/hunter.py`: 사냥터 배정, 상태머신 스냅샷 엔드포인트 추가
- `routers/ads.py`: 누적 후원 단계 및 진행률 확장 Transport layer
- `routers/` contains API endpoints grouped by feature.

##
## 2026-03-12 backend modules
- `core/hunter_state_machine.py`: 헌터 자율 루프 상태 계산과 운영자 TODO 도출
- `core/operator_progression.py`: 후원/명망 단계 계산, 중간 보상 단계화
- `routers/hunter.py`: 사냥터 배정, 상태머신 스냅샷 엔드포인트 추가
- `routers/ads.py`: 누적 후원 단계 및 진행률 확장 Persistence
- `storage/` contains in-memory and SQLite repository logic.

##
## 2026-03-12 backend modules
- `core/hunter_state_machine.py`: 헌터 자율 루프 상태 계산과 운영자 TODO 도출
- `core/operator_progression.py`: 후원/명망 단계 계산, 중간 보상 단계화
- `routers/hunter.py`: 사냥터 배정, 상태머신 스냅샷 엔드포인트 추가
- `routers/ads.py`: 누적 후원 단계 및 진행률 확장 Quality
- `tests/` contains pytest validation and should remain green after changes.

##
## 2026-03-12 backend modules
- `core/hunter_state_machine.py`: 헌터 자율 루프 상태 계산과 운영자 TODO 도출
- `core/operator_progression.py`: 후원/명망 단계 계산, 중간 보상 단계화
- `routers/hunter.py`: 사냥터 배정, 상태머신 스냅샷 엔드포인트 추가
- `routers/ads.py`: 누적 후원 단계 및 진행률 확장 Recommended AI reading order
1. `main.py`
2. `routers/`
3. `core/`
4. `storage/`
5. `tests/`

##
## 2026-03-12 backend modules
- `core/hunter_state_machine.py`: 헌터 자율 루프 상태 계산과 운영자 TODO 도출
- `core/operator_progression.py`: 후원/명망 단계 계산, 중간 보상 단계화
- `routers/hunter.py`: 사냥터 배정, 상태머신 스냅샷 엔드포인트 추가
- `routers/ads.py`: 누적 후원 단계 및 진행률 확장 UI 방향 추가 고정
- 기준 문서: `DEV_DIRECTION_UI_LOCK_2026_03.md`
- 앞으로의 UI/HUD/씬 설계는 세로형 TownWorld 운영형 구조를 우선한다.
- 핵심 뼈대는 `상단 자원바 + 좌측 미션 + 중앙 월드 + 우측 숏컷 + 하단 고정 메뉴`다.
- 패널은 씬 전환보다 오버레이 우선으로 설계한다.
- 참고 이미지는 감성 참고만 가능하며, 직접 복제는 금지한다.
