#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

test -x .venv/bin/python || { echo "先に ./scripts/prepare_jetson.sh を実行してください。"; exit 1; }
source config/robot.env
exec .venv/bin/python src/run_robot.py
