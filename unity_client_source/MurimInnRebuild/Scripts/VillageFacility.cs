// DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
using System;
using UnityEngine;

namespace MurimInnRebuild
{
    [Serializable]
    public sealed class VillageFacility
    {
        public FacilityType facilityType;
        public Vector3 worldPoint;
        public int recoverAmountPerTick = 8;
        public float useDuration = 2.5f;

        public bool CanHandle(NeedType need)
        {
            return (facilityType == FacilityType.Clinic && need == NeedType.HP)
                || (facilityType == FacilityType.Tavern && need == NeedType.Hunger)
                || (facilityType == FacilityType.Inn && need == NeedType.Stamina);
        }
    }
}
