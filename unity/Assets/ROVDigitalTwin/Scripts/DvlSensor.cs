using UnityEngine;

namespace ROVDigitalTwin
{
    [RequireComponent(typeof(Rigidbody))]
    public sealed class DvlSensor : MonoBehaviour
    {
        public LayerMask SeafloorMask = ~0;
        [Min(0.1f)] public float MaxAltitudeMeters = 30f;
        [Min(0f)] public float VelocityNoise = 0.01f;
        public WaterCurrentField CurrentField;

        private Rigidbody body;

        public Vector3 RelativeVelocityLocal { get; private set; }
        public float AltitudeMeters { get; private set; }
        public float Quality { get; private set; }
        public bool BottomLock => Quality > 0.5f;

        private void Awake() => body = GetComponent<Rigidbody>();

        private void FixedUpdate()
        {
            Vector3 waterVelocity = CurrentField != null ? CurrentField.Sample(transform.position, Time.time) : Vector3.zero;
            RelativeVelocityLocal = transform.InverseTransformDirection(body.linearVelocity - waterVelocity) + SensorNoise.GaussianVector(VelocityNoise);
            if (Physics.Raycast(transform.position, Vector3.down, out RaycastHit hit, MaxAltitudeMeters, SeafloorMask, QueryTriggerInteraction.Ignore))
            {
                AltitudeMeters = hit.distance;
                Quality = Mathf.Clamp01(1f - hit.distance / MaxAltitudeMeters * 0.35f);
            }
            else
            {
                AltitudeMeters = MaxAltitudeMeters;
                Quality = 0f;
            }
        }
    }
}
