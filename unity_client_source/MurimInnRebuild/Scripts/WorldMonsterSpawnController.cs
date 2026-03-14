// DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
using System.Collections.Generic;
using UnityEngine;

namespace MurimInnRebuild
{
    public sealed class WorldMonsterSpawnController : MonoBehaviour
    {
        [System.Serializable]
        public sealed class MonsterSpawnZone
        {
            public string zoneId;
            public Transform center;
            public float radius = 3f;
            public int targetCount = 4;
        }

        [SerializeField] private GameObject monsterPrefab;
        [SerializeField] private MonsterSpawnZone[] zones;
        [SerializeField] private List<GameObject> liveMonsters = new List<GameObject>();

        public void Warmup()
        {
            if (monsterPrefab == null || zones == null)
            {
                return;
            }

            foreach (MonsterSpawnZone zone in zones)
            {
                if (zone == null || zone.center == null) continue;
                for (int i = 0; i < Mathf.Max(0, zone.targetCount); i++)
                {
                    Vector2 offset2 = Random.insideUnitCircle * zone.radius;
                    Vector3 spawnPos = zone.center.position + new Vector3(offset2.x, 0f, offset2.y);
                    GameObject instance = Instantiate(monsterPrefab, spawnPos, Quaternion.identity, transform);
                    instance.name = $"{zone.zoneId}_monster_{i + 1:00}";
                    liveMonsters.Add(instance);
                }
            }
        }
    }
}
