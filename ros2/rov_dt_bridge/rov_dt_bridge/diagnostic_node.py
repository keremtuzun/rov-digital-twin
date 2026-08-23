"""ROS 2 adapter example. Requires rclpy and generated message packages."""
import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from rov_dt.decision import SafetyDecisionAgent
from rov_dt.model import SoftmaxWeakPointClassifier
from rov_dt.telemetry_contract import TelemetryContractError, telemetry_sample_from_json


class DiagnosticNode(Node):
    def __init__(self):
        super().__init__("rov_diagnostic_agent")
        self.declare_parameter("model_path", "models/weakpoint.json")
        model = SoftmaxWeakPointClassifier.load(self.get_parameter("model_path").value)
        self.agent = SafetyDecisionAgent(model)
        self.publisher = self.create_publisher(String, "/rov/diagnostic_decision", 10)
        self.create_subscription(String, "/rov/telemetry_json", self.on_telemetry, 10)

    def on_telemetry(self, message: String) -> None:
        try:
            sample = telemetry_sample_from_json(message.data)
        except TelemetryContractError as exc:
            self.get_logger().warning(f"Rejected invalid telemetry: {exc}")
            return
        output = String()
        output.data = json.dumps(self.agent.decide(sample).to_dict())
        self.publisher.publish(output)


def main() -> None:
    rclpy.init()
    node = DiagnosticNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
