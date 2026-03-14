using System;

[Serializable]
public sealed class HunterDto
{
    public string hunterId;
    public string accountId;
    public int slotIndex;
    public string name;
    public string jobId;
    public int level;
    public int exp;
    public float powerScore;
    public float hp;
    public float atk;
    public float defense;
    public string tierId;
    public string seasonId;
    public string mbti;
    public string aiMode;
    public string preferredActivity;
    public string assignedHuntZoneId;
    public int desiredLoopCount;
    public float morale;
    public float fatigue;
    public float satiety;
    public float stamina;
    public float bagLoad;
    public float durability;
    public float loyalty;
}

[Serializable]
public sealed class HunterArrayWrapper
{
    public HunterDto[] items;
}

[Serializable]
public sealed class CreateHunterRequest
{
    public string hunterId;
    public string accountId;
    public int slotIndex;
    public string name;
}
