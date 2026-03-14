// DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
using System;
using System.Collections.Generic;

namespace MurimInnRebuild
{
    [Serializable] public sealed class StoryProgressDto { public string accountId; public string currentChapterId; public string updatedAt; }
    [Serializable] public sealed class StoryChaptersResponseDto { public string workingTitle; public List<StoryChapterData> chapters; public StoryProgressDto progress; public List<AnnouncementDto> announcements; }
    [Serializable] public sealed class TutorialQuestResponseDto { public string workingTitle; public List<GuideQuestData> quests; public string nextRequiredQuestId; }
    [Serializable] public sealed class TutorialProgressRowsDto { public string accountId; public List<string> completedQuestIds; }
    [Serializable] public sealed class TutorialQuestCompleteReqDto { public string accountId; public string questId; }
    [Serializable] public sealed class AdRewardDto { public string type; public string label; public int amount; }
    [Serializable] public sealed class AdSessionStartReqDto { public string accountId; public string offerId; public string placement; }
    [Serializable] public sealed class AdSessionStartResponseDto { public string accountId; public string offerId; public string adViewToken; public string placement; public long expiresAt; public AdRewardDto rewardPreview; }
    [Serializable] public sealed class AdSessionCompleteReqDto { public string accountId; public string offerId; public string adViewToken; public string placement; public string adNetwork; public string adUnitId; public string completionProof; }
    [Serializable] public sealed class AdSessionCompleteResponseDto { public string accountId; public string offerId; public string adViewToken; public string completionToken; public string status; public long verifiedAt; }
    [Serializable] public sealed class AdClaimReqDto { public string accountId; public string offerId; public string adViewToken; public string completionToken; public string placement; public string adNetwork; public string adUnitId; }
    [Serializable] public sealed class AdClaimResponseDto { public string accountId; public string offerId; public string adViewToken; public string status; public AdRewardDto reward; public int dailyClaimCount; public int dailyCap; public string note; }
    [Serializable] public sealed class MailboxMessageDto { public string messageId; public string title; public string body; public string rewardCurrency; public int rewardAmount; public bool isClaimed; }
    [Serializable] public sealed class MailboxListResponseDto { public string accountId; public List<MailboxMessageDto> messages; }
    [Serializable] public sealed class AnnouncementDto { public string announcementId; public string title; public string body; public int startsAt; public int endsAt; public int priority; }
    [Serializable] public sealed class AnnouncementListResponseDto { public List<AnnouncementDto> announcements; }
    [Serializable] public sealed class TelemetryEventDto { public string accountId; public string eventType; public string eventName; public string payloadJson; }
    [Serializable] public sealed class TelemetryBatchDto { public List<TelemetryEventDto> events; }
}


[System.Serializable]
public sealed class TownFacilityAnchorDto
{
    public string facilityId;
    public string label;
    public string kind;
    public float x;
    public float y;
    public float z;
}

[System.Serializable]
public sealed class TownMonsterZoneDto
{
    public string zoneId;
    public string label;
    public int difficulty;
    public int spawnCount;
    public float x;
    public float y;
    public float z;
    public float radius;
}

[System.Serializable]
public sealed class TownHudRulesDto
{
    public bool useOverlayPanels;
    public bool battleSceneAllowed;
    public bool optionalAdsOnlyAtBreaks;
    public bool mailboxButton;
    public bool announcementButton;
    public bool storyButton;
}

[System.Serializable]
public sealed class TownWorldDefinitionDto
{
    public string worldId;
    public string worldName;
    public string sceneName;
    public string cameraMode;
    public TownFacilityAnchorDto[] facilities;
    public TownMonsterZoneDto[] monsterZones;
    public TownHudRulesDto hudRules;
}

[System.Serializable]
public sealed class TownWorldSnapshotDto
{
    public string accountId;
    public string worldId;
    public string[] recommendedFlow;
}
