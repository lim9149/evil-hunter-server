// DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
using UnityEngine;

namespace MurimInnRebuild
{
    public sealed class TownWorldDirector : MonoBehaviour
    {
        [SerializeField] private HunterSystemManager hunterSystemManager;
        [SerializeField] private TownWorldHudController hudController;
        [SerializeField] private OptionalAdOfferPresenter adOfferPresenter;
        [SerializeField] private float hudRefreshSeconds = 1.0f;

        private float timer;

        private void Update()
        {
            timer += Time.deltaTime;
            if (timer < hudRefreshSeconds)
            {
                return;
            }

            timer = 0f;

            if (hunterSystemManager == null)
            {
                return;
            }

            int restingCount = 0;
            foreach (HunterProfile hunter in hunterSystemManager.Hunters)
            {
                if (hunter.state == HunterState.Recovering)
                {
                    restingCount++;
                }
            }

            if (restingCount > 0 && adOfferPresenter != null)
            {
                adOfferPresenter.SetNaturalBreakContext("rest_window");
            }
        }

        public void OpenMailbox() => hudController?.ShowMailbox();
        public void OpenStory() => hudController?.ShowStory();
        public void OpenAnnouncements() => hudController?.ShowAnnouncement();
    }
}
