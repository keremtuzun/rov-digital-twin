using System.Collections;
using System.IO;
using System.Net.Sockets;
using System.Text;
using NUnit.Framework;
using Unity.MLAgents.Policies;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
using Object = UnityEngine.Object;

namespace ROVDigitalTwin.Tests.PlayMode
{
    public sealed class Twin1RuntimePlayModeTests
    {
        private const string SceneName = "OceanSenseDemo";
        [UnityTest]
        public IEnumerator Twin1SceneRuntimeSmokeHasRequiredObjectsAndReferences()
        {
            yield return LoadTwin1Scene();

            ROVVehicle vehicle = Object.FindAnyObjectByType<ROVVehicle>();
            DutyManager duties = Object.FindAnyObjectByType<DutyManager>();
            OceanSenseApiClient api = Object.FindAnyObjectByType<OceanSenseApiClient>();
            ROVCameraCapture capture = Object.FindAnyObjectByType<ROVCameraCapture>();
            TelemetryUdpBridge telemetry = Object.FindAnyObjectByType<TelemetryUdpBridge>();
            FaultInjectionController faults = Object.FindAnyObjectByType<FaultInjectionController>();
            ROVRLAgent agent = Object.FindAnyObjectByType<ROVRLAgent>();

            Assert.NotNull(vehicle, "Twin 1 scene must contain an ROVVehicle.");
            Assert.NotNull(duties, "Twin 1 scene must contain a DutyManager.");
            Assert.NotNull(api, "Twin 1 scene must contain the Model 1 HTTP adapter.");
            Assert.NotNull(capture, "Twin 1 scene must contain an inspection-camera capture component.");
            Assert.NotNull(telemetry, "Twin 1 scene must contain the high-level telemetry bridge.");
            Assert.NotNull(faults, "Twin 1 scene must contain fault-injection support.");
            Assert.NotNull(agent, "Twin 1 scene must contain the navigation/control agent.");

            Assert.NotNull(vehicle.Body);
            Assert.AreEqual(8, vehicle.Thrusters.Length);
            Assert.NotNull(api.CameraCapture);
            Assert.NotNull(api.Vehicle);
            Assert.NotNull(api.Depth);
            Assert.NotNull(capture.SourceCamera);
            Assert.NotNull(telemetry.Vehicle);
            Assert.NotNull(telemetry.Duties);
            Assert.NotNull(telemetry.Depth);
            Assert.NotNull(telemetry.Dvl);
            Assert.NotNull(telemetry.Power);
            Assert.NotNull(telemetry.Environment);
            Assert.NotNull(faults.Vehicle);
            Assert.NotNull(faults.Hydrodynamics);
            Assert.NotNull(faults.Depth);
            Assert.NotNull(faults.Imu);
            Assert.NotNull(faults.Dvl);
            Assert.NotNull(faults.Sonar);
            Assert.NotNull(faults.Power);
            Assert.NotNull(faults.Telemetry);
            Assert.AreEqual(39, ROVRLAgent.ObservationSize);
            Assert.AreEqual(8, ROVRLAgent.ActionSize);
        }

        [UnityTest]
        public IEnumerator Twin1CameraCaptureWritesPngAndCleansUp()
        {
            yield return LoadTwin1Scene();
            ROVCameraCapture capture = Object.FindAnyObjectByType<ROVCameraCapture>();
            Assert.NotNull(capture);
            Assert.NotNull(capture.SourceCamera);
            Assert.IsTrue(capture.IsConfigured);

            string capturedPath = null;
            yield return capture.Capture(path => capturedPath = path);

            try
            {
                Assert.IsNotEmpty(capturedPath);
                Assert.IsTrue(File.Exists(capturedPath), "Capture must write a PNG artifact.");
                byte[] bytes = File.ReadAllBytes(capturedPath);
                Assert.Greater(bytes.Length, 8, "Capture must not be an empty placeholder.");
                Assert.AreEqual(0x89, bytes[0]);
                Assert.AreEqual((byte)'P', bytes[1]);
                Assert.AreEqual((byte)'N', bytes[2]);
                Assert.AreEqual((byte)'G', bytes[3]);
            }
            finally
            {
                if (!string.IsNullOrWhiteSpace(capturedPath) && File.Exists(capturedPath))
                    File.Delete(capturedPath);
            }

            yield return null;
        }

        [UnityTest]
        public IEnumerator Twin1HttpAdapterHandlesUnavailableServiceAndIdentifiesFixtureExpectation()
        {
            yield return LoadTwin1Scene();
            OceanSenseApiClient api = Object.FindAnyObjectByType<OceanSenseApiClient>();
            Assert.NotNull(api);
            Assert.IsTrue(api.ExpectsFixtureBackend,
                "The committed Twin 1 scene must identify its default API expectation as fixture mode.");
            Assert.AreEqual("fixture", api.BackendExpectationLabel);

            api.ApiBaseUrl = "http://127.0.0.1:1";
            api.AnalyzeCurrentView();
            float deadline = Time.realtimeSinceStartup + 8f;
            while (!api.LastStatus.StartsWith("API error") && Time.realtimeSinceStartup < deadline)
                yield return null;

            try
            {
                Assert.That(api.LastStatus, Does.StartWith("API error"),
                    "An unavailable Model 1 service must become an explicit adapter error, not fake inference.");
                Assert.IsEmpty(api.LastPerceptionJson);
                Assert.IsEmpty(api.LastDecisionJson);
                Assert.AreEqual("fixture", api.BackendExpectationLabel,
                    "Network failure must not relabel fixture expectation as real Model 1 inference.");
            }
            finally
            {
                string capturePath = api.CameraCapture != null ? api.CameraCapture.LastImagePath : null;
                if (!string.IsNullOrWhiteSpace(capturePath) && File.Exists(capturePath))
                    File.Delete(capturePath);
            }
        }

        [UnityTest]
        public IEnumerator Twin1NavigationUsesExplicitHeuristicModeUntilPolicyIsRequalified()
        {
            yield return LoadTwin1Scene();
            BehaviorParameters behavior = Object.FindAnyObjectByType<BehaviorParameters>();
            Assert.NotNull(behavior, "Twin 1 must expose its ML-Agents navigation/control contract.");
            Assert.AreEqual("OceanSenseROV", behavior.BehaviorName);

            Assert.AreEqual(BehaviorType.HeuristicOnly, behavior.BehaviorType,
                "Twin 1 must explicitly use recoverable heuristic guidance until a current policy is qualified.");
            Assert.IsNull(behavior.Model,
                "The legacy navigation ONNX must not be activated in heuristic-only mode, and is not Model 1.");
        }

        [UnityTest]
        public IEnumerator Twin1PhysicsAndSensorsRemainFiniteDuringRuntime()
        {
            yield return LoadTwin1Scene();
            ROVVehicle vehicle = Object.FindAnyObjectByType<ROVVehicle>();
            DepthSensor depth = Object.FindAnyObjectByType<DepthSensor>();
            DvlSensor dvl = Object.FindAnyObjectByType<DvlSensor>();
            ImuSensor imu = Object.FindAnyObjectByType<ImuSensor>();
            Assert.NotNull(vehicle);
            Assert.NotNull(depth);
            Assert.NotNull(dvl);
            Assert.NotNull(imu);

            for (int index = 0; index < 20; index++)
                yield return new WaitForFixedUpdate();

            AssertFinite(vehicle.transform.position, "vehicle position");
            AssertFinite(vehicle.Body.linearVelocity, "vehicle velocity");
            AssertFinite(vehicle.Body.angularVelocity, "vehicle angular velocity");
            AssertFinite(depth.DepthMeters, "depth");
            AssertFinite(depth.PressureKpa, "pressure");
            AssertFinite(dvl.RelativeVelocityLocal, "DVL relative velocity");
            AssertFinite(dvl.AltitudeMeters, "DVL altitude");
            AssertFinite(dvl.Quality, "DVL quality");
            AssertFinite(imu.LinearAccelerationLocal, "IMU acceleration");
            AssertFinite(imu.AngularVelocityLocal, "IMU angular velocity");
        }

        [UnityTest]
        public IEnumerator Twin1EmergencyStopZerosEveryThrusterImmediately()
        {
            yield return LoadTwin1Scene();
            ROVVehicle vehicle = Object.FindAnyObjectByType<ROVVehicle>();
            Assert.NotNull(vehicle);
            foreach (Thruster thruster in vehicle.Thrusters)
                thruster.SetCommand(0.8f);
            bool observedNonZero = false;
            foreach (Thruster thruster in vehicle.Thrusters)
                observedNonZero |= Mathf.Abs(thruster.RequestedCommand) > 0f;
            Assert.IsTrue(observedNonZero, "The test must establish a non-zero command before stopping.");

            vehicle.StopThrusters();

            foreach (Thruster thruster in vehicle.Thrusters)
            {
                Assert.AreEqual(0f, thruster.Command);
                Assert.AreEqual(0f, thruster.RequestedCommand);
                Assert.AreEqual(0f, thruster.ActualThrustNewtons);
            }
            yield return null;
        }

        [UnityTest]
        public IEnumerator Twin1SyntheticCaptureWritesExplicitProvenanceSidecar()
        {
            yield return LoadTwin1Scene();
            SyntheticCaptureController fixture = Object.FindAnyObjectByType<SyntheticCaptureController>();
            Assert.NotNull(fixture);
            Assert.NotNull(fixture.Capture);
            string previousPath = fixture.Capture.LastImagePath;
            fixture.CaptureRandomizedSample();
            float deadline = Time.realtimeSinceStartup + 10f;
            string imagePath = null;
            string sidecarPath = null;
            while (Time.realtimeSinceStartup < deadline)
            {
                imagePath = fixture.Capture.LastImagePath;
                sidecarPath = string.IsNullOrWhiteSpace(imagePath) ? null : Path.ChangeExtension(imagePath, ".json");
                if (imagePath != previousPath && File.Exists(imagePath) && File.Exists(sidecarPath))
                    break;
                yield return null;
            }

            try
            {
                Assert.IsNotEmpty(imagePath);
                Assert.AreNotEqual(previousPath, imagePath);
                Assert.IsTrue(File.Exists(imagePath));
                Assert.IsTrue(File.Exists(sidecarPath));
                string metadata = File.ReadAllText(sidecarPath);
                Assert.That(metadata, Does.Contain("\"real_or_synthetic\": \"synthetic\""));
                Assert.That(metadata, Does.Contain("visual indicator only; not physical damage evidence"));
                Assert.That(metadata, Does.Contain("\"random_seed\""));
                Assert.That(metadata, Does.Contain("\"contamination_01\""));
                Assert.That(metadata, Does.Contain("\"significant_wave_height_m\""));
            }
            finally
            {
                if (!string.IsNullOrWhiteSpace(imagePath) && File.Exists(imagePath))
                    File.Delete(imagePath);
                if (!string.IsNullOrWhiteSpace(sidecarPath) && File.Exists(sidecarPath))
                    File.Delete(sidecarPath);
            }
        }

        [UnityTest]
        public IEnumerator Twin1UdpLifecycleRejectsRawActuationAndRebindsCleanly()
        {
            yield return LoadTwin1Scene();
            TelemetryUdpBridge original = Object.FindAnyObjectByType<TelemetryUdpBridge>();
            Assert.NotNull(original);
            GameObject host = original.gameObject;
            int commandPort = original.CommandPort;
            ROVVehicle vehicle = original.Vehicle;
            DutyManager duties = original.Duties;
            DepthSensor depth = original.Depth;
            DvlSensor dvl = original.Dvl;
            SimulatedPowerSensor power = original.Power;
            UnderwaterEnvironment environment = original.Environment;
            Object.Destroy(original);
            yield return null;

            TelemetryUdpBridge replacement = host.AddComponent<TelemetryUdpBridge>();
            replacement.Vehicle = vehicle;
            replacement.Duties = duties;
            replacement.Depth = depth;
            replacement.Dvl = dvl;
            replacement.Power = power;
            replacement.Environment = environment;
            replacement.CommandPort = commandPort;
            replacement.PublishEnabled = false;
            yield return null;
            Assert.IsTrue(replacement.enabled, "The command socket must rebind after teardown.");

            using (var client = new UdpClient())
            {
                byte[] rawActuation = Encoding.UTF8.GetBytes("{\"intent\":\"thruster_pwm\"}");
                client.Send(rawActuation, rawActuation.Length, "127.0.0.1", commandPort);
                byte[] highLevel = Encoding.UTF8.GetBytes("{\"intent\":\"hold_position\"}");
                client.Send(highLevel, highLevel.Length, "127.0.0.1", commandPort);
            }
            float deadline = Time.realtimeSinceStartup + 3f;
            while (!replacement.LastHighLevelCommand.Contains("hold_position") &&
                   Time.realtimeSinceStartup < deadline)
                yield return null;
            Assert.That(replacement.LastHighLevelCommand, Does.Contain("hold_position"));
            Assert.That(replacement.LastHighLevelCommand, Does.Not.Contain("thruster"));

            Object.Destroy(replacement);
            yield return null;
            TelemetryUdpBridge secondSession = host.AddComponent<TelemetryUdpBridge>();
            secondSession.Vehicle = vehicle;
            secondSession.Duties = duties;
            secondSession.Depth = depth;
            secondSession.Dvl = dvl;
            secondSession.Power = power;
            secondSession.Environment = environment;
            secondSession.CommandPort = commandPort;
            secondSession.PublishEnabled = false;
            yield return null;
            Assert.IsTrue(secondSession.enabled, "A second consecutive Play session must rebind the UDP port.");
            Object.Destroy(secondSession);
            yield return null;
        }

        [UnityTest]
        public IEnumerator Twin1BoundaryKeepsModel1Model2Twin2NavigationAndVisualFixturesDistinct()
        {
            yield return LoadTwin1Scene();
            OceanSenseApiClient api = Object.FindAnyObjectByType<OceanSenseApiClient>();
            SyntheticCaptureController fixture = Object.FindAnyObjectByType<SyntheticCaptureController>();
            BehaviorParameters navigation = Object.FindAnyObjectByType<BehaviorParameters>();

            Assert.NotNull(api, "Model 1 integration is an external HTTP adapter, not a navigation model.");
            Assert.NotNull(fixture, "Visual fixture capture must remain explicitly synthetic/demo behavior.");
            Assert.NotNull(navigation, "Navigation/control must remain a separate ML-Agents component.");
            Assert.IsTrue(api.ExpectsFixtureBackend,
                "Default fixture expectation must never be presented as real Model 1 inference.");
            Assert.AreNotEqual("model1", api.BackendExpectationLabel,
                "Fixture expectation must be distinguishable from real Model 1 inference.");
            Assert.AreEqual("OceanSenseROV", navigation.BehaviorName);
            Assert.AreNotEqual(api.GetType(), fixture.GetType());
            Assert.AreNotEqual(api.GetType(), navigation.GetType());
        }

        private static IEnumerator LoadTwin1Scene()
        {
            AsyncOperation load = SceneManager.LoadSceneAsync(SceneName, LoadSceneMode.Single);
            Assert.NotNull(load, $"Twin 1 scene '{SceneName}' must be present in build settings.");
            while (!load.isDone)
                yield return null;
            yield return null;
            Assert.AreEqual(SceneName, SceneManager.GetActiveScene().name);
        }

        private static void AssertFinite(float value, string label)
        {
            Assert.IsFalse(float.IsNaN(value) || float.IsInfinity(value), $"{label} must be finite.");
        }

        private static void AssertFinite(Vector3 value, string label)
        {
            AssertFinite(value.x, $"{label}.x");
            AssertFinite(value.y, $"{label}.y");
            AssertFinite(value.z, $"{label}.z");
        }

    }
}
