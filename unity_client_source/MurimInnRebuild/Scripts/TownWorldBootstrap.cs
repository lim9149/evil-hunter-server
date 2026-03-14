// DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
using UnityEngine;

namespace MurimInnRebuild
{
    public sealed class TownWorldBootstrap : MonoBehaviour
    {
        [Header("Core References")]
        public HunterSystemManager hunterSystemManager;
        public WorldMonsterSpawnController monsterSpawnController;
        public TownWorldHudController hudController;

        [Header("Optional")]
        public TownWorldDefinitionCatalog worldCatalog;

        private void Start()
        {
            if (monsterSpawnController != null)
            {
                monsterSpawnController.Warmup();
            }

            if (hunterSystemManager != null)
            {
                Debug.Log("[TownWorldBootstrap] Hunter system ready for TownWorldScene.");
            }

            if (worldCatalog != null)
            {
                Debug.Log("[TownWorldBootstrap] " + worldCatalog.directionMemo);
            }
        }
    }
}
