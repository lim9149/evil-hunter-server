// DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
using UnityEngine;

namespace MurimInnRebuild
{
    public sealed class TownWorldHudController : MonoBehaviour
    {
        [Header("Overlay Panels")]
        public GameObject storyPanel;
        public GameObject mailboxPanel;
        public GameObject announcementPanel;
        public GameObject probabilityPanel;

        public void ShowStory() => ToggleOnly(storyPanel);
        public void ShowMailbox() => ToggleOnly(mailboxPanel);
        public void ShowAnnouncement() => ToggleOnly(announcementPanel);
        public void ShowProbability() => ToggleOnly(probabilityPanel);
        public void HideAll() => ToggleOnly(null);

        private void ToggleOnly(GameObject target)
        {
            SetPanel(storyPanel, target == storyPanel);
            SetPanel(mailboxPanel, target == mailboxPanel);
            SetPanel(announcementPanel, target == announcementPanel);
            SetPanel(probabilityPanel, target == probabilityPanel);
        }

        private static void SetPanel(GameObject panel, bool active)
        {
            if (panel != null) panel.SetActive(active);
        }
    }
}
