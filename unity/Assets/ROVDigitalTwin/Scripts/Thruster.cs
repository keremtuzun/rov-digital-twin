using UnityEngine;

namespace ROVDigitalTwin
{
    [DisallowMultipleComponent]
    public sealed class Thruster : MonoBehaviour
    {
        [Min(0.1f)] public float MaxForceNewtons = 50f;
        [Range(-1f, 1f)] public float Command;
        [Range(0f, 1f)] public float Efficiency = 1f;
        [Min(0.01f)] public float ResponseTimeSeconds = 0.14f;
        [Min(0.1f)] public float MaximumCommandRatePerSecond = 4f;
        public bool DrawDebugForce = true;

        private Rigidbody body;
        private float requestedCommand;

        public float AppliedForceNewtons => Command * MaxForceNewtons * Efficiency;
        public float RequestedCommand => requestedCommand;

        public void Initialize(Rigidbody targetBody) => body = targetBody;

        public void SetCommand(float value) => requestedCommand = Mathf.Clamp(value, -1f, 1f);

        public void StopImmediately()
        {
            requestedCommand = 0f;
            Command = 0f;
        }

        private void Awake()
        {
            if (body == null)
                body = GetComponentInParent<Rigidbody>();
        }

        private void FixedUpdate()
        {
            if (body == null)
                return;
            float filtered = Mathf.Lerp(Command, requestedCommand,
                1f - Mathf.Exp(-Time.fixedDeltaTime / ResponseTimeSeconds));
            Command = Mathf.MoveTowards(Command, filtered,
                MaximumCommandRatePerSecond * Time.fixedDeltaTime);
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
