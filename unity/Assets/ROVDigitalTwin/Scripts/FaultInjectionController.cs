using UnityEngine;

namespace ROVDigitalTwin
{
    public enum SimulatedFault
    {
        None, ThrusterDegradation, ThrusterFouling, SensorDrift, ImuRandomWalk,
        ImuDropout, DepthStuck, DepthJump, BuoyancyImbalance, AddedDrag, LowBattery,
        CommunicationLoss, CommunicationsDegraded, DvlDropout, DvlIntermittent,
        SonarBlindness, MultipleFaults
    }

    public sealed class FaultInjectionController : MonoBehaviour
    {
        public SimulatedFault ActiveFault;
        public ROVVehicle Vehicle;
        public Hydrodynamics6Dof Hydrodynamics;
        public DepthSensor Depth;
        public ImuSensor Imu;
        public DvlSensor Dvl;
        public ForwardSonarSensor Sonar;
        public SimulatedPowerSensor Power;
        public TelemetryUdpBridge Telemetry;
        [Range(0f, 1f)] public float NominalBatteryLevel = 1f;

        public void ApplyFault(SimulatedFault fault)
        {
            ActiveFault = fault;
            Hydrodynamics.ExternalDragMultiplier = 1f;
            Hydrodynamics.CenterOfBuoyancyOffset = new Vector3(0f, 0.20f, 0f);
            Depth.BiasMeters = 0f;
            Depth.BiasDriftMetersPerSecond = 0f;
            Depth.SuddenJumpMeters = 0f;
            Depth.StuckReading = false;
            Depth.NoiseMultiplier = 1f;
            Imu.ConstantAccelerationBias = Vector3.zero;
            Imu.ConstantGyroBias = Vector3.zero;
            Imu.AccelerationBiasDriftPerSecond = Vector3.zero;
            Imu.GyroBiasDriftPerSecond = Vector3.zero;
            Imu.RandomWalkStandardDeviation = 0f;
            Imu.DropoutProbability = 0f;
            Dvl.QualityScale = 1f;
            Dvl.DropoutProbability = 0f;
            Dvl.IntermittentDropoutProbability = 0f;
            Dvl.VelocityBias = Vector3.zero;
            Sonar.DropoutProbability = 0f;
            Sonar.FalseReturnProbability = 0f;
            Sonar.BlindFraction = 0f;
            Sonar.RangeClipRatio = 1f;
            Sonar.ScatteringNoiseMultiplier = 1f;
            Power.ThrusterResponseRatio = 1f;
            Telemetry.PublishEnabled = true;
            Telemetry.CompleteOutage = false;
            Telemetry.SimulatedLatencyMs = 0f;
            Telemetry.SimulatedJitterMs = 0f;
            Telemetry.PacketLossProbability = 0f;
            Telemetry.PacketDuplicationProbability = 0f;
            Telemetry.PacketReorderingProbability = 0f;
            Vehicle.BatteryLevel = NominalBatteryLevel;
            foreach (Thruster thruster in Vehicle.Thrusters)
            {
                thruster.Efficiency = 1f;
                thruster.Fouling01 = 0f;
            }
            if (fault is SimulatedFault.ThrusterDegradation or SimulatedFault.MultipleFaults)
            {
                Power.ThrusterResponseRatio = 0.55f;
                if (Vehicle.Thrusters.Length > 0)
                    Vehicle.Thrusters[0].Efficiency = 0.45f;
            }
            if (fault == SimulatedFault.ThrusterFouling)
                foreach (Thruster thruster in Vehicle.Thrusters)
                    thruster.Fouling01 = 0.7f;
            if (fault is SimulatedFault.SensorDrift or SimulatedFault.MultipleFaults)
            {
                Depth.BiasMeters = 1.2f;
                Depth.BiasDriftMetersPerSecond = 0.008f;
            }
            if (fault == SimulatedFault.ImuRandomWalk)
                Imu.RandomWalkStandardDeviation = 0.025f;
            if (fault == SimulatedFault.ImuDropout)
                Imu.DropoutProbability = 0.85f;
            if (fault == SimulatedFault.DepthStuck)
                Depth.StuckReading = true;
            if (fault == SimulatedFault.DepthJump)
                Depth.SuddenJumpMeters = 2.5f;
            if (fault == SimulatedFault.BuoyancyImbalance)
                Hydrodynamics.CenterOfBuoyancyOffset = new Vector3(0.35f, 0.12f, 0f);
            if (fault is SimulatedFault.AddedDrag or SimulatedFault.MultipleFaults)
                Hydrodynamics.ExternalDragMultiplier = 2.2f;
            if (fault == SimulatedFault.LowBattery)
                Vehicle.BatteryLevel = 0.15f;
            if (fault == SimulatedFault.CommunicationLoss)
            {
                Telemetry.PublishEnabled = false;
                Telemetry.CompleteOutage = true;
                Vehicle.StopThrusters();
            }
            if (fault == SimulatedFault.CommunicationsDegraded)
            {
                Telemetry.SimulatedLatencyMs = 180f;
                Telemetry.SimulatedJitterMs = 75f;
                Telemetry.PacketLossProbability = 0.18f;
                Telemetry.PacketDuplicationProbability = 0.05f;
                Telemetry.PacketReorderingProbability = 0.12f;
            }
            if (fault is SimulatedFault.DvlDropout or SimulatedFault.MultipleFaults)
                Dvl.QualityScale = 0f;
            if (fault == SimulatedFault.DvlIntermittent)
                Dvl.IntermittentDropoutProbability = 0.45f;
            if (fault == SimulatedFault.SonarBlindness)
            {
                Sonar.BlindFraction = 0.5f;
                Sonar.FalseReturnProbability = 0.12f;
                Sonar.ScatteringNoiseMultiplier = 4f;
            }
        }
    }
}
