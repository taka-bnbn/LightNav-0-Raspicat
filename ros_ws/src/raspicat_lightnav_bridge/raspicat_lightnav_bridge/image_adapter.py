"""Convert the existing Raspicat camera_server BGR stream to LightNav RGB."""

from cv_bridge import CvBridge
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Image


class ImageAdapter(Node):
    def __init__(self) -> None:
        super().__init__("lightnav_image_adapter")
        self.declare_parameter("input_topic", "/camera/color/image_raw")
        self.declare_parameter("output_topic", "/lightnav/camera/color/image_raw")
        input_topic = str(self.get_parameter("input_topic").value)
        output_topic = str(self.get_parameter("output_topic").value)
        if not input_topic or not output_topic or input_topic == output_topic:
            raise ValueError("image adapter topics must be non-empty and different")

        qos = QoSProfile(
            depth=2,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
        )
        self.bridge = CvBridge()
        self.publisher = self.create_publisher(Image, output_topic, qos)
        self.create_subscription(Image, input_topic, self._on_image, qos)
        self._last_error = ""
        self.get_logger().info(
            f"camera adapter ready: {input_topic} (BGR) -> {output_topic} (rgb8)"
        )

    def _on_image(self, message: Image) -> None:
        try:
            rgb = self.bridge.imgmsg_to_cv2(message, desired_encoding="rgb8")
            converted = self.bridge.cv2_to_imgmsg(rgb, encoding="rgb8")
            converted.header = message.header
            if converted.header.stamp.sec == 0 and converted.header.stamp.nanosec == 0:
                converted.header.stamp = self.get_clock().now().to_msg()
            self.publisher.publish(converted)
            self._last_error = ""
        except Exception as exc:
            error = str(exc)
            if error != self._last_error:
                self._last_error = error
                self.get_logger().error(f"camera image conversion failed: {error}")


def main(args=None) -> None:
    rclpy.init(args=args)
    node = ImageAdapter()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
