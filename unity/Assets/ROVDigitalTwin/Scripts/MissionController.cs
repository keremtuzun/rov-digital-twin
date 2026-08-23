using UnityEngine;

namespace ROVDigitalTwin
{
    public sealed class MissionController : MonoBehaviour
    {
        public ROVVehicle Vehicle;
        public DutyManager Duties;
        public OceanSenseApiClient Api;

        private void Update()
        {
            if (Input.GetKeyDown(KeyCode.Alpha1)) Duties.CurrentDuty.Duty = DutyType.StationKeeping;
            if (Input.GetKeyDown(KeyCode.Alpha2)) Duties.CurrentDuty.Duty = DutyType.PipelineTracking;
            if (Input.GetKeyDown(KeyCode.Alpha3)) Duties.CurrentDuty.Duty = DutyType.TargetWaypoint;
            if (Input.GetKeyDown(KeyCode.C)) Api.AnalyzeCurrentView();
            if (Input.GetKeyDown(KeyCode.R))
            {
                Vehicle.ResetToSpawn();
                Duties.BeginEpisode();
            }
            if (Input.GetKeyDown(KeyCode.Escape)) Vehicle.StopThrusters();
        }
    }
}
