# unity_patch_village_hunter_list

## 목적
- `/hunters`가 JSON 배열로 반환될 때도 Unity에서 파싱 가능하게 수정
- 헌터 목록을 텍스트 형태로 우선 안정적으로 표시
- 헌터 생성 시 자동으로 다음 빈 슬롯을 찾아 요청

## 포함 파일
- `HunterApiDtos.cs`
- `JsonArrayHelper.cs`
- `VillageSceneController.cs`

## 적용 전 주의
- 기존 Unity 프로젝트 안에 같은 이름의 클래스가 있으면 덮어써야 합니다.
- `SessionData`는 기존 프로젝트의 클래스를 그대로 사용합니다.
- 이 패치는 사용자가 설명한 `VillageScene` 기준 UI 오브젝트를 대상으로 작성되었습니다.
