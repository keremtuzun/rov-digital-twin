using UnityEngine;

namespace ROVDigitalTwin
{
    [RequireComponent(typeof(Rigidbody))]
    public class Hydrodynamics6Dof : MonoBehaviour
    {
        public float WaterSurfaceY = 0f;
        public Vector3 CenterOfBuoyancyOffset = new Vector3(0f, 0.12f, 0f);
        public float FluidDensity = 1025f;
        public float DisplacedVolume = 0.02f;
        [Min(0.01f)] public float SubmersionDepth = 0.8f;
        public Vector3 LinearDrag = new Vector3(18f, 22f, 28f);
        public Vector3 AngularDrag = new Vector3(4f, 4f, 6f);
        public Vector3 AddedMass = new Vector3(5f, 8f, 10f);
        [Min(0f)] public float RestoringTorque = 15f;
        public WaterCurrentField CurrentField;
        private Rigidbody body;
        private Vector3 previousLocalVelocity;

        public float SubmergedFraction { get; private set; }
        public Vector3 RelativeWaterVelocity { get; private set; }

        void Awake()
        {
            body = GetComponent<Rigidbody>();
            previousLocalVelocity = transform.InverseTransformDirection(body.linearVelocity);
        }

        void FixedUpdate()
        {
            SubmergedFraction = Mathf.Clamp01((WaterSurfaceY - transform.position.y) / SubmersionDepth);
            if (SubmergedFraction <= 0f)
                return;

            Vector3 buoyancy = Vector3.up * FluidDensity * DisplacedVolume * Physics.gravity.magnitude * SubmergedFraction;
            body.AddForceAtPosition(buoyancy, transform.TransformPoint(CenterOfBuoyancyOffset));

            Vector3 current = CurrentField != null ? CurrentField.Sample(transform.position, Time.time) : Vector3.zero;
            RelativeWaterVelocity = body.linearVelocity - current;
            Vector3 localVelocity = transform.InverseTransformDirection(RelativeWaterVelocity);
            body.AddForce(transform.TransformDirection(QuadraticDrag(localVelocity, LinearDrag)) * SubmergedFraction);

            Vector3 localAcceleration = (localVelocity - previousLocalVelocity) / Mathf.Max(Time.fixedDeltaTime, 0.0001f);
            body.AddForce(transform.TransformDirection(-Vector3.Scale(AddedMass, localAcceleration)) * SubmergedFraction);
            previousLocalVelocity = localVelocity;

            Vector3 localAngular = transform.InverseTransformDirection(body.angularVelocity);
            body.AddTorque(transform.TransformDirection(QuadraticDrag(localAngular, AngularDrag)) * SubmergedFraction);

            Vector3 uprightError = Vector3.Cross(transform.up, Vector3.up);
            body.AddTorque(uprightError * RestoringTorque * SubmergedFraction);
        }

        public static Vector3 QuadraticDrag(Vector3 value, Vector3 coefficients) =>
            -Vector3.Scale(coefficients, new Vector3(
                value.x * Mathf.Abs(value.x),
                value.y * Mathf.Abs(value.y),
                value.z * Mathf.Abs(value.z)));
    }
}
