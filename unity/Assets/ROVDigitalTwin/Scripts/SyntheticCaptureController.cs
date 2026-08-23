using System;
using System.Collections;
using System.IO;
using UnityEngine;

namespace ROVDigitalTwin
{
    public sealed class SyntheticCaptureController : MonoBehaviour
    {
        [Serializable]
        private sealed class CaptureMetadata
        {
            public string sample_id;
            public string captured_at_utc;
            public string real_or_synthetic = "synthetic";
            public int random_seed;
            public float camera_distance_m;
            public float fog_density;
            public float light_intensity;
            public Color light_color;
            public Color fog_color;
            public Vector3 current_mps;
            public float significant_wave_height_m;
            public float peak_wave_period_s;
            public float contamination_01;
            public float turbidity_ntu;
            public float suspended_sediment_mg_l;
            public float optical_visibility_m;
            public string label_policy = "visual indicator only; not physical damage evidence";
        }

        public ROVCameraCapture Capture;
        public Transform Target;
        public WaterCurrentField Current;
        public UnderwaterEnvironment Environment;
        public Light SceneLight;
        public int Seed = 42;

        public void CaptureRandomizedSample() => StartCoroutine(CaptureOne());

        private IEnumerator CaptureOne()
        {
            Environment ??= FindAnyObjectByType<UnderwaterEnvironment>();
            UnityEngine.Random.InitState(Seed++);
            RenderSettings.fogDensity = UnityEngine.Random.Range(0.012f, 0.065f);
            RenderSettings.fogColor = Color.Lerp(new Color(0.01f, 0.12f, 0.18f), new Color(0.10f, 0.28f, 0.20f), UnityEngine.Random.value);
            SceneLight.intensity = UnityEngine.Random.Range(0.25f, 1.1f);
            SceneLight.color = Color.Lerp(new Color(0.35f, 0.65f, 1f), Color.white, UnityEngine.Random.value);
            Current.BaseCurrentMetersPerSecond = UnityEngine.Random.insideUnitSphere * 0.45f;
            Current.SignificantWaveHeightMeters = UnityEngine.Random.Range(0.1f, 1.4f);
            Current.PeakWavePeriodSeconds = UnityEngine.Random.Range(4f, 9f);
            if (Environment != null)
            {
                Environment.Contamination01 = UnityEngine.Random.Range(0.01f, 0.35f);
                Environment.TurbidityNtu = UnityEngine.Random.Range(0.25f, 8f);
                Environment.SuspendedSedimentMgPerLiter = UnityEngine.Random.Range(0.5f, 20f);
                Environment.RefreshConditionVisuals();
            }
            float distance = UnityEngine.Random.Range(2f, 12f);
            Capture.SourceCamera.transform.position = Target.position - Target.forward * distance + UnityEngine.Random.insideUnitSphere * 1.5f;
            Capture.SourceCamera.transform.LookAt(Target);
            string path = null;
            yield return Capture.Capture(value => path = value);
            var metadata = new CaptureMetadata
            {
                sample_id = Path.GetFileNameWithoutExtension(path), captured_at_utc = DateTime.UtcNow.ToString("O"),
                random_seed = Seed - 1, camera_distance_m = distance, fog_density = RenderSettings.fogDensity,
                light_intensity = SceneLight.intensity, light_color = SceneLight.color,
                fog_color = RenderSettings.fogColor, current_mps = Current.BaseCurrentMetersPerSecond,
                significant_wave_height_m = Current.SignificantWaveHeightMeters,
                peak_wave_period_s = Current.PeakWavePeriodSeconds,
                contamination_01 = Environment != null ? Environment.Contamination01 : 0f,
                turbidity_ntu = Environment != null ? Environment.TurbidityNtu : 0f,
                suspended_sediment_mg_l = Environment != null ? Environment.SuspendedSedimentMgPerLiter : 0f,
                optical_visibility_m = Environment != null ? Environment.OpticalVisibilityMeters : 0f,
            };
            File.WriteAllText(Path.ChangeExtension(path, ".json"), JsonUtility.ToJson(metadata, true));
        }
    }
}
