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

モータを接続する前に、RealSense が `realsense-viewer` で RGB/Depth を表示できること、`config/robot.env` の `ROBOT_PORT` が正しいことを確認してください。

## 重要な状態

現時点では、このリポジトリには実際の Light-Nav-0 推論コード、モデル重み、Raspberry Pi Cat の制御ライブラリはまだ入っていません。そのため `src/run_robot.py` は安全に停止します。既存の動作済みコードを `src/` に追加したら、依存を `requirements/common.txt` に固定し、起動処理を `src/run_robot.py` に接続してください。

モデル重みは Git に直接入れず、ライセンスを確認してダウンロードスクリプトまたはリリース配布にしてください。明日ネットワークに頼れない場合は、事前に重みを `models/` へ置いてください。

## 構成

```text
config/          Jetson と機体ごとの差分（Gitには雛形のみ）
requirements/    x86/ARM で異なる依存を分離
scripts/         Jetson導入・診断・安全な起動
src/             ロボットアプリ本体
```
