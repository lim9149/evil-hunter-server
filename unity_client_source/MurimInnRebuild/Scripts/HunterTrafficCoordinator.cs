using System.Collections.Generic;
using UnityEngine;

namespace MurimInnRebuild
{
    public sealed class HunterTrafficCoordinator
    {
        private readonly Dictionary<FacilityType, int> facilityUsage = new Dictionary<FacilityType, int>();
        private readonly List<Vector3> huntLaneOffsets = new List<Vector3>
        {
            new Vector3(-0.80f, 0f, -0.35f),
            new Vector3(-0.20f, 0f, -0.15f),
            new Vector3(0.35f, 0f, 0.10f),
            new Vector3(0.78f, 0f, 0.32f),
            new Vector3(-0.58f, 0f, 0.48f),
            new Vector3(0.10f, 0f, 0.55f),
        };

        public Vector3 ReserveHuntLane(int hunterIndex)
        {
            if (hunterIndex < 0) hunterIndex = 0;
            return huntLaneOffsets[hunterIndex % huntLaneOffsets.Count];
        }

        public Vector3 ReserveFacilitySlot(FacilityType facilityType, Vector3 origin)
        {
            facilityUsage.TryGetValue(facilityType, out int count);
            facilityUsage[facilityType] = count + 1;
            int ring = count / 4;
            float angle = (count % 4) * Mathf.PI * 0.5f + (ring * 0.23f);
            float radius = 0.35f + (ring * 0.22f);
            return origin + new Vector3(Mathf.Cos(angle), 0f, Mathf.Sin(angle)) * radius;
        }

        public Vector3 ReservePatrolPoint(Vector3 center, int hunterIndex, float radius)
        {
            float safeRadius = Mathf.Max(0.8f, radius);
            float angle = (hunterIndex % 8) * 0.7853982f;
            return center + new Vector3(Mathf.Cos(angle), 0f, Mathf.Sin(angle)) * safeRadius;
        }

        public void ReleaseFacilitySlot(FacilityType facilityType)
        {
            if (!facilityUsage.TryGetValue(facilityType, out int count)) return;
            facilityUsage[facilityType] = Mathf.Max(0, count - 1);
        }

        public float GetCongestionPenalty(FacilityType facilityType)
        {
            facilityUsage.TryGetValue(facilityType, out int count);
            return Mathf.Clamp01(count * 0.08f);
        }
    }
}
