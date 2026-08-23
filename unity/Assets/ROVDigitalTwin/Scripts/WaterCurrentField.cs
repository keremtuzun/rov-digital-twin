using UnityEngine;

namespace ROVDigitalTwin
{
    public sealed class WaterCurrentField : MonoBehaviour
    {
        public Vector3 BaseCurrentMetersPerSecond = new Vector3(0.12f, 0f, 0.04f);
        [Min(0f)] public float Turbulence = 0.08f;
        [Min(0.01f)] public float SpatialScale = 0.08f;
        [Min(0.01f)] public float TemporalScale = 0.12f;
        [Min(0f)] public float DepthShearPerMeter = 0.006f;
        [Min(0f)] public float GustStrength = 0.04f;
        [Min(1f)] public float GustPeriodSeconds = 11f;
        [Min(0f)] public float SignificantWaveHeightMeters = 0.45f;
        [Min(1f)] public float PeakWavePeriodSeconds = 6.5f;
        [Range(0f, 360f)] public float WaveDirectionDegrees = 25f;
        [Range(0f, 0.5f)] public float SecondaryWaveRatio = 0.28f;
        public float WaterSurfaceY;

        public Vector3 Sample(Vector3 worldPosition, float time)
        {
            float x = Mathf.PerlinNoise(worldPosition.z * SpatialScale, time * TemporalScale) * 2f - 1f;
            float y = Mathf.PerlinNoise(worldPosition.x * SpatialScale + 31f, time * TemporalScale) * 2f - 1f;
            float z = Mathf.PerlinNoise(worldPosition.y * SpatialScale + 67f, time * TemporalScale) * 2f - 1f;
            float depth = Mathf.Max(0f, -worldPosition.y);
            float shearAngle = depth * DepthShearPerMeter;
            Vector3 shearCurrent = Quaternion.Euler(0f, shearAngle * Mathf.Rad2Deg, 0f) * BaseCurrentMetersPerSecond;
            float gust = Mathf.Sin(time * Mathf.PI * 2f / GustPeriodSeconds + worldPosition.x * 0.03f) * GustStrength;
            Vector3 turbulentVelocity = new Vector3(x, y * 0.2f, z) * Turbulence;
            Vector3 gustVelocity = new Vector3(gust, 0f, -gust * 0.4f);
            return shearCurrent + turbulentVelocity + gustVelocity + SampleWaveOrbitalVelocity(worldPosition, time);
        }

        public Vector3 SampleWaveOrbitalVelocity(Vector3 worldPosition, float time)
        {
            Vector3 primary = WaveComponent(worldPosition, time, SignificantWaveHeightMeters,
                PeakWavePeriodSeconds, WaveDirectionDegrees, WaterSurfaceY, 0f);
            Vector3 secondary = WaveComponent(worldPosition, time, SignificantWaveHeightMeters * SecondaryWaveRatio,
                PeakWavePeriodSeconds * 0.72f, WaveDirectionDegrees + 67f, WaterSurfaceY, 1.9f);
            return primary + secondary;
        }

        public float SampleSurfaceElevation(Vector3 worldPosition, float time)
        {
            return SurfaceComponent(worldPosition, time, SignificantWaveHeightMeters,
                       PeakWavePeriodSeconds, WaveDirectionDegrees, 0f)
                   + SurfaceComponent(worldPosition, time, SignificantWaveHeightMeters * SecondaryWaveRatio,
                       PeakWavePeriodSeconds * 0.72f, WaveDirectionDegrees + 67f, 1.9f);
        }

        public static Vector3 WaveComponent(Vector3 position, float time, float waveHeight, float period,
            float directionDegrees, float surfaceY, float phaseOffset)
        {
            float safePeriod = Mathf.Max(1f, period);
            float omega = 2f * Mathf.PI / safePeriod;
            float waveNumber = omega * omega / Physics.gravity.magnitude;
            float angle = directionDegrees * Mathf.Deg2Rad;
            Vector3 direction = new Vector3(Mathf.Cos(angle), 0f, Mathf.Sin(angle));
            float phase = waveNumber * Vector3.Dot(position, direction) - omega * time + phaseOffset;
            float depth = Mathf.Max(0f, surfaceY - position.y);
            float decay = Mathf.Exp(-waveNumber * depth);
            float orbitalSpeed = 0.5f * Mathf.Max(0f, waveHeight) * omega * decay;
            return direction * (orbitalSpeed * Mathf.Cos(phase))
                   + Vector3.up * (orbitalSpeed * Mathf.Sin(phase));
        }

        private static float SurfaceComponent(Vector3 position, float time, float waveHeight, float period,
            float directionDegrees, float phaseOffset)
        {
            float safePeriod = Mathf.Max(1f, period);
            float omega = 2f * Mathf.PI / safePeriod;
            float waveNumber = omega * omega / Physics.gravity.magnitude;
            float angle = directionDegrees * Mathf.Deg2Rad;
            Vector3 direction = new Vector3(Mathf.Cos(angle), 0f, Mathf.Sin(angle));
            float phase = waveNumber * Vector3.Dot(position, direction) - omega * time + phaseOffset;
            return 0.5f * Mathf.Max(0f, waveHeight) * Mathf.Sin(phase);
        }
    }
}
