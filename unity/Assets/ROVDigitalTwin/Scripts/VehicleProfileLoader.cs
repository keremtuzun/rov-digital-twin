using System;
using UnityEngine;

namespace ROVDigitalTwin
{
    [Serializable]
    public sealed class VehicleProfileDocument
    {
        public string profile_schema_version;
        public string vehicle_id;
        public VehicleProfileParameters parameters;
        public VehicleProfileValidity validity;
    }

    [Serializable]
    public sealed class VehicleProfileParameters
    {
        public float thruster_gain_mps2_per_command;
        public float linear_drag_per_second;
        public float quadratic_drag_per_meter;
        public float battery_internal_resistance_ohm;
        public float added_mass_kg;
        public float buoyancy_newtons;
        public float thruster_lag_seconds;
        public float[] center_of_buoyancy_m;
    }

    [Serializable]
    public sealed class VehicleProfileValidity
    {
        public bool thruster_gain_mps2_per_command;
        public bool linear_drag_per_second;
        public bool quadratic_drag_per_meter;
        public bool battery_internal_resistance_ohm;
        public bool added_mass_kg;
        public bool buoyancy_newtons;
        public bool thruster_lag_seconds;
        public bool center_of_buoyancy_m;
    }

    public sealed class VehicleProfileLoader : MonoBehaviour
    {
        public TextAsset ProfileJson;
        public ROVVehicle Vehicle;
        public Hydrodynamics6Dof Hydrodynamics;
        public SimulatedPowerSensor Power;
        public string LoadedVehicleProfileVersion { get; private set; } = "default";

        private void Awake()
        {
            Vehicle ??= GetComponent<ROVVehicle>();
            Hydrodynamics ??= GetComponent<Hydrodynamics6Dof>();
            Power ??= GetComponent<SimulatedPowerSensor>();
            if (ProfileJson != null)
                ApplyProfile(ProfileJson.text);
        }

        public void ApplyProfile(string json)
        {
            VehicleProfileDocument profile = JsonUtility.FromJson<VehicleProfileDocument>(json);
            if (profile == null || profile.parameters == null || profile.validity == null)
                throw new ArgumentException("Vehicle profile is missing parameters or validity flags.");
            VehicleProfileParameters values = profile.parameters;
            VehicleProfileValidity valid = profile.validity;
            float vehicleMass = Mathf.Max(0.1f, Vehicle.Body.mass);
            if (valid.linear_drag_per_second)
                Hydrodynamics.ViscousLinearDrag = Vector3.one
                    * Mathf.Max(0f, values.linear_drag_per_second * vehicleMass);
            if (valid.quadratic_drag_per_meter)
                Hydrodynamics.LinearDrag = Vector3.one
                    * Mathf.Max(0f, values.quadratic_drag_per_meter * vehicleMass);
            if (valid.added_mass_kg)
                Hydrodynamics.AddedMass = Vector3.one * Mathf.Max(0f, values.added_mass_kg);
            if (valid.buoyancy_newtons)
                Hydrodynamics.DisplacedVolume = Mathf.Max(0f, values.buoyancy_newtons)
                    / (Hydrodynamics.FluidDensity * Physics.gravity.magnitude);
            if (valid.battery_internal_resistance_ohm)
                Power.InternalResistanceOhm = Mathf.Max(0f, values.battery_internal_resistance_ohm);
            if (valid.center_of_buoyancy_m && values.center_of_buoyancy_m != null
                && values.center_of_buoyancy_m.Length == 3)
                Hydrodynamics.CenterOfBuoyancyOffset = new Vector3(values.center_of_buoyancy_m[0],
                    values.center_of_buoyancy_m[1], values.center_of_buoyancy_m[2]);
            foreach (Thruster thruster in Vehicle.Thrusters)
            {
                if (valid.thruster_lag_seconds)
                    thruster.ResponseTimeSeconds = Mathf.Max(0.01f, values.thruster_lag_seconds);
                if (valid.thruster_gain_mps2_per_command)
                    thruster.MaxForceNewtons = Mathf.Max(0.1f,
                        values.thruster_gain_mps2_per_command * vehicleMass
                        / Mathf.Max(1, Vehicle.Thrusters.Length));
            }
            LoadedVehicleProfileVersion = $"{profile.profile_schema_version}:{profile.vehicle_id}";
        }
    }
}
