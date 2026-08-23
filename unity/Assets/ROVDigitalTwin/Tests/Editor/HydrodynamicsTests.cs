using NUnit.Framework;
using UnityEngine;

namespace ROVDigitalTwin.Tests
{
    public sealed class HydrodynamicsTests
    {
        [Test]
        public void QuadraticDragOpposesMotion()
        {
            Vector3 velocity = new Vector3(2f, -3f, 0.5f);
            Vector3 drag = Hydrodynamics6Dof.QuadraticDrag(velocity, new Vector3(1f, 2f, 4f));
            Assert.Less(Vector3.Dot(velocity, drag), 0f);
            Assert.AreEqual(new Vector3(-4f, 18f, -1f), drag);
        }

        [Test]
        public void QuadraticDragIsZeroAtRest()
        {
            Assert.AreEqual(Vector3.zero, Hydrodynamics6Dof.QuadraticDrag(Vector3.zero, Vector3.one));
        }

        [Test]
        public void AgentContractSizesRemainStable()
        {
            Assert.AreEqual(39, ROVRLAgent.ObservationSize);
            Assert.AreEqual(8, ROVRLAgent.ActionSize);
        }

        [Test]
        public void WaveOrbitalVelocityDecaysWithDepth()
        {
            Vector3 nearSurface = WaterCurrentField.WaveComponent(
                new Vector3(0f, -1f, 0f), 0.7f, 0.6f, 6.5f, 25f, 0f, 0f);
            Vector3 deepWater = WaterCurrentField.WaveComponent(
                new Vector3(0f, -25f, 0f), 0.7f, 0.6f, 6.5f, 25f, 0f, 0f);
            Assert.Greater(nearSurface.magnitude, deepWater.magnitude);
            Assert.Greater(deepWater.magnitude, 0f);
        }

        [Test]
        public void ContaminationReducesVisibilityAndAcousticQuality()
        {
            GameObject root = new GameObject("water-quality-test");
            try
            {
                UnderwaterEnvironment ocean = root.AddComponent<UnderwaterEnvironment>();
                ocean.TurbidityNtu = 0.5f;
                ocean.Contamination01 = 0.02f;
                float clearVisibility = ocean.OpticalVisibilityMeters;
                float clearAcoustic = ocean.AcousticQuality01;
                ocean.TurbidityNtu = 6f;
                ocean.Contamination01 = 0.35f;
                ocean.SuspendedSedimentMgPerLiter = 15f;
                Assert.Less(ocean.OpticalVisibilityMeters, clearVisibility);
                Assert.Less(ocean.AcousticQuality01, clearAcoustic);
            }
            finally
            {
                Object.DestroyImmediate(root);
            }
        }

        [Test]
        public void FaultResetRestoresNominalStateDeterministically()
        {
            GameObject root = new GameObject("fault-test");
            try
            {
                root.AddComponent<Rigidbody>();
                ROVVehicle vehicle = root.AddComponent<ROVVehicle>();
                GameObject thrusterObject = new GameObject("thruster");
                thrusterObject.transform.SetParent(root.transform);
                Thruster thruster = thrusterObject.AddComponent<Thruster>();
                vehicle.Thrusters = new[] { thruster };
                var controller = root.AddComponent<FaultInjectionController>();
                controller.Vehicle = vehicle;
                controller.Hydrodynamics = root.AddComponent<Hydrodynamics6Dof>();
                controller.Depth = root.AddComponent<DepthSensor>();
                controller.Dvl = root.AddComponent<DvlSensor>();
                controller.Power = root.AddComponent<SimulatedPowerSensor>();
                controller.Telemetry = root.AddComponent<TelemetryUdpBridge>();

                controller.ApplyFault(SimulatedFault.LowBattery);
                Assert.AreEqual(0.15f, vehicle.BatteryLevel, 0.0001f);
                controller.ApplyFault(SimulatedFault.MultipleFaults);
                controller.ApplyFault(SimulatedFault.None);

                Assert.AreEqual(1f, vehicle.BatteryLevel, 0.0001f);
                Assert.AreEqual(1f, thruster.Efficiency, 0.0001f);
                Assert.AreEqual(0f, controller.Depth.BiasMeters, 0.0001f);
                Assert.AreEqual(1f, controller.Hydrodynamics.ExternalDragMultiplier, 0.0001f);
                Assert.AreEqual(1f, controller.Dvl.QualityScale, 0.0001f);
                Assert.IsTrue(controller.Telemetry.PublishEnabled);
            }
            finally
            {
                Object.DestroyImmediate(root);
            }
        }
    }
}
