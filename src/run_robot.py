"""Light-Nav-0 と Raspberry Pi Cat のROS 2接続入口。

モデルが未追加の間は、/cmd_velへゼロ速度を一度だけpublishして終了する。
"""

import os

from cmd_vel_bridge import CmdVelBridge


def main() -> None:
    topic = os.getenv("CMD_VEL_TOPIC", "/cmd_vel")
    bridge = CmdVelBridge(topic=topic)
    try:
        bridge.publish_command(0.0, 0.0)
        print(f"停止指令を {topic} へ送信しました。")
        print("Light-Nav-0推論コードは未接続のため、走行は開始しません。")
    finally:
        bridge.close()


if __name__ == "__main__":
    main()
