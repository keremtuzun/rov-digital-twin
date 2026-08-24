using UnityEngine;
using Unity.MLAgents;

namespace ROVDigitalTwin
{
    [System.Serializable]
    public sealed class DomainRandomizationProfileSet { public DomainRandomizationProfile[] profiles; }
    [System.Serializable]
    public sealed class DomainRandomizationProfile
    {
        public string name;
        public float current_min;
        public float current_max;
        public float wave_height_min;
        public float wave_height_max;
        public float latency_max_ms;
        public float packet_loss_max;
    }

    public sealed class DomainRandomization : MonoBehaviour
    {
        public bool Enabled = true;
        public ROVVehicle Vehicle;
        public Hydrodynamics6Dof Hydrodynamics;
        public WaterCurrentField CurrentField;
        public UnderwaterEnvironment Environment;
        public DutyManager DutyManager;
        public SimulatedPowerSensor Power;
        public TelemetryUdpBridge Telemetry;
        public Vector2 MassRangeKg = new Vector2(20.5f, 23.5f);
        public Vector2 DragMultiplierRange = new Vector2(0.85f, 1.2f);
        public Vector2 CurrentSpeedRange = new Vector2(0.03f, 0.3f);
        public Vector2 ThrusterEfficiencyRange = new Vector2(0.88f, 1f);
        public string ProfileName = "moderate_sea";
        public TextAsset ProfileConfigurationJson;
        private DomainRandomizationProfile selectedProfile;

        private ImuSensor imu;
        private DepthSensor depth;
        private DvlSensor dvl;
        private ForwardSonarSensor sonar;

        private void Awake()
        {
            Vehicle ??= GetComponent<ROVVehicle>();
            Hydrodynamics ??= GetComponent<Hydrodynamics6Dof>();
            DutyManager ??= FindAnyObjectByType<DutyManager>();
            Environment ??= FindAnyObjectByType<UnderwaterEnvironment>();
            Power ??= GetComponent<SimulatedPowerSensor>();
            Telemetry ??= GetComponent<TelemetryUdpBridge>();
            imu = GetComponent<ImuSensor>();
            depth = GetComponent<DepthSensor>();
            dvl = GetComponent<DvlSensor>();
            sonar = GetComponent<ForwardSonarSensor>();
            ProfileConfigurationJson ??= Resources.Load<TextAsset>("domain_randomization_profiles");
            LoadSelectedProfile();
        }

        public void LoadSelectedProfile()
        {
            selectedProfile = null;
            if (ProfileConfigurationJson == null)
                return;
            DomainRandomizationProfileSet profileSet =
                JsonUtility.FromJson<DomainRandomizationProfileSet>(ProfileConfigurationJson.text);
            if (profileSet?.profiles == null)
                return;
            foreach (DomainRandomizationProfile profile in profileSet.profiles)
                if (profile.name == ProfileName) selectedProfile = profile;
            if (selectedProfile != null)
                CurrentSpeedRange = new Vector2(selectedProfile.current_min, selectedProfile.current_max);
        }

        public void ApplyEpisodeRandomization()
        {
            if (!Enabled || Vehicle == null || Hydrodynamics == null)
                return;

            float difficulty = Mathf.Clamp01(Academy.Instance.EnvironmentParameters.GetWithDefault("difficulty", 1f));
            Vehicle.Body.mass = Random.Range(Mathf.Lerp(21.5f, MassRangeKg.x, difficulty), Mathf.Lerp(22.5f, MassRangeKg.y, difficulty));
            Vehicle.Body.centerOfMass = new Vector3(
                Random.Range(-0.04f, 0.04f), Random.Range(-0.03f, 0.04f),
                Random.Range(-0.05f, 0.05f)) * difficulty;
            float dragMin = Mathf.Lerp(0.96f, DragMultiplierRange.x, difficulty);
            float dragMax = Mathf.Lerp(1.04f, DragMultiplierRange.y, difficulty);
            Hydrodynamics.ExternalDragMultiplier = Random.Range(dragMin, dragMax);
            Hydrodynamics.CenterOfBuoyancyOffset = new Vector3(
                Random.Range(-0.035f, 0.035f) * difficulty,
                Random.Range(0.17f, 0.23f),
                Random.Range(-0.035f, 0.035f) * difficulty);
            if (CurrentField != null)
            {
                float maxCurrent = Mathf.Lerp(0.1f, CurrentSpeedRange.y, difficulty);
                float speed = Random.Range(CurrentSpeedRange.x, maxCurrent);
                float heading = Random.Range(0f, Mathf.PI * 2f);
                CurrentField.BaseCurrentMetersPerSecond = new Vector3(Mathf.Cos(heading) * speed,
                    Random.Range(-0.06f, 0.06f) * difficulty, Mathf.Sin(heading) * speed);
                CurrentField.DepthShearPerMeter = Random.Range(0.002f, Mathf.Lerp(0.007f, 0.02f, difficulty));
                CurrentField.Turbulence = Random.Range(0.02f, Mathf.Lerp(0.06f, 0.14f, difficulty));
                float waveMin = selectedProfile != null ? selectedProfile.wave_height_min : 0.12f;
                float waveMax = selectedProfile != null ? selectedProfile.wave_height_max : 1.35f;
                CurrentField.SignificantWaveHeightMeters = Random.Range(waveMin,
                    Mathf.Lerp(Mathf.Max(waveMin, 0.45f), waveMax, difficulty));
                CurrentField.PeakWavePeriodSeconds = Random.Range(Mathf.Lerp(5.5f, 4f, difficulty), 9f);
                CurrentField.WaveDirectionDegrees = Random.Range(0f, 360f);
            }
            if (Environment != null)
            {
                Environment.Contamination01 = Random.Range(0.02f, Mathf.Lerp(0.12f, 0.35f, difficulty));
                Environment.TurbidityNtu = Random.Range(0.3f, Mathf.Lerp(2.5f, 7f, difficulty));
                Environment.SuspendedSedimentMgPerLiter = Random.Range(0.5f, Mathf.Lerp(5f, 18f, difficulty));
                Environment.SalinityPsu = Random.Range(Mathf.Lerp(32f, 5f, difficulty), 37f);
                Environment.WaterTemperatureC = Random.Range(4f, Mathf.Lerp(16f, 28f, difficulty));
                Environment.Biofouling01 = Random.Range(0f, 0.25f * difficulty);
                Environment.CameraExposureMultiplier = Random.Range(
                    Mathf.Lerp(0.9f, 0.55f, difficulty), Mathf.Lerp(1.1f, 1.45f, difficulty));
                Hydrodynamics.FluidDensity = Environment.EstimatedWaterDensityKgPerCubicMeter;
                Environment.RefreshConditionVisuals();
            }
            float efficiencyMin = Mathf.Lerp(0.96f, ThrusterEfficiencyRange.x, difficulty);
            foreach (Thruster thruster in Vehicle.Thrusters)
            {
                thruster.Efficiency = Random.Range(efficiencyMin, ThrusterEfficiencyRange.y);
                thruster.ManufacturingGain = Random.Range(0.94f, 1.06f);
                thruster.ResponseTimeSeconds = Random.Range(0.11f, Mathf.Lerp(0.16f, 0.32f, difficulty));
                thruster.Fouling01 = Environment != null ? Environment.Biofouling01
                    * Random.Range(0.7f, 1.3f) : 0f;
                thruster.WaterDensityKgPerCubicMeter = Hydrodynamics.FluidDensity;
            }
            if (Power != null)
            {
                Power.InternalResistanceOhm = Random.Range(0.025f,
                    Mathf.Lerp(0.045f, 0.09f, difficulty));
                Power.NominalVoltage = Random.Range(46.5f, 49f);
            }
            if (Telemetry != null)
            {
                float latencyMax = selectedProfile != null ? selectedProfile.latency_max_ms : 180f;
                float lossMax = selectedProfile != null ? selectedProfile.packet_loss_max : 0.08f;
                Telemetry.SimulatedLatencyMs = Random.Range(0f, Mathf.Lerp(15f, latencyMax, difficulty));
                Telemetry.SimulatedJitterMs = Random.Range(0f, Mathf.Lerp(4f, 55f, difficulty));
                Telemetry.PacketLossProbability = Random.Range(0f, Mathf.Lerp(0.005f, lossMax, difficulty));
            }

            if (DutyManager != null)
            {
                DutyManager.RandomTargetMinimum = Vector3.Lerp(new Vector3(-3f, -8f, -11f), new Vector3(-12f, -10f, -12f), difficulty);
                DutyManager.RandomTargetMaximum = Vector3.Lerp(new Vector3(3f, -4f, -5f), new Vector3(12f, -3f, 12f), difficulty);
                DutyManager.CurrentDuty.SuccessRadiusMeters = Mathf.Lerp(1.5f, 0.8f, difficulty);
            }

            if (imu != null) { imu.AccelerationNoise = Random.Range(0.008f, Mathf.Lerp(0.015f, 0.03f, difficulty)); imu.GyroNoise = Random.Range(0.001f, Mathf.Lerp(0.002f, 0.005f, difficulty)); }
            if (depth != null) { depth.NoiseStandardDeviationMeters = Random.Range(0.005f, Mathf.Lerp(0.012f, 0.035f, difficulty)); depth.BiasMeters = Random.Range(-0.025f, 0.025f) * difficulty; }
            if (dvl != null) { dvl.VelocityNoise = Random.Range(0.005f, Mathf.Lerp(0.012f, 0.03f, difficulty)); dvl.QualityScale = Random.Range(Mathf.Lerp(0.94f, 0.82f, difficulty), 1f); }
            if (sonar != null) sonar.NoiseStandardDeviationMeters = Random.Range(0.005f, Mathf.Lerp(0.015f, 0.04f, difficulty));
        }
    }
}
