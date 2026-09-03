from setuptools import find_packages, setup

package_name = "lightnav_camera"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="LightNav-0-Raspicat",
    maintainer_email="noreply@example.invalid",
    description="V4L2 RGB camera publisher for LightNav-0.",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "realsense_camera = lightnav_camera.realsense_camera:main",
        ],
    },
)
