using UnityEngine;

namespace ROVDigitalTwin
{
    [RequireComponent(typeof(ROVVehicle))]
    public sealed class SimulatedPowerSensor : MonoBehaviour
    {
        public float NominalVoltage = 48f;
        public float InternalResistanceOhm = 0.035f;
        public float IdleCurrentA = 1.8f;
        public float FullCommandCurrentA = 38f;
        public float AmbientTemperatureC = 18f;
        [Range(0f, 1.5f)] public float ThrusterResponseRatio = 1f;

        public float CurrentA { get; private set; }
        public float VoltageV { get; private set; }
        public float TemperatureC { get; private set; }

        private ROVVehicle vehicle;

        private void Awake() => vehicle = GetComponent<ROVVehicle>();

        private void FixedUpdate()
        {
            CurrentA = IdleCurrentA + vehicle.MeanAbsoluteCommand * FullCommandCurrentA;
            float stateOfChargeVoltage = NominalVoltage * Mathf.Lerp(0.84f, 1f, vehicle.BatteryLevel01);
            VoltageV = Mathf.Max(0f, stateOfChargeVoltage - CurrentA * InternalResistanceOhm);
            TemperatureC = AmbientTemperatureC + CurrentA * 0.18f;
            foreach (Thruster thruster in vehicle.Thrusters)
            {
                thruster.SupplyVoltageV = VoltageV;
                thruster.MotorTemperatureC = TemperatureC;
            }
        }
    }
}
