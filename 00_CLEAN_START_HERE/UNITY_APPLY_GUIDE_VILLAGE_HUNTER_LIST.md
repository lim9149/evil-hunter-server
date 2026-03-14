# UNITY_APPLY_GUIDE_VILLAGE_HUNTER_LIST

## 이번에 Unity에서 할 일
이번에는 딱 1가지만 합니다.
- `VillageScene`에서 헌터 목록이 보이게 만들기

## 1. 어떤 코드를 사용할지
- `deliverables/unity_patch_village_hunter_list/HunterApiDtos.cs`
- `deliverables/unity_patch_village_hunter_list/JsonArrayHelper.cs`
- `deliverables/unity_patch_village_hunter_list/VillageSceneController.cs`

## 2. Unity에서 파일 넣는 위치
추천 위치:
- `Assets/Scripts/Village/`

순서:
1. Unity를 엽니다.
2. 아래 `Project` 창에서 `Assets` 클릭
3. 오른쪽 버튼 -> `Create` -> `Folder`
4. 이름을 `Scripts`
5. `Scripts` 안에서 다시 폴더 생성
6. 이름을 `Village`
7. 이 폴더 안에 위 3개 C# 파일을 넣습니다.

## 3. 기존 VillageSceneController.cs가 있다면
- 새 파일로 덮어쓰기 하거나
- 기존 파일 내용을 통째로 바꾸세요.

중요:
같은 이름의 `VillageSceneController`가 2개 있으면 에러가 납니다.

## 4. VillageScene 오브젝트 연결
필요 오브젝트:
- `AccountInfoText`
- `HunterNameInput`
- `CreateHunterButton`
- `ListHuntersButton`
- `CreateResultText`
- `HunterListText`

### 컨트롤러 오브젝트 만들기
1. `Hierarchy` 빈 곳에서 오른쪽 버튼 클릭
2. `Create Empty`
3. 이름을 `VillageSceneController` 로 변경
4. Inspector에서 `Add Component`
5. `VillageSceneController` 검색 후 추가

## 5. 인스펙터 연결
- `Account Info Text` -> `AccountInfoText` 의 TextMeshProUGUI
- `Hunter Name Input` -> `HunterNameInput` 의 TMP_InputField
- `Create Result Text` -> `CreateResultText` 의 TextMeshProUGUI
- `Hunter List Text` -> `HunterListText` 의 TextMeshProUGUI
- `Create Hunter Button` -> `CreateHunterButton` 의 Button
- `List Hunters Button` -> `ListHuntersButton` 의 Button

## 6. 버튼 OnClick 연결
### CreateHunterButton
1. `CreateHunterButton` 클릭
2. Inspector 아래 `Button (Script)` 찾기
3. `On Click ()` 에서 `+`
4. `VillageSceneController` 오브젝트 드래그
5. 드롭다운 클릭
6. `VillageSceneController -> OnCreateHunterButtonClicked()` 선택

### ListHuntersButton
1. `ListHuntersButton` 클릭
2. `On Click ()` 에서 `+`
3. `VillageSceneController` 오브젝트 드래그
4. 드롭다운 클릭
5. `VillageSceneController -> OnListHuntersButtonClicked()` 선택

## 7. 플레이 테스트 방법
1. FastAPI 서버를 켭니다.
2. Unity에서 `LoginScene`부터 실행합니다.
3. Guest Login 버튼을 누릅니다.
4. 자동으로 `VillageScene`으로 넘어갑니다.
5. 화면 위 계정 정보가 보이면 1차 성공
6. `List Hunters` 버튼 클릭
7. 아래 `HunterListText` 영역에 목록이 보이면 성공
8. 헌터가 없으면 `등록된 헌터가 없습니다.` 표시 가능
9. `HunterNameInput`에 이름 입력
10. `Create Hunter` 버튼 클릭
11. 성공 후 목록이 자동 갱신되면 성공

## 8. 자주 하는 실수
- TextMeshPro 칸에 오브젝트 자체를 넣는 실수
- 버튼 OnClick 연결 누락
- 기존 `VillageSceneController` 중복
- `SessionData.ServerUrl`, `SessionData.AccountId` 비어 있음
- 서버 주소 끝에 `/`가 여러 개 붙음

## 9. 다음 단계
- `HunterListText`를 Scroll View로 바꾸기
- 그다음 `TownWorldScene` 기초 HUD 만들기
