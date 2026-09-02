#!/usr/bin/env bash
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source config/robot.env

echo "== Jetson / GPU =="
uname -m
cat /etc/nv_tegra_release 2>/dev/null || true

if [[ -x .venv/bin/python ]]; then
  .venv/bin/python - <<'PY'
try:
    import torch
    print("torch:", torch.__version__)
    print("CUDA available:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("GPU:", torch.cuda.get_device_name(0))
except ImportError:
    print("torch: 未導入（config/jetson.env を設定して prepare_jetson.sh を再実行）")
PY
fi

echo
echo "== USB / RealSense =="
lsusb | grep -Ei 'Intel|RealSense' || echo "RealSense はUSBで未検出です。"
v4l2-ctl --list-devices 2>/dev/null || true
command -v realsense-viewer >/dev/null && echo "realsense-viewer: 利用可能" || echo "realsense-viewer: 未導入"

echo
echo "== ROS 2 / Raspberry Pi Cat =="
if [[ -f "/opt/ros/${ROS_DISTRO}/setup.bash" ]]; then
  # shellcheck disable=SC1090
  source "/opt/ros/${ROS_DISTRO}/setup.bash"
  export ROS_DOMAIN_ID
  echo "ROS_DISTRO=${ROS_DISTRO}, ROS_DOMAIN_ID=${ROS_DOMAIN_ID}"
  ros2 topic list || true
  echo "期待するトピック: ${CMD_VEL_TOPIC}, /odom"
else
  echo "ROS 2 ${ROS_DISTRO} がJetsonにありません。"
fi

echo
echo "安全確認: このスクリプトはカメラ・機体へ制御コマンドを一切送りません。"
