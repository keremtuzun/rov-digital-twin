using UnityEngine;

namespace ROVDigitalTwin
{
    public sealed class DutyManager : MonoBehaviour
    {
        public DutyDefinition CurrentDuty = new DutyDefinition();
        public Vector3 RandomTargetMinimum = new Vector3(-12f, -10f, -12f);
        public Vector3 RandomTargetMaximum = new Vector3(12f, -3f, 12f);
        public bool RandomizeTargetOnEpisode = true;

        public float EpisodeElapsedSeconds { get; private set; }
        public Vector3 TargetPosition => CurrentDuty.Target != null ? CurrentDuty.Target.position : transform.position;
        public bool TimedOut => EpisodeElapsedSeconds >= CurrentDuty.TimeoutSeconds;

        private void FixedUpdate() => EpisodeElapsedSeconds += Time.fixedDeltaTime;

        public void BeginEpisode()
        {
            EpisodeElapsedSeconds = 0f;
            if (!RandomizeTargetOnEpisode || CurrentDuty.Target == null)
                return;
            CurrentDuty.Target.position = new Vector3(
                Random.Range(RandomTargetMinimum.x, RandomTargetMaximum.x),
                Random.Range(RandomTargetMinimum.y, RandomTargetMaximum.y),
                Random.Range(RandomTargetMinimum.z, RandomTargetMaximum.z));
            CurrentDuty.TargetDepthMeters = -CurrentDuty.Target.position.y;
        }

        public float PipelineCrossTrackError(Vector3 position)
        {
            if (CurrentDuty.PipelineStart == null || CurrentDuty.PipelineEnd == null)
                return Vector3.Distance(position, TargetPosition);
            Vector3 start = CurrentDuty.PipelineStart.position;
            Vector3 segment = CurrentDuty.PipelineEnd.position - start;
            float t = Mathf.Clamp01(Vector3.Dot(position - start, segment) / Mathf.Max(segment.sqrMagnitude, 0.0001f));
            return Vector3.Distance(position, start + segment * t);
        }

        public Vector3 PipelineDirection =>
            CurrentDuty.PipelineStart != null && CurrentDuty.PipelineEnd != null
                ? (CurrentDuty.PipelineEnd.position - CurrentDuty.PipelineStart.position).normalized
                : transform.forward;
    }
}
