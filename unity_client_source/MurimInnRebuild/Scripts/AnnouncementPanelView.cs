// DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
using System.Collections.Generic;
using UnityEngine;

namespace MurimInnRebuild
{
    public sealed class AnnouncementPanelView : MonoBehaviour
    {
        public ServerApiClient apiClient;
        [TextArea] public string latestDebugText;
        public List<AnnouncementDto> announcements = new List<AnnouncementDto>();

        public void RefreshAnnouncements()
        {
            StartCoroutine(apiClient.GetJson("/player/announcements", OnLoaded, OnError));
        }

        private void OnLoaded(string json)
        {
            AnnouncementListResponseDto dto = JsonUtility.FromJson<AnnouncementListResponseDto>(json);
            announcements = dto != null && dto.announcements != null ? new List<AnnouncementDto>(dto.announcements) : new List<AnnouncementDto>();
            latestDebugText = $"공지 {announcements.Count}개";
        }

        private void OnError(string message)
        {
            latestDebugText = message;
        }
    }
}
