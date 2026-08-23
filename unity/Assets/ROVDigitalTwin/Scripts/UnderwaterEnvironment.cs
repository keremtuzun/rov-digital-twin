using UnityEngine;

namespace ROVDigitalTwin
{
    public sealed class UnderwaterEnvironment : MonoBehaviour
    {
        public Light FilteredSun;
        public Transform WaterSurface;
        public WaterCurrentField CurrentField;
        [Min(0f)] public float WaterSurfaceY;
        [Range(0f, 1f)] public float Contamination01 = 0.08f;
        [Min(0f)] public float TurbidityNtu = 1.2f;
        [Min(0f)] public float SuspendedSedimentMgPerLiter = 2.5f;
        [Min(0f)] public float BaseFogDensity = 0.012f;
        [Min(0f)] public float DepthFogDensity = 0.0012f;
        [Min(0f)] public float ClearWaterLightAttenuationPerMeter = 0.045f;
        public bool EnableParticulates = true;

        private Vector3 surfaceStart;
        private ParticleSystem particulateSystem;
        private float nextVisualRefresh;

        public float OpticalVisibilityMeters => Mathf.Clamp(
            32f / (1f + TurbidityNtu * 0.75f + Contamination01 * 5f), 2.5f, 40f);
        public float AcousticQuality01 => Mathf.Clamp01(
            1f - TurbidityNtu * 0.012f - SuspendedSedimentMgPerLiter * 0.002f - Contamination01 * 0.12f);
        public float EffectiveLightAttenuationPerMeter => ClearWaterLightAttenuationPerMeter
            + TurbidityNtu * 0.012f + Contamination01 * 0.035f;

        private void Awake()
        {
            if (WaterSurface != null)
                surfaceStart = WaterSurface.position;
            CurrentField ??= GetComponent<WaterCurrentField>();
            if (EnableParticulates)
                CreateParticulateField();
            RefreshConditionVisuals();
        }

        private void Update()
        {
            Camera view = Camera.main;
            float depth = view != null ? Mathf.Max(0f, WaterSurfaceY - view.transform.position.y) : 6f;
            RenderSettings.fogDensity = BaseFogDensity + 0.003f * TurbidityNtu
                + 0.018f * Contamination01 + depth * DepthFogDensity;
            float attenuation = Mathf.Exp(-depth * EffectiveLightAttenuationPerMeter);
            Color deepColor = Color.Lerp(new Color(0.006f, 0.035f, 0.045f),
                new Color(0.018f, 0.042f, 0.025f), Contamination01);
            RenderSettings.ambientLight = Color.Lerp(deepColor, new Color(0.04f, 0.13f, 0.16f), attenuation);
            if (FilteredSun != null)
                FilteredSun.intensity = Mathf.Lerp(0.12f, 0.65f, attenuation);
            if (WaterSurface != null)
            {
                Vector3 position = surfaceStart;
                position.y = WaterSurfaceY + (CurrentField != null
                    ? CurrentField.SampleSurfaceElevation(surfaceStart, Time.time) : 0f);
                WaterSurface.position = position;
                if (CurrentField != null)
                {
                    float dx = CurrentField.SampleSurfaceElevation(surfaceStart + Vector3.right, Time.time)
                               - CurrentField.SampleSurfaceElevation(surfaceStart - Vector3.right, Time.time);
                    float dz = CurrentField.SampleSurfaceElevation(surfaceStart + Vector3.forward, Time.time)
                               - CurrentField.SampleSurfaceElevation(surfaceStart - Vector3.forward, Time.time);
                    WaterSurface.rotation = Quaternion.Euler(-Mathf.Atan(dz * 0.5f) * Mathf.Rad2Deg, 0f,
                        Mathf.Atan(dx * 0.5f) * Mathf.Rad2Deg);
                }
            }
            if (Time.time >= nextVisualRefresh)
            {
                nextVisualRefresh = Time.time + 0.5f;
                RefreshConditionVisuals();
            }
        }

        public void RefreshConditionVisuals()
        {
            RenderSettings.fogColor = Color.Lerp(new Color(0.015f, 0.16f, 0.21f),
                new Color(0.08f, 0.14f, 0.07f), Contamination01);
            if (particulateSystem == null)
                return;
            ParticleSystem.MainModule main = particulateSystem.main;
            main.maxParticles = Mathf.RoundToInt(Mathf.Lerp(180f, 850f,
                Mathf.Clamp01(TurbidityNtu / 8f + Contamination01 * 0.5f)));
            main.startColor = Color.Lerp(new Color(0.65f, 0.82f, 0.78f, 0.18f),
                new Color(0.46f, 0.38f, 0.18f, 0.48f), Contamination01);
            ParticleSystem.EmissionModule emission = particulateSystem.emission;
            emission.rateOverTime = 5f + TurbidityNtu * 4f + SuspendedSedimentMgPerLiter * 0.6f
                                    + Contamination01 * 18f;
        }

        private void CreateParticulateField()
        {
            GameObject field = new GameObject("Suspended Particulates");
            field.transform.SetParent(transform, false);
            field.transform.position = new Vector3(0f, -6f, 0f);
            ParticleSystem particles = field.AddComponent<ParticleSystem>();
            particulateSystem = particles;
            ParticleSystem.MainModule main = particles.main;
            main.loop = true;
            main.startLifetime = 35f;
            main.startSpeed = new ParticleSystem.MinMaxCurve(0.01f, 0.04f);
            main.startSize = new ParticleSystem.MinMaxCurve(0.015f, 0.055f);
            main.startColor = new Color(0.65f, 0.82f, 0.78f, 0.28f);
            main.maxParticles = 450;
            main.simulationSpace = ParticleSystemSimulationSpace.World;
            ParticleSystem.EmissionModule emission = particles.emission;
            emission.rateOverTime = 14f;
            ParticleSystem.ShapeModule shape = particles.shape;
            shape.shapeType = ParticleSystemShapeType.Box;
            shape.scale = new Vector3(35f, 11f, 35f);
            Shader shader = Shader.Find("Particles/Standard Unlit") ?? Shader.Find("Legacy Shaders/Particles/Alpha Blended");
            if (shader != null)
                field.GetComponent<ParticleSystemRenderer>().material = new Material(shader);
        }
    }
}
