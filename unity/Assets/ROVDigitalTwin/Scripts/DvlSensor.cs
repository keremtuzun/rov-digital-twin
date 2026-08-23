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
        public UnderwaterEnvironment Environment;
        [Range(0f, 1f)] public float QualityScale = 1f;
        [Min(0.01f)] public float SamplePeriodSeconds = 0.05f;

        private Rigidbody body;
        private float nextSampleTime;

        public Vector3 RelativeVelocityLocal { get; private set; }
        public float AltitudeMeters { get; private set; }
        public float Quality { get; private set; }
        public bool BottomLock => Quality > 0.5f;

        private void Awake()
        {
            body = GetComponent<Rigidbody>();
            Environment ??= FindAnyObjectByType<UnderwaterEnvironment>();
        }

        private void FixedUpdate()
        {
            if (Time.time < nextSampleTime)
                return;
            nextSampleTime = Time.time + SamplePeriodSeconds;
            Vector3 waterVelocity = CurrentField != null ? CurrentField.Sample(transform.position, Time.time) : Vector3.zero;
            RelativeVelocityLocal = transform.InverseTransformDirection(body.linearVelocity - waterVelocity) + SensorNoise.GaussianVector(VelocityNoise);
            if (Physics.Raycast(transform.position, Vector3.down, out RaycastHit hit, MaxAltitudeMeters, SeafloorMask, QueryTriggerInteraction.Ignore))
            {
                AltitudeMeters = hit.distance;
                float environmentalQuality = Environment != null ? Environment.AcousticQuality01 : 1f;
                Quality = Mathf.Clamp01(1f - hit.distance / MaxAltitudeMeters * 0.35f)
                          * QualityScale * environmentalQuality;
            }
            else
            {
                AltitudeMeters = MaxAltitudeMeters;
                Quality = 0f;
            }
        }
    }
}
