#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
lightnav_dir="${LIGHTNAV_SOURCE_DIR:-${HOME}/LightNav-0}"
source_dir="${lightnav_dir}/robot_deploy/src"

if [[ ! -d "${source_dir}/vln_client" || ! -d "${source_dir}/vln_mpc" ]]; then
  echo "LightNav ROS packages not found under ${source_dir}" >&2
  echo "Set LIGHTNAV_SOURCE_DIR to the LightNav-0 source checkout." >&2
  exit 1
fi

ln -sfn "${source_dir}/vln_client" "${repo_dir}/ros_ws/src/vln_client"
ln -sfn "${source_dir}/vln_mpc" "${repo_dir}/ros_ws/src/vln_mpc"

python3 -m pip install --user -r "${repo_dir}/requirements/ros-jetson.txt"

source /opt/ros/humble/setup.bash
colcon --log-base "${repo_dir}/ros_ws/log" build \
  --symlink-install \
  --base-paths "${repo_dir}/ros_ws/src" \
  --build-base "${repo_dir}/ros_ws/build" \
  --install-base "${repo_dir}/ros_ws/install" \
  --packages-select vln_client vln_mpc raspicat_lightnav_bridge

echo "ROS packages prepared. Source ${repo_dir}/ros_ws/install/setup.bash"
