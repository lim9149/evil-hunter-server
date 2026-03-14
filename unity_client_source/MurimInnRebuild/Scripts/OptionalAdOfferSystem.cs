// DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
using System.Collections.Generic;
using UnityEngine;

namespace MurimInnRebuild
{
    public enum OptionalAdPlacement
    {
        AdShrine = 0,
        ResultScreen = 1,
        DailyPass = 2,
        DungeonRetry = 3,
        CommunityBoard = 4,
    }

    [System.Serializable]
    public sealed class OptionalAdOfferData
    {
        public string offerId;
        public OptionalAdPlacement placement;
        public string buttonLabel;
        public string rewardSummary;
        public int dailyCap = 1;
        public bool showOnlyAtNaturalBreaks = true;
    }

    public sealed class OptionalAdDirector : MonoBehaviour
    {
        [Tooltip("광고는 자동으로 재생하지 않고, 플레이어가 버튼을 눌렀을 때만 연다.")]
        public List<OptionalAdOfferData> offers = new List<OptionalAdOfferData>();

        public bool CanOfferNow(bool isPlayerBusy, bool duringBossIntro)
        {
            return !isPlayerBusy && !duringBossIntro;
        }

        public bool ShouldSuggest(OptionalAdOfferData offer, bool naturalBreak)
        {
            if (offer == null)
            {
                return false;
            }

            if (offer.showOnlyAtNaturalBreaks && !naturalBreak)
            {
                return false;
            }

            return true;
        }

        public static List<OptionalAdOfferData> CreateRuntimeDefault()
        {
            return new List<OptionalAdOfferData>
            {
                new OptionalAdOfferData { offerId = "ad_temple_gold_small", placement = OptionalAdPlacement.AdShrine, buttonLabel = "광고 보고 골드 받기", rewardSummary = "소량 골드 + 객잔 운영비 보충", dailyCap = 3 },
                new OptionalAdOfferData { offerId = "ad_pass_daily_1", placement = OptionalAdPlacement.DailyPass, buttonLabel = "광고 패스 진행", rewardSummary = "누적 시청 포인트 +1", dailyCap = 10 },
                new OptionalAdOfferData { offerId = "ad_dungeon_retry", placement = OptionalAdPlacement.DungeonRetry, buttonLabel = "광고 보고 1회 재도전", rewardSummary = "던전 입장권 1장", dailyCap = 2 },
            };
        }
    }
}
