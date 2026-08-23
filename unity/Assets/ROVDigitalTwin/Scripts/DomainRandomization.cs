using UnityEngine;
using Unity.MLAgents;

namespace ROVDigitalTwin
{
    public sealed class DomainRandomization : MonoBehaviour
    {
        public bool Enabled = true;
        public ROVVehicle Vehicle;
        public Hydrodynamics6Dof Hydrodynamics;
        public WaterCurrentField CurrentField;
        public UnderwaterEnvironment Environment;
        public DutyManager DutyManager;
        public Vector2 MassRangeKg = new Vector2(20.5f, 23.5f);
        public Vector2 DragMultiplierRange = new Vector2(0.85f, 1.2f);
        public Vector2 CurrentSpeedRange = new Vector2(0.03f, 0.3f);
        public Vector2 ThrusterEfficiencyRange = new Vector2(0.88f, 1f);

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
            imu = GetComponent<ImuSensor>();
            depth = GetComponent<DepthSensor>();
            dvl = GetComponent<DvlSensor>();
            sonar = GetComponent<ForwardSonarSensor>();
        }

        public void ApplyEpisodeRandomization()
        {
            if (!Enabled || Vehicle == null || Hydrodynamics == null)
                return;

            float difficulty = Mathf.Clamp01(Academy.Instance.EnvironmentParameters.GetWithDefault("difficulty", 1f));
            Vehicle.Body.mass = Random.Range(Mathf.Lerp(21.5f, MassRangeKg.x, difficulty), Mathf.Lerp(22.5f, MassRangeKg.y, difficulty));
            float dragMin = Mathf.Lerp(0.96f, DragMultiplierRange.x, difficulty);
            float dragMax = Mathf.Lerp(1.04f, DragMultiplierRange.y, difficulty);
            Hydrodynamics.ExternalDragMultiplier = Random.Range(dragMin, dragMax);
            if (CurrentField != null)
            {
                float maxCurrent = Mathf.Lerp(0.1f, CurrentSpeedRange.y, difficulty);
                float speed = Random.Range(CurrentSpeedRange.x, maxCurrent);
                float heading = Random.Range(0f, Mathf.PI * 2f);
                CurrentField.BaseCurrentMetersPerSecond = new Vector3(Mathf.Cos(heading) * speed, 0f, Mathf.Sin(heading) * speed);
                CurrentField.Turbulence = Random.Range(0.02f, Mathf.Lerp(0.06f, 0.14f, difficulty));
                CurrentField.SignificantWaveHeightMeters = Random.Range(0.12f, Mathf.Lerp(0.45f, 1.35f, difficulty));
                CurrentField.PeakWavePeriodSeconds = Random.Range(Mathf.Lerp(5.5f, 4f, difficulty), 9f);
                CurrentField.WaveDirectionDegrees = Random.Range(0f, 360f);
            }
            if (Environment != null)
            {
                Environment.Contamination01 = Random.Range(0.02f, Mathf.Lerp(0.12f, 0.35f, difficulty));
                Environment.TurbidityNtu = Random.Range(0.3f, Mathf.Lerp(2.5f, 7f, difficulty));
                Environment.SuspendedSedimentMgPerLiter = Random.Range(0.5f, Mathf.Lerp(5f, 18f, difficulty));
                Environment.RefreshConditionVisuals();
            }
            float efficiencyMin = Mathf.Lerp(0.96f, ThrusterEfficiencyRange.x, difficulty);
            foreach (Thruster thruster in Vehicle.Thrusters)
                thruster.Efficiency = Random.Range(efficiencyMin, ThrusterEfficiencyRange.y);

            if (DutyManager != null)
            {
                DutyManager.RandomTargetMinimum = Vector3.Lerp(new Vector3(-3f, -8f, -11f), new Vector3(-12f, -10f, -12f), difficulty);
                DutyManager.RandomTargetMaximum = Vector3.Lerp(new Vector3(3f, -4f, -5f), new Vector3(12f, -3f, 12f), difficulty);
            }

            if (imu != null) { imu.AccelerationNoise = Random.Range(0.008f, Mathf.Lerp(0.015f, 0.03f, difficulty)); imu.GyroNoise = Random.Range(0.001f, Mathf.Lerp(0.002f, 0.005f, difficulty)); }
            if (depth != null) { depth.NoiseStandardDeviationMeters = Random.Range(0.005f, Mathf.Lerp(0.012f, 0.035f, difficulty)); depth.BiasMeters = Random.Range(-0.025f, 0.025f) * difficulty; }
            if (dvl != null) { dvl.VelocityNoise = Random.Range(0.005f, Mathf.Lerp(0.012f, 0.03f, difficulty)); dvl.QualityScale = Random.Range(Mathf.Lerp(0.94f, 0.82f, difficulty), 1f); }
            if (sonar != null) sonar.NoiseStandardDeviationMeters = Random.Range(0.005f, Mathf.Lerp(0.015f, 0.04f, difficulty));
        }
    }
}
