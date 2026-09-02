"""Light-Nav-0の判断をROS 2のTwistへ安全に変換する小さな橋渡し。"""

import os

import rclpy
from geometry_msgs.msg import Twist


class CmdVelBridge:
    """Raspberry Pi Catの速度指令トピックへTwistをpublishする。

    非ゼロの指令は、ALLOW_MOTION=1を明示したときだけ許可する。
    """

    def __init__(self, topic: str) -> None:
        rclpy.init()
        self.node = rclpy.create_node("lightnav_cmd_vel_bridge")
        self.publisher = self.node.create_publisher(Twist, topic, 10)

    def publish_command(self, linear_x: float, angular_z: float) -> None:
        if (linear_x != 0.0 or angular_z != 0.0) and os.getenv("ALLOW_MOTION") != "1":
            raise PermissionError(
                "非ゼロの速度指令は拒否しました。実機の安全確認後に ALLOW_MOTION=1 を設定してください。"
            )
        command = Twist()
        command.linear.x = float(linear_x)
        command.angular.z = float(angular_z)
        self.publisher.publish(command)
        rclpy.spin_once(self.node, timeout_sec=0.1)

    def close(self) -> None:
        self.node.destroy_node()
        rclpy.shutdown()
