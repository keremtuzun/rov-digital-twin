using UnityEngine;

namespace ROVDigitalTwin
{
    public sealed class ForwardSonarSensor : MonoBehaviour
    {
        [Range(4, 64)] public int RayCount = 16;
        [Range(5f, 180f)] public float HorizontalFieldOfView = 90f;
        [Min(0.1f)] public float MaxRangeMeters = 15f;
        public LayerMask DetectionMask = ~0;
        public UnderwaterEnvironment Environment;
        [Min(0f)] public float NoiseStandardDeviationMeters = 0.01f;
        [Min(0.01f)] public float SamplePeriodSeconds = 0.1f;

        public float[] Distances { get; private set; }
        private float nextSampleTime;

        private void Awake()
        {
            Distances = new float[RayCount];
            Environment ??= FindAnyObjectByType<UnderwaterEnvironment>();
        }

        private void FixedUpdate()
        {
            if (Time.time < nextSampleTime)
                return;
            nextSampleTime = Time.time + SamplePeriodSeconds;
            if (Distances == null || Distances.Length != RayCount)
                Distances = new float[RayCount];
            for (int index = 0; index < RayCount; index++)
            {
                float t = RayCount == 1 ? 0.5f : index / (float)(RayCount - 1);
                float yaw = Mathf.Lerp(-HorizontalFieldOfView * 0.5f, HorizontalFieldOfView * 0.5f, t);
                Vector3 direction = Quaternion.AngleAxis(yaw, transform.up) * transform.forward;
                float distance = Physics.Raycast(transform.position, direction, out RaycastHit hit, MaxRangeMeters, DetectionMask, QueryTriggerInteraction.Ignore)
                    ? hit.distance
                    : MaxRangeMeters;
                float environmentalNoise = Environment != null
                    ? 1f + Environment.TurbidityNtu * 0.08f + Environment.Contamination01 * 0.5f : 1f;
                Distances[index] = Mathf.Clamp(distance
                    + SensorNoise.Gaussian(NoiseStandardDeviationMeters * environmentalNoise), 0f, MaxRangeMeters);
            }
        }

        public float NormalizedDistance(int index) =>
            Distances == null || index < 0 || index >= Distances.Length ? 1f : Distances[index] / MaxRangeMeters;

        private void OnDrawGizmosSelected()
        {
            Gizmos.color = Color.green;
            int count = Mathf.Max(2, RayCount);
            for (int index = 0; index < count; index++)
            {
                float yaw = Mathf.Lerp(-HorizontalFieldOfView * 0.5f, HorizontalFieldOfView * 0.5f, index / (float)(count - 1));
                Gizmos.DrawRay(transform.position, Quaternion.AngleAxis(yaw, transform.up) * transform.forward * MaxRangeMeters);
            }
        }
    }
}
