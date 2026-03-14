> DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only. See `DEV_DIRECTION_UI_LOCK_2026_03.md`.

# EvilHunter Tycoon Server

EvilHunter Tycoon 기반 방치형 모바일 게임 백엔드 (FastAPI).

## 현재 우선 구현 방향
- Unity UI가 아닌 서버 계산/데이터/안정성 영역부터 계속 보강합니다.
- 상태머신/후원 단계/운영자 TODO는 UI 없이도 테스트 가능한 API로 유지합니다.
- 스토리/튜토리얼/확률표기 조회용 엔드포인트를 포함합니다.
- 수익화는 **선택형 보상광고** 중심입니다.
- 배너 광고 / 강제 전면 광고 / 중간 삽입 광고는 프로젝트 기본안에서 제외합니다.
- 최근 무협 장르 감성은 참고하지만 스토리는 오리지널 플롯으로 유지합니다.

## 주요 추가 API
- `/hunters/{hunter_id}/state-machine`
- `/hunters/{hunter_id}/assign-hunt-zone`
- `/ads/vip-status` (누적 후원 단계 + 진행률 확장)
- `/story/chapters`
- `/tutorial/guide-quests`
- `/ads/ux-rules`
- `/compliance/probability-disclosures`
- `/compliance/lootbox-rules`

## UI 방향 추가 고정
- 기준 문서: `DEV_DIRECTION_UI_LOCK_2026_03.md`
- 앞으로의 UI/HUD/씬 설계는 세로형 TownWorld 운영형 구조를 우선한다.
- 핵심 뼈대는 `상단 자원바 + 좌측 미션 + 중앙 월드 + 우측 숏컷 + 하단 고정 메뉴`다.
- 패널은 씬 전환보다 오버레이 우선으로 설계한다.
- 참고 이미지는 감성 참고만 가능하며, 직접 복제는 금지한다.

- 운영 배포 시 JWT/HMAC 비밀키는 32바이트 이상으로 유지해 약한 키 경고를 피한다.

## 2026-03-12 추가 서버 API
- `/world/operator/summary`
- `/hunters/{hunter_id}/settle-return`
- `/world/operator/craft`
- `/world/operator/sell`
- `/hunters/{hunter_id}/train`
- `/hunters/{hunter_id}/body-reforge`

## 표준 resultCode
- 성공: `OK_SETTLED`, `OK_CRAFTED`, `OK_SOLD`, `OK_TRAINED`, `OK_REFORGED`
- 실패: `ERR_NOT_FOUND`, `ERR_INVALID_INPUT`, `ERR_NOT_ENOUGH_GOLD`, `ERR_NOT_ENOUGH_MATERIAL`, `ERR_LOW_LOYALTY`, `ERR_TRAINING_LOCKED`, `ERR_REFORGE_LIMIT`, `ERR_UNSAFE_STATE`

## 영속 저장 확장
- `operator_treasury`: 운영자 보유 골드와 운영 경험치
- `operator_inventory`: 재료/제작 아이템 재고
- `operator_action_log`: 제작/판매/교육/정산/환골탈태 로그
- `hunter_state_snapshot`: 상태머신 조회 이력


[2026-03-12 final update]
- v6에서 문서상 예고되었던 운영 랭크 12단계 축을 실제 코드/요약 응답 기준으로 재확인하고 유지했다.
- 다음 이어가기 항목도 선반영: 일일/주간 운영 미션, 레시피 확장, 전직/환골탈태의 증표/문파 규율 연동, 레시피 카탈로그 API, 성장 조건 조회 API.
- 새 API: GET /world/operator/missions, POST /world/operator/missions/claim, GET /world/operator/recipes, GET /hunters/{hunter_id}/growth-rules
