using UnityEngine;
using System.Collections.Generic;

namespace ROVDigitalTwin
{
    public sealed class DepthSensor : MonoBehaviour
    {
        public float WaterSurfaceY = 0f;
        [Min(0f)] public float NoiseStandardDeviationMeters = 0.01f;
        [Min(0f)] public float MaxDepthMeters = 100f;
        public float BiasMeters;
        public float BiasDriftMetersPerSecond;
        public float SuddenJumpMeters;
        public bool StuckReading;
        [Min(0.1f)] public float NoiseMultiplier = 1f;
        [Range(0f, 1f)] public float DropoutProbability;
        [Min(0f)] public float DelaySeconds;
        [Min(0.01f)] public float SamplePeriodSeconds = 0.05f;

        public float DepthMeters { get; private set; }
        public float PressureKpa { get; private set; }
        private float nextSampleTime;
        private readonly Queue<DepthFrame> delayedFrames = new Queue<DepthFrame>();
        private struct DepthFrame { public float Time; public float Depth; }

        private void FixedUpdate()
        {
            if (Time.time < nextSampleTime)
                return;
            nextSampleTime = Time.time + SamplePeriodSeconds;
            BiasMeters += BiasDriftMetersPerSecond * SamplePeriodSeconds;
            if (!StuckReading && Random.value >= DropoutProbability)
            {
                delayedFrames.Enqueue(new DepthFrame
                {
                    Time = Time.time,
                    Depth = Mathf.Clamp(WaterSurfaceY - transform.position.y + BiasMeters
                        + SuddenJumpMeters + SensorNoise.Gaussian(NoiseStandardDeviationMeters * NoiseMultiplier),
                        0f, MaxDepthMeters)
                });
            }
            while (delayedFrames.Count > 0 && delayedFrames.Peek().Time <= Time.time - DelaySeconds)
                DepthMeters = delayedFrames.Dequeue().Depth;
            PressureKpa = 101.325f + DepthMeters * 10.06f;
        }
    }
}
