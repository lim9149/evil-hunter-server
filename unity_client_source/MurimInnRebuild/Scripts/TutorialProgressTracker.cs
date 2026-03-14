// DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
using System.Collections.Generic;
using UnityEngine;

namespace MurimInnRebuild
{
    public sealed class TutorialProgressTracker : MonoBehaviour
    {
        public GuideQuestCatalogSO guideCatalog;
        public ServerApiClient apiClient;
        public string accountId = "acc_demo";
        [SerializeField] private bool saveToPlayerPrefs = true;
        [SerializeField] private string saveKey = "murim_tutorial_completed";
        private readonly HashSet<string> completedQuestIds = new HashSet<string>();

        private void Awake()
        {
            if (!saveToPlayerPrefs) return;
            string raw = PlayerPrefs.GetString(saveKey, string.Empty);
            if (string.IsNullOrWhiteSpace(raw)) return;
            string[] parts = raw.Split('|');
            for (int i = 0; i < parts.Length; i++) if (!string.IsNullOrWhiteSpace(parts[i])) completedQuestIds.Add(parts[i]);
        }

        public void RefreshFromServer()
        {
            StartCoroutine(apiClient.GetJson($"/tutorial/progress/{accountId}", OnLoaded, Debug.LogWarning));
        }

        public bool IsCompleted(string questId) => completedQuestIds.Contains(questId);

        public void MarkCompleted(string questId)
        {
            if (string.IsNullOrWhiteSpace(questId)) return;
            string body = JsonUtility.ToJson(new TutorialQuestCompleteReqDto { accountId = accountId, questId = questId });
            StartCoroutine(apiClient.PostJson("/tutorial/progress/complete", body, _ => { completedQuestIds.Add(questId); SaveLocal(); }, Debug.LogWarning));
        }

        public GuideQuestData GetNextRequiredQuest()
        {
            if (guideCatalog == null) return null;
            for (int i = 0; i < guideCatalog.quests.Count; i++)
            {
                GuideQuestData quest = guideCatalog.quests[i];
                if (!quest.isOptionalAdQuest && !completedQuestIds.Contains(quest.questId)) return quest;
            }
            return null;
        }

        private void OnLoaded(string json)
        {
            TutorialProgressRowsDto dto = JsonUtility.FromJson<TutorialProgressRowsDto>(json);
            completedQuestIds.Clear();
            if (dto != null && dto.completedQuestIds != null)
            {
                for (int i = 0; i < dto.completedQuestIds.Count; i++) completedQuestIds.Add(dto.completedQuestIds[i]);
            }
            SaveLocal();
        }

        private void SaveLocal()
        {
            if (!saveToPlayerPrefs) return;
            PlayerPrefs.SetString(saveKey, string.Join("|", completedQuestIds));
            PlayerPrefs.Save();
        }
    }
}
