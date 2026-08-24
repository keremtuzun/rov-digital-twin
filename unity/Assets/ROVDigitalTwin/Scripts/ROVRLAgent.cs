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
        public Hydrodynamics6Dof Hydrodynamics;
        public float EnergyPenalty = 0.00004f;
        public float AttitudePenalty = 0.003f;
        public float AngularRatePenalty = 0.0008f;
        public float ActionSmoothnessPenalty = 0.00015f;
        [Range(0f, 1f)] public float PolicyResidualAuthority = 0.25f;
        private Rigidbody body;
        private float previousError;
        private readonly float[] previousActions = new float[ActionSize];
        private readonly float[] guidanceCommands = new float[ActionSize];

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
            Hydrodynamics ??= GetComponent<Hydrodynamics6Dof>();
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
            float commandAuthority = Hydrodynamics != null
                ? Hydrodynamics.PolicyCommandAuthority01 : 1f;
            ComputeGuidanceCommands(guidanceCommands);
            for (int index = 0; index < count; index++)
            {
                // RL learns bounded residual corrections around a deterministic guidance
                // controller. This keeps baseline navigation available if the policy is
                // uncertain or encounters conditions outside its training distribution.
                float residual = Mathf.Clamp(actions.ContinuousActions[index], -1f, 1f)
                                 * PolicyResidualAuthority;
                float command = Mathf.Clamp(guidanceCommands[index] + residual, -1f, 1f)
                                * commandAuthority;
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
            float tiltDegrees = Hydrodynamics != null ? Hydrodynamics.TiltDegrees
                : Vector3.Angle(transform.up, Vector3.up);
            float normalizedTilt = tiltDegrees / 90f;
            float rollPitchRate = (body.angularVelocity
                - Vector3.Project(body.angularVelocity, transform.up)).magnitude;
            // Potential-based progress dominates the shaping reward. The old positive
            // upright/proximity reward let a motionless but level vehicle outscore a
            // vehicle that spent energy reaching a distant target.
            AddReward(0.5f * progress + 0.002f * alignment);
            AddReward(-EnergyPenalty * energy - ActionSmoothnessPenalty * actionDelta
                - AttitudePenalty * normalizedTilt * normalizedTilt
                - AngularRatePenalty * rollPitchRate * rollPitchRate - 0.00025f);
            Academy.Instance.StatsRecorder.Add("Safety/TiltDegrees", tiltDegrees);
            Academy.Instance.StatsRecorder.Add("Safety/RollPitchRate", rollPitchRate);
            Academy.Instance.StatsRecorder.Add("Control/ActionDeltaSquared", actionDelta);
            Academy.Instance.StatsRecorder.Add("Control/PolicyCommandAuthority", commandAuthority);
            Academy.Instance.StatsRecorder.Add("Task/TrackingErrorMeters", error);

            if (error <= duty.SuccessRadiusMeters && duty.Duty != DutyType.PipelineTracking)
            {
                AddReward(8f);
                Academy.Instance.StatsRecorder.Add("Task/Success", 1f);
                Vehicle.StopThrusters();
                EndEpisode();
            }
            else if (tiltDegrees > 72f ||
                     error > (duty.Duty == DutyType.PipelineTracking ? duty.MaxDeviationMeters * 4f : 25f) ||
                     !Vehicle.IsInsideSafeVolume ||
                     DutyManager.TimedOut || Vehicle.BatteryLevel01 <= 0.02f)
            {
                bool flipped = tiltDegrees > 72f;
                AddReward(flipped ? -8f : -2f);
                Academy.Instance.StatsRecorder.Add("Safety/FlipEvent", flipped ? 1f : 0f,
                    StatAggregationMethod.Sum);
                Academy.Instance.StatsRecorder.Add("Task/Success", 0f);
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

        private void ComputeGuidanceCommands(float[] commands)
        {
            System.Array.Clear(commands, 0, commands.Length);
            Vector3 targetLocal = transform.InverseTransformDirection(
                DutyManager.TargetPosition - transform.position);
            Vector3 velocityLocal = transform.InverseTransformDirection(body.linearVelocity);
            float desiredSpeed = Mathf.Max(0.1f, DutyManager.CurrentDuty.DesiredSpeedMetersPerSecond);
            Vector2 horizontalOffset = new Vector2(targetLocal.x, targetLocal.z);
            Vector2 desiredHorizontalVelocity = Vector2.ClampMagnitude(
                horizontalOffset * 0.18f, desiredSpeed);
            float sway = Mathf.Clamp((desiredHorizontalVelocity.x - velocityLocal.x) * 0.55f, -0.55f, 0.55f);
            float surge = Mathf.Clamp((desiredHorizontalVelocity.y - velocityLocal.z) * 0.55f, -0.55f, 0.55f);
            float yaw = Mathf.Clamp(Mathf.Atan2(targetLocal.x, targetLocal.z) / Mathf.PI * 0.18f,
                -0.18f, 0.18f);

            // Symmetric X-frame mixer: front-left, front-right, rear-left, rear-right.
            commands[0] = Mathf.Clamp(surge + sway + yaw, -0.75f, 0.75f);
            commands[1] = Mathf.Clamp(surge - sway - yaw, -0.75f, 0.75f);
            commands[2] = Mathf.Clamp(surge - sway + yaw, -0.75f, 0.75f);
            commands[3] = Mathf.Clamp(surge + sway - yaw, -0.75f, 0.75f);

            float heave = Mathf.Clamp(targetLocal.y * 0.18f - velocityLocal.y * 0.45f, -0.6f, 0.6f);
            for (int index = 4; index < commands.Length; index++)
                commands[index] = heave;
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
