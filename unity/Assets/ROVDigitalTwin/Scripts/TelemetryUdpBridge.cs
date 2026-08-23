using System;
using System.Collections.Concurrent;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;

namespace ROVDigitalTwin
{
    public sealed class TelemetryUdpBridge : MonoBehaviour
    {
        [Serializable]
        private sealed class IntentEnvelope { public string intent; }
        public ROVVehicle Vehicle;
        public DutyManager Duties;
        public DepthSensor Depth;
        public DvlSensor Dvl;
        public SimulatedPowerSensor Power;
        public string RemoteHost = "127.0.0.1";
        public int TelemetryPort = 15000;
        public int CommandPort = 15001;
        [Min(0.02f)] public float PublishIntervalSeconds = 0.1f;
        public bool PublishEnabled = true;
        public string LastHighLevelCommand { get; private set; } = "none";

        private UdpClient sender;
        private UdpClient receiver;
        private Thread receiveThread;
        private readonly ConcurrentQueue<string> commands = new ConcurrentQueue<string>();
        private float elapsed;
        private string missionId;

        private void Start()
        {
            missionId = $"unity-{Guid.NewGuid():N}";
            sender = new UdpClient();
            try
            {
                receiver = new UdpClient(CommandPort);
            }
            catch (SocketException exception)
            {
                Debug.LogError($"OceanSense command UDP port {CommandPort} unavailable: {exception.Message}");
                enabled = false;
                sender.Close();
                return;
            }
            receiveThread = new Thread(ReceiveLoop) { IsBackground = true, Name = "OceanSense UDP commands" };
            receiveThread.Start();
        }

        private void Update()
        {
            elapsed += Time.unscaledDeltaTime;
            if (PublishEnabled && elapsed >= PublishIntervalSeconds)
            {
                elapsed = 0f;
                byte[] bytes = Encoding.UTF8.GetBytes(BuildTelemetryJson());
                sender.Send(bytes, bytes.Length, RemoteHost, TelemetryPort);
            }
            while (commands.TryDequeue(out string command))
            {
                if (IsHighLevelIntent(command)) LastHighLevelCommand = command;
                else Debug.LogWarning("Rejected UDP command that was not an allowlisted high-level intent.");
            }
        }

        private string BuildTelemetryJson()
        {
            Vector3 p = transform.position;
            Vector3 v = Vehicle.Body.linearVelocity;
            Vector3 euler = transform.eulerAngles;
            float roll = Mathf.DeltaAngle(0f, euler.z);
            float pitch = Mathf.DeltaAngle(0f, euler.x);
            float trueDepth = Mathf.Max(0f, Depth.WaterSurfaceY - transform.position.y);
            string duty = Duties.CurrentDuty.Duty switch
            {
                DutyType.StationKeeping => "station_keeping",
                DutyType.PipelineTracking => "pipeline_tracking",
                _ => "target_waypoint"
            };
            return FormattableString.Invariant(
                $"{{\"schema_version\":\"1.0.0\",\"timestamp_s\":{Time.realtimeSinceStartupAsDouble:F3}," +
                $"\"mission_id\":\"{missionId}\",\"duty\":\"{duty}\",\"depth_m\":{Depth.DepthMeters:F4}," +
                $"\"depth_error_m\":{Duties.CurrentDuty.TargetDepthMeters - Depth.DepthMeters:F4},\"speed_mps\":{v.magnitude:F4}," +
                $"\"vertical_speed_mps\":{v.y:F4},\"roll_deg\":{roll:F3},\"pitch_deg\":{pitch:F3}," +
                $"\"yaw_rate_dps\":{Vehicle.Body.angularVelocity.y * Mathf.Rad2Deg:F3},\"current_a\":{Power.CurrentA:F3}," +
                $"\"voltage_v\":{Power.VoltageV:F3},\"thruster_cmd_mean\":{Vehicle.MeanAbsoluteCommand:F4}," +
                $"\"thruster_response_ratio\":{Power.ThrusterResponseRatio:F4},\"imu_depth_disagreement_m\":{Mathf.Abs(Depth.DepthMeters - trueDepth):F4}," +
                $"\"dvl_quality\":{Dvl.Quality:F4},\"temperature_c\":{Power.TemperatureC:F3}," +
                $"\"battery_level\":{Vehicle.BatteryLevel01:F4},\"position_m\":[{p.x:F4},{p.y:F4},{p.z:F4}]," +
                $"\"velocity_mps\":[{v.x:F4},{v.y:F4},{v.z:F4}],\"field_status\":{{" +
                $"\"current_a\":\"simulated\",\"voltage_v\":\"simulated\",\"temperature_c\":\"simulated\"," +
                $"\"thruster_response_ratio\":\"simulated\",\"imu_depth_disagreement_m\":\"derived\"}}}}");
        }

        private void ReceiveLoop()
        {
            var endpoint = new IPEndPoint(IPAddress.Any, 0);
            try
            {
                while (receiver != null)
                    commands.Enqueue(Encoding.UTF8.GetString(receiver.Receive(ref endpoint)));
            }
            catch (SocketException) { }
            catch (ObjectDisposedException) { }
        }

        private static bool IsHighLevelIntent(string json)
        {
            string[] intents = { "continue_survey", "inspect_closer", "hold_position", "request_human_review", "mark_location", "capture_more_data", "avoid_area", "return_to_base", "surface_or_recover", "send_alert" };
            string lower = json.ToLowerInvariant();
            if (lower.Contains("thruster") || lower.Contains("motor") || lower.Contains("pwm") || lower.Contains("force") || lower.Contains("voltage"))
                return false;
            foreach (string intent in intents)
            {
                IntentEnvelope envelope;
                try { envelope = JsonUtility.FromJson<IntentEnvelope>(json); }
                catch (ArgumentException) { return false; }
                if (envelope != null && envelope.intent == intent) return true;
            }
            return false;
        }

        private void OnDestroy()
        {
            receiver?.Close();
            sender?.Close();
            receiveThread?.Join(250);
        }
    }
}
