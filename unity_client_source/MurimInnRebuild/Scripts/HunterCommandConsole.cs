using UnityEngine;

namespace MurimInnRebuild
{
    public sealed class HunterCommandConsole : MonoBehaviour
    {
        [SerializeField] private HunterSystemManager hunterSystemManager;
        [SerializeField] private int huntMonsterCount = 3;

        private void Update()
        {
            if (hunterSystemManager == null)
            {
                return;
            }

            if (Input.GetKeyDown(KeyCode.Tab))
            {
                hunterSystemManager.SelectNextHunter();
            }

            HunterProfile selected = hunterSystemManager.GetSelectedHunter();
            if (selected == null)
            {
                return;
            }

            if (Input.GetKeyDown(KeyCode.H)) hunterSystemManager.IssueCommandToHunter(selected.hunterId, HunterCommandType.Hunt, huntMonsterCount);
            else if (Input.GetKeyDown(KeyCode.T)) hunterSystemManager.IssueCommandToHunter(selected.hunterId, HunterCommandType.Train, 1);
            else if (Input.GetKeyDown(KeyCode.R)) hunterSystemManager.IssueCommandToHunter(selected.hunterId, HunterCommandType.Rest, 1);
            else if (Input.GetKeyDown(KeyCode.E)) hunterSystemManager.IssueCommandToHunter(selected.hunterId, HunterCommandType.Eat, 1);
            else if (Input.GetKeyDown(KeyCode.C)) hunterSystemManager.IssueCommandToHunter(selected.hunterId, HunterCommandType.Heal, 1);
            else if (Input.GetKeyDown(KeyCode.P)) hunterSystemManager.IssueCommandToHunter(selected.hunterId, HunterCommandType.Patrol, 1);
            else if (Input.GetKeyDown(KeyCode.B)) hunterSystemManager.IssueCommandToHunter(selected.hunterId, HunterCommandType.Return, 1);
            else if (Input.GetKeyDown(KeyCode.K)) hunterSystemManager.IssueCommandToHunter(selected.hunterId, HunterCommandType.LearnSkill, 1);
            else if (Input.GetKeyDown(KeyCode.F)) hunterSystemManager.IssueCommandToHunter(selected.hunterId, HunterCommandType.Craft, 1);
            else if (Input.GetKeyDown(KeyCode.V)) hunterSystemManager.IssueCommandToHunter(selected.hunterId, HunterCommandType.ChangeClass, 1);
            else if (Input.GetKeyDown(KeyCode.Space)) hunterSystemManager.IssueCommandToHunter(selected.hunterId, HunterCommandType.Hold, 1);
        }
    }
}
