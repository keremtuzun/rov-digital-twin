using UnityEngine;

namespace ROVDigitalTwin
{
    public sealed class OceanSenseDashboard : MonoBehaviour
    {
        public ROVVehicle Vehicle;
        public DutyManager Duties;
        public DepthSensor Depth;
        public DvlSensor Dvl;
        public OceanSenseApiClient Api;

        private GUIStyle style;

        private void OnGUI()
        {
            style ??= new GUIStyle(GUI.skin.box) { alignment = TextAnchor.UpperLeft, fontSize = 15, padding = new RectOffset(14, 14, 12, 12) };
            string text = $"OCEANSENSE DIGITAL TWIN\n" +
                          $"Duty: {Duties.CurrentDuty.Duty}\nDepth: {Depth.DepthMeters:F2} m\n" +
                          $"Velocity: {Vehicle.Body.linearVelocity.magnitude:F2} m/s\nBattery: {Vehicle.BatteryLevel01:P0}\n" +
                          $"DVL: {(Dvl.BottomLock ? "bottom lock" : "no lock")} ({Dvl.Quality:P0})\n" +
                          $"API: {Api.LastStatus}\n\n1/2/3 duty  C analyze  G synthetic  R reset  Esc stop";
            GUI.Box(new Rect(18, 18, 360, 220), text, style);
        }
    }
}
