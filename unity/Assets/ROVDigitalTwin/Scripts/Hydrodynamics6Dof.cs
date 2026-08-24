using UnityEngine;

namespace ROVDigitalTwin
{
    [RequireComponent(typeof(Rigidbody))]
    public class Hydrodynamics6Dof : MonoBehaviour
    {
        public float WaterSurfaceY = 0f;
        public Vector3 CenterOfBuoyancyOffset = new Vector3(0f, 0.20f, 0f);
        public float FluidDensity = 1025f;
        public float DisplacedVolume = 0.02f;
        [Min(0.01f)] public float SubmersionDepth = 0.8f;
        public Vector3 ViscousLinearDrag = new Vector3(2f, 3f, 4f);
        public Vector3 LinearDrag = new Vector3(18f, 22f, 28f);
        public Vector3 AngularDrag = new Vector3(4f, 4f, 6f);
        public Vector3 AddedMass = new Vector3(5f, 8f, 10f);
        [Min(0f)] public float RestoringTorque = 25f;
        public bool EnableAttitudeSafetyEnvelope = true;
        [Range(0f, 60f)] public float SoftTiltLimitDegrees = 20f;
        [Range(30f, 85f)] public float HardTiltLimitDegrees = 50f;
        [Min(0f)] public float SafetyRecoveryTorque = 180f;
        [Min(0f)] public float SafetyAngularDamping = 28f;
        [Min(0.1f)] public float ExternalDragMultiplier = 1f;
        public WaterCurrentField CurrentField;
        private Rigidbody body;
        private Vector3 previousLocalVelocity;

        public float SubmergedFraction { get; private set; }
        public Vector3 RelativeWaterVelocity { get; private set; }
        public float TiltDegrees => Vector3.Angle(transform.up, Vector3.up);
        public bool IsOutsideAttitudeEnvelope => TiltDegrees > HardTiltLimitDegrees;
        public float PolicyCommandAuthority01 => Mathf.Lerp(1f, 0.18f,
            Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(SoftTiltLimitDegrees,
                HardTiltLimitDegrees, TiltDegrees)));

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
            Vector3 viscousDrag = -Vector3.Scale(ViscousLinearDrag, localVelocity);
            Vector3 quadraticDrag = QuadraticDrag(localVelocity, LinearDrag);
            body.AddForce(transform.TransformDirection(viscousDrag + quadraticDrag)
                * SubmergedFraction * ExternalDragMultiplier);

            Vector3 localAcceleration = (localVelocity - previousLocalVelocity) / Mathf.Max(Time.fixedDeltaTime, 0.0001f);
            body.AddForce(transform.TransformDirection(-Vector3.Scale(AddedMass, localAcceleration)) * SubmergedFraction);
            previousLocalVelocity = localVelocity;

            Vector3 localAngular = transform.InverseTransformDirection(body.angularVelocity);
            body.AddTorque(transform.TransformDirection(QuadraticDrag(localAngular, AngularDrag)) * SubmergedFraction);

            Vector3 uprightError = Vector3.Cross(transform.up, Vector3.up);
            body.AddTorque(uprightError * RestoringTorque * SubmergedFraction);
            ApplyAttitudeSafetyEnvelope(uprightError);
        }

        private void ApplyAttitudeSafetyEnvelope(Vector3 uprightError)
        {
            if (!EnableAttitudeSafetyEnvelope || TiltDegrees <= SoftTiltLimitDegrees)
                return;
            float authority = Mathf.SmoothStep(0f, 1f,
                Mathf.InverseLerp(SoftTiltLimitDegrees, HardTiltLimitDegrees, TiltDegrees));
            Vector3 rollPitchRate = body.angularVelocity
                - Vector3.Project(body.angularVelocity, transform.up);
            Vector3 recovery = uprightError * SafetyRecoveryTorque
                               - rollPitchRate * SafetyAngularDamping;
            body.AddTorque(recovery * authority * SubmergedFraction, ForceMode.Force);
        }

        public static Vector3 QuadraticDrag(Vector3 value, Vector3 coefficients) =>
            -Vector3.Scale(coefficients, new Vector3(
                value.x * Mathf.Abs(value.x),
                value.y * Mathf.Abs(value.y),
                value.z * Mathf.Abs(value.z)));
    }
}
