#!/usr/bin/env bash
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

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
echo "== Raspberry Pi Cat 候補ポート =="
ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || echo "シリアルUSB機器は未検出です。"

echo
echo "安全確認: このスクリプトはカメラ・機体へ制御コマンドを一切送りません。"
