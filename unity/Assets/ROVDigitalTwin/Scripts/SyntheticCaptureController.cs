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
            public string label_policy = "visual indicator only; not physical damage evidence";
        }

        public ROVCameraCapture Capture;
        public Transform Target;
        public WaterCurrentField Current;
        public Light SceneLight;
        public int Seed = 42;

        public void CaptureRandomizedSample() => StartCoroutine(CaptureOne());

        private IEnumerator CaptureOne()
        {
            UnityEngine.Random.InitState(Seed++);
            RenderSettings.fogDensity = UnityEngine.Random.Range(0.012f, 0.065f);
            RenderSettings.fogColor = Color.Lerp(new Color(0.01f, 0.12f, 0.18f), new Color(0.10f, 0.28f, 0.20f), UnityEngine.Random.value);
            SceneLight.intensity = UnityEngine.Random.Range(0.25f, 1.1f);
            SceneLight.color = Color.Lerp(new Color(0.35f, 0.65f, 1f), Color.white, UnityEngine.Random.value);
            Current.BaseCurrentMetersPerSecond = UnityEngine.Random.insideUnitSphere * 0.45f;
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
            };
            File.WriteAllText(Path.ChangeExtension(path, ".json"), JsonUtility.ToJson(metadata, true));
        }
    }
}
