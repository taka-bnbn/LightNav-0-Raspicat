#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_NAME="lightnav-jetson:jp622"
MODEL_DIR="${ROOT_DIR}/models/LightNav-0"

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/lightnav_container.sh build
  ./scripts/lightnav_container.sh serve [vln|tracking] [port]

build: LightNav-0用のJetson GPUコンテナを作る（初回のみ）。
serve: モデルサーバーを前面で起動する。Ctrl-Cで安全に停止する。
USAGE
}

case "${1:-}" in
  build)
    sudo docker build \
      --file "${ROOT_DIR}/docker/Dockerfile.jetson" \
      --tag "${IMAGE_NAME}" \
      "${ROOT_DIR}"
    ;;
  serve)
    TASK="${2:-vln}"
    PORT="${3:-8051}"
    [[ "${TASK}" == "vln" || "${TASK}" == "tracking" ]] || {
      echo "taskは vln または tracking を指定してください。" >&2
      exit 2
    }
    [[ -f "${MODEL_DIR}/model-00001-of-00001.safetensors" ]] || {
      echo "モデル重みがありません: ${MODEL_DIR}" >&2
      exit 1
    }
    exec sudo docker run --rm \
      --runtime nvidia \
      --network host \
      --ipc host \
      --ulimit memlock=-1 \
      --ulimit stack=67108864 \
      --volume "${MODEL_DIR}:/models/LightNav-0:ro" \
      "${IMAGE_NAME}" \
      --task "${TASK}" \
      --model_path /models/LightNav-0 \
      --backend hf \
      --port "${PORT}"
    ;;
  *)
    usage
    exit 2
    ;;
esac
