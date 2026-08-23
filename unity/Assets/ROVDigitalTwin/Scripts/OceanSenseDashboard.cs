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
        public UnderwaterEnvironment Environment;

        private GUIStyle style;

        private void OnGUI()
        {
            Environment ??= FindAnyObjectByType<UnderwaterEnvironment>();
            style ??= new GUIStyle(GUI.skin.box) { alignment = TextAnchor.UpperLeft, fontSize = 15, padding = new RectOffset(14, 14, 12, 12) };
            WaterCurrentField current = Environment != null ? Environment.CurrentField : null;
            string sea = Environment != null
                ? $"Sea: Hs {(current != null ? current.SignificantWaveHeightMeters : 0f):F2} m / "
                  + $"turbidity {Environment.TurbidityNtu:F1} NTU / visibility {Environment.OpticalVisibilityMeters:F1} m\n"
                : string.Empty;
            string text = $"OCEANSENSE DIGITAL TWIN\n" +
                          $"Duty: {Duties.CurrentDuty.Duty}\nDepth: {Depth.DepthMeters:F2} m\n" +
                          $"Velocity: {Vehicle.Body.linearVelocity.magnitude:F2} m/s\nBattery: {Vehicle.BatteryLevel01:P0}\n" +
                          $"DVL: {(Dvl.BottomLock ? "bottom lock" : "no lock")} ({Dvl.Quality:P0})\n" +
                          sea +
                          $"API: {Api.LastStatus}\n\n1/2/3 duty  C analyze  G synthetic  R reset  Esc stop";
            GUI.Box(new Rect(18, 18, 440, 246), text, style);
        }
    }
}
