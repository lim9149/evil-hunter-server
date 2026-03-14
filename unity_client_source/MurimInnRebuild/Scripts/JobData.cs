// DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
using System;
using System.Collections.Generic;
using UnityEngine;

namespace MurimInnRebuild
{
    [Serializable]
    public sealed class JobMarkData
    {
        public MarkSlot slot = MarkSlot.None;
        public MarkVisualType visualType = MarkVisualType.None;
        public int spriteId = -1;         // 나중에 markSprites 배열 인덱스에 연결
        public Color tint = Color.clear;  // 픽셀 증표의 대표 색상

        [TextArea]
        public string description;
    }

    [Serializable]
    public sealed class JobData
    {
        public string jobId;
        public string displayName;
        public HunterPosition position;
        public HunterStage stage;
        public string promoteFromJobId;
        public string promoteToJobId;

        [Header("Base Stats")]
        public int maxHP;
        public int maxHunger;
        public int maxStamina;
        public int attack;
        public int defense;
        public float huntPower;
        public float moveSpeed;

        [Header("Visual Signature")]
        public Color symbolicColor = Color.white;
        public int outfitSpriteId;
        public int weaponSpriteId;
        public List<JobMarkData> marks = new List<JobMarkData>();

        [TextArea]
        public string note;
    }

    [CreateAssetMenu(fileName = "JobDatabase", menuName = "MurimInnRebuild/Job Database")]
    public sealed class JobDatabaseSO : ScriptableObject
    {
        [Tooltip("픽셀 에셋이 생기면 이 리스트의 outfitSpriteId / weaponSpriteId / marks.spriteId 와 실제 Sprite 배열 인덱스를 맞춰서 연결하세요.")]
        public List<JobData> jobs = new List<JobData>();

        private Dictionary<string, JobData> lookup;

        public void BuildLookup()
        {
            lookup = new Dictionary<string, JobData>(StringComparer.OrdinalIgnoreCase);
            for (int i = 0; i < jobs.Count; i++)
            {
                JobData data = jobs[i];
                if (data == null || string.IsNullOrWhiteSpace(data.jobId))
                {
                    continue;
                }
                lookup[data.jobId] = data;
            }
        }

        public JobData Get(string jobId)
        {
            if (lookup == null)
            {
                BuildLookup();
            }

            if (string.IsNullOrWhiteSpace(jobId))
            {
                return null;
            }

            lookup.TryGetValue(jobId, out JobData result);
            return result;
        }

        public bool TryGetPromotedJob(string currentJobId, out JobData nextJob)
        {
            nextJob = null;
            JobData current = Get(currentJobId);
            if (current == null || string.IsNullOrWhiteSpace(current.promoteToJobId))
            {
                return false;
            }

            nextJob = Get(current.promoteToJobId);
            return nextJob != null;
        }

        public static JobDatabaseSO CreateRuntimeDefault()
        {
            JobDatabaseSO db = CreateInstance<JobDatabaseSO>();
            db.jobs = DefaultJobs.Create();
            db.BuildLookup();
            return db;
        }
    }

    public static class DefaultJobs
    {
        public static List<JobData> Create()
        {
            return new List<JobData>
            {
                Make("tank_apprentice", "견습 철갑", HunterPosition.Tanker, HunterStage.Apprentice, null, "tank_first", 160, 100, 90, 10, 16, 0.85f, 2.8f, new Color(0.85f, 0.72f, 0.15f), 0, 0),
                Make("tank_first", "철갑 입문", HunterPosition.Tanker, HunterStage.First, "tank_apprentice", "tank_second", 220, 110, 95, 14, 25, 1.00f, 2.85f, new Color(0.90f, 0.75f, 0.20f), 1, 1),
                Make("tank_second", "철갑 등봉", HunterPosition.Tanker, HunterStage.Second, "tank_first", "tank_third", 300, 120, 100, 18, 35, 1.20f, 2.90f, new Color(0.95f, 0.80f, 0.25f), 2, 2,
                    Mark(MarkSlot.Shoulder, MarkVisualType.ShoulderPlate, 201, new Color(1.00f, 0.84f, 0.25f), "어깨의 금색 징")),
                Make("tank_third", "철갑 화경", HunterPosition.Tanker, HunterStage.Third, "tank_second", null, 380, 130, 110, 24, 46, 1.40f, 3.00f, new Color(1.00f, 0.84f, 0.30f), 3, 3,
                    Mark(MarkSlot.Head, MarkVisualType.Mane, 301, new Color(1.00f, 0.86f, 0.30f), "머리 뒤 황금빛 갈기 포인트")),

                Make("dealer_apprentice", "견습 검객", HunterPosition.Dealer, HunterStage.Apprentice, null, "dealer_first", 120, 100, 95, 18, 8, 1.05f, 3.05f, new Color(0.86f, 0.20f, 0.22f), 4, 4),
                Make("dealer_first", "검객 입문", HunterPosition.Dealer, HunterStage.First, "dealer_apprentice", "dealer_second", 150, 105, 100, 26, 12, 1.25f, 3.10f, new Color(0.92f, 0.24f, 0.24f), 5, 5),
                Make("dealer_second", "검객 등봉", HunterPosition.Dealer, HunterStage.Second, "dealer_first", "dealer_third", 190, 110, 105, 36, 16, 1.50f, 3.15f, new Color(0.97f, 0.28f, 0.28f), 6, 6,
                    Mark(MarkSlot.Head, MarkVisualType.Headband, 202, new Color(0.97f, 0.20f, 0.20f), "이마의 붉은 띠")),
                Make("dealer_third", "검객 화경", HunterPosition.Dealer, HunterStage.Third, "dealer_second", null, 240, 115, 110, 48, 22, 1.80f, 3.20f, new Color(1.00f, 0.32f, 0.32f), 7, 7,
                    Mark(MarkSlot.Back, MarkVisualType.SmallFlag, 302, new Color(1.00f, 0.24f, 0.24f), "등의 붉은 등 장식(작은 깃발)")),

                Make("ranger_apprentice", "견습 신궁", HunterPosition.Ranger, HunterStage.Apprentice, null, "ranger_first", 115, 105, 100, 16, 9, 1.00f, 3.15f, new Color(0.24f, 0.76f, 0.25f), 8, 8),
                Make("ranger_first", "신궁 입문", HunterPosition.Ranger, HunterStage.First, "ranger_apprentice", "ranger_second", 145, 110, 105, 23, 13, 1.20f, 3.20f, new Color(0.28f, 0.82f, 0.30f), 9, 9),
                Make("ranger_second", "신궁 등봉", HunterPosition.Ranger, HunterStage.Second, "ranger_first", "ranger_third", 180, 115, 110, 32, 17, 1.45f, 3.25f, new Color(0.34f, 0.88f, 0.35f), 10, 10,
                    Mark(MarkSlot.Head, MarkVisualType.Feather, 203, new Color(0.35f, 0.90f, 0.40f), "머리의 녹색 깃털")),
                Make("ranger_third", "신궁 화경", HunterPosition.Ranger, HunterStage.Third, "ranger_second", null, 220, 120, 115, 42, 22, 1.70f, 3.35f, new Color(0.40f, 0.94f, 0.40f), 11, 11,
                    Mark(MarkSlot.Head, MarkVisualType.EyePattern, 303, new Color(0.45f, 1.00f, 0.45f), "눈가의 녹색 문양 포인트")),

                Make("support_apprentice", "견습 도사", HunterPosition.Supporter, HunterStage.Apprentice, null, "support_first", 130, 100, 105, 12, 10, 0.95f, 2.95f, new Color(0.15f, 0.86f, 0.92f), 12, 12),
                Make("support_first", "도사 입문", HunterPosition.Supporter, HunterStage.First, "support_apprentice", "support_second", 165, 105, 115, 16, 14, 1.10f, 3.00f, new Color(0.20f, 0.90f, 0.96f), 13, 13),
                Make("support_second", "도사 등봉", HunterPosition.Supporter, HunterStage.Second, "support_first", "support_third", 205, 110, 125, 22, 18, 1.28f, 3.05f, new Color(0.25f, 0.95f, 1.00f), 14, 14,
                    Mark(MarkSlot.Head, MarkVisualType.Hairpin, 204, new Color(0.30f, 0.95f, 1.00f), "머리 위 푸른색 상투 비녀")),
                Make("support_third", "도사 화경", HunterPosition.Supporter, HunterStage.Third, "support_second", null, 260, 120, 135, 30, 24, 1.48f, 3.10f, new Color(0.30f, 1.00f, 1.00f), 15, 15,
                    Mark(MarkSlot.Back, MarkVisualType.Talisman, 304, new Color(0.35f, 1.00f, 1.00f), "등 뒤에 떠 있는 푸른 부적 1장")),
            };
        }

        private static JobData Make(string id, string name, HunterPosition position, HunterStage stage, string from, string to, int hp, int hunger, int stamina, int attack, int defense, float huntPower, float moveSpeed, Color color, int outfitId, int weaponId, params JobMarkData[] marks)
        {
            return new JobData
            {
                jobId = id,
                displayName = name,
                position = position,
                stage = stage,
                promoteFromJobId = from,
                promoteToJobId = to,
                maxHP = hp,
                maxHunger = hunger,
                maxStamina = stamina,
                attack = attack,
                defense = defense,
                huntPower = huntPower,
                moveSpeed = moveSpeed,
                symbolicColor = color,
                outfitSpriteId = outfitId,
                weaponSpriteId = weaponId,
                marks = marks != null ? new List<JobMarkData>(marks) : new List<JobMarkData>(),
                note = "픽셀 아트가 들어오면 outfitSpriteId / weaponSpriteId / marks.spriteId 기준으로 실제 Sprite 매핑",
            };
        }

        private static JobMarkData Mark(MarkSlot slot, MarkVisualType visualType, int spriteId, Color tint, string description)
        {
            return new JobMarkData
            {
                slot = slot,
                visualType = visualType,
                spriteId = spriteId,
                tint = tint,
                description = description,
            };
        }
    }
}
