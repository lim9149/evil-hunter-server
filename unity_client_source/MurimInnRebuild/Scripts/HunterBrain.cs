// DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
using System;
using UnityEngine;

namespace MurimInnRebuild
{
    public interface IMovementAgent
    {
        void MoveTo(Vector3 target, float deltaTime);
        bool Reached(Vector3 target, float stoppingDistance);
    }

    public sealed class HunterBrain
    {
        private readonly HunterProfile profile;
        private readonly JobDatabaseSO jobDatabase;
        private readonly Func<FacilityType, VillageFacility> facilityResolver;
        private readonly IMovementAgent movementAgent;
        private readonly HunterTrafficCoordinator trafficCoordinator;
        private readonly float statTickSeconds;
        private readonly float stoppingDistance;
        private readonly System.Random rng;
        private float encounterDurationTarget = 2.6f;
        private float trainingDurationTarget = 4.0f;
        private float socialDurationTarget = 3.5f;
        private float craftDurationTarget = 4.5f;
        private float skillDurationTarget = 5.0f;

        public HunterBrain(HunterProfile profile, JobDatabaseSO jobDatabase, Func<FacilityType, VillageFacility> facilityResolver, IMovementAgent movementAgent, HunterTrafficCoordinator trafficCoordinator, float statTickSeconds = 1.0f, float stoppingDistance = 0.12f)
        {
            this.profile = profile;
            this.jobDatabase = jobDatabase;
            this.facilityResolver = facilityResolver;
            this.movementAgent = movementAgent;
            this.trafficCoordinator = trafficCoordinator;
            this.statTickSeconds = Mathf.Max(0.25f, statTickSeconds);
            encounterDurationTarget = Mathf.Max(1.4f, 2.6f / Mathf.Max(0.7f, profile.tempoBias));
            trainingDurationTarget = Mathf.Max(2.0f, 4.0f / Mathf.Max(0.8f, profile.recoveryBias));
            socialDurationTarget = Mathf.Max(2.0f, 3.5f - profile.sociability);
            craftDurationTarget = Mathf.Max(2.5f, 4.8f - profile.discipline);
            skillDurationTarget = Mathf.Max(3.0f, 5.2f - profile.curiosity);
            this.stoppingDistance = Mathf.Max(0.05f, stoppingDistance);
            rng = new System.Random((profile.hunterId ?? "hunter").GetHashCode());
        }

        public SharedAnimState CurrentAnimState { get; private set; } = SharedAnimState.Idle;

        public void Tick(float deltaTime)
        {
            if (profile == null || !profile.IsAlive)
            {
                profile.state = HunterState.Dead;
                CurrentAnimState = SharedAnimState.Die;
                return;
            }

            profile.autonomyCooldown = Mathf.Max(0f, profile.autonomyCooldown - deltaTime);
            profile.speechCooldown = Mathf.Max(0f, profile.speechCooldown - deltaTime);
            profile.speechRemaining = Mathf.Max(0f, profile.speechRemaining - deltaTime);
            if (profile.speechRemaining <= 0f && !string.IsNullOrEmpty(profile.lastSpokenLine))
            {
                profile.lastSpokenLine = string.Empty;
            }

            profile.thinkCooldown -= deltaTime;
            if (profile.thinkCooldown > 0f)
            {
                UpdateMovementOnly(deltaTime);
                return;
            }

            profile.thinkCooldown = statTickSeconds;
            UpdateNeeds();
            StepStateMachine(deltaTime, statTickSeconds);
        }

        public bool TryPromote()
        {
            if (!jobDatabase.TryGetPromotedJob(profile.currentJobId, out JobData nextJob))
            {
                return false;
            }

            profile.ApplyJob(nextJob);
            profile.Speak("다음 경지로 올랐다.");
            return true;
        }

        private void UpdateNeeds()
        {
            if (profile.state == HunterState.EngagingMonster)
            {
                profile.hunger = Mathf.Max(0, profile.hunger - 4);
                profile.stamina = Mathf.Max(0, profile.stamina - 4);
                profile.hp = Mathf.Max(1, profile.hp - UnityEngine.Random.Range(0, 3));
                profile.fatigue = Mathf.Clamp(profile.fatigue + 2.4f, 0f, 100f);
            }
            else if (profile.state == HunterState.Training || profile.state == HunterState.Crafting || profile.state == HunterState.LearningSkill)
            {
                profile.hunger = Mathf.Max(0, profile.hunger - 2);
                profile.stamina = Mathf.Max(0, profile.stamina - 3);
                profile.fatigue = Mathf.Clamp(profile.fatigue + 1.4f, 0f, 100f);
            }
            else
            {
                profile.hunger = Mathf.Max(0, profile.hunger - (profile.restDiscipline == HunterRestDiscipline.Frugal ? 1 : 0));
            }

            if (profile.IsInjured)
            {
                profile.currentNeed = NeedType.HP;
            }
            else if (profile.IsHungry)
            {
                profile.currentNeed = NeedType.Hunger;
            }
            else if (profile.IsTired)
            {
                profile.currentNeed = NeedType.Stamina;
            }
            else
            {
                profile.currentNeed = NeedType.None;
            }
        }

        private void StepStateMachine(float deltaTime, float simulatedStep)
        {
            switch (profile.state)
            {
                case HunterState.Idle:
                case HunterState.AwaitingCommand:
                case HunterState.Selected:
                    ProcessQueuedOrAutonomousCommand(deltaTime);
                    break;

                case HunterState.MovingToBoard:
                    ProcessMoveTo(profile.huntPoint + profile.laneOffset, HunterState.MovingToHunt, "출정", deltaTime);
                    break;

                case HunterState.MovingToHunt:
                    if (movementAgent.Reached(profile.huntPoint + profile.laneOffset, stoppingDistance))
                    {
                        profile.state = HunterState.EngagingMonster;
                        profile.uiStateLabel = "교전";
                        profile.hasDestination = false;
                        MaybeSpeak("이번 의뢰는 내가 끝낸다.");
                        CurrentAnimState = SharedAnimState.Attack;
                    }
                    else
                    {
                        SetDestination(profile.huntPoint + profile.laneOffset, deltaTime);
                    }
                    break;

                case HunterState.EngagingMonster:
                    if (profile.currentNeed != NeedType.None)
                    {
                        BeginRecoveryReturn();
                        break;
                    }

                    profile.huntElapsed += simulatedStep;
                    profile.commandProgress = Mathf.Clamp01(profile.huntElapsed / encounterDurationTarget);
                    profile.huntLoopProgress = Mathf.Clamp01((float)profile.defeatedMonsterCount / Mathf.Max(1, profile.targetMonsterCount));
                    profile.morale = Mathf.Clamp(profile.morale + 0.2f * simulatedStep, 0f, 100f);
                    if (profile.huntElapsed >= encounterDurationTarget)
                    {
                        profile.huntElapsed = 0f;
                        profile.defeatedMonsterCount += 1;
                        profile.huntLoopProgress = Mathf.Clamp01((float)profile.defeatedMonsterCount / Mathf.Max(1, profile.targetMonsterCount));
                        MaybeSpeak(profile.defeatedMonsterCount >= profile.targetMonsterCount ? "목표 수를 채웠다." : "한 마리 더 간다.");
                    }

                    if (profile.defeatedMonsterCount >= profile.targetMonsterCount)
                    {
                        profile.currentCommand = HunterCommandType.Return;
                        profile.state = HunterState.ReturningToVillage;
                        profile.uiStateLabel = "귀환";
                        CurrentAnimState = SharedAnimState.Move;
                    }
                    else
                    {
                        CurrentAnimState = SharedAnimState.Attack;
                    }
                    break;

                case HunterState.ReturningToVillage:
                    ProcessReturn(deltaTime);
                    break;

                case HunterState.MovingToFacility:
                    ProcessMovingToFacility(deltaTime);
                    break;

                case HunterState.Recovering:
                    ProcessRecovery(simulatedStep);
                    break;

                case HunterState.MovingToTraining:
                    ProcessMoveTo(profile.patrolPoint, HunterState.Training, "훈련", deltaTime);
                    break;

                case HunterState.Training:
                    ProcessTimedAction(simulatedStep, trainingDurationTarget, HunterState.ReturningToVillage, "훈련", () =>
                    {
                        profile.attack += profile.trainingFocus == HunterTrainingFocus.Weapon ? 1 : 0;
                        profile.defense += profile.trainingFocus == HunterTrainingFocus.Body ? 1 : 0;
                        profile.moveSpeed += profile.trainingFocus == HunterTrainingFocus.Footwork ? 0.02f : 0f;
                        profile.morale = Mathf.Clamp(profile.morale + 1.5f, 0f, 100f);
                        MaybeSpeak("몸이 조금 더 가벼워졌다.");
                    });
                    break;

                case HunterState.Patrolling:
                    ProcessPatrol(deltaTime, simulatedStep);
                    break;

                case HunterState.Socializing:
                    ProcessTimedAction(simulatedStep, socialDurationTarget, HunterState.ReturningToVillage, "담소", () =>
                    {
                        profile.morale = Mathf.Clamp(profile.morale + 3f, 0f, 100f);
                        MaybeSpeak("마을 분위기가 괜찮군.");
                    });
                    break;

                case HunterState.BrowsingShop:
                    ProcessTimedAction(simulatedStep, craftDurationTarget, HunterState.ReturningToVillage, "상점 구경", () =>
                    {
                        profile.morale = Mathf.Clamp(profile.morale + 2f, 0f, 100f);
                        MaybeSpeak("새 장비가 들어왔나?");
                    });
                    break;

                case HunterState.LearningSkill:
                    ProcessTimedAction(simulatedStep, skillDurationTarget, HunterState.ReturningToVillage, "무공 수련", () =>
                    {
                        profile.attack += 1;
                        profile.morale = Mathf.Clamp(profile.morale + 1f, 0f, 100f);
                        MaybeSpeak("새로운 보법을 익혔다.");
                    });
                    break;

                case HunterState.Crafting:
                    ProcessTimedAction(simulatedStep, craftDurationTarget, HunterState.ReturningToVillage, "제작", () =>
                    {
                        profile.defense += 1;
                        MaybeSpeak("수리와 제작을 끝냈다.");
                    });
                    break;

                case HunterState.Wandering:
                    ProcessWander(deltaTime, simulatedStep);
                    break;
            }
        }

        private void ProcessQueuedOrAutonomousCommand(float deltaTime)
        {
            if (profile.currentNeed != NeedType.None && profile.currentCommand == HunterCommandType.None)
            {
                BeginRecoveryReturn();
                return;
            }

            HunterCommandType command = profile.queuedCommand;
            if (command == HunterCommandType.None || command == HunterCommandType.Hold)
            {
                if (profile.autonomousBehaviorEnabled && profile.autonomyCooldown <= 0f)
                {
                    command = ChooseAutonomousCommand();
                    if (command != HunterCommandType.None)
                    {
                        profile.IssueCommand(command, Mathf.Max(1, Mathf.RoundToInt(2 + profile.bravery * 3f)));
                        profile.queuedCommand = command;
                    }
                }
                else
                {
                    profile.state = profile.isSelected ? HunterState.Selected : HunterState.AwaitingCommand;
                    profile.uiStateLabel = profile.isSelected ? "선택됨" : "자유 행동";
                    CurrentAnimState = SharedAnimState.Idle;
                    return;
                }
            }

            command = profile.queuedCommand;
            profile.currentCommand = command;
            profile.queuedCommand = HunterCommandType.None;
            switch (command)
            {
                case HunterCommandType.Hunt:
                    profile.state = HunterState.MovingToBoard;
                    profile.uiStateLabel = "출정 준비";
                    SetDestination(profile.huntPoint + profile.laneOffset, deltaTime);
                    MaybeSpeak("의뢰를 받고 출발한다.");
                    CurrentAnimState = SharedAnimState.Move;
                    break;
                case HunterCommandType.Train:
                    profile.state = HunterState.MovingToTraining;
                    profile.uiStateLabel = "훈련 이동";
                    SetDestination(profile.patrolPoint, deltaTime);
                    CurrentAnimState = SharedAnimState.Move;
                    break;
                case HunterCommandType.Patrol:
                    profile.state = HunterState.Patrolling;
                    profile.uiStateLabel = "순찰";
                    profile.commandProgress = 0f;
                    CurrentAnimState = SharedAnimState.Move;
                    break;
                case HunterCommandType.Return:
                case HunterCommandType.Rest:
                case HunterCommandType.Eat:
                case HunterCommandType.Heal:
                    BeginRecoveryReturn();
                    break;
                case HunterCommandType.LearnSkill:
                    profile.targetFacility = FacilityType.SkillHall;
                    profile.state = HunterState.MovingToFacility;
                    profile.uiStateLabel = "무공당 이동";
                    SetDestination(profile.skillPoint, deltaTime);
                    CurrentAnimState = SharedAnimState.Move;
                    break;
                case HunterCommandType.Craft:
                case HunterCommandType.ChangeClass:
                    profile.targetFacility = FacilityType.Forge;
                    profile.state = HunterState.MovingToFacility;
                    profile.uiStateLabel = command == HunterCommandType.Craft ? "대장간 이동" : "전직 준비";
                    SetDestination(profile.craftPoint, deltaTime);
                    CurrentAnimState = SharedAnimState.Move;
                    break;
                default:
                    profile.state = profile.isSelected ? HunterState.Selected : HunterState.AwaitingCommand;
                    CurrentAnimState = SharedAnimState.Idle;
                    break;
            }
        }

        private HunterCommandType ChooseAutonomousCommand()
        {
            profile.autonomyCooldown = UnityEngine.Random.Range(2.5f, 5.5f);
            profile.autonomyCycleCount += 1;

            if (profile.currentNeed == NeedType.HP) return HunterCommandType.Heal;
            if (profile.currentNeed == NeedType.Hunger) return HunterCommandType.Eat;
            if (profile.currentNeed == NeedType.Stamina) return HunterCommandType.Rest;

            float roll = (float)rng.NextDouble();
            if (profile.morale < 32f && roll < 0.35f + profile.sociability * 0.25f)
            {
                return HunterCommandType.Patrol;
            }
            if (profile.fatigue > 65f)
            {
                return HunterCommandType.Rest;
            }
            if (roll < 0.30f + profile.bravery * 0.30f)
            {
                return HunterCommandType.Hunt;
            }
            if (roll < 0.52f + profile.discipline * 0.12f)
            {
                return HunterCommandType.Train;
            }
            if (roll < 0.67f + profile.curiosity * 0.12f)
            {
                return HunterCommandType.LearnSkill;
            }
            if (roll < 0.82f)
            {
                return HunterCommandType.Craft;
            }
            return HunterCommandType.Patrol;
        }

        private void BeginRecoveryReturn()
        {
            profile.state = HunterState.ReturningToVillage;
            profile.uiStateLabel = "정비 귀환";
            CurrentAnimState = SharedAnimState.Move;
        }

        private void ProcessReturn(float deltaTime)
        {
            profile.targetFacility = ResolveFacilityTypeForCurrentNeed();
            VillageFacility facility = facilityResolver(profile.targetFacility);
            if (facility == null)
            {
                profile.state = HunterState.AwaitingCommand;
                CurrentAnimState = SharedAnimState.Idle;
                return;
            }

            profile.state = HunterState.MovingToFacility;
            profile.uiStateLabel = "시설 이동";
            Vector3 slot = trafficCoordinator != null ? trafficCoordinator.ReserveFacilitySlot(profile.targetFacility, facility.worldPoint) : facility.worldPoint;
            SetDestination(slot, deltaTime);
            CurrentAnimState = SharedAnimState.Move;
        }

        private void ProcessMovingToFacility(float deltaTime)
        {
            VillageFacility target = facilityResolver(profile.targetFacility);
            if (target == null)
            {
                profile.state = HunterState.AwaitingCommand;
                return;
            }

            if (movementAgent.Reached(target.worldPoint, stoppingDistance))
            {
                profile.recoverProgress = 0f;
                profile.hasDestination = false;
                profile.facilityIdleElapsed = 0f;
                profile.state = profile.currentCommand switch
                {
                    HunterCommandType.LearnSkill => HunterState.LearningSkill,
                    HunterCommandType.Craft => HunterState.Crafting,
                    HunterCommandType.ChangeClass => HunterState.LearningSkill,
                    _ => HunterState.Recovering,
                };
                profile.uiStateLabel = profile.state == HunterState.Recovering ? "회복" : profile.uiStateLabel;
                CurrentAnimState = SharedAnimState.Idle;
            }
            else
            {
                SetDestination(target.worldPoint, deltaTime);
                CurrentAnimState = SharedAnimState.Move;
            }
        }

        private void ProcessRecovery(float simulatedStep)
        {
            VillageFacility facility = facilityResolver(profile.targetFacility);
            if (facility == null)
            {
                profile.state = HunterState.AwaitingCommand;
                return;
            }

            profile.recoverProgress += simulatedStep;
            profile.commandProgress = Mathf.Clamp01(profile.recoverProgress / Mathf.Max(0.4f, facility.useDuration));
            if (profile.recoverProgress < facility.useDuration)
            {
                CurrentAnimState = SharedAnimState.Idle;
                if (profile.commandProgress > 0.3f) MaybeSpeak(GetFacilityTalk(profile.targetFacility));
                return;
            }

            profile.recoverProgress = 0f;
            switch (profile.targetFacility)
            {
                case FacilityType.Clinic:
                    profile.hp = Mathf.Min(profile.maxHP, profile.hp + facility.recoverAmountPerTick);
                    profile.fatigue = Mathf.Clamp(profile.fatigue - 6f * profile.recoveryBias, 0f, 100f);
                    break;
                case FacilityType.Tavern:
                    profile.hunger = Mathf.Min(profile.maxHunger, profile.hunger + facility.recoverAmountPerTick * 2);
                    profile.morale = Mathf.Clamp(profile.morale + 2f, 0f, 100f);
                    break;
                default:
                    profile.stamina = Mathf.Min(profile.maxStamina, profile.stamina + facility.recoverAmountPerTick * 2);
                    profile.fatigue = Mathf.Clamp(profile.fatigue - 8f * profile.recoveryBias, 0f, 100f);
                    break;
            }

            if (!profile.IsInjured && !profile.IsHungry && !profile.IsTired)
            {
                trafficCoordinator?.ReleaseFacilitySlot(profile.targetFacility);
                profile.currentNeed = NeedType.None;
                profile.currentCommand = HunterCommandType.None;
                profile.state = profile.isSelected ? HunterState.Selected : HunterState.AwaitingCommand;
                profile.uiStateLabel = profile.isSelected ? "선택됨" : "자유 행동";
                profile.commandLabel = "대기";
                profile.commandProgress = 0f;
                profile.autonomyCooldown = UnityEngine.Random.Range(1.6f, 3.6f);
                CurrentAnimState = SharedAnimState.Idle;
            }
        }

        private void ProcessTimedAction(float simulatedStep, float duration, HunterState nextState, string label, Action onComplete)
        {
            if (profile.currentNeed != NeedType.None && profile.currentCommand != HunterCommandType.ChangeClass)
            {
                BeginRecoveryReturn();
                return;
            }

            profile.recoverProgress += simulatedStep;
            profile.commandProgress = Mathf.Clamp01(profile.recoverProgress / Mathf.Max(1f, duration));
            profile.uiStateLabel = label;
            CurrentAnimState = SharedAnimState.Attack;
            if (profile.recoverProgress < duration)
            {
                if (profile.commandProgress > 0.4f) MaybeSpeak(GetStateTalk(profile.state));
                return;
            }

            profile.recoverProgress = 0f;
            onComplete?.Invoke();
            profile.currentCommand = HunterCommandType.Return;
            profile.state = nextState;
            profile.uiStateLabel = "귀환";
            CurrentAnimState = SharedAnimState.Move;
        }

        private void ProcessPatrol(float deltaTime, float simulatedStep)
        {
            profile.commandProgress = Mathf.Clamp01(profile.commandProgress + simulatedStep / 5f);
            if (!profile.hasDestination || movementAgent.Reached(profile.currentDestination, stoppingDistance))
            {
                profile.roamPoint = profile.villageCenter + new Vector3(UnityEngine.Random.Range(-2.5f, 2.5f), 0f, UnityEngine.Random.Range(-2.0f, 2.0f));
                SetDestination(profile.roamPoint, deltaTime);
            }
            else
            {
                SetDestination(profile.currentDestination, deltaTime);
            }

            if (profile.commandProgress >= 1f)
            {
                profile.currentCommand = HunterCommandType.None;
                profile.state = profile.sociability > 0.65f ? HunterState.Socializing : HunterState.Wandering;
                profile.commandProgress = 0f;
                profile.hasDestination = false;
                profile.uiStateLabel = profile.state == HunterState.Socializing ? "담소" : "산책";
            }
            MaybeSpeak("마을을 한 번 둘러보지.");
            CurrentAnimState = SharedAnimState.Move;
        }

        private void ProcessWander(float deltaTime, float simulatedStep)
        {
            profile.commandProgress = Mathf.Clamp01(profile.commandProgress + simulatedStep / 4f);
            if (!profile.hasDestination || movementAgent.Reached(profile.currentDestination, stoppingDistance))
            {
                Vector3 next = profile.villageCenter + new Vector3(UnityEngine.Random.Range(-3.0f, 3.0f), 0f, UnityEngine.Random.Range(-2.5f, 2.5f));
                SetDestination(next, deltaTime);
            }

            MaybeSpeak(profile.morale < 40f ? "오늘은 조금 지치는군." : "객잔이 북적여서 좋군.");
            if (profile.commandProgress >= 1f)
            {
                profile.currentCommand = HunterCommandType.None;
                profile.state = profile.isSelected ? HunterState.Selected : HunterState.AwaitingCommand;
                profile.commandProgress = 0f;
                profile.hasDestination = false;
                profile.autonomyCooldown = UnityEngine.Random.Range(1.0f, 2.5f);
            }
            CurrentAnimState = SharedAnimState.Move;
        }

        private void ProcessMoveTo(Vector3 target, HunterState arriveState, string arriveLabel, float deltaTime)
        {
            if (movementAgent.Reached(target, stoppingDistance))
            {
                profile.state = arriveState;
                profile.uiStateLabel = arriveLabel;
                profile.hasDestination = false;
                profile.commandProgress = 0f;
                CurrentAnimState = arriveState == HunterState.Training ? SharedAnimState.Attack : SharedAnimState.Move;
            }
            else
            {
                SetDestination(target, deltaTime);
                CurrentAnimState = SharedAnimState.Move;
            }
        }

        private FacilityType ResolveFacilityTypeForCurrentNeed()
        {
            if (profile.currentCommand == HunterCommandType.Heal || profile.currentNeed == NeedType.HP)
            {
                return FacilityType.Clinic;
            }
            if (profile.currentCommand == HunterCommandType.Eat || profile.currentNeed == NeedType.Hunger)
            {
                return FacilityType.Tavern;
            }
            if (profile.currentCommand == HunterCommandType.LearnSkill || profile.currentCommand == HunterCommandType.ChangeClass)
            {
                return FacilityType.SkillHall;
            }
            if (profile.currentCommand == HunterCommandType.Craft)
            {
                return FacilityType.Forge;
            }
            return FacilityType.Inn;
        }

        private void UpdateMovementOnly(float deltaTime)
        {
            if (!profile.hasDestination)
            {
                return;
            }
            movementAgent.MoveTo(profile.currentDestination, deltaTime);
            CurrentAnimState = SharedAnimState.Move;
        }

        private void SetDestination(Vector3 target, float deltaTime)
        {
            profile.currentDestination = target;
            profile.hasDestination = true;
            movementAgent.MoveTo(target, deltaTime);
        }

        private void MaybeSpeak(string line)
        {
            if (profile.speechCooldown > 0f || string.IsNullOrWhiteSpace(line))
            {
                return;
            }
            profile.Speak(line, UnityEngine.Random.Range(1.8f, 2.8f));
        }

        private static string GetFacilityTalk(FacilityType facilityType)
        {
            return facilityType switch
            {
                FacilityType.Clinic => "침 한 번 맞고 다시 나가야지.",
                FacilityType.Tavern => "따뜻한 국밥 한 그릇이면 충분하다.",
                FacilityType.SkillHall => "호흡을 가다듬고 식을 익힌다.",
                FacilityType.Forge => "무구 손질이 곧 생존이지.",
                _ => "객잔에서 숨을 고른다.",
            };
        }

        private static string GetStateTalk(HunterState state)
        {
            return state switch
            {
                HunterState.Socializing => "소문도 정보다.",
                HunterState.LearningSkill => "한 수 더 익히면 판이 달라진다.",
                HunterState.Crafting => "장비 상태가 곧 실력이다.",
                _ => "조금만 더 하면 끝난다.",
            };
        }
    }
}
