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
        public ROVVehicle Vehicle;
        public DutyManager Duties;
        public DepthSensor Depth;
        public DvlSensor Dvl;
        public string RemoteHost = "127.0.0.1";
        public int TelemetryPort = 15000;
        public int CommandPort = 15001;
        [Min(0.02f)] public float PublishIntervalSeconds = 0.1f;
        public string LastHighLevelCommand { get; private set; } = "none";

        private UdpClient sender;
        private UdpClient receiver;
        private Thread receiveThread;
        private readonly ConcurrentQueue<string> commands = new ConcurrentQueue<string>();
        private float elapsed;

        private void Start()
        {
            sender = new UdpClient();
            receiver = new UdpClient(CommandPort);
            receiveThread = new Thread(ReceiveLoop) { IsBackground = true, Name = "OceanSense UDP commands" };
            receiveThread.Start();
        }

        private void Update()
        {
            elapsed += Time.unscaledDeltaTime;
            if (elapsed >= PublishIntervalSeconds)
            {
                elapsed = 0f;
                byte[] bytes = Encoding.UTF8.GetBytes(BuildTelemetryJson());
                sender.Send(bytes, bytes.Length, RemoteHost, TelemetryPort);
            }
            while (commands.TryDequeue(out string command))
                LastHighLevelCommand = command;
        }

        private string BuildTelemetryJson()
        {
            Vector3 p = transform.position;
            Vector3 v = Vehicle.Body.linearVelocity;
            return FormattableString.Invariant($"{{\"timestamp\":{Time.realtimeSinceStartupAsDouble:F3},\"duty\":\"{Duties.CurrentDuty.Duty}\",\"position_m\":[{p.x:F4},{p.y:F4},{p.z:F4}],\"velocity_mps\":[{v.x:F4},{v.y:F4},{v.z:F4}],\"depth_m\":{Depth.DepthMeters:F3},\"battery_level\":{Vehicle.BatteryLevel01:F4},\"dvl_quality\":{Dvl.Quality:F4}}}");
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

        private void OnDestroy()
        {
            receiver?.Close();
            sender?.Close();
            receiveThread?.Join(250);
        }
    }
}
