using UnityEngine;

namespace MurimInnRebuild
{
    public sealed class HunterSpeechBubblePresenter : MonoBehaviour
    {
        [SerializeField] private HunterSystemManager hunterSystemManager;
        [TextArea] [SerializeField] private string debugPreview;

        private void Update()
        {
            if (hunterSystemManager == null)
            {
                return;
            }

            HunterProfile selected = hunterSystemManager.GetSelectedHunter();
            debugPreview = selected != null ? selected.lastSpokenLine : string.Empty;
        }
    }
}
