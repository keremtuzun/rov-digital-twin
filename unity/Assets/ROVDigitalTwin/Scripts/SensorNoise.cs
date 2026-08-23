using UnityEngine;

namespace ROVDigitalTwin
{
    public static class SensorNoise
    {
        public static float Gaussian(float standardDeviation)
        {
            if (standardDeviation <= 0f)
                return 0f;
            float u1 = Mathf.Max(1e-7f, Random.value);
            float u2 = Random.value;
            return standardDeviation * Mathf.Sqrt(-2f * Mathf.Log(u1)) * Mathf.Cos(2f * Mathf.PI * u2);
        }

        public static Vector3 GaussianVector(float standardDeviation) =>
            new Vector3(Gaussian(standardDeviation), Gaussian(standardDeviation), Gaussian(standardDeviation));
    }
}
