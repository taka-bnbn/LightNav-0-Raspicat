#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

test -x .venv/bin/python || { echo "先に ./scripts/prepare_jetson.sh を実行してください。"; exit 1; }
source config/robot.env
test -f "/opt/ros/${ROS_DISTRO}/setup.bash" || { echo "ROS 2 ${ROS_DISTRO} が見つかりません。"; exit 1; }
# shellcheck disable=SC1090
source "/opt/ros/${ROS_DISTRO}/setup.bash"
export ROS_DOMAIN_ID CMD_VEL_TOPIC ALLOW_MOTION
exec .venv/bin/python src/run_robot.py
