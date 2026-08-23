using UnityEngine;

namespace ROVDigitalTwin
{
    [RequireComponent(typeof(Rigidbody))]
    public sealed class ImuSensor : MonoBehaviour
    {
        [Min(0f)] public float AccelerationNoise = 0.015f;
        [Min(0f)] public float GyroNoise = 0.002f;

        private Rigidbody body;
        private Vector3 previousVelocity;

        public Vector3 LinearAccelerationLocal { get; private set; }
        public Vector3 AngularVelocityLocal { get; private set; }
        public Quaternion Orientation => transform.rotation;

        private void Awake()
        {
            body = GetComponent<Rigidbody>();
            previousVelocity = body.linearVelocity;
        }

        private void FixedUpdate()
        {
            Vector3 acceleration = (body.linearVelocity - previousVelocity) / Mathf.Max(Time.fixedDeltaTime, 0.0001f);
            LinearAccelerationLocal = transform.InverseTransformDirection(acceleration - Physics.gravity) + SensorNoise.GaussianVector(AccelerationNoise);
            AngularVelocityLocal = transform.InverseTransformDirection(body.angularVelocity) + SensorNoise.GaussianVector(GyroNoise);
            previousVelocity = body.linearVelocity;
        }
    }
}
