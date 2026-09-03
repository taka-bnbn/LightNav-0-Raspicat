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

研究室のJetsonはJetPack 6.2.2（R36.5 / CUDA 12.6）であることを確認済みです。このリポジトリには、その環境とOrin GPU向けのDocker定義を含めています。初回だけビルドします。

```bash
./scripts/lightnav_container.sh build
```

完了後、まずは言語ナビゲーション用のサーバーを起動します。

```bash
./scripts/lightnav_container.sh serve vln 8051
```

`LightNav-0 server listening`のような待受メッセージが出れば成功です。この段階ではカメラやモータへ一切の命令を送りません。別のターミナルからROS 2クライアントをつなぐのは、その後です。

この初回イメージは、JetPack対応済みのNVIDIA PyTorch 2.8を維持し、`--backend hf`で動かします。LightNav-0公式のvLLM/FlashAttentionはJetson上で未検証のため、最初から導入しません。

### 6. 接続時の注意点

既存の[`camera_server`](https://github.com/wadajun8/camera_server)は`/camera/color/image_raw`を`bgr8`で配信します。LightNav-0公式のROS 2クライアントは`rgb8`を要求するため、BGR→RGB変換ノードを追加して接続します。トピック名だけの変更では不十分です。

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
