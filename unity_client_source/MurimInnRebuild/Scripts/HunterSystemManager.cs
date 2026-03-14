// DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
using System.Collections.Generic;
using UnityEngine;

namespace MurimInnRebuild
{
    public sealed class HunterSystemManager : MonoBehaviour
    {
        [Header("Data")]
        public JobDatabaseSO jobDatabase;

        [Header("Spawn")]
        public string accountId = "guest";
        public int initialHunterCount = 8;
        public Transform villageSpawnPoint;
        public Transform huntPoint;
        public Transform villageCenterPoint;
        public Transform patrolPoint;
        public Transform socialPoint;
        public Transform craftPoint;
        public Transform skillPoint;

        [Header("Facilities")]
        public Transform tavernPoint;
        public Transform innPoint;
        public Transform clinicPoint;
        public Transform adShrinePoint;
        public Transform communityBoardPoint;
        public Transform trainingHallPoint;
        public Transform forgePoint;
        public Transform skillHallPoint;

        [Header("Optimization")]
        [Tooltip("매 프레임 20명을 전부 돌지 않고, 분산 처리합니다.")]
        [Range(1, HunterProfile.MaxPopulation)]
        public int maxAgentsPerFrame = 5;
        [Range(0.1f, 1.5f)]
        public float thinkIntervalSeconds = 0.5f;

        private readonly List<HunterProfile> hunters = new List<HunterProfile>(HunterProfile.MaxPopulation);
        private readonly List<HunterBrain> brains = new List<HunterBrain>(HunterProfile.MaxPopulation);
        private readonly Dictionary<FacilityType, VillageFacility> facilities = new Dictionary<FacilityType, VillageFacility>();
        private readonly System.Random random = new System.Random();
        private readonly HunterTrafficCoordinator trafficCoordinator = new HunterTrafficCoordinator();
        private int roundRobinIndex;

        public IReadOnlyList<HunterProfile> Hunters => hunters;
        public int SelectedHunterIndex { get; private set; } = -1;

        private void Awake()
        {
            if (jobDatabase == null)
            {
                jobDatabase = JobDatabaseSO.CreateRuntimeDefault();
            }
            else
            {
                jobDatabase.BuildLookup();
            }

            BuildFacilities();

            int spawnCount = Mathf.Clamp(initialHunterCount, 0, HunterProfile.MaxPopulation);
            for (int i = 0; i < spawnCount; i++)
            {
                RecruitRandomHunter($"hunter_{i + 1:00}");
            }
        }

        private void Update()
        {
            if (brains.Count == 0)
            {
                return;
            }

            int tickCount = Mathf.Min(maxAgentsPerFrame, brains.Count);
            float delta = Time.deltaTime;
            for (int i = 0; i < tickCount; i++)
            {
                if (roundRobinIndex >= brains.Count)
                {
                    roundRobinIndex = 0;
                }

                brains[roundRobinIndex].Tick(delta);
                roundRobinIndex++;
            }
        }

        public bool RecruitRandomHunter(string hunterId)
        {
            if (hunters.Count >= HunterProfile.MaxPopulation)
            {
                return false;
            }

            HunterPosition lane = (HunterPosition)(hunters.Count % 4);
            string jobId = lane switch
            {
                HunterPosition.Tanker => "tank_apprentice",
                HunterPosition.Dealer => "dealer_apprentice",
                HunterPosition.Ranger => "ranger_apprentice",
                _ => "support_apprentice",
            };

            JobData startJob = jobDatabase.Get(jobId);
            Vector3 spawn = GetPoint(villageSpawnPoint);
            Vector3 hunt = GetPoint(huntPoint);
            HunterProfile profile = HunterProfile.CreateRandom(hunterId, accountId, $"헌터 {hunters.Count + 1}", startJob, spawn, random);
            profile.huntPoint = hunt;
            profile.villageCenter = GetPoint(villageCenterPoint, spawn);
            profile.patrolPoint = GetPoint(patrolPoint, profile.villageCenter + new Vector3(1.6f, 0f, -1.2f));
            profile.socialPoint = GetPoint(socialPoint, profile.villageCenter + new Vector3(-1.2f, 0f, 1.2f));
            profile.craftPoint = GetPoint(craftPoint, profile.villageCenter + new Vector3(2.3f, 0f, 0.6f));
            profile.skillPoint = GetPoint(skillPoint, profile.villageCenter + new Vector3(-2.2f, 0f, 0.4f));
            profile.operationStyle = (HunterOperationStyle)(hunters.Count % 4);
            profile.restDiscipline = (HunterRestDiscipline)(hunters.Count % 3);
            profile.trainingFocus = (HunterTrainingFocus)((hunters.Count + 1) % 4);
            profile.bondedFacilityId = profile.restDiscipline == HunterRestDiscipline.Lavish ? "clinic_spring" : "inn_main";
            profile.laneOffset = trafficCoordinator.ReserveHuntLane(hunters.Count);
            profile.ApplyOperationBiases();
            hunters.Add(profile);

            IMovementAgent movementAgent = new LightweightMovementAgent(profile);
            HunterBrain brain = new HunterBrain(profile, jobDatabase, ResolveFacility, movementAgent, trafficCoordinator, thinkIntervalSeconds);
            brains.Add(brain);
            return true;
        }

        public bool IssueCommandToHunter(string hunterId, HunterCommandType command, int targetMonsterCount = 3)
        {
            for (int i = 0; i < hunters.Count; i++)
            {
                if (hunters[i].hunterId == hunterId)
                {
                    hunters[i].IssueCommand(command, targetMonsterCount);
                    return true;
                }
            }
            return false;
        }

        public HunterProfile SelectNextHunter()
        {
            if (hunters.Count == 0)
            {
                SelectedHunterIndex = -1;
                return null;
            }

            if (SelectedHunterIndex >= 0 && SelectedHunterIndex < hunters.Count)
            {
                hunters[SelectedHunterIndex].isSelected = false;
                if (hunters[SelectedHunterIndex].state == HunterState.Selected)
                {
                    hunters[SelectedHunterIndex].state = HunterState.AwaitingCommand;
                }
            }

            SelectedHunterIndex = (SelectedHunterIndex + 1) % hunters.Count;
            return SelectHunterByIndex(SelectedHunterIndex);
        }

        public HunterProfile SelectHunterByIndex(int index)
        {
            if (index < 0 || index >= hunters.Count)
            {
                return null;
            }

            for (int i = 0; i < hunters.Count; i++)
            {
                hunters[i].isSelected = i == index;
                if (!hunters[i].isSelected && hunters[i].state == HunterState.Selected)
                {
                    hunters[i].state = HunterState.AwaitingCommand;
                }
            }

            SelectedHunterIndex = index;
            HunterProfile selected = hunters[index];
            selected.isSelected = true;
            if (selected.state == HunterState.AwaitingCommand || selected.state == HunterState.Idle)
            {
                selected.state = HunterState.Selected;
                selected.uiStateLabel = "선택됨";
            }
            return selected;
        }

        public HunterProfile SelectNearestHunter(Vector3 worldPoint, float maxDistance = 1.25f)
        {
            float bestSqr = maxDistance * maxDistance;
            int bestIndex = -1;
            for (int i = 0; i < hunters.Count; i++)
            {
                float sqr = Vector3.SqrMagnitude(hunters[i].worldPosition - worldPoint);
                if (sqr < bestSqr)
                {
                    bestSqr = sqr;
                    bestIndex = i;
                }
            }
            return bestIndex >= 0 ? SelectHunterByIndex(bestIndex) : null;
        }

        public HunterProfile GetSelectedHunter()
        {
            if (SelectedHunterIndex < 0 || SelectedHunterIndex >= hunters.Count)
            {
                return null;
            }
            return hunters[SelectedHunterIndex];
        }

        public bool PromoteHunter(string hunterId)
        {
            for (int i = 0; i < hunters.Count; i++)
            {
                if (hunters[i].hunterId == hunterId)
                {
                    return brains[i].TryPromote();
                }
            }
            return false;
        }

        private void BuildFacilities()
        {
            facilities[FacilityType.Tavern] = new VillageFacility { facilityType = FacilityType.Tavern, worldPoint = GetPoint(tavernPoint), recoverAmountPerTick = 12, useDuration = 1.5f };
            facilities[FacilityType.Inn] = new VillageFacility { facilityType = FacilityType.Inn, worldPoint = GetPoint(innPoint), recoverAmountPerTick = 10, useDuration = 2.2f };
            facilities[FacilityType.Clinic] = new VillageFacility { facilityType = FacilityType.Clinic, worldPoint = GetPoint(clinicPoint), recoverAmountPerTick = 8, useDuration = 2.0f };
            facilities[FacilityType.AdShrine] = new VillageFacility { facilityType = FacilityType.AdShrine, worldPoint = GetPoint(adShrinePoint), recoverAmountPerTick = 0, useDuration = 0f };
            facilities[FacilityType.CommunityBoard] = new VillageFacility { facilityType = FacilityType.CommunityBoard, worldPoint = GetPoint(communityBoardPoint), recoverAmountPerTick = 0, useDuration = 0f };
            facilities[FacilityType.TrainingHall] = new VillageFacility { facilityType = FacilityType.TrainingHall, worldPoint = GetPoint(trainingHallPoint, GetPoint(patrolPoint)), recoverAmountPerTick = 0, useDuration = 4.0f };
            facilities[FacilityType.Forge] = new VillageFacility { facilityType = FacilityType.Forge, worldPoint = GetPoint(forgePoint, GetPoint(craftPoint)), recoverAmountPerTick = 0, useDuration = 4.5f };
            facilities[FacilityType.SkillHall] = new VillageFacility { facilityType = FacilityType.SkillHall, worldPoint = GetPoint(skillHallPoint, GetPoint(skillPoint)), recoverAmountPerTick = 0, useDuration = 5.0f };
        }

        private VillageFacility ResolveFacility(FacilityType type)
        {
            if (!facilities.TryGetValue(type, out VillageFacility facility))
            {
                return null;
            }

            facility.worldPoint = type switch
            {
                FacilityType.Tavern => GetPoint(tavernPoint, facility.worldPoint),
                FacilityType.Inn => GetPoint(innPoint, facility.worldPoint),
                FacilityType.Clinic => GetPoint(clinicPoint, facility.worldPoint),
                FacilityType.AdShrine => GetPoint(adShrinePoint, facility.worldPoint),
                FacilityType.CommunityBoard => GetPoint(communityBoardPoint, facility.worldPoint),
                FacilityType.TrainingHall => GetPoint(trainingHallPoint, facility.worldPoint),
                FacilityType.Forge => GetPoint(forgePoint, facility.worldPoint),
                FacilityType.SkillHall => GetPoint(skillHallPoint, facility.worldPoint),
                _ => facility.worldPoint,
            };
            return facility;
        }

        private static Vector3 GetPoint(Transform point)
        {
            return point != null ? point.position : Vector3.zero;
        }

        private static Vector3 GetPoint(Transform point, Vector3 fallback)
        {
            return point != null ? point.position : fallback;
        }
    }

    public sealed class LightweightMovementAgent : IMovementAgent
    {
        private readonly HunterProfile profile;
        private Vector3 target;

        public LightweightMovementAgent(HunterProfile profile)
        {
            this.profile = profile;
            target = profile.worldPosition;
        }

        public void MoveTo(Vector3 newTarget, float deltaTime)
        {
            target = newTarget;
            float safeDelta = Mathf.Max(0.01f, deltaTime);
            profile.worldPosition = Vector3.MoveTowards(profile.worldPosition, target, profile.moveSpeed * safeDelta);
        }

        public bool Reached(Vector3 point, float stoppingDistance)
        {
            return Vector3.SqrMagnitude(profile.worldPosition - point) <= stoppingDistance * stoppingDistance;
        }
    }
}
