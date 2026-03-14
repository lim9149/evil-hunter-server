// DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
using System;
using System.Collections.Generic;
using UnityEngine;

namespace MurimInnRebuild
{
    public sealed class OptionalAdOfferPresenter : MonoBehaviour
    {
        private string naturalBreakContext = "generic_break";
        public OptionalAdDirector director;
        public ServerApiClient apiClient;
        public string accountId = "acc_demo";
        public bool isPlayerBusy;
        public bool duringBossIntro;
        public bool naturalBreak = true;
        public float refreshCooldownSec = 3f;

        private float lastRefreshAt = -999f;
        private readonly Dictionary<string, string> sessionTokenByOfferId = new Dictionary<string, string>();
        private readonly Dictionary<string, string> completionTokenByOfferId = new Dictionary<string, string>();
        private readonly Dictionary<string, long> offerExpiryById = new Dictionary<string, long>();

        public List<OptionalAdOfferData> GetVisibleOffers()
        {
            List<OptionalAdOfferData> result = new List<OptionalAdOfferData>();
            if (director == null || !director.CanOfferNow(isPlayerBusy, duringBossIntro)) return result;
            for (int i = 0; i < director.offers.Count; i++)
            {
                OptionalAdOfferData offer = director.offers[i];
                if (director.ShouldSuggest(offer, naturalBreak)) result.Add(offer);
            }
            return result;
        }

        public bool CanRequestFreshSession() => Time.unscaledTime - lastRefreshAt >= refreshCooldownSec;

        public void RequestSession(string offerId, string placement)
        {
            if (!CanRequestFreshSession()) return;
            lastRefreshAt = Time.unscaledTime;
            string body = JsonUtility.ToJson(new AdSessionStartReqDto { accountId = accountId, offerId = offerId, placement = placement });
            StartCoroutine(apiClient.PostJson("/ads/session/start", body, json =>
            {
                AdSessionStartResponseDto dto = JsonUtility.FromJson<AdSessionStartResponseDto>(json);
                if (dto != null)
                {
                    sessionTokenByOfferId[offerId] = dto.adViewToken;
                    offerExpiryById[offerId] = dto.expiresAt;
                }
            }, Debug.LogWarning));
        }

        public void MarkAdCompleted(string offerId, string placement, string sdkProof)
        {
            if (!sessionTokenByOfferId.TryGetValue(offerId, out string adViewToken)) return;
            string body = JsonUtility.ToJson(new AdSessionCompleteReqDto
            {
                accountId = accountId,
                offerId = offerId,
                adViewToken = adViewToken,
                placement = placement,
                adNetwork = "rewarded",
                adUnitId = offerId,
                completionProof = sdkProof
            });
            StartCoroutine(apiClient.PostJson("/ads/session/complete", body, json =>
            {
                AdSessionCompleteResponseDto dto = JsonUtility.FromJson<AdSessionCompleteResponseDto>(json);
                if (dto != null) completionTokenByOfferId[offerId] = dto.completionToken;
            }, Debug.LogWarning));
        }

        public void ClaimReward(string offerId, string placement)
        {
            if (!sessionTokenByOfferId.TryGetValue(offerId, out string adViewToken)) return;
            if (!completionTokenByOfferId.TryGetValue(offerId, out string completionToken)) return;
            string body = JsonUtility.ToJson(new AdClaimReqDto
            {
                accountId = accountId,
                offerId = offerId,
                adViewToken = adViewToken,
                completionToken = completionToken,
                placement = placement,
                adNetwork = "rewarded",
                adUnitId = offerId
            });
            StartCoroutine(apiClient.PostJson("/ads/reward-claim", body, _ => { }, Debug.LogWarning));
        }

        public bool HasUsableSession(string offerId)
        {
            if (string.IsNullOrWhiteSpace(offerId) || !offerExpiryById.TryGetValue(offerId, out long expiresAt)) return false;
            long now = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
            return expiresAt > now;
        }
    }
}
