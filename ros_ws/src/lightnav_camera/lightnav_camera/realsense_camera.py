"""Publish the RealSense colour V4L2 stream as sensor_msgs/Image rgb8."""

import cv2
from cv_bridge import CvBridge
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image


class RealSenseCamera(Node):
    def __init__(self) -> None:
        super().__init__("lightnav_realsense_camera")
        self.declare_parameter("device", "/dev/video4")
        self.declare_parameter("width", 640)
        self.declare_parameter("height", 360)
        self.declare_parameter("fps", 10.0)
        self.declare_parameter("topic", "/camera/color/image_raw")

        device = str(self.get_parameter("device").value)
        width = int(self.get_parameter("width").value)
        height = int(self.get_parameter("height").value)
        fps = float(self.get_parameter("fps").value)
        topic = str(self.get_parameter("topic").value)
        if fps <= 0:
            raise ValueError("fps must be positive")

        self.publisher = self.create_publisher(Image, topic, 10)
        self.bridge = CvBridge()
        self.cap = cv2.VideoCapture(device, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"YUYV"))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        if not self.cap.isOpened():
            raise RuntimeError(f"cannot open {device}")

        self.create_timer(1.0 / fps, self._publish_frame)
        self.get_logger().info(
            f"publishing {device} as rgb8 to {topic} at up to {fps:g} Hz"
        )

    def _publish_frame(self) -> None:
        ok, frame_bgr = self.cap.read()
        if not ok:
            self.get_logger().warning("failed to read a camera frame")
            return
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        message = self.bridge.cv2_to_imgmsg(frame_rgb, encoding="rgb8")
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = "camera_color_optical_frame"
        self.publisher.publish(message)

    def destroy_node(self) -> None:
        self.cap.release()
        super().destroy_node()


def main() -> None:
    rclpy.init()
    node = RealSenseCamera()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
