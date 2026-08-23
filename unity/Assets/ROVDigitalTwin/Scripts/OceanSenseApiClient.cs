using System;
using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

namespace ROVDigitalTwin
{
    public sealed class OceanSenseApiClient : MonoBehaviour
    {
        public string ApiBaseUrl = "http://127.0.0.1:8000";
        public ROVCameraCapture CameraCapture;
        public ROVVehicle Vehicle;
        public DepthSensor Depth;
        public string LastStatus { get; private set; } = "idle";
        public string LastPerceptionJson { get; private set; } = "";
        public string LastDecisionJson { get; private set; } = "";

        public void AnalyzeCurrentView() => StartCoroutine(CaptureAndAnalyze());

        private IEnumerator CaptureAndAnalyze()
        {
            LastStatus = "capturing";
            string imagePath = null;
            yield return CameraCapture.Capture(path => imagePath = path);
            string frameId = Guid.NewGuid().ToString("N");
            string context = ContextJson();
            string request = $"{{\"frame_id\":\"{frameId}\",\"image_path\":\"{Escape(imagePath)}\",\"mission_context\":{context}}}";
            yield return PostJson("/api/perception/analyze", request, result => LastPerceptionJson = result);
            if (string.IsNullOrEmpty(LastPerceptionJson)) yield break;
            string decisionRequest = $"{{\"frame_id\":\"{frameId}\",\"perception_output\":{LastPerceptionJson},\"mission_context\":{context}}}";
            yield return PostJson("/api/agent/decide", decisionRequest, result => LastDecisionJson = result);
            if (!string.IsNullOrEmpty(LastDecisionJson)) LastStatus = "decision ready";
        }

        private IEnumerator PostJson(string route, string json, Action<string> completed)
        {
            LastStatus = $"POST {route}";
            using var request = new UnityWebRequest(ApiBaseUrl.TrimEnd('/') + route, "POST");
            request.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(json));
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");
            yield return request.SendWebRequest();
            if (request.result != UnityWebRequest.Result.Success)
            {
                LastStatus = $"API error: {request.responseCode} {request.error}";
                yield break;
            }
            completed(request.downloadHandler.text);
        }

        private string ContextJson() => $"{{\"visibility_level\":\"moderate\",\"depth_m\":{Depth.DepthMeters.ToString(System.Globalization.CultureInfo.InvariantCulture)},\"battery_level\":{Vehicle.BatteryLevel01.ToString(System.Globalization.CultureInfo.InvariantCulture)},\"communication_status\":\"stable\",\"operator_mode\":\"semi_autonomous\",\"survey_goal\":\"structure\"}}";
        private static string Escape(string value) => value.Replace("\\", "\\\\").Replace("\"", "\\\"");
    }
}
