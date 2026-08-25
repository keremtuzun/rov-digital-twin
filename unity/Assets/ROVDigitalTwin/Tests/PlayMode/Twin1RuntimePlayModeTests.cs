using System.Collections;
using System.IO;
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
        private const string ExpectedNavigationPolicyName = "OceanSenseROV_OpenSea_Experimental";

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
        public IEnumerator Twin1NavigationPolicyReferenceIsAssignedOrExplicitlyBlocked()
        {
            yield return LoadTwin1Scene();
            BehaviorParameters behavior = Object.FindAnyObjectByType<BehaviorParameters>();
            Assert.NotNull(behavior, "Twin 1 must expose its ML-Agents navigation/control contract.");
            Assert.AreEqual("OceanSenseROV", behavior.BehaviorName);

            if (behavior.Model == null)
            {
                Assert.Ignore(
                    "Known Twin 1 blocker: the committed scene has no navigation ONNX assigned. " +
                    "This policy is navigation/control only and must never be treated as a Model 1 checkpoint.");
            }

            Assert.AreEqual(ExpectedNavigationPolicyName, behavior.Model.name,
                "Only the expected navigation/control policy may be assigned to Twin 1 BehaviorParameters.");
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

    }
}
