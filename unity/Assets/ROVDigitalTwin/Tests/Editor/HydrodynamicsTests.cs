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
    }
}
