using System;
using System.Collections;
using System.IO;
using UnityEngine;

namespace ROVDigitalTwin
{
    public sealed class ROVCameraCapture : MonoBehaviour
    {
        public Camera SourceCamera;
        public int Width = 640;
        public int Height = 360;
        public string LastImagePath { get; private set; }

        public IEnumerator Capture(Action<string> completed)
        {
            yield return new WaitForEndOfFrame();
            RenderTexture target = RenderTexture.GetTemporary(Width, Height, 24, RenderTextureFormat.ARGB32);
            RenderTexture previous = RenderTexture.active;
            SourceCamera.targetTexture = target;
            SourceCamera.Render();
            RenderTexture.active = target;
            var texture = new Texture2D(Width, Height, TextureFormat.RGB24, false);
            texture.ReadPixels(new Rect(0, 0, Width, Height), 0, 0);
            texture.Apply();
            SourceCamera.targetTexture = null;
            RenderTexture.active = previous;
            string directory = Path.Combine(Application.persistentDataPath, "OceanSenseCaptures");
            Directory.CreateDirectory(directory);
            LastImagePath = Path.Combine(directory, $"rov_{DateTime.UtcNow:yyyyMMdd_HHmmss_fff}.png");
            File.WriteAllBytes(LastImagePath, texture.EncodeToPNG());
            Destroy(texture);
            RenderTexture.ReleaseTemporary(target);
            completed?.Invoke(LastImagePath);
        }
    }
}
