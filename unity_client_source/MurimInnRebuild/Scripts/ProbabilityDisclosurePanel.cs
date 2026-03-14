// DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
using UnityEngine;

namespace MurimInnRebuild
{
    public sealed class ProbabilityDisclosurePanel : MonoBehaviour
    {
        public ProbabilityDisclosureCatalogSO disclosureCatalog;

        public string BuildDisclosureText()
        {
            if (disclosureCatalog == null || disclosureCatalog.tables.Count == 0)
            {
                return "확률표기 데이터가 없습니다.";
            }

            ProbabilityDisclosureTable table = disclosureCatalog.tables[0];
            string text = $"{table.displayName} ({table.lastUpdated})";
            for (int i = 0; i < table.entries.Count; i++)
            {
                ProbabilityDisclosureEntry entry = table.entries[i];
                text += $"\n- {entry.itemName}: {entry.probabilityPercent:0.##}%";
            }

            text += $"\n합계: {table.GetTotalProbability():0.##}%";
            return text;
        }
    }
}
