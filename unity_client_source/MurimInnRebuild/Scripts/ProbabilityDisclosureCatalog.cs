// DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
using System.Collections.Generic;
using UnityEngine;

namespace MurimInnRebuild
{
    [System.Serializable]
    public sealed class ProbabilityDisclosureEntry
    {
        public string itemId;
        public string itemName;
        [Range(0f, 100f)] public float probabilityPercent;
    }

    [System.Serializable]
    public sealed class ProbabilityDisclosureTable
    {
        public string tableId;
        public string displayName;
        public bool isPaid;
        public string lastUpdated;
        public List<ProbabilityDisclosureEntry> entries = new List<ProbabilityDisclosureEntry>();

        public float GetTotalProbability()
        {
            float total = 0f;
            for (int i = 0; i < entries.Count; i++)
            {
                total += entries[i].probabilityPercent;
            }
            return total;
        }
    }

    [CreateAssetMenu(fileName = "ProbabilityDisclosureCatalog", menuName = "MurimInnRebuild/Probability Disclosure Catalog")]
    public sealed class ProbabilityDisclosureCatalogSO : ScriptableObject
    {
        public List<ProbabilityDisclosureTable> tables = new List<ProbabilityDisclosureTable>();

        public static ProbabilityDisclosureCatalogSO CreateRuntimeDefault()
        {
            ProbabilityDisclosureCatalogSO catalog = CreateInstance<ProbabilityDisclosureCatalogSO>();
            catalog.tables = new List<ProbabilityDisclosureTable>
            {
                new ProbabilityDisclosureTable
                {
                    tableId = "ad_chest_common",
                    displayName = "광고 보물상자 - 일반",
                    isPaid = false,
                    lastUpdated = "2026-03-10",
                    entries = new List<ProbabilityDisclosureEntry>
                    {
                        new ProbabilityDisclosureEntry { itemId = "gold_small", itemName = "소량 골드", probabilityPercent = 60f },
                        new ProbabilityDisclosureEntry { itemId = "exp_note", itemName = "수련 비급 조각", probabilityPercent = 25f },
                        new ProbabilityDisclosureEntry { itemId = "repair_kit", itemName = "수리 도구", probabilityPercent = 10f },
                        new ProbabilityDisclosureEntry { itemId = "rare_mat", itemName = "희귀 제작 재료", probabilityPercent = 4f },
                        new ProbabilityDisclosureEntry { itemId = "hero_talisman", itemName = "문파 부적", probabilityPercent = 1f },
                    },
                },
            };
            return catalog;
        }
    }
}
