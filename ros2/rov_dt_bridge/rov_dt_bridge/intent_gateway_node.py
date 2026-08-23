"""Explicit, disabled-by-default simulation-only diagnostic intent gateway."""

from __future__ import annotations

import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from rov_dt.intent_gateway import decision_to_simulation_intent
from rov_dt.telemetry_contract import TelemetryContractError


class IntentGatewayNode(Node):
    def __init__(self) -> None:
        super().__init__("diagnostic_intent_gateway")
        self.declare_parameter("enabled", False)
        self.declare_parameter("simulation_only", True)
        self.publisher = self.create_publisher(String, "/rov/high_level_command", 10)
        self.create_subscription(String, "/rov/diagnostic_decision", self.on_decision, 10)
        self.get_logger().warning(
            "Intent gateway is disabled by default and can only operate with simulation_only=true"
        )

    def on_decision(self, message: String) -> None:
        try:
            decision = json.loads(message.data)
            intent = decision_to_simulation_intent(
                decision,
                enabled=bool(self.get_parameter("enabled").value),
                simulation_only=bool(self.get_parameter("simulation_only").value),
            )
        except (json.JSONDecodeError, TelemetryContractError, PermissionError) as exc:
            self.get_logger().warning(f"Rejected diagnostic decision: {exc}")
            return
        if intent is None:
            return
        output = String()
        output.data = json.dumps(intent, separators=(",", ":"))
        self.publisher.publish(output)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = IntentGatewayNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
