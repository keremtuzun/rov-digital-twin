using UnityEngine;

namespace ROVDigitalTwin
{
    public enum DutyType { StationKeeping, PipelineTracking, TargetWaypoint }

    [System.Serializable]
    public class DutyDefinition
    {
        public DutyType Duty = DutyType.StationKeeping;
        public Transform Target;
        public Transform PipelineStart;
        public Transform PipelineEnd;
        [Min(0.1f)] public float MaxDeviationMeters = 1.5f;
        public float TargetDepthMeters = 10f;
        [Min(1f)] public float TimeoutSeconds = 120f;
        [Min(0.05f)] public float SuccessRadiusMeters = 0.6f;
        [Min(0f)] public float DesiredSpeedMetersPerSecond = 0.6f;
    }
}
