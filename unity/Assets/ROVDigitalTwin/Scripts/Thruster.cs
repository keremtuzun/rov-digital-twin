using UnityEngine;

namespace ROVDigitalTwin
{
    public enum ThrusterModelType { LegacyLinear, AdvancedCurve }

    [DisallowMultipleComponent]
    public sealed class Thruster : MonoBehaviour
    {
        [Min(0.1f)] public float MaxForceNewtons = 50f;
        [Range(-1f, 1f)] public float Command;
        [Range(0f, 1f)] public float Efficiency = 1f;
        public ThrusterModelType ModelType = ThrusterModelType.AdvancedCurve;
        [Min(0.01f)] public float ResponseTimeSeconds = 0.14f;
        [Min(0.1f)] public float MaximumCommandRatePerSecond = 4f;
        [Range(0f, 0.3f)] public float CommandDeadZone = 0.06f;
        [Range(1f, 3f)] public float ThrustCurveExponent = 1.65f;
        [Range(0.2f, 1f)] public float ReverseThrustRatio = 0.82f;
        [Range(0.1f, 1f)] public float SaturationCommand = 0.96f;
        [Range(0f, 1f)] public float Fouling01;
        [Range(0.8f, 1.2f)] public float ManufacturingGain = 1f;
        [Min(1f)] public float SupplyVoltageV = 48f;
        [Min(1f)] public float ReferenceVoltageV = 48f;
        [Min(900f)] public float WaterDensityKgPerCubicMeter = 1025f;
        [Min(900f)] public float ReferenceWaterDensityKgPerCubicMeter = 1025f;
        public float MotorTemperatureC = 25f;
        public float DeratingStartTemperatureC = 55f;
        public float ShutdownTemperatureC = 85f;
        public bool DrawDebugForce = true;

        private Rigidbody body;
        private float requestedCommand;

        public float ActualThrustNewtons { get; private set; }
        public float AppliedForceNewtons => ActualThrustNewtons;
        public float RequestedCommand => requestedCommand;

        public void Initialize(Rigidbody targetBody) => body = targetBody;

        public void SetCommand(float value) => requestedCommand = Mathf.Clamp(value, -1f, 1f);

        public void StopImmediately()
        {
            requestedCommand = 0f;
            Command = 0f;
            ActualThrustNewtons = 0f;
        }

        private void Awake()
        {
            if (body == null)
                body = GetComponentInParent<Rigidbody>();
        }

        private void FixedUpdate()
        {
            if (body == null)
                return;
            float filtered = Mathf.Lerp(Command, requestedCommand,
                1f - Mathf.Exp(-Time.fixedDeltaTime / ResponseTimeSeconds));
            Command = Mathf.MoveTowards(Command, filtered,
                MaximumCommandRatePerSecond * Time.fixedDeltaTime);
            ActualThrustNewtons = EvaluateThrust(Command);
            body.AddForceAtPosition(transform.forward * AppliedForceNewtons, transform.position, ForceMode.Force);
        }

        public float EvaluateThrust(float command)
        {
            float limited = Mathf.Clamp(command, -SaturationCommand, SaturationCommand);
            if (ModelType == ThrusterModelType.LegacyLinear)
                return limited * MaxForceNewtons * Efficiency;
            float magnitude = Mathf.Abs(limited);
            if (magnitude <= CommandDeadZone)
                return 0f;
            float normalized = Mathf.InverseLerp(CommandDeadZone, SaturationCommand, magnitude);
            float curve = Mathf.Pow(normalized, ThrustCurveExponent);
            float reverse = limited < 0f ? ReverseThrustRatio : 1f;
            float voltageScale = Mathf.Clamp(SupplyVoltageV / Mathf.Max(ReferenceVoltageV, 1f), 0.45f, 1.1f);
            float densityScale = Mathf.Sqrt(Mathf.Max(0.1f,
                WaterDensityKgPerCubicMeter / Mathf.Max(ReferenceWaterDensityKgPerCubicMeter, 1f)));
            float thermal = 1f - Mathf.InverseLerp(DeratingStartTemperatureC,
                Mathf.Max(ShutdownTemperatureC, DeratingStartTemperatureC + 1f), MotorTemperatureC);
            float fouling = Mathf.Lerp(1f, 0.55f, Fouling01);
            return Mathf.Sign(limited) * MaxForceNewtons * curve * reverse * Efficiency
                   * ManufacturingGain * voltageScale * densityScale * thermal * fouling;
        }

        private void OnDrawGizmosSelected()
        {
            if (!DrawDebugForce)
                return;
            Gizmos.color = Command >= 0f ? Color.cyan : Color.magenta;
            Gizmos.DrawRay(transform.position, transform.forward * Mathf.Lerp(0.25f, 1.5f, Mathf.Abs(Command)));
        }
    }
}
