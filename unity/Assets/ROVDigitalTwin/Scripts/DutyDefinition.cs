using UnityEngine;

namespace ROVDigitalTwin
{
    public enum DutyType { StationKeeping, PipelineTracking, TargetWaypoint }

    [System.Serializable]
    public class DutyDefinition
    {
        public DutyType Duty = DutyType.StationKeeping;
        public Transform Target;
        [Min(0.1f)] public float MaxDeviationMeters = 1.5f;
        public float TargetDepthMeters = 10f;
        [Min(1f)] public float TimeoutSeconds = 120f;
    }
}
