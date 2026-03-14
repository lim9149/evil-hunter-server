// DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
using UnityEngine;

namespace MurimInnRebuild
{
    [CreateAssetMenu(menuName = "MurimInn/TownWorldDefinitionCatalog")]
    public sealed class TownWorldDefinitionCatalog : ScriptableObject
    {
        [TextArea] public string serverPath = "/world/definition";
        [TextArea] public string snapshotPath = "/world/snapshot?accountId={ACCOUNT_ID}";
        [TextArea] public string directionMemo = "TownWorldScene 단일 씬 기준. 마을 안에서 헌터 이동/전투/귀환/회복이 모두 보여야 한다.";
    }
}
