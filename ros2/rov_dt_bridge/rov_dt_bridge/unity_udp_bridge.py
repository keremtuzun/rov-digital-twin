"""Bridge Unity JSON telemetry to ROS 2 without issuing raw actuator commands."""

from __future__ import annotations

import json
import socket

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from rov_dt.telemetry_contract import (
    TelemetryContractError,
    telemetry_envelope_from_json,
    validate_high_level_intent,
)


class UnityUdpBridge(Node):
    def __init__(self) -> None:
        super().__init__("unity_udp_bridge")
        self.declare_parameter("unity_host", "127.0.0.1")
        self.declare_parameter("telemetry_port", 15000)
        self.declare_parameter("command_port", 15001)
        self.unity_host = str(self.get_parameter("unity_host").value)
        self.command_port = int(self.get_parameter("command_port").value)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", int(self.get_parameter("telemetry_port").value)))
        self.sock.setblocking(False)
        self.publisher = self.create_publisher(String, "/rov/telemetry_json", 10)
        self.subscription = self.create_subscription(String, "/rov/high_level_command", self.forward_command, 10)
        self.timer = self.create_timer(0.02, self.poll_telemetry)
        self.get_logger().info("Unity UDP bridge ready; only high-level intent messages are forwarded")

    def poll_telemetry(self) -> None:
        try:
            payload, _ = self.sock.recvfrom(65535)
        except BlockingIOError:
            return
        try:
            envelope = telemetry_envelope_from_json(payload)
        except TelemetryContractError as exc:
            self.get_logger().warning(f"Ignored invalid Unity telemetry: {exc}")
            return
        message = String()
        message.data = json.dumps(envelope, separators=(",", ":"), sort_keys=True)
        self.publisher.publish(message)

    def forward_command(self, message: String) -> None:
        try:
            validate_high_level_intent(message.data)
        except TelemetryContractError as exc:
            self.get_logger().warning(f"Rejected command: {exc}")
            return
        self.sock.sendto(message.data.encode("utf-8"), (self.unity_host, self.command_port))

    def destroy_node(self) -> bool:
        self.sock.close()
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = UnityUdpBridge()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
