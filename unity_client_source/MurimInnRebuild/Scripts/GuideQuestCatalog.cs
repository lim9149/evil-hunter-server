// DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
using System.Collections.Generic;
using UnityEngine;

namespace MurimInnRebuild
{
    public enum GuideQuestCategory
    {
        Village = 0,
        Recruit = 1,
        Hunt = 2,
        Facility = 3,
        Gear = 4,
        Progression = 5,
        Story = 6,
        Ads = 7,
        Compliance = 8,
    }

    [System.Serializable]
    public sealed class GuideQuestData
    {
        public string questId;
        public string title;
        [TextArea(2, 4)] public string description;
        public GuideQuestCategory category;
        public bool isOptionalAdQuest;
    }

    [CreateAssetMenu(fileName = "GuideQuestCatalog", menuName = "MurimInnRebuild/Guide Quest Catalog")]
    public sealed class GuideQuestCatalogSO : ScriptableObject
    {
        public List<GuideQuestData> quests = new List<GuideQuestData>();

        public static GuideQuestCatalogSO CreateRuntimeDefault()
        {
            GuideQuestCatalogSO catalog = CreateInstance<GuideQuestCatalogSO>();
            catalog.quests = new List<GuideQuestData>
            {
                Make("guide_001", "객잔 간판 닦기", "객잔 간판을 눌러 현재 상태를 확인하세요.", GuideQuestCategory.Village, false),
                Make("guide_002", "첫 헌터 모집", "떠돌이 무인 1명을 객잔에 받아들이세요.", GuideQuestCategory.Recruit, false),
                Make("guide_003", "첫 사냥 보내기", "헌터를 사냥터로 출발시키세요.", GuideQuestCategory.Hunt, false),
                Make("guide_004", "주점 이용", "배고픈 헌터를 주점으로 보내세요.", GuideQuestCategory.Facility, false),
                Make("guide_005", "의원 이용", "다친 헌터를 의원으로 보내세요.", GuideQuestCategory.Facility, false),
                Make("guide_006", "객잔 장부 읽기", "스토리 패널에서 다음 목표를 확인하세요.", GuideQuestCategory.Story, false),
                Make("guide_007", "선택형 광고 안내", "광고 신전 설명을 읽어 보세요. 이 단계는 선택 사항입니다.", GuideQuestCategory.Ads, true),
                Make("guide_008", "확률표기 열람", "확률형 보상 표기 버튼을 눌러 비율을 확인하세요.", GuideQuestCategory.Compliance, false),
            };
            return catalog;
        }

        private static GuideQuestData Make(string id, string title, string description, GuideQuestCategory category, bool isOptional)
        {
            return new GuideQuestData
            {
                questId = id,
                title = title,
                description = description,
                category = category,
                isOptionalAdQuest = isOptional,
            };
        }
    }
}
