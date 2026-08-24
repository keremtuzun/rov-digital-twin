using UnityEngine;
using System.Collections.Generic;

namespace ROVDigitalTwin
{
    [RequireComponent(typeof(Rigidbody))]
    public sealed class ImuSensor : MonoBehaviour
    {
        [Min(0f)] public float AccelerationNoise = 0.015f;
        [Min(0f)] public float GyroNoise = 0.002f;
        public Vector3 ConstantAccelerationBias;
        public Vector3 ConstantGyroBias;
        public Vector3 AccelerationBiasDriftPerSecond;
        public Vector3 GyroBiasDriftPerSecond;
        [Min(0f)] public float RandomWalkStandardDeviation = 0f;
        [Range(0f, 1f)] public float SpikeProbabilityPerSample;
        [Min(0f)] public float SpikeMagnitude = 2f;
        [Min(0f)] public float AccelerationClipMagnitude = 100f;
        [Min(0f)] public float GyroClipMagnitude = 20f;
        [Range(0f, 1f)] public float DropoutProbability;
        [Min(0f)] public float DelaySeconds;

        private Rigidbody body;
        private Vector3 previousVelocity;
        private Vector3 accelerationDrift;
        private Vector3 gyroDrift;
        private readonly Queue<ImuFrame> delayedFrames = new Queue<ImuFrame>();

        private struct ImuFrame
        {
            public float Time;
            public Vector3 Acceleration;
            public Vector3 Gyro;
        }

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
            accelerationDrift += AccelerationBiasDriftPerSecond * Time.fixedDeltaTime
                                 + SensorNoise.GaussianVector(RandomWalkStandardDeviation * Mathf.Sqrt(Time.fixedDeltaTime));
            gyroDrift += GyroBiasDriftPerSecond * Time.fixedDeltaTime
                         + SensorNoise.GaussianVector(RandomWalkStandardDeviation * 0.1f * Mathf.Sqrt(Time.fixedDeltaTime));
            if (Random.value >= DropoutProbability)
            {
                Vector3 spike = Random.value < SpikeProbabilityPerSample
                    ? Random.onUnitSphere * SpikeMagnitude : Vector3.zero;
                Vector3 measuredAcceleration = transform.InverseTransformDirection(acceleration - Physics.gravity)
                    + ConstantAccelerationBias + accelerationDrift
                    + SensorNoise.GaussianVector(AccelerationNoise) + spike;
                Vector3 measuredGyro = transform.InverseTransformDirection(body.angularVelocity)
                    + ConstantGyroBias + gyroDrift + SensorNoise.GaussianVector(GyroNoise);
                delayedFrames.Enqueue(new ImuFrame
                {
                    Time = Time.time,
                    Acceleration = Vector3.ClampMagnitude(measuredAcceleration, AccelerationClipMagnitude),
                    Gyro = Vector3.ClampMagnitude(measuredGyro, GyroClipMagnitude)
                });
            }
            while (delayedFrames.Count > 0 && delayedFrames.Peek().Time <= Time.time - DelaySeconds)
            {
                ImuFrame frame = delayedFrames.Dequeue();
                LinearAccelerationLocal = frame.Acceleration;
                AngularVelocityLocal = frame.Gyro;
            }
            previousVelocity = body.linearVelocity;
        }
    }
}
