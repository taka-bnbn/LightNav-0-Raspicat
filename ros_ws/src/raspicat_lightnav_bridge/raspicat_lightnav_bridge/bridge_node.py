"""Safely adapt LightNav MPC TwistStamped commands to Raspicat /cmd_vel."""

from __future__ import annotations

import time

import rclpy
from geometry_msgs.msg import Twist, TwistStamped
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import Bool, String

from .core import limit_command


class RaspicatLightNavBridge(Node):
    def __init__(self) -> None:
        super().__init__("raspicat_lightnav_bridge")
        self.declare_parameter("enabled", False)
        self.declare_parameter("input_topic", "mpc/cmd_vel")
        self.declare_parameter("output_topic", "/cmd_vel")
        self.declare_parameter("enable_topic", "control/enable")
        self.declare_parameter("vln_status_topic", "vln/status")
        self.declare_parameter("mpc_status_topic", "mpc/status")
        self.declare_parameter("max_linear_velocity", 0.08)
        self.declare_parameter("max_angular_velocity", 0.25)
        self.declare_parameter("command_timeout_s", 0.5)
        self.declare_parameter("publish_rate_hz", 10.0)
        self.declare_parameter("allow_reverse", False)

        self.enabled = bool(self.get_parameter("enabled").value)
        self.max_linear = float(
            self.get_parameter("max_linear_velocity").value
        )
        self.max_angular = float(
            self.get_parameter("max_angular_velocity").value
        )
        self.timeout_s = float(self.get_parameter("command_timeout_s").value)
        publish_rate = float(self.get_parameter("publish_rate_hz").value)
        self.allow_reverse = bool(self.get_parameter("allow_reverse").value)
        if min(self.max_linear, self.max_angular, self.timeout_s, publish_rate) <= 0:
            raise ValueError("velocity limits, timeout, and publish rate must be positive")

        latched = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self.publisher = self.create_publisher(
            Twist, str(self.get_parameter("output_topic").value), 10
        )
        self.create_subscription(
            TwistStamped,
            str(self.get_parameter("input_topic").value),
            self._on_command,
            10,
        )
        self.create_subscription(
            Bool,
            str(self.get_parameter("enable_topic").value),
            self._on_enable,
            10,
        )
        self.create_subscription(
            String,
            str(self.get_parameter("vln_status_topic").value),
            self._on_vln_status,
            latched,
        )
        self.create_subscription(
            String,
            str(self.get_parameter("mpc_status_topic").value),
            self._on_mpc_status,
            latched,
        )

        self.vln_status = ""
        self.mpc_status = ""
        self.last_command: tuple[float, float] | None = None
        self.last_command_at = 0.0
        self.was_active = False
        self.create_timer(1.0 / publish_rate, self._tick)
        self.get_logger().info(
            "Raspicat bridge ready: enabled=%s input=%s output=%s "
            "limits=(%.3f m/s, %.3f rad/s) timeout=%.3fs"
            % (
                self.enabled,
                self.get_parameter("input_topic").value,
                self.get_parameter("output_topic").value,
                self.max_linear,
                self.max_angular,
                self.timeout_s,
            )
        )

    def _on_command(self, message: TwistStamped) -> None:
        self.last_command = limit_command(
            message.twist.linear.x,
            message.twist.angular.z,
            self.max_linear,
            self.max_angular,
            self.allow_reverse,
        )
        self.last_command_at = time.monotonic()

    def _on_enable(self, message: Bool) -> None:
        if self.enabled != message.data:
            self.enabled = message.data
            self.get_logger().info(
                "Raspicat command output %s" % ("enabled" if self.enabled else "disabled")
            )
        if not self.enabled:
            self._publish_stop()

    def _on_vln_status(self, message: String) -> None:
        self.vln_status = message.data.strip()
        if self.vln_status != "RUNNING":
            self._publish_stop()

    def _on_mpc_status(self, message: String) -> None:
        self.mpc_status = message.data.strip()
        if self.mpc_status != "RUNNING":
            self._publish_stop()

    def _active(self, now: float) -> bool:
        return (
            self.enabled
            and self.vln_status == "RUNNING"
            and self.mpc_status == "RUNNING"
            and self.last_command is not None
            and now - self.last_command_at <= self.timeout_s
        )

    def _tick(self) -> None:
        now = time.monotonic()
        if self._active(now):
            assert self.last_command is not None
            message = Twist()
            message.linear.x, message.angular.z = self.last_command
            self.publisher.publish(message)
            self.was_active = True
            return
        # Keep feeding zero to the robot watchdog after an active command stops.
        if self.enabled or self.was_active:
            self._publish_stop()

    def _publish_stop(self) -> None:
        if rclpy.ok():
            self.publisher.publish(Twist())
        self.was_active = False

    def destroy_node(self):
        self._publish_stop()
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = RaspicatLightNavBridge()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
