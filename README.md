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

## 現在の実装

LightNav-0公式の`vln_client`と`vln_mpc`を使用し、`raspicat_lightnav_bridge`が
`mpc/cmd_vel`（`TwistStamped`）をRaspberry Pi Cat用の`/cmd_vel`
（`Twist`）へ変換します。ブリッジには独立したwatchdogと速度制限があります。

```text
/camera/color/image_raw (bgr8) -> image_adapter (rgb8)
  -> /lightnav/camera/color/image_raw -> vln_client -> vln/response
  -> vln_mpc + /odom -> mpc/cmd_vel
  -> raspicat_lightnav_bridge -> /cmd_vel
```

JetPack 6.2.2ではCasADi 3.8.0が要求する`GLIBCXX_3.4.32`を利用できないため、
ARM64互換の`casadi==3.7.2`へ固定しています。ROSパッケージの準備は次で行います。

```bash
./scripts/prepare_lightnav_ros.sh
```

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

Jetson側のLightNavスタックは、最初は速度出力を無効にして起動します。

```bash
source /opt/ros/humble/setup.bash
source ~/LightNav-0-Raspicat/ros_ws/install/setup.bash
ros2 launch raspicat_lightnav_bridge lightnav_raspicat.launch.py enable_motion:=false
```

カメラ、`/odom`、`vln/response`、`mpc/status`を確認後、速度出力を有効にします。

```bash
ros2 launch raspicat_lightnav_bridge lightnav_raspicat.launch.py enable_motion:=true
```

既定値では前進`0.08 m/s`、旋回`0.25 rad/s`までに制限され、MPC指令が
0.5秒更新されない場合、VLN/MPCが停止した場合、または`control/enable`へ
`false`を送った場合はゼロ速度になります。後退は既定で禁止されています。

## 明日の実施チェックリスト

### 1. Jetsonの版を記録する

最初に一度だけ、Jetson上で次を実行します。

```bash
cat /etc/nv_tegra_release
python3 --version
```

この結果は必ず控えてください。LightNav-0のGPU用PyTorchはJetPack/CUDA/Pythonの組み合わせに合わせる必要があります。x86用wheelを入れるとJetsonでは動きません。

### 2. Raspberry Pi Cat本体を起動する

本体Raspberry Piで、手動操作時と同じドライバとモータ電源を起動します。

```bash
ros2 launch raspicat raspicat.launch.py
ros2 service call /motor_power std_srvs/srv/SetBool '{data: true}'
```

Jetsonと本体Raspberry Piは同じLANまたはWi-Fiへつなぎ、両方で同じROS 2ドメインを使います。

```bash
export ROS_DOMAIN_ID=42
```

### 3. Jetson側のカメラ・ROS 2接続を確認する

```bash
./scripts/check_hardware.sh
ros2 topic echo /odom --once
```

`/odom`が見えれば、JetsonからRaspberry Pi CatのROS 2ネットワークへ接続できています。

### 4. LightNav-0本体とモデルを準備する

LightNav-0はOmniVLAではありません。公式コードと公開チェックポイントを使います。

チェックポイントは現在**約9.7 GB**です（主な`model-00001-of-00001.safetensors`が約9.70 GB）。Gitへコミットせず、Jetsonの空き容量に余裕がなければ外付けSSDへ保存して持ち込みます。

```bash
git clone https://github.com/lightorigins/LightNav-0.git
cd LightNav-0
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[video]"
hf download LightOriginsHQ/LightNav-0 --local-dir checkpoints/LightNav-0
```

ダウンロードが完了したことは、次で確認できます。

```bash
du -sh checkpoints/LightNav-0
test -f checkpoints/LightNav-0/model-00001-of-00001.safetensors && echo "重みOK"
```

外付けSSDへ置いた場合は、Jetsonでそのディレクトリをコピーするか、`lightnav-serve --model_path /media/<ユーザー名>/<SSD名>/LightNav-0`のように実際の保存先を指定します。

Jetsonでは、この前にJetPack対応のARM64 PyTorchを導入する必要があります。`vllm`を使う場合も、JetPackとの対応確認後に導入します。JetPack版が未確認のうちは、公式のx86用Dockerイメージやx86用FlashAttentionを使わないでください。

### 5. JetPack 6.2.2でLightNav-0サーバーを起動する

Jetson AGX OrinではDocker版のCUDA kernel imageエラーを確認済みのため、
動作確認済みのネイティブvenvとHugging Faceバックエンドを使います。

```bash
source ~/lightnav-venv/bin/activate
lightnav-serve --task vln --model_path ~/models/LightNav-0 --backend hf --port 8051
```

### 6. 接続時の注意点

既存の[`camera_server`](https://github.com/wadajun8/camera_server)は`/camera/color/image_raw`を`bgr8`で配信します。LightNav-0公式のROS 2クライアントは`rgb8`を要求するため、BGR→RGB変換ノードを追加して接続します。トピック名だけの変更では不十分です。

研究室のJetsonでは、RealSenseのカラー映像が`/dev/video4`（YUYV）で見つかりました。`ros_ws/src/lightnav_camera`のノードはこれをRGBへ変換し、LightNav-0互換の`/camera/color/image_raw`（`rgb8`）として配信します。

最初の確認は、必ずこの順番で行います。

1. `realsense-viewer`でRGB映像を確認する。
2. `/odom`を確認する。
3. LightNav-0が動画から経路点を返すことを確認する。
4. `/cmd_vel`へゼロ速度だけを送る。
5. 低速・車輪を浮かせた状態で短い動作と停止を確認する。
6. 最後に言語指示の自律走行を有効にする。

## 使うコード

- [LightNav-0公式リポジトリ](https://github.com/lightorigins/LightNav-0): モデル、WebSocketサーバー、ROS 2実機デプロイの参照実装。
- [camera_server](https://github.com/wadajun8/camera_server): 既存のカメラROS 2ノード。
- [Raspberry Pi Cat手動操作資料](https://cit-autonomous-robot-lab.github.io/raspicat_documentation/document/tutorial/6_teleop/): 本体側ドライバの起動方法。

`raspicat_omnivla`はOmniVLA用のため、LightNav-0を動かす今回の構成では使いません。
