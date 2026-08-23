using System;
using UnityEngine;

namespace ROVDigitalTwin
{
    [RequireComponent(typeof(Rigidbody))]
    public sealed class ROVVehicle : MonoBehaviour
    {
        public Thruster[] Thrusters = Array.Empty<Thruster>();
        [Range(0f, 1f)] public float BatteryLevel = 1f;
        [Min(0f)] public float BatteryDrainPerNewtonSecond = 0.0000006f;
        public Vector3 SafeMinimum = new Vector3(-35f, -14f, -35f);
        public Vector3 SafeMaximum = new Vector3(35f, -0.5f, 35f);

        private Rigidbody body;
        private Vector3 spawnPosition;
        private Quaternion spawnRotation;

        public Rigidbody Body => body;
        public float BatteryLevel01 => BatteryLevel;
        public float EnergyCommandSquared { get; private set; }
        public bool IsInsideSafeVolume =>
            transform.position.x >= SafeMinimum.x && transform.position.y >= SafeMinimum.y && transform.position.z >= SafeMinimum.z &&
            transform.position.x <= SafeMaximum.x && transform.position.y <= SafeMaximum.y && transform.position.z <= SafeMaximum.z;

        private void Awake()
        {
            body = GetComponent<Rigidbody>();
            spawnPosition = transform.position;
            spawnRotation = transform.rotation;
            if (Thrusters.Length == 0)
                Thrusters = GetComponentsInChildren<Thruster>();
            foreach (Thruster thruster in Thrusters)
                thruster.Initialize(body);
        }

        private void FixedUpdate()
        {
            EnergyCommandSquared = 0f;
            foreach (Thruster thruster in Thrusters)
                EnergyCommandSquared += thruster.Command * thruster.Command;
            BatteryLevel = Mathf.Clamp01(BatteryLevel - EnergyCommandSquared * BatteryDrainPerNewtonSecond * Time.fixedDeltaTime);
        }

        public void SetThrusterCommands(float[] commands)
        {
            for (int index = 0; index < Thrusters.Length; index++)
                Thrusters[index].SetCommand(index < commands.Length ? commands[index] : 0f);
        }

        public void SetThrusterCommand(int index, float command)
        {
            if (index >= 0 && index < Thrusters.Length)
                Thrusters[index].SetCommand(command);
        }

        public void StopThrusters()
        {
            foreach (Thruster thruster in Thrusters)
                thruster.SetCommand(0f);
        }

        public void ResetVehicle(Vector3 position, Quaternion rotation, bool recharge = true)
        {
            transform.SetPositionAndRotation(position, rotation);
            body.linearVelocity = Vector3.zero;
            body.angularVelocity = Vector3.zero;
            StopThrusters();
            if (recharge)
                BatteryLevel = 1f;
        }

        public void ResetToSpawn() => ResetVehicle(spawnPosition, spawnRotation);

        public void ResetVehicle()
        {
            Vector3 jitter = new Vector3(UnityEngine.Random.Range(-0.5f, 0.5f), UnityEngine.Random.Range(-0.25f, 0.25f), UnityEngine.Random.Range(-0.5f, 0.5f));
            ResetVehicle(spawnPosition + jitter, Quaternion.Euler(0f, UnityEngine.Random.Range(-10f, 10f), 0f));
        }
    }
}
