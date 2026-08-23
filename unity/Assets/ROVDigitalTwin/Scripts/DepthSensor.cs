using UnityEngine;

namespace ROVDigitalTwin
{
    public sealed class DepthSensor : MonoBehaviour
    {
        public float WaterSurfaceY = 0f;
        [Min(0f)] public float NoiseStandardDeviationMeters = 0.01f;
        [Min(0f)] public float MaxDepthMeters = 100f;
        public float BiasMeters;
        [Min(0.01f)] public float SamplePeriodSeconds = 0.05f;

        public float DepthMeters { get; private set; }
        public float PressureKpa { get; private set; }
        private float nextSampleTime;

        private void FixedUpdate()
        {
            if (Time.time < nextSampleTime)
                return;
            nextSampleTime = Time.time + SamplePeriodSeconds;
            DepthMeters = Mathf.Clamp(WaterSurfaceY - transform.position.y + BiasMeters + SensorNoise.Gaussian(NoiseStandardDeviationMeters), 0f, MaxDepthMeters);
            PressureKpa = 101.325f + DepthMeters * 10.06f;
        }
    }
}
