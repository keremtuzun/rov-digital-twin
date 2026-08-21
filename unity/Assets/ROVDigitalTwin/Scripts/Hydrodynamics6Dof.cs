using UnityEngine;

namespace ROVDigitalTwin
{
    [RequireComponent(typeof(Rigidbody))]
    public class Hydrodynamics6Dof : MonoBehaviour
    {
        public Vector3 CenterOfBuoyancyOffset = new Vector3(0f, 0.12f, 0f);
        public float FluidDensity = 1025f;
        public float DisplacedVolume = 0.02f;
        public Vector3 LinearDrag = new Vector3(18f, 22f, 28f);
        public Vector3 AngularDrag = new Vector3(4f, 4f, 6f);
        private Rigidbody body;

        void Awake() => body = GetComponent<Rigidbody>();

        void FixedUpdate()
        {
            Vector3 buoyancy = Vector3.up * FluidDensity * DisplacedVolume * Physics.gravity.magnitude;
            body.AddForceAtPosition(buoyancy, transform.TransformPoint(CenterOfBuoyancyOffset));

            Vector3 localVelocity = transform.InverseTransformDirection(body.velocity);
            Vector3 localDrag = -Vector3.Scale(LinearDrag, new Vector3(
                localVelocity.x * Mathf.Abs(localVelocity.x),
                localVelocity.y * Mathf.Abs(localVelocity.y),
                localVelocity.z * Mathf.Abs(localVelocity.z)));
            body.AddForce(transform.TransformDirection(localDrag));

            Vector3 localAngular = transform.InverseTransformDirection(body.angularVelocity);
            Vector3 angularForce = -Vector3.Scale(AngularDrag, new Vector3(
                localAngular.x * Mathf.Abs(localAngular.x),
                localAngular.y * Mathf.Abs(localAngular.y),
                localAngular.z * Mathf.Abs(localAngular.z)));
            body.AddTorque(transform.TransformDirection(angularForce));
        }
    }
}
