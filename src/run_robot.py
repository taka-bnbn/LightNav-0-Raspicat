"""Light-Nav-0 と機体制御を接続する入口。

実際のモデル・制御コードをまだ追加していないため、危険な走行は行わずに終了する。
"""

from pathlib import Path
import os


def main() -> None:
    print("LightNav-0-Raspicat launcher")
    print(f"robot port: {os.getenv('ROBOT_PORT', '未設定')}")
    print(f"project: {Path(__file__).resolve().parents[1]}")
    raise SystemExit(
        "実行コード未追加: 動作確認済みのLight-Nav-0推論とRaspberry Pi Cat制御を "
        "src/ に追加してから、この入口へ接続してください。"
    )


if __name__ == "__main__":
    main()
