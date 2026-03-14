// DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
using UnityEngine;

namespace MurimInnRebuild
{
    public enum HunterGender
    {
        Male = 0,
        Female = 1,
    }

    public enum HunterStage
    {
        Apprentice = 0,
        First = 1,
        Second = 2,
        Third = 3,
    }

    public enum HunterPosition
    {
        Tanker = 0,
        Dealer = 1,
        Ranger = 2,
        Supporter = 3,
    }

    public enum HunterState
    {
        Idle = 0,
        AwaitingCommand = 1,
        MovingToBoard = 2,
        MovingToHunt = 3,
        EngagingMonster = 4,
        ReturningToVillage = 5,
        MovingToFacility = 6,
        Recovering = 7,
        MovingToTraining = 8,
        Training = 9,
        Patrolling = 10,
        Selected = 11,
        Socializing = 12,
        BrowsingShop = 13,
        LearningSkill = 14,
        Crafting = 15,
        Wandering = 16,
        Dead = 17,
    }


    public enum HunterCommandType
    {
        None = 0,
        Hunt = 1,
        Train = 2,
        Rest = 3,
        Eat = 4,
        Heal = 5,
        Patrol = 6,
        Return = 7,
        Hold = 8,
        LearnSkill = 9,
        Craft = 10,
        ChangeClass = 11,
    }

    public enum NeedType
    {
        None = 0,
        HP = 1,
        Hunger = 2,
        Stamina = 3,
    }

    public enum FacilityType
    {
        Tavern = 0,
        Inn = 1,
        Clinic = 2,
        AdShrine = 3,
        CommunityBoard = 4,
        TrainingHall = 5,
        Forge = 6,
        SkillHall = 7,
    }

    public enum SharedAnimState
    {
        Idle = 0,
        Move = 1,
        Attack = 2,
        Hit = 3,
        Die = 4,
    }


    public enum HunterOperationStyle
    {
        Steady = 0,
        Vanguard = 1,
        Shadow = 2,
        Support = 3,
    }

    public enum HunterRestDiscipline
    {
        Frugal = 0,
        Measured = 1,
        Lavish = 2,
    }

    public enum HunterTrainingFocus
    {
        Body = 0,
        Weapon = 1,
        Mind = 2,
        Footwork = 3,
    }

    public enum MarkSlot
    {
        None = 0,
        Head = 1,
        Shoulder = 2,
        Back = 3,
    }

    public enum MarkVisualType
    {
        None = 0,
        Headband = 1,
        ShoulderPlate = 2,
        SpiritOrb = 3,
        Crown = 4,
        Mane = 5,
        SmallFlag = 6,
        Feather = 7,
        EyePattern = 8,
        Hairpin = 9,
        Talisman = 10,
    }
}
