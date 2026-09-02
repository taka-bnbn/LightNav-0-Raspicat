#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ "$(uname -m)" != "aarch64" ]]; then
  echo "ERROR: このスクリプトは Jetson (aarch64) 上で実行してください。"
  exit 1
fi

echo "== Jetson 情報 =="
cat /etc/nv_tegra_release || true
echo "Python: $(python3 --version)"
echo

sudo apt-get update
sudo apt-get install -y \
  python3-venv python3-pip python3-dev \
  libopenblas-dev libusb-1.0-0-dev libudev-dev \
  usbutils v4l-utils curl gpg

if [[ ! -f config/robot.env ]]; then
  cp config/robot.env.example config/robot.env
fi
if [[ ! -f config/jetson.env ]]; then
  cp config/jetson.env.example config/jetson.env
fi

# RealSense の公式APTリポジトリ。失敗しても、GPU環境の診断を先へ進められるようにする。
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://librealsense.realsenseai.com/Debian/librealsenseai.asc \
  | gpg --dearmor | sudo tee /etc/apt/keyrings/librealsenseai.gpg >/dev/null
echo "deb [signed-by=/etc/apt/keyrings/librealsenseai.gpg] https://librealsense.realsenseai.com/Debian/apt-repo $(lsb_release -cs) main" \
  | sudo tee /etc/apt/sources.list.d/librealsense.list >/dev/null
sudo apt-get update
sudo apt-get install -y librealsense2-utils librealsense2-dev || {
  echo "WARNING: RealSense APT導入に失敗しました。READMEのRealSense節に従ってRSUSB/カーネル対策を行ってください。"
}

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements/common.txt

# GPU PyTorch はJetPackごとにwheelが異なる。空欄のままではCPU版を勝手に入れない。
source config/jetson.env
if [[ -n "${TORCH_WHEEL_URL:-}" ]]; then
  python -m pip install --no-cache-dir numpy==1.26.1
  python -m pip install --no-cache-dir "$TORCH_WHEEL_URL"
else
  cat <<'MSG'

ACTION REQUIRED: config/jetson.env の TORCH_WHEEL_URL を、このJetPack/Pythonに一致する
NVIDIA提供aarch64 PyTorch wheelへ設定してください。CPU版torchをPyPIから入れると
Light-Nav-0はJetson GPUを使えません。
MSG
fi

echo
echo "準備完了。次は ./scripts/check_hardware.sh を実行してください。"
