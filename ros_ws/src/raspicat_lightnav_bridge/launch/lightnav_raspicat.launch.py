"""Launch the LightNav client, MPC, and guarded Raspicat adapter."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    server_url = LaunchConfiguration("server_url")
    camera_topic = LaunchConfiguration("camera_topic")
    image_topic = LaunchConfiguration("lightnav_image_topic")
    enable_motion = LaunchConfiguration("enable_motion")
    return LaunchDescription(
        [
            DeclareLaunchArgument("server_url", default_value="ws://127.0.0.1:8051"),
            DeclareLaunchArgument("camera_topic", default_value="/camera/color/image_raw"),
            DeclareLaunchArgument(
                "lightnav_image_topic",
                default_value="/lightnav/camera/color/image_raw",
            ),
            DeclareLaunchArgument("enable_motion", default_value="false"),
            Node(
                package="raspicat_lightnav_bridge",
                executable="image_adapter",
                parameters=[{"input_topic": camera_topic, "output_topic": image_topic}],
            ),
            Node(
                package="vln_client",
                executable="vln_client",
                parameters=[{"server_url": server_url, "image_topic": image_topic}],
            ),
            Node(
                package="vln_mpc",
                executable="vln_mpc",
                parameters=[
                    {
                        "enabled": enable_motion,
                        "track_v_max": 0.08,
                        "objnav_v_max": 0.08,
                        "w_max": 0.25,
                        "a_max_v": 0.16,
                        "a_max_w": 0.5,
                    }
                ],
            ),
            Node(
                package="raspicat_lightnav_bridge",
                executable="bridge",
                parameters=[{"enabled": enable_motion}],
            ),
        ]
    )
