// DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
using System;
using System.Collections.Generic;
using UnityEngine;

namespace MurimInnRebuild
{
    [Serializable]
    public sealed class ActiveMarkProfile
    {
        public MarkSlot slot;
        public MarkVisualType visualType;
        public int spriteId = -1;
        public Color tint = Color.clear;
        public string description;
    }

    [Serializable]
    public sealed class HunterProfile
    {
        public const int MaxPopulation = 20;
        public const int HairVariantCount = 5;
        public const int SkinToneCount = 3;

        [Header("Identity")]
        public string hunterId;
        public string accountId;
        public string displayName;
        public HunterGender gender;

        [Header("Random Appearance")]
        public int hairId;
        public int skinToneId;
        public int outfitSpriteId;
        public int weaponSpriteId;
        public Color bodyTint = Color.white;
        public List<ActiveMarkProfile> activeMarks = new List<ActiveMarkProfile>(3);

        [Header("Progression")]
        public string currentJobId;
        public HunterPosition position;
        public HunterStage currentStage;
        public int level = 1;

        [Header("Runtime Stats")]
        public int maxHP;
        public int hp;
        public int maxHunger;
        public int hunger;
        public int maxStamina;
        public int stamina;
        public int attack;
        public int defense;
        public float huntPower;
        public float moveSpeed;

        [Header("Operation")]
        public HunterOperationStyle operationStyle = HunterOperationStyle.Steady;
        public HunterRestDiscipline restDiscipline = HunterRestDiscipline.Measured;
        public HunterTrainingFocus trainingFocus = HunterTrainingFocus.Body;
        [Range(0f, 100f)] public float morale = 55f;
        [Range(0f, 100f)] public float fatigue = 20f;
        public string bondedFacilityId = "inn_main";
        public float tempoBias = 1f;
        public float recoveryBias = 1f;

        [Header("Autonomy")]
        public bool autonomousBehaviorEnabled = true;
        [Range(0f, 1f)] public float bravery = 0.5f;
        [Range(0f, 1f)] public float discipline = 0.5f;
        [Range(0f, 1f)] public float sociability = 0.5f;
        [Range(0f, 1f)] public float curiosity = 0.5f;
        public float autonomyCooldown;
        public float speechCooldown;
        public int autonomyCycleCount;

        [Header("AI")]
        public HunterState state = HunterState.AwaitingCommand;
        public NeedType currentNeed = NeedType.None;
        public HunterCommandType currentCommand = HunterCommandType.None;
        public HunterCommandType queuedCommand = HunterCommandType.None;
        public FacilityType targetFacility;
        public Vector3 worldPosition;
        public Vector3 huntPoint;
        public Vector3 currentDestination;
        public bool hasDestination;
        public float recoverProgress;
        public float thinkCooldown;
        public float huntLoopProgress;
        public float huntElapsed;
        public float commandProgress;
        public int targetMonsterCount = 3;
        public int defeatedMonsterCount;
        public bool manualControlEnabled = true;
        public bool isSelected;
        public string uiStateLabel = "Awaiting";
        public string commandLabel = "대기";
        public Vector3 laneOffset;
        public Vector3 villageCenter;
        public Vector3 patrolPoint;
        public Vector3 socialPoint;
        public Vector3 craftPoint;
        public Vector3 skillPoint;
        public Vector3 roamPoint;
        public string lastSpokenLine = "";
        public float speechRemaining;
        public float facilityIdleElapsed;

        public bool IsAlive => hp > 0;
        public bool IsHungry => hunger <= Mathf.CeilToInt(maxHunger * 0.25f);
        public bool IsTired => stamina <= Mathf.CeilToInt(maxStamina * 0.25f);
        public bool IsInjured => hp <= Mathf.CeilToInt(maxHP * 0.35f);

        public void ApplyJob(JobData job)
        {
            if (job == null)
            {
                return;
            }

            currentJobId = job.jobId;
            position = job.position;
            currentStage = job.stage;
            maxHP = job.maxHP;
            maxHunger = job.maxHunger;
            maxStamina = job.maxStamina;
            attack = job.attack;
            defense = job.defense;
            huntPower = job.huntPower;
            moveSpeed = job.moveSpeed;
            outfitSpriteId = job.outfitSpriteId;
            weaponSpriteId = job.weaponSpriteId;
            ApplyMarks(job);

            hp = Mathf.Clamp(hp <= 0 ? maxHP : hp, 1, maxHP);
            hunger = Mathf.Clamp(hunger <= 0 ? maxHunger : hunger, 1, maxHunger);
            stamina = Mathf.Clamp(stamina <= 0 ? maxStamina : stamina, 1, maxStamina);
        }

        public void ApplyOperationBiases()
        {
            tempoBias = 1f;
            recoveryBias = 1f;
            switch (operationStyle)
            {
                case HunterOperationStyle.Vanguard: tempoBias += 0.12f; fatigue += 4f; break;
                case HunterOperationStyle.Shadow: tempoBias += 0.18f; bravery += 0.15f; break;
                case HunterOperationStyle.Support: tempoBias -= 0.04f; morale += 6f; sociability += 0.15f; break;
            }

            switch (restDiscipline)
            {
                case HunterRestDiscipline.Frugal: recoveryBias -= 0.05f; discipline += 0.1f; break;
                case HunterRestDiscipline.Lavish: recoveryBias += 0.14f; sociability += 0.1f; break;
            }

            switch (trainingFocus)
            {
                case HunterTrainingFocus.Weapon: attack += 2; discipline += 0.1f; break;
                case HunterTrainingFocus.Mind: recoveryBias += 0.07f; curiosity += 0.08f; break;
                case HunterTrainingFocus.Footwork: moveSpeed += 0.2f; tempoBias += 0.08f; break;
            }

            morale = Mathf.Clamp(morale, 10f, 100f);
            fatigue = Mathf.Clamp(fatigue, 0f, 100f);
            bravery = Mathf.Clamp01(bravery);
            discipline = Mathf.Clamp01(discipline);
            sociability = Mathf.Clamp01(sociability);
            curiosity = Mathf.Clamp01(curiosity);
        }

        public void RestoreAll()
        {
            hp = maxHP;
            hunger = maxHunger;
            stamina = maxStamina;
            currentNeed = NeedType.None;
        }

        public void IssueCommand(HunterCommandType command, int monsterCount = 3)
        {
            currentCommand = command;
            queuedCommand = command;
            targetMonsterCount = Mathf.Max(1, monsterCount);
            defeatedMonsterCount = 0;
            commandProgress = 0f;
            huntLoopProgress = 0f;
            autonomyCooldown = 4.0f;
            manualControlEnabled = true;
            commandLabel = command switch
            {
                HunterCommandType.Hunt => "사냥",
                HunterCommandType.Train => "훈련",
                HunterCommandType.Rest => "휴식",
                HunterCommandType.Eat => "식사",
                HunterCommandType.Heal => "치료",
                HunterCommandType.Patrol => "순찰",
                HunterCommandType.Return => "귀환",
                HunterCommandType.LearnSkill => "수련",
                HunterCommandType.Craft => "제작",
                HunterCommandType.ChangeClass => "전직",
                HunterCommandType.Hold => "대기",
                _ => "대기",
            };
            uiStateLabel = commandLabel;
        }

        public void Speak(string line, float holdSeconds = 2.2f)
        {
            if (string.IsNullOrWhiteSpace(line))
            {
                return;
            }

            lastSpokenLine = line.Trim();
            speechRemaining = Mathf.Max(0.8f, holdSeconds);
            speechCooldown = UnityEngine.Random.Range(4.0f, 8.0f);
        }

        private void ApplyMarks(JobData job)
        {
            activeMarks.Clear();
            if (job.marks == null)
            {
                return;
            }

            for (int i = 0; i < job.marks.Count; i++)
            {
                JobMarkData mark = job.marks[i];
                if (mark == null || mark.slot == MarkSlot.None || mark.spriteId < 0)
                {
                    continue;
                }

                activeMarks.Add(new ActiveMarkProfile
                {
                    slot = mark.slot,
                    visualType = mark.visualType,
                    spriteId = mark.spriteId,
                    tint = mark.tint,
                    description = mark.description,
                });
            }
        }

        public static HunterProfile CreateRandom(string hunterId, string accountId, string displayName, JobData startJob, Vector3 spawnPoint, System.Random random)
        {
            int skinToneId = random.Next(0, SkinToneCount);
            HunterProfile profile = new HunterProfile
            {
                hunterId = hunterId,
                accountId = accountId,
                displayName = displayName,
                gender = random.NextDouble() < 0.5d ? HunterGender.Male : HunterGender.Female,
                hairId = random.Next(0, HairVariantCount),
                skinToneId = skinToneId,
                bodyTint = SkinTonePalette.FromId(skinToneId),
                worldPosition = spawnPoint,
                huntPoint = spawnPoint,
                currentDestination = spawnPoint,
                state = HunterState.AwaitingCommand,
                bravery = (float)random.NextDouble(),
                discipline = (float)random.NextDouble(),
                sociability = (float)random.NextDouble(),
                curiosity = (float)random.NextDouble(),
                autonomyCooldown = 1.0f + (float)random.NextDouble() * 2.0f,
                speechCooldown = 2.5f + (float)random.NextDouble() * 3.0f,
            };

            profile.ApplyJob(startJob);
            profile.ApplyOperationBiases();
            return profile;
        }
    }

    public static class SkinTonePalette
    {
        private static readonly Color[] Colors =
        {
            new Color(1.00f, 0.87f, 0.72f),
            new Color(0.85f, 0.67f, 0.50f),
            new Color(0.57f, 0.39f, 0.27f),
        };

        public static Color FromId(int skinToneId)
        {
            if (skinToneId < 0 || skinToneId >= Colors.Length)
            {
                return Colors[0];
            }
            return Colors[0 + skinToneId];
        }
    }
}
