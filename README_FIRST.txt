[DEV-DIRECTION-LOCK] Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.

이 패키지는 무림객잔 프로젝트의 최신 AI 유지보수 패키지입니다.

이번 업데이트 핵심
1) 광고는 강제 노출 없이 서버 세션 검증형 선택형 광고만 유지
2) 운영 도구(공지/우편/계정 요약) 추가
3) Apple 로그인 stub 제거
4) 테스트 25개 통과

권장 순서
- server_source/PROJECT_STATE.md 확인
- design_sheet의 진행도 / API 명세 / DB_SCHEMA / 개발_연속성부터 확인
- Unity는 OptionalAdOfferPresenter / TutorialProgressTracker / StoryPanelView / ProbabilityDisclosurePanel 순서로 연결

[개발 방향 고정 안내]
- 최우선 방향 문서: DEV_DIRECTION_UI_LOCK_2026_03.md
- UI 방향: 세로형 픽셀 TownWorld / 상단 자원바 / 좌측 미션 / 우측 숏컷 / 하단 고정 메뉴
- 구현 원칙: 마을 단일 Scene + 오버레이 UI + 월드 안에서 보이는 사냥/귀환 루프
- 주의: 참고 감성은 허용하지만 직접 복제는 금지


2026-03-12 추가: 플레이어 역할은 헌터 직접 조작이 아니라 문파 운영자이며, 헌터 상태머신/운영자 루프 기준은 PROJECT_STATE.md 와 ai_context/GAME_CONCEPT.md 를 우선 확인.

2026-03-12 추가 2:
- 이번 패키지부터 `귀환 정산 / 제작 / 판매 / 교육 / 환골탈태` 서버 루프가 실제 API로 반영됨
- 실패 사유는 `ERR_NOT_ENOUGH_GOLD`, `ERR_LOW_LOYALTY`, `ERR_TRAINING_LOCKED` 등 표준 코드로 반환
- SQLite에 `operator_treasury`, `operator_inventory`, `operator_action_log`, `hunter_state_snapshot` 테이블 추가
- 다음 연속 개발은 Unity UI가 아니라도 `/world/operator/summary` 와 액션 로그를 기준으로 이어갈 수 있음


[2026-03-12 final update]
- v6에서 문서상 예고되었던 운영 랭크 12단계 축을 실제 코드/요약 응답 기준으로 재확인하고 유지했다.
- 다음 이어가기 항목도 선반영: 일일/주간 운영 미션, 레시피 확장, 전직/환골탈태의 증표/문파 규율 연동, 레시피 카탈로그 API, 성장 조건 조회 API.
- 새 API: GET /world/operator/missions, POST /world/operator/missions/claim, GET /world/operator/recipes, GET /hunters/{hunter_id}/growth-rules
