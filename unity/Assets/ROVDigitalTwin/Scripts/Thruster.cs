using UnityEngine;

namespace ROVDigitalTwin
{
    [DisallowMultipleComponent]
    public sealed class Thruster : MonoBehaviour
    {
        [Min(0.1f)] public float MaxForceNewtons = 50f;
        [Range(-1f, 1f)] public float Command;
        public bool DrawDebugForce = true;

        private Rigidbody body;

        public float AppliedForceNewtons => Command * MaxForceNewtons;

        public void Initialize(Rigidbody targetBody) => body = targetBody;

        public void SetCommand(float value) => Command = Mathf.Clamp(value, -1f, 1f);

        private void Awake()
        {
            if (body == null)
                body = GetComponentInParent<Rigidbody>();
        }

        private void FixedUpdate()
        {
            if (body == null)
                return;
            body.AddForceAtPosition(transform.forward * AppliedForceNewtons, transform.position, ForceMode.Force);
        }

        private void OnDrawGizmosSelected()
        {
            if (!DrawDebugForce)
                return;
            Gizmos.color = Command >= 0f ? Color.cyan : Color.magenta;
            Gizmos.DrawRay(transform.position, transform.forward * Mathf.Lerp(0.25f, 1.5f, Mathf.Abs(Command)));
        }
    }
}
