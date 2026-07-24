# 汎用説明動画PPTX自動生成 v3.1.0

## 目的

多様な説明・講義・操作動画からPowerPointを生成します。品質採点、公開ブロック、事後評価、修復ジョブは使用しません。

v3.1.0では、大容量の全体編集JSONへの依存を廃止し、少数スライド単位の分割編集とローカル編集フォールバックを採用しました。

## ファイル

- `video_training_pptx_generator_v3.1.0.py`: Open WebUI Tool
- `video_training_pptx_generator_prompt_v3.1.0.md`: システムプロンプト
- `video_training_pptx_generator_v3.1.0_optimization_report_ko.md`: 최적화 보고서
- `video_training_pptx_generator_v3.1.0_tests.py`: 自動テスト
- `video_training_pptx_generator_v3.1.0_test_report.txt`: テスト結果
- `video_training_pptx_generator_v3.0.0_to_v3.1.0.patch`: v3.0.0からの差分
- `SHA256SUMS.txt`: ファイルハッシュ

## 公開アクション

```text
debug_ping
generate_training_material
```

## v3.1.0の主要変更

- トップレベルJSON配列を`slides`または`chapters`へ自動変換
- 全スライド一括編集を最大4枚単位の分割編集へ変更
- 編集LLM失敗時はローカル編集結果でPPTX生成を継続
- 章・スライド計画のJSON形式エラーまたはタイムアウト時も規則ベース案へフォールバック
- 同じ`message_id`からの重複Tool呼出しは最初の結果を再利用
- エラー後の同一ターン自動再実行を禁止
- 成功後は作業ディレクトリにPPTXだけを残す

## 推奨導入手順

1. v3.0.0以前の動画生成Toolを無効化します。
2. `video_training_pptx_generator_v3.1.0.py`をToolとして登録します。
3. `video_training_pptx_generator_prompt_v3.1.0.md`を対象モデルのシステムプロンプトへ設定します。
4. 動画生成モデルでは他の資料生成Toolを無効化します。
5. 新しいチャットで`debug_ping`を実行し、versionが`3.1.0`であることを確認します。
6. 動画を添付し、「この動画から説明資料を生成してください。」を1回送信します。
