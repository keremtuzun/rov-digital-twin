using UnityEngine;

namespace ROVDigitalTwin
{
    public sealed class DepthSensor : MonoBehaviour
    {
        public float WaterSurfaceY = 0f;
        [Min(0f)] public float NoiseStandardDeviationMeters = 0.01f;
        [Min(0f)] public float MaxDepthMeters = 100f;
        public float BiasMeters;

        public float DepthMeters { get; private set; }
        public float PressureKpa { get; private set; }

        private void FixedUpdate()
        {
            DepthMeters = Mathf.Clamp(WaterSurfaceY - transform.position.y + BiasMeters + SensorNoise.Gaussian(NoiseStandardDeviationMeters), 0f, MaxDepthMeters);
            PressureKpa = 101.325f + DepthMeters * 10.06f;
        }
    }
}
