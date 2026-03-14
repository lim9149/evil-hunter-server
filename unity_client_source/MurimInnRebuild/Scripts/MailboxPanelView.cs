// DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
using System;
using System.Collections.Generic;
using UnityEngine;

namespace MurimInnRebuild
{
    public sealed class MailboxPanelView : MonoBehaviour
    {
        public ServerApiClient apiClient;
        public string accountId = "acc_demo";
        [TextArea] public string latestDebugText;
        public List<MailboxMessageDto> cachedMessages = new List<MailboxMessageDto>();

        public void RefreshMailbox()
        {
            StartCoroutine(apiClient.GetJson($"/player/mailbox/{accountId}", OnMailboxLoaded, OnError));
        }

        public void ClaimMessage(string messageId)
        {
            StartCoroutine(apiClient.PostJson($"/player/mailbox/{messageId}/claim", "{}", _ => RefreshMailbox(), OnError));
        }

        private void OnMailboxLoaded(string json)
        {
            MailboxListResponseDto dto = JsonUtility.FromJson<MailboxListResponseDto>(json);
            cachedMessages = dto != null && dto.messages != null ? new List<MailboxMessageDto>(dto.messages) : new List<MailboxMessageDto>();
            latestDebugText = dto == null ? "우편함 파싱 실패" : $"우편 {cachedMessages.Count}개";
        }

        private void OnError(string message)
        {
            latestDebugText = message;
        }
    }
}
