using UnityEngine;
using System.Collections.Generic;

namespace ROVDigitalTwin
{
    [RequireComponent(typeof(Rigidbody))]
    public sealed class DvlSensor : MonoBehaviour
    {
        public LayerMask SeafloorMask = ~0;
        [Min(0.1f)] public float MaxAltitudeMeters = 30f;
        [Min(0f)] public float VelocityNoise = 0.01f;
        public WaterCurrentField CurrentField;
        public UnderwaterEnvironment Environment;
        [Range(0f, 1f)] public float QualityScale = 1f;
        [Min(0.01f)] public float SamplePeriodSeconds = 0.05f;
        public Vector3 VelocityBias;
        [Range(0f, 1f)] public float DropoutProbability;
        [Range(0f, 1f)] public float IntermittentDropoutProbability;
        [Min(0f)] public float DelaySeconds;

        private Rigidbody body;
        private float nextSampleTime;
        private readonly Queue<DvlFrame> delayedFrames = new Queue<DvlFrame>();
        private struct DvlFrame { public float Time; public Vector3 Velocity; public float Altitude; public float Quality; }

        public Vector3 RelativeVelocityLocal { get; private set; }
        public float AltitudeMeters { get; private set; }
        public float Quality { get; private set; }
        public bool BottomLock => Quality > 0.5f;

        private void Awake()
        {
            body = GetComponent<Rigidbody>();
            Environment ??= FindAnyObjectByType<UnderwaterEnvironment>();
        }

        private void FixedUpdate()
        {
            if (Time.time < nextSampleTime)
                return;
            nextSampleTime = Time.time + SamplePeriodSeconds;
            Vector3 waterVelocity = CurrentField != null ? CurrentField.Sample(transform.position, Time.time) : Vector3.zero;
            Vector3 measuredVelocity = transform.InverseTransformDirection(body.linearVelocity - waterVelocity)
                                       + VelocityBias + SensorNoise.GaussianVector(VelocityNoise);
            float measuredAltitude;
            float measuredQuality;
            if (Physics.Raycast(transform.position, Vector3.down, out RaycastHit hit, MaxAltitudeMeters, SeafloorMask, QueryTriggerInteraction.Ignore))
            {
                measuredAltitude = hit.distance;
                float environmentalQuality = Environment != null ? Environment.AcousticQuality01 : 1f;
                measuredQuality = Mathf.Clamp01(1f - hit.distance / MaxAltitudeMeters * 0.35f)
                          * QualityScale * environmentalQuality;
            }
            else
            {
                measuredAltitude = MaxAltitudeMeters;
                measuredQuality = 0f;
            }
            if (Random.value < DropoutProbability || Random.value < IntermittentDropoutProbability)
                measuredQuality = 0f;
            delayedFrames.Enqueue(new DvlFrame
            {
                Time = Time.time, Velocity = measuredVelocity,
                Altitude = measuredAltitude, Quality = measuredQuality
            });
            while (delayedFrames.Count > 0 && delayedFrames.Peek().Time <= Time.time - DelaySeconds)
            {
                DvlFrame frame = delayedFrames.Dequeue();
                RelativeVelocityLocal = frame.Velocity;
                AltitudeMeters = frame.Altitude;
                Quality = frame.Quality;
            }
        }
    }
}
