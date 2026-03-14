using System.Collections.Generic;
using UnityEngine;

namespace MurimInnRebuild
{
    public sealed class TownBuildingPlacementSystem : MonoBehaviour
    {
        [System.Serializable]
        public sealed class PlaceableBuilding
        {
            public string buildingId;
            public FacilityType facilityType;
            public Transform root;
            public Vector2Int gridSize = Vector2Int.one;
            public bool essential = true;
        }

        [SerializeField] private Vector3 gridOrigin = Vector3.zero;
        [SerializeField] private float gridSize = 1.0f;
        [SerializeField] private List<PlaceableBuilding> buildings = new List<PlaceableBuilding>();

        private readonly Dictionary<string, Vector2Int> occupiedCells = new Dictionary<string, Vector2Int>();

        public IReadOnlyList<PlaceableBuilding> Buildings => buildings;

        public bool MoveBuilding(string buildingId, Vector2Int cell)
        {
            PlaceableBuilding building = buildings.Find(x => x != null && x.buildingId == buildingId);
            if (building == null || building.root == null)
            {
                return false;
            }

            occupiedCells[buildingId] = cell;
            building.root.position = CellToWorld(cell);
            return true;
        }

        public Vector3 CellToWorld(Vector2Int cell)
        {
            return gridOrigin + new Vector3(cell.x * gridSize, 0f, cell.y * gridSize);
        }

        public Vector2Int WorldToCell(Vector3 point)
        {
            Vector3 local = point - gridOrigin;
            return new Vector2Int(Mathf.RoundToInt(local.x / Mathf.Max(0.1f, gridSize)), Mathf.RoundToInt(local.z / Mathf.Max(0.1f, gridSize)));
        }

        public void SnapAllToGrid()
        {
            for (int i = 0; i < buildings.Count; i++)
            {
                PlaceableBuilding building = buildings[i];
                if (building == null || building.root == null)
                {
                    continue;
                }
                Vector2Int cell = WorldToCell(building.root.position);
                MoveBuilding(building.buildingId, cell);
            }
        }
    }
}
