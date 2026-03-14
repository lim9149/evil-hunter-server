> DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only. See `DEV_DIRECTION_UI_LOCK_2026_03.md`.

AI 작업 로드맵 v0.5.0

1. TownWorldScene 기준 월드 오브젝트 배치
2. 헌터 FSM / 몬스터 스폰 / 시설 복귀 루프 연결
3. TownHUD 오버레이 연결(우편함/스토리/광고 신전/공지)
4. 서버 API와 실제 Unity 버튼/패널 바인딩
5. 소프트런치용 지표/운영툴 보강
6. 헌터 상태머신을 `NeedCheck -> IntentSelect -> Move -> PerformAction -> Settlement -> ResumeAutonomy`로 고정
7. 운영자 루프(제작/판매/교육/전직/환골탈태/수수료) UI와 데이터 테이블 연결
8. 단계 해금 순서를 초반/중반/후반으로 분리해 과밀 UI 방지
9. 후원 단계(광고/VIP 대체) 10단계 설계와 운영 보너스 밸런싱
10. 상태머신 스냅샷 로그를 경제/전직/환골탈태 판단과 연결
11. 서버 안전장치(수치 클램프/예외 케이스/누적 카운트 정확성) 강화

## UI 방향 추가 고정
- 기준 문서: `DEV_DIRECTION_UI_LOCK_2026_03.md`
- 앞으로의 UI/HUD/씬 설계는 세로형 TownWorld 운영형 구조를 우선한다.
- 핵심 뼈대는 `상단 자원바 + 좌측 미션 + 중앙 월드 + 우측 숏컷 + 하단 고정 메뉴`다.
- 패널은 씬 전환보다 오버레이 우선으로 설계한다.
- 참고 이미지는 감성 참고만 가능하며, 직접 복제는 금지한다.

## 2026-03-12 이어서 반영된 서버 로드맵 (v0.5.0)
12. 운영자 루프 API(`/world/operator/summary`, `settle-return`, `craft`, `sell`, `train`, `body-reforge`) 유지보수
13. 실패 사유 코드 표준화(`resultCode`)를 Unity/로그/QA 공용 기준으로 고정
14. SQLite에 운영 재고/운영 자금/행동 로그/상태 스냅샷 저장
15. operator log 기반 밸런스 분석과 미션 확장
16. 직업별 교육 패키지/환골탈태 조건 세분화
17. 운영 랭크와 후원 단계를 별도 축으로 병행 성장


[2026-03-12 final update]
- v6에서 문서상 예고되었던 운영 랭크 12단계 축을 실제 코드/요약 응답 기준으로 재확인하고 유지했다.
- 다음 이어가기 항목도 선반영: 일일/주간 운영 미션, 레시피 확장, 전직/환골탈태의 증표/문파 규율 연동, 레시피 카탈로그 API, 성장 조건 조회 API.
- 새 API: GET /world/operator/missions, POST /world/operator/missions/claim, GET /world/operator/recipes, GET /hunters/{hunter_id}/growth-rules
