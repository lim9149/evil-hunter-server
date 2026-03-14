// DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
using UnityEngine;

namespace MurimInnRebuild
{
    [CreateAssetMenu(menuName = "MurimInn/Api Config", fileName = "ApiConfig")]
    public sealed class ApiConfig : ScriptableObject
    {
        public string baseUrl = "http://127.0.0.1:8000";
        public float timeoutSec = 10f;
        public int maxRetryCount = 2;
    }
}
