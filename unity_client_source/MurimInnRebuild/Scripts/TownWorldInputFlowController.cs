using System.Collections.Generic;
using UnityEngine;

namespace MurimInnRebuild
{
    public sealed class TownWorldInputFlowController : MonoBehaviour
    {
        [SerializeField] private HunterSystemManager hunterSystemManager;
        [SerializeField] private TownWorldHudController hudController;
        [SerializeField] private Camera worldCamera;
        [SerializeField] private KeyCode nextHunterKey = KeyCode.Tab;
        [SerializeField] private KeyCode focusTownKey = KeyCode.Space;
        [SerializeField] private KeyCode mailboxKey = KeyCode.M;
        [SerializeField] private KeyCode storyKey = KeyCode.J;
        [SerializeField] private LayerMask groundMask = ~0;

        private int selectedIndex = -1;
        private readonly List<float> timeScaleCycle = new List<float> { 1f, 1.5f, 2f };
        private int timeScaleIndex;

        public HunterProfile SelectedHunter
        {
            get
            {
                if (hunterSystemManager == null || hunterSystemManager.Hunters.Count == 0 || selectedIndex < 0) return null;
                return hunterSystemManager.Hunters[selectedIndex];
            }
        }

        private void Update()
        {
            if (hunterSystemManager == null) return;
            if (Input.GetKeyDown(nextHunterKey)) SelectNextHunter();
            if (Input.GetKeyDown(focusTownKey)) FocusSelection();
            if (Input.GetKeyDown(KeyCode.Alpha1)) SetTimeScaleIndex(0);
            if (Input.GetKeyDown(KeyCode.Alpha2)) SetTimeScaleIndex(1);
            if (Input.GetKeyDown(KeyCode.Alpha3)) SetTimeScaleIndex(2);
            if (Input.GetKeyDown(mailboxKey)) hudController?.ShowMailbox();
            if (Input.GetKeyDown(storyKey)) hudController?.ShowStory();
            if (Input.GetMouseButtonDown(0)) TrySelectByPointer();
        }

        public void SelectNextHunter()
        {
            HunterProfile selected = hunterSystemManager.SelectNextHunter();
            if (selected == null)
            {
                selectedIndex = -1;
                return;
            }

            selectedIndex = hunterSystemManager.SelectedHunterIndex;
            FocusSelection();
        }

        public void FocusSelection()
        {
            HunterProfile selected = SelectedHunter;
            if (selected == null || worldCamera == null) return;
            Vector3 focus = selected.worldPosition + new Vector3(-6.0f, 8.5f, -6.0f);
            worldCamera.transform.position = Vector3.Lerp(worldCamera.transform.position, focus, 0.85f);
        }

        public void SetTimeScaleIndex(int index)
        {
            timeScaleIndex = Mathf.Clamp(index, 0, timeScaleCycle.Count - 1);
            Time.timeScale = timeScaleCycle[timeScaleIndex];
        }

        private void TrySelectByPointer()
        {
            if (worldCamera == null)
            {
                return;
            }

            Ray ray = worldCamera.ScreenPointToRay(Input.mousePosition);
            if (Physics.Raycast(ray, out RaycastHit hit, 200f, groundMask))
            {
                HunterProfile selected = hunterSystemManager.SelectNearestHunter(hit.point);
                if (selected != null)
                {
                    selectedIndex = hunterSystemManager.SelectedHunterIndex;
                    FocusSelection();
                }
            }
            else
            {
                Plane plane = new Plane(Vector3.up, Vector3.zero);
                if (plane.Raycast(ray, out float enter))
                {
                    Vector3 point = ray.GetPoint(enter);
                    HunterProfile selected = hunterSystemManager.SelectNearestHunter(point);
                    if (selected != null)
                    {
                        selectedIndex = hunterSystemManager.SelectedHunterIndex;
                        FocusSelection();
                    }
                }
            }
        }
    }
}
