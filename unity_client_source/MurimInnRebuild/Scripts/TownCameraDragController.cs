using UnityEngine;

namespace MurimInnRebuild
{
    public sealed class TownCameraDragController : MonoBehaviour
    {
        [SerializeField] private Camera targetCamera;
        [SerializeField] private float dragSpeed = 0.025f;
        [SerializeField] private float keyPanSpeed = 7.5f;
        [SerializeField] private Vector2 xBounds = new Vector2(-18f, 18f);
        [SerializeField] private Vector2 zBounds = new Vector2(-18f, 18f);

        private Vector3 lastPointerPosition;
        private bool dragging;

        private void Update()
        {
            if (targetCamera == null)
            {
                targetCamera = Camera.main;
            }
            if (targetCamera == null)
            {
                return;
            }

            HandleMouseDrag();
            HandleKeyboardPan();
            ClampCamera();
        }

        private void HandleMouseDrag()
        {
            if (Input.GetMouseButtonDown(1))
            {
                dragging = true;
                lastPointerPosition = Input.mousePosition;
            }
            else if (Input.GetMouseButtonUp(1))
            {
                dragging = false;
            }

            if (!dragging)
            {
                return;
            }

            Vector3 delta = Input.mousePosition - lastPointerPosition;
            lastPointerPosition = Input.mousePosition;
            Vector3 move = new Vector3(-delta.x, 0f, -delta.y) * dragSpeed;
            targetCamera.transform.position += move;
        }

        private void HandleKeyboardPan()
        {
            Vector3 direction = new Vector3(Input.GetAxisRaw("Horizontal"), 0f, Input.GetAxisRaw("Vertical"));
            if (direction.sqrMagnitude <= 0f)
            {
                return;
            }

            targetCamera.transform.position += new Vector3(direction.x, 0f, direction.z) * keyPanSpeed * Time.unscaledDeltaTime;
        }

        private void ClampCamera()
        {
            Vector3 pos = targetCamera.transform.position;
            pos.x = Mathf.Clamp(pos.x, xBounds.x, xBounds.y);
            pos.z = Mathf.Clamp(pos.z, zBounds.x, zBounds.y);
            targetCamera.transform.position = pos;
        }
    }
}
