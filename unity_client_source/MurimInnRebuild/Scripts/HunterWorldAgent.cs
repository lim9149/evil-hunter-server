// DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
using UnityEngine;

namespace MurimInnRebuild
{
    public sealed class HunterWorldAgent : MonoBehaviour, IMovementAgent
    {
        [SerializeField] private HunterProfile profile;
        [SerializeField] private float stoppingDistance = 0.15f;

        public void Bind(HunterProfile hunterProfile)
        {
            profile = hunterProfile;
            transform.position = hunterProfile.worldPosition;
        }

        public void MoveTo(Vector3 target, float deltaTime)
        {
            if (profile == null) return;
            float safeDelta = Mathf.Max(0.01f, deltaTime);
            profile.worldPosition = Vector3.MoveTowards(profile.worldPosition, target, profile.moveSpeed * safeDelta);
            transform.position = profile.worldPosition;
        }

        public bool Reached(Vector3 point, float customStoppingDistance)
        {
            float useDistance = customStoppingDistance > 0f ? customStoppingDistance : stoppingDistance;
            return Vector3.SqrMagnitude(transform.position - point) <= useDistance * useDistance;
        }
    }
}
