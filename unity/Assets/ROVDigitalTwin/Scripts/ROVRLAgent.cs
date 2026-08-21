using UnityEngine;
using Unity.MLAgents;
using Unity.MLAgents.Actuators;
using Unity.MLAgents.Sensors;

namespace ROVDigitalTwin
{
    [RequireComponent(typeof(Rigidbody))]
    public class ROVRLAgent : Agent
    {
        public DutyDefinition CurrentDuty;
        public Transform[] Thrusters;
        public float MaxThrusterForce = 50f;
        public float EnergyPenalty = 0.0005f;
        private Rigidbody body;
        private Vector3 initialPosition;

        public override void Initialize()
        {
            body = GetComponent<Rigidbody>();
            initialPosition = transform.position;
        }

        public override void OnEpisodeBegin()
        {
            body.velocity = Vector3.zero;
            body.angularVelocity = Vector3.zero;
            transform.position = initialPosition + Random.insideUnitSphere * 0.5f;
            transform.rotation = Quaternion.Euler(0f, Random.Range(-10f, 10f), 0f);
        }

        public override void CollectObservations(VectorSensor sensor)
        {
            Vector3 targetOffset = CurrentDuty.Target.position - transform.position;
            sensor.AddObservation(transform.InverseTransformDirection(targetOffset));
            sensor.AddObservation(transform.InverseTransformDirection(body.velocity));
            sensor.AddObservation(transform.InverseTransformDirection(body.angularVelocity));
            sensor.AddObservation(transform.rotation);
            sensor.AddObservation(CurrentDuty.TargetDepthMeters + transform.position.y);
        }

        public override void OnActionReceived(ActionBuffers actions)
        {
            float energy = 0f;
            for (int i = 0; i < Thrusters.Length; i++)
            {
                float command = Mathf.Clamp(actions.ContinuousActions[i], -1f, 1f);
                body.AddForceAtPosition(Thrusters[i].forward * command * MaxThrusterForce, Thrusters[i].position);
                energy += command * command;
            }
            float distance = Vector3.Distance(transform.position, CurrentDuty.Target.position);
            AddReward(0.002f * Mathf.Exp(-distance) - EnergyPenalty * energy);
            if (distance > CurrentDuty.MaxDeviationMeters * 4f)
            {
                AddReward(-1f);
                EndEpisode();
            }
        }
    }
}
