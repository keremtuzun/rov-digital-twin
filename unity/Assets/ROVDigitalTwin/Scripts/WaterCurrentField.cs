using UnityEngine;

namespace ROVDigitalTwin
{
    public sealed class WaterCurrentField : MonoBehaviour
    {
        public Vector3 BaseCurrentMetersPerSecond = new Vector3(0.12f, 0f, 0.04f);
        [Min(0f)] public float Turbulence = 0.08f;
        [Min(0.01f)] public float SpatialScale = 0.08f;
        [Min(0.01f)] public float TemporalScale = 0.12f;

        public Vector3 Sample(Vector3 worldPosition, float time)
        {
            float x = Mathf.PerlinNoise(worldPosition.z * SpatialScale, time * TemporalScale) * 2f - 1f;
            float y = Mathf.PerlinNoise(worldPosition.x * SpatialScale + 31f, time * TemporalScale) * 2f - 1f;
            float z = Mathf.PerlinNoise(worldPosition.y * SpatialScale + 67f, time * TemporalScale) * 2f - 1f;
            return BaseCurrentMetersPerSecond + new Vector3(x, y * 0.2f, z) * Turbulence;
        }
    }
}
