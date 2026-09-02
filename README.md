# LightNav-0-Raspicat

Jetson AGX Orin 上で Light-Nav-0 と Intel RealSense、Raspberry Pi Cat を動かすための配布用リポジトリです。

## Jetson で最初に実行すること

GitHub から取得した後、次の一行を実行します。

```bash
git clone <このリポジトリのURL> LightNav-0-Raspicat
cd LightNav-0-Raspicat
./scripts/prepare_jetson.sh
```

このスクリプトは Jetson の機種・L4T (JetPack)・Python を表示し、RealSense のホスト側ツール、Python 仮想環境、共通依存を準備します。**GPU 用 PyTorch は JetPack と一致した wheel またはコンテナが必要**なので、JetPack 判定結果に従って `config/jetson.env` を一度だけ設定します。x86 の仮想環境をコピーしないでください。

設定後は、ハードウェアだけを安全に確認できます。

```bash
./scripts/check_hardware.sh
```

モータを接続する前に、RealSense が `realsense-viewer` で RGB/Depth を表示できること、Jetson と機体側 Raspberry Pi で同じ `ROS_DOMAIN_ID` を使っていることを確認してください。

## 重要な状態

現時点では、このリポジトリには実際の Light-Nav-0 推論コードとモデル重みはまだ入っていません。そのため `src/run_robot.py` はゼロ速度だけを送って安全に停止します。既存の動作済みコードを `src/` に追加したら、依存を `requirements/common.txt` に固定し、推論結果を `src/cmd_vel_bridge.py` の `publish_command()` へ渡してください。

モデル重みは Git に直接入れず、ライセンスを確認してダウンロードスクリプトまたはリリース配布にしてください。明日ネットワークに頼れない場合は、事前に重みを `models/` へ置いてください。

## 構成

```text
config/          Jetson と機体ごとの差分（Gitには雛形のみ）
requirements/    x86/ARM で異なる依存を分離
scripts/         Jetson導入・診断・安全な起動
src/             ロボットアプリ本体
```

## Raspberry Pi Cat との接続

JetsonはモータをUSBシリアルで直接制御しません。機体側Raspberry PiでRaspberry Pi CatのROS 2ドライバを起動し、Jetsonはネットワーク越しに`/cmd_vel`をpublishします。

```text
Jetson: Light-Nav-0 + RealSense -- ROS 2 /cmd_vel --> Raspberry Pi Cat: ROS 2ドライバ + モータ
```

両方でROS 2 Humbleを使い、`config/robot.env`の`ROS_DOMAIN_ID`を同じ値にしてください。機体側では、手動操作資料の手順に従い`raspicat`を起動し、モータ電源を有効化します。

```bash
ros2 launch raspicat raspicat.launch.py
ros2 service call /motor_power std_srvs/srv/SetBool '{data: true}'
```

Jetson側では次を実行し、`/cmd_vel`と`/odom`が見えることを確認します。

```bash
./scripts/check_hardware.sh
```

`./scripts/run_robot.sh`は、実装が未追加の間は**停止命令（ゼロ速度）だけ**を送ります。推論結果による走行を許可するには、実装を接続した上で`ALLOW_MOTION=1`を明示します。
