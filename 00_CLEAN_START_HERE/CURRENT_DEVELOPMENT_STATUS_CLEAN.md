# CURRENT_DEVELOPMENT_STATUS_CLEAN

## A. 이전 실제 작업 상태(사용자 Unity 진행 기준)
### 완료된 것
- Unity 프로젝트 생성
- LoginScene 생성
- VillageScene 생성
- LoginScene UI 구성 완료
- FastAPI 서버 연결 성공
- `/health` 호출 성공
- `/auth/guest` 호출 성공
- 로그인 성공 후 SessionData 저장 성공
- LoginScene -> VillageScene 이동 성공
- VillageScene에서 계정 정보 표시 성공
- Hunter 생성 API 호출 성공
- Hunter 생성 성공 응답 확인
- 같은 `accountId + slotIndex` 중복 시 `409 Conflict` 확인
- `GET /hunters` 호출 성공
- 서버 응답이 JSON 배열이라는 점 확인
- LoginScene / VillageScene 모바일 세로 배치 1차 완료

### 아직 막힌 것
- Unity 쪽 Hunter 목록 JSON 배열 파싱 실패
- Hunter 목록 UI가 정상 표시되지 않음

## B. 최신 패키지 기준 큰 방향
- 메인 방향은 `TownWorldScene` 단일 Scene 중심
- UI는 오버레이 패널 중심
- 플레이어 역할은 운영자
- 헌터는 자율 AI
- 서버는 운영자 루프와 상태머신 판정을 담당
- Unity는 월드 표현과 UX를 담당

## C. 개발 전략
1. 지금 막힌 `VillageScene` 목록 출력 문제를 먼저 해결
2. VillageScene을 완성형으로 키우지 않기
3. 다음부터는 `TownWorldScene` 구조로 옮겨가기

## D. 이번 정리본 코드 패치
- `deliverables/unity_patch_village_hunter_list/HunterApiDtos.cs`
- `deliverables/unity_patch_village_hunter_list/JsonArrayHelper.cs`
- `deliverables/unity_patch_village_hunter_list/VillageSceneController.cs`

목적:
- 서버의 JSON 배열 응답을 안전하게 파싱
- Hunter 목록을 줄바꿈 텍스트로 우선 표시
- 다음 단계 Scroll View 전환 전까지 가장 작은 성공 단위 확보

## E. 주의
이 패치는 사용자가 설명한 기존 Scene/오브젝트 이름을 기준으로 만들었습니다.
실제 Unity 프로젝트 파일 전체는 이 ZIP 안에 없으므로, 인스펙터 연결은 사용자가 직접 해야 합니다.
