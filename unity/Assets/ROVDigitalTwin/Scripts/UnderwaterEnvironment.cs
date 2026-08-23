using UnityEngine;

namespace ROVDigitalTwin
{
    public sealed class UnderwaterEnvironment : MonoBehaviour
    {
        public Light FilteredSun;
        public Transform WaterSurface;
        [Min(0f)] public float WaterSurfaceY;
        [Min(0f)] public float BaseFogDensity = 0.018f;
        [Min(0f)] public float DepthFogDensity = 0.0012f;
        [Min(0f)] public float LightAttenuationPerMeter = 0.055f;
        [Min(0f)] public float WaveAmplitudeMeters = 0.08f;
        [Min(0.01f)] public float WaveFrequency = 0.35f;
        public bool EnableParticulates = true;

        private Vector3 surfaceStart;

        private void Awake()
        {
            if (WaterSurface != null)
                surfaceStart = WaterSurface.position;
            if (EnableParticulates)
                CreateParticulateField();
        }

        private void Update()
        {
            Camera view = Camera.main;
            float depth = view != null ? Mathf.Max(0f, WaterSurfaceY - view.transform.position.y) : 6f;
            RenderSettings.fogDensity = BaseFogDensity + depth * DepthFogDensity;
            float attenuation = Mathf.Exp(-depth * LightAttenuationPerMeter);
            RenderSettings.ambientLight = Color.Lerp(new Color(0.006f, 0.035f, 0.045f), new Color(0.04f, 0.13f, 0.16f), attenuation);
            if (FilteredSun != null)
                FilteredSun.intensity = Mathf.Lerp(0.12f, 0.65f, attenuation);
            if (WaterSurface != null)
            {
                Vector3 position = surfaceStart;
                position.y += Mathf.Sin(Time.time * WaveFrequency) * WaveAmplitudeMeters;
                WaterSurface.position = position;
            }
        }

        private void CreateParticulateField()
        {
            GameObject field = new GameObject("Suspended Particulates");
            field.transform.SetParent(transform, false);
            field.transform.position = new Vector3(0f, -6f, 0f);
            ParticleSystem particles = field.AddComponent<ParticleSystem>();
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
