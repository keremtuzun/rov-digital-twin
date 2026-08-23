using UnityEngine;

namespace ROVDigitalTwin
{
    public sealed class FollowCamera : MonoBehaviour
    {
        public Transform Target;
        public Vector3 Offset = new Vector3(0f, 3f, -7f);
        [Min(0.1f)] public float SmoothSpeed = 4f;

        private void LateUpdate()
        {
            if (Target == null) return;
            // Keep the operator view horizon-stabilized. A body-relative offset
            // makes the camera roll with an upset vehicle and can hide the ROV.
            Vector3 desired = Target.position + Offset;
            transform.position = Vector3.Lerp(transform.position, desired, 1f - Mathf.Exp(-SmoothSpeed * Time.deltaTime));
            transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(Target.position - transform.position, Vector3.up), 1f - Mathf.Exp(-SmoothSpeed * Time.deltaTime));
        }
    }
}
