using System.IO;
using Unity.MLAgents;
using Unity.MLAgents.Actuators;
using Unity.MLAgents.Policies;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace ROVDigitalTwin.Editor
{
    [InitializeOnLoad]
    public static class CompleteProjectBuilder
    {
        private const string Root = "Assets/ROVDigitalTwin";
        private const string ScenePath = Root + "/Scenes/OceanSenseDemo.unity";

        static CompleteProjectBuilder()
        {
            EditorApplication.delayCall += () =>
            {
                if (!File.Exists(ScenePath) && !Application.isPlaying)
                    BuildCompleteDemo();
            };
        }

        [MenuItem("OceanSense/Build Complete Demo")]
        public static void BuildCompleteDemo()
        {
            EnsureFolders();
            Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            Material water = Material("Water", new Color(0.02f, 0.22f, 0.30f, 0.75f));
            Material sand = Material("Sand", new Color(0.28f, 0.24f, 0.15f));
            Material metal = Material("RobotMetal", new Color(0.1f, 0.17f, 0.2f));
            Material yellow = Material("SafetyYellow", new Color(1f, 0.55f, 0.03f));
            Material pipelineMaterial = Material("Pipeline", new Color(0.34f, 0.19f, 0.08f));

            RenderSettings.fog = true;
            RenderSettings.fogColor = new Color(0.015f, 0.16f, 0.21f);
            RenderSettings.fogMode = FogMode.ExponentialSquared;
            RenderSettings.fogDensity = 0.025f;
            RenderSettings.ambientLight = new Color(0.04f, 0.13f, 0.16f);

            GameObject sunObject = new GameObject("Filtered Sunlight");
            Light sun = sunObject.AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.intensity = 0.65f;
            sun.color = new Color(0.55f, 0.82f, 0.9f);
            sunObject.transform.rotation = Quaternion.Euler(55f, -25f, 0f);

            GameObject environment = new GameObject("Underwater Environment");
            WaterCurrentField current = environment.AddComponent<WaterCurrentField>();
            CreatePrimitive("Seafloor", PrimitiveType.Cube, new Vector3(0f, -12.5f, 0f), new Vector3(70f, 1f, 70f), sand, environment.transform);
            GameObject surface = CreatePrimitive("Water Surface", PrimitiveType.Cube, new Vector3(0f, 0.25f, 0f), new Vector3(70f, 0.25f, 70f), water, environment.transform);
            Object.DestroyImmediate(surface.GetComponent<Collider>());
            UnderwaterEnvironment ocean = environment.AddComponent<UnderwaterEnvironment>();
            ocean.FilteredSun = sun;
            ocean.WaterSurface = surface.transform;
            ocean.CurrentField = current;

            GameObject pipelineStart = new GameObject("Pipeline Start");
            pipelineStart.transform.position = new Vector3(-12f, -11.4f, -15f);
            GameObject pipelineEnd = new GameObject("Pipeline End");
            pipelineEnd.transform.position = new Vector3(-12f, -11.4f, 15f);
            for (int index = -7; index <= 7; index++)
            {
                GameObject pipe = CreatePrimitive($"Pipeline {index + 8:00}", PrimitiveType.Cylinder, new Vector3(-12f, -11.4f, index * 2f), new Vector3(0.7f, 1.15f, 0.7f), pipelineMaterial, environment.transform);
                pipe.transform.rotation = Quaternion.Euler(90f, 0f, 0f);
            }
            for (int index = 0; index < 26; index++)
            {
                Vector3 position = new Vector3(Random.Range(-27f, 27f), -11.6f, Random.Range(-27f, 27f));
                PrimitiveType type = index % 3 == 0 ? PrimitiveType.Capsule : PrimitiveType.Sphere;
                GameObject rock = CreatePrimitive($"Reef {index:00}", type, position, Vector3.one * Random.Range(0.45f, 1.8f), index % 4 == 0 ? yellow : sand, environment.transform);
                rock.transform.rotation = Random.rotation;
            }

            GameObject target = CreatePrimitive("Mission Target", PrimitiveType.Sphere, new Vector3(8f, -7f, 9f), Vector3.one * 0.8f, yellow, null);
            Object.DestroyImmediate(target.GetComponent<Collider>());
            DutyManager duties = new GameObject("Duty Manager").AddComponent<DutyManager>();
            duties.CurrentDuty.Target = target.transform;
            duties.CurrentDuty.PipelineStart = pipelineStart.transform;
            duties.CurrentDuty.PipelineEnd = pipelineEnd.transform;

            GameObject rov = BuildRov(metal, yellow, current, ocean, duties);
            PrefabUtility.SaveAsPrefabAsset(rov, Root + "/Prefabs/OceanSenseROV.prefab");

            GameObject cameraObject = new GameObject("Operator Camera");
            cameraObject.tag = "MainCamera";
            Camera camera = cameraObject.AddComponent<Camera>();
            camera.fieldOfView = 65f;
            cameraObject.transform.position = rov.transform.TransformPoint(new Vector3(0f, 3f, -7f));
            FollowCamera follow = cameraObject.AddComponent<FollowCamera>();
            follow.Target = rov.transform;

            WireIntegration(rov, duties, camera);
            EditorSceneManager.SaveScene(scene, ScenePath);
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
            AssetDatabase.SaveAssets();
            Selection.activeGameObject = rov;
            Debug.Log("OceanSense demo, procedural ROV prefab, sensors, dashboard, ML-Agents and bridges were generated.");
        }

        private static GameObject BuildRov(Material metal, Material yellow, WaterCurrentField current,
            UnderwaterEnvironment ocean, DutyManager duties)
        {
            GameObject rov = new GameObject("OceanSense ROV");
            rov.transform.position = new Vector3(0f, -6f, -8f);
            Rigidbody body = rov.AddComponent<Rigidbody>();
            body.mass = 22f;
            body.linearDamping = 0.08f;
            body.angularDamping = 0.12f;
            body.useGravity = true;
            CreatePrimitive("Pressure Hull", PrimitiveType.Cube, Vector3.zero, new Vector3(2.2f, 0.75f, 2.8f), metal, rov.transform, true);
            CreatePrimitive("Top Float", PrimitiveType.Cube, new Vector3(0f, 0.65f, 0f), new Vector3(2.5f, 0.35f, 2.9f), yellow, rov.transform, true);
            for (int x = -1; x <= 1; x += 2)
                for (int z = -1; z <= 1; z += 2)
                    CreatePrimitive("Frame", PrimitiveType.Cylinder, new Vector3(x * 1.35f, 0f, z * 1.5f), new Vector3(0.11f, 1.5f, 0.11f), yellow, rov.transform, true).transform.localRotation = Quaternion.Euler(90f, 0f, 0f);

            var thrusters = new Thruster[8];
            Vector3[] positions =
            {
                new Vector3(-1.15f, 0f, 1.1f), new Vector3(1.15f, 0f, 1.1f),
                new Vector3(-1.15f, 0f, -1.1f), new Vector3(1.15f, 0f, -1.1f),
                new Vector3(-1.15f, 0.45f, 1.1f), new Vector3(1.15f, 0.45f, 1.1f),
                new Vector3(-1.15f, 0.45f, -1.1f), new Vector3(1.15f, 0.45f, -1.1f)
            };
            for (int index = 0; index < thrusters.Length; index++)
            {
                GameObject thrusterObject = new GameObject($"Thruster {index + 1}");
                thrusterObject.transform.SetParent(rov.transform, false);
                thrusterObject.transform.localPosition = positions[index];
                thrusterObject.transform.localRotation = index < 4
                    ? Quaternion.Euler(0f, index % 2 == 0 ? 45f : -45f, 0f)
                    : Quaternion.Euler(-90f, 0f, 0f);
                GameObject visual = CreatePrimitive("Housing", PrimitiveType.Cylinder, Vector3.zero, new Vector3(0.35f, 0.35f, 0.35f), metal, thrusterObject.transform, true);
                visual.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);
                thrusters[index] = thrusterObject.AddComponent<Thruster>();
                thrusters[index].MaxForceNewtons = index < 4 ? 65f : 55f;
            }

            ROVVehicle vehicle = rov.AddComponent<ROVVehicle>();
            vehicle.Thrusters = thrusters;
            rov.AddComponent<SimulatedPowerSensor>();
            Hydrodynamics6Dof hydrodynamics = rov.AddComponent<Hydrodynamics6Dof>();
            hydrodynamics.CurrentField = current;
            DomainRandomization randomization = rov.AddComponent<DomainRandomization>();
            randomization.Vehicle = vehicle;
            randomization.Hydrodynamics = hydrodynamics;
            randomization.CurrentField = current;
            randomization.Environment = ocean;
            rov.AddComponent<ImuSensor>();
            rov.AddComponent<DepthSensor>();
            DvlSensor dvl = rov.AddComponent<DvlSensor>();
            dvl.CurrentField = current;
            dvl.Environment = ocean;
            ForwardSonarSensor sonar = rov.AddComponent<ForwardSonarSensor>();
            sonar.Environment = ocean;

            GameObject sensorHead = new GameObject("Inspection Camera");
            sensorHead.transform.SetParent(rov.transform, false);
            sensorHead.transform.localPosition = new Vector3(0f, 0.1f, 1.5f);
            Camera inspectionCamera = sensorHead.AddComponent<Camera>();
            inspectionCamera.enabled = false;
            inspectionCamera.fieldOfView = 70f;
            Light lamp = sensorHead.AddComponent<Light>();
            lamp.type = LightType.Spot;
            lamp.range = 18f;
            lamp.spotAngle = 65f;
            lamp.intensity = 5f;

            BehaviorParameters behavior = rov.AddComponent<BehaviorParameters>();
            behavior.BehaviorName = "OceanSenseROV";
            behavior.BrainParameters.VectorObservationSize = ROVRLAgent.ObservationSize;
            behavior.BrainParameters.ActionSpec = ActionSpec.MakeContinuous(ROVRLAgent.ActionSize);
            // Add the concrete agent before DecisionRequester. DecisionRequester requires an
            // Agent, and adding it first makes Unity silently attach an extra base Agent that
            // emits empty observations and placeholder heuristic actions at runtime.
            ROVRLAgent agent = rov.AddComponent<ROVRLAgent>();
            agent.Vehicle = vehicle;
            agent.DutyManager = duties;
            agent.DomainRandomization = randomization;
            DecisionRequester requester = rov.AddComponent<DecisionRequester>();
            requester.DecisionPeriod = 5;
            requester.TakeActionsBetweenDecisions = true;
            return rov;
        }

        private static void WireIntegration(GameObject rov, DutyManager duties, Camera operatorCamera)
        {
            ROVVehicle vehicle = rov.GetComponent<ROVVehicle>();
            DepthSensor depth = rov.GetComponent<DepthSensor>();
            DvlSensor dvl = rov.GetComponent<DvlSensor>();
            ROVCameraCapture capture = rov.AddComponent<ROVCameraCapture>();
            capture.SourceCamera = rov.GetComponentInChildren<Camera>();
            OceanSenseApiClient api = rov.AddComponent<OceanSenseApiClient>();
            api.CameraCapture = capture; api.Vehicle = vehicle; api.Depth = depth;
            MissionController mission = rov.AddComponent<MissionController>();
            mission.Vehicle = vehicle; mission.Duties = duties; mission.Api = api;
            TelemetryUdpBridge bridge = rov.AddComponent<TelemetryUdpBridge>();
            bridge.Vehicle = vehicle; bridge.Duties = duties; bridge.Depth = depth; bridge.Dvl = dvl;
            bridge.Power = rov.GetComponent<SimulatedPowerSensor>();
            bridge.Environment = Object.FindAnyObjectByType<UnderwaterEnvironment>();
            SyntheticCaptureController synthetic = rov.AddComponent<SyntheticCaptureController>();
            synthetic.Capture = capture; synthetic.Target = duties.CurrentDuty.Target;
            synthetic.Current = Object.FindAnyObjectByType<WaterCurrentField>();
            synthetic.Environment = Object.FindAnyObjectByType<UnderwaterEnvironment>();
            synthetic.SceneLight = Object.FindAnyObjectByType<Light>();
            mission.SyntheticCapture = synthetic;
            FaultInjectionController faults = rov.AddComponent<FaultInjectionController>();
            faults.Vehicle = vehicle; faults.Hydrodynamics = rov.GetComponent<Hydrodynamics6Dof>();
            faults.Depth = depth; faults.Dvl = dvl; faults.Power = bridge.Power; faults.Telemetry = bridge;
            OceanSenseDashboard dashboard = operatorCamera.gameObject.AddComponent<OceanSenseDashboard>();
            dashboard.Vehicle = vehicle; dashboard.Duties = duties; dashboard.Depth = depth; dashboard.Dvl = dvl; dashboard.Api = api;
            dashboard.Environment = Object.FindAnyObjectByType<UnderwaterEnvironment>();
        }

        private static GameObject CreatePrimitive(string name, PrimitiveType type, Vector3 position, Vector3 scale, Material material, Transform parent, bool local = false)
        {
            GameObject item = GameObject.CreatePrimitive(type);
            item.name = name;
            if (parent != null) item.transform.SetParent(parent, false);
            if (local) item.transform.localPosition = position; else item.transform.position = position;
            item.transform.localScale = scale;
            item.GetComponent<Renderer>().sharedMaterial = material;
            return item;
        }

        private static Material Material(string name, Color color)
        {
            string path = Root + "/Materials/" + name + ".mat";
            Material material = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (material != null) return material;
            Shader shader = Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard");
            material = new Material(shader) { color = color };
            AssetDatabase.CreateAsset(material, path);
            return material;
        }

        private static void EnsureFolders()
        {
            foreach (string folder in new[] { Root + "/Editor", Root + "/Scenes", Root + "/Prefabs", Root + "/Materials" })
                Directory.CreateDirectory(folder);
            AssetDatabase.Refresh();
        }
    }
}
