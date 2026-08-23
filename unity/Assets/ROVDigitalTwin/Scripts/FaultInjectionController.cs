using UnityEngine;

namespace ROVDigitalTwin
{
    public enum SimulatedFault { None, ThrusterDegradation, SensorDrift, BuoyancyImbalance, AddedDrag, LowBattery, CommunicationLoss, DvlDropout, MultipleFaults }

    public sealed class FaultInjectionController : MonoBehaviour
    {
        public SimulatedFault ActiveFault;
        public ROVVehicle Vehicle;
        public Hydrodynamics6Dof Hydrodynamics;
        public DepthSensor Depth;
        public DvlSensor Dvl;
        public SimulatedPowerSensor Power;
        public TelemetryUdpBridge Telemetry;
        [Range(0f, 1f)] public float NominalBatteryLevel = 1f;

        public void ApplyFault(SimulatedFault fault)
        {
            ActiveFault = fault;
            Hydrodynamics.ExternalDragMultiplier = 1f;
            Hydrodynamics.CenterOfBuoyancyOffset = new Vector3(0f, 0.12f, 0f);
            Depth.BiasMeters = 0f;
            Dvl.QualityScale = 1f;
            Power.ThrusterResponseRatio = 1f;
            Telemetry.PublishEnabled = true;
            Vehicle.BatteryLevel = NominalBatteryLevel;
            foreach (Thruster thruster in Vehicle.Thrusters)
                thruster.Efficiency = 1f;
            if (fault is SimulatedFault.ThrusterDegradation or SimulatedFault.MultipleFaults)
            {
                Power.ThrusterResponseRatio = 0.55f;
                if (Vehicle.Thrusters.Length > 0)
                    Vehicle.Thrusters[0].Efficiency = 0.45f;
            }
            if (fault is SimulatedFault.SensorDrift or SimulatedFault.MultipleFaults)
                Depth.BiasMeters = 1.2f;
            if (fault == SimulatedFault.BuoyancyImbalance)
                Hydrodynamics.CenterOfBuoyancyOffset = new Vector3(0.35f, 0.12f, 0f);
            if (fault is SimulatedFault.AddedDrag or SimulatedFault.MultipleFaults)
                Hydrodynamics.ExternalDragMultiplier = 2.2f;
            if (fault == SimulatedFault.LowBattery)
                Vehicle.BatteryLevel = 0.15f;
            if (fault == SimulatedFault.CommunicationLoss)
            {
                Telemetry.PublishEnabled = false;
                Vehicle.StopThrusters();
            }
            if (fault is SimulatedFault.DvlDropout or SimulatedFault.MultipleFaults)
                Dvl.QualityScale = 0f;
        }
    }
}
