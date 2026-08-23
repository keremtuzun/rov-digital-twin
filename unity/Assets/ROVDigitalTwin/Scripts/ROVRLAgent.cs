using UnityEngine;
using Unity.MLAgents;
using Unity.MLAgents.Actuators;
using Unity.MLAgents.Sensors;

namespace ROVDigitalTwin
{
    [RequireComponent(typeof(Rigidbody))]
    public class ROVRLAgent : Agent
    {
        public const int ObservationSize = 39;
        public const int ActionSize = 8;
        public ROVVehicle Vehicle;
        public DutyManager DutyManager;
        public ImuSensor Imu;
        public DepthSensor Depth;
        public DvlSensor Dvl;
        public ForwardSonarSensor Sonar;
        public DomainRandomization DomainRandomization;
        public float EnergyPenalty = 0.0005f;
        public float AttitudePenalty = 0.0002f;
        public float ActionSmoothnessPenalty = 0.00015f;
        private Rigidbody body;
        private float previousError;
        private readonly float[] previousActions = new float[ActionSize];

        public override void Initialize()
        {
            body = GetComponent<Rigidbody>();
            Vehicle ??= GetComponent<ROVVehicle>();
            DutyManager ??= FindAnyObjectByType<DutyManager>();
            Imu ??= GetComponent<ImuSensor>();
            Depth ??= GetComponent<DepthSensor>();
            Dvl ??= GetComponent<DvlSensor>();
            Sonar ??= GetComponent<ForwardSonarSensor>();
            DomainRandomization ??= GetComponent<DomainRandomization>();
        }

        public override void OnEpisodeBegin()
        {
            Vehicle.ResetVehicle();
            DomainRandomization?.ApplyEpisodeRandomization();
            DutyManager.BeginEpisode();
            previousError = CurrentTrackingError();
            System.Array.Clear(previousActions, 0, previousActions.Length);
        }

        public override void CollectObservations(VectorSensor sensor)
        {
            DutyDefinition duty = DutyManager.CurrentDuty;
            Vector3 targetOffset = DutyManager.TargetPosition - transform.position;
            sensor.AddObservation(transform.InverseTransformDirection(targetOffset));
            sensor.AddObservation(transform.InverseTransformDirection(body.linearVelocity));
            sensor.AddObservation(transform.InverseTransformDirection(body.angularVelocity));
            sensor.AddObservation(transform.rotation);
            sensor.AddObservation((duty.TargetDepthMeters - Depth.DepthMeters) / 20f);
            sensor.AddObservation(Vehicle.BatteryLevel01);
            sensor.AddObservation(duty.Duty == DutyType.StationKeeping ? 1f : 0f);
            sensor.AddObservation(duty.Duty == DutyType.PipelineTracking ? 1f : 0f);
            sensor.AddObservation(duty.Duty == DutyType.TargetWaypoint ? 1f : 0f);
            sensor.AddObservation(Dvl.RelativeVelocityLocal);
            sensor.AddObservation(Dvl.AltitudeMeters / Dvl.MaxAltitudeMeters);
            sensor.AddObservation(Dvl.Quality);
            for (int index = 0; index < 16; index++)
                sensor.AddObservation(Sonar.NormalizedDistance(index));
        }

        public override void OnActionReceived(ActionBuffers actions)
        {
            int count = Mathf.Min(actions.ContinuousActions.Length, Vehicle.Thrusters.Length);
            float energy = 0f;
            float actionDelta = 0f;
            for (int index = 0; index < count; index++)
            {
                float command = Mathf.Clamp(actions.ContinuousActions[index], -1f, 1f);
                Vehicle.SetThrusterCommand(index, command);
                energy += command * command;
                float delta = command - previousActions[index];
                actionDelta += delta * delta;
                previousActions[index] = command;
            }

            DutyDefinition duty = DutyManager.CurrentDuty;
            float error = CurrentTrackingError();
            float progress = Mathf.Clamp(previousError - error, -1f, 1f);
            previousError = error;
            float alignment = duty.Duty == DutyType.PipelineTracking
                ? Mathf.Max(0f, Vector3.Dot(transform.forward, DutyManager.PipelineDirection))
                : 0f;
            AddReward(0.02f * progress + 0.0025f * Mathf.Exp(-0.35f * error) + 0.0005f * alignment);
            AddReward(-EnergyPenalty * energy - ActionSmoothnessPenalty * actionDelta
                - AttitudePenalty * Vector3.Angle(transform.up, Vector3.up) / 180f - 0.0001f);

            if (error <= duty.SuccessRadiusMeters && duty.Duty != DutyType.PipelineTracking)
            {
                AddReward(1f);
                Vehicle.StopThrusters();
                EndEpisode();
            }
            else if (error > (duty.Duty == DutyType.PipelineTracking ? duty.MaxDeviationMeters * 4f : 25f) ||
                     !Vehicle.IsInsideSafeVolume ||
                     DutyManager.TimedOut || Vehicle.BatteryLevel01 <= 0.02f)
            {
                AddReward(-1f);
                Vehicle.StopThrusters();
                EndEpisode();
            }
        }

        private float CurrentTrackingError()
        {
            DutyDefinition duty = DutyManager.CurrentDuty;
            return duty.Duty == DutyType.PipelineTracking
                ? DutyManager.PipelineCrossTrackError(transform.position)
                : Vector3.Distance(transform.position, DutyManager.TargetPosition);
        }

        public override void Heuristic(in ActionBuffers actionsOut)
        {
            var commands = actionsOut.ContinuousActions;
            Vector3 localTarget = transform.InverseTransformDirection(DutyManager.TargetPosition - transform.position).normalized;
            for (int index = 0; index < commands.Length; index++)
            {
                Thruster thruster = index < Vehicle.Thrusters.Length ? Vehicle.Thrusters[index] : null;
                commands[index] = thruster == null ? 0f : Mathf.Clamp(Vector3.Dot(thruster.transform.forward, transform.TransformDirection(localTarget)), -1f, 1f);
            }
        }

        private void OnCollisionEnter(Collision collision)
        {
            AddReward(-Mathf.Clamp01(collision.relativeVelocity.magnitude / 5f));
        }
    }
}
