// DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
using UnityEngine;

namespace MurimInnRebuild
{
    public sealed class StoryPanelView : MonoBehaviour
    {
        public StoryChapterCatalogSO storyCatalog;
        public ServerApiClient apiClient;
        public string accountId = "acc_demo";
        [SerializeField] private string currentChapterId = "prologue_burning_ledgers";
        [SerializeField] private bool fallbackToFirstChapter = true;
        [TextArea] public string latestDebugText;

        public StoryChapterData CurrentChapter
        {
            get
            {
                var chapters = storyCatalog != null ? storyCatalog.chapters : null;
                if (chapters == null || chapters.Count == 0) return null;
                for (int i = 0; i < chapters.Count; i++)
                {
                    if (chapters[i].chapterId == currentChapterId) return chapters[i];
                }
                return fallbackToFirstChapter ? chapters[0] : null;
            }
        }

        public void RefreshFromServer()
        {
            StartCoroutine(apiClient.GetJson($"/story/chapters?accountId={accountId}", OnLoaded, OnError));
        }

        public void SetCurrentChapter(string chapterId)
        {
            if (!string.IsNullOrWhiteSpace(chapterId)) currentChapterId = chapterId;
        }

        public string BuildSummaryText()
        {
            StoryChapterData chapter = CurrentChapter;
            if (chapter == null) return "스토리 데이터가 없습니다.";
            return $"{chapter.title}
목표: {chapter.goal}
{chapter.summary}
추천 연출: {chapter.directionNote}";
        }

        private void OnLoaded(string json)
        {
            StoryChaptersResponseDto dto = JsonUtility.FromJson<StoryChaptersResponseDto>(json);
            if (dto != null && dto.progress != null && !string.IsNullOrWhiteSpace(dto.progress.currentChapterId))
            {
                currentChapterId = dto.progress.currentChapterId;
            }
            latestDebugText = BuildSummaryText();
        }

        private void OnError(string message)
        {
            latestDebugText = message;
        }
    }
}
