# 為替レートETLパイプライン

公開為替レートAPIから日次でレートを取得し、pandas で整形・クレンジングして MySQL に蓄積・集計する ETL パイプラインです。データエンジニア転向に向けたポートフォリオとして開発しています。

> 🚧 **開発中** — 設計フェーズ完了、実装に着手しています。進捗は下記ロードマップと [Issues](../../issues) を参照してください。

## 概要

- 公開為替レートAPI（Frankfurter API）から為替レートを日次で取得
- pandas で整形・クレンジングし、データ品質チェックを実施
- MySQL に raw データ・集計データを蓄積
- 集計結果を CSV・グラフ（PNG）で出力
- 毎日実行するバッチ処理

## 処理フロー

```
Extract → Transform → 品質チェック → Load(raw) → 集計 → 出力(CSV/PNG)
```

## 技術スタック

| 区分 | 採用 | 主な選定理由 |
|---|---|---|
| 言語 | Python | データ処理の定番。requests / pandas 等が充実 |
| 為替レートAPI | Frankfurter API | 無料・APIキー不要・過去データ取得可で ETL バッチに最適 |
| データベース | MySQL | 実務で広く使われ、無料で普及。ポートフォリオに最適 |
| 主要ライブラリ | requests, pandas, SQLAlchemy, PyMySQL, matplotlib, pytest | — |

技術選定の比較・理由の詳細は [設計ドキュメント](docs/design.md) を参照。

## 実装ロードマップ

各STEPで「動く成果物」が残るように分割しています。

| STEP | 内容 | 状況 |
|---|---|---|
| 1 | 基盤整備（構成・requirements） | ✅ 完了 |
| 2 | Extract（API取得） | ✅ 完了 |
| 3 | Transform + 品質チェック | ⬜ 未着手 |
| 4 | Load（MySQL保存） | ⬜ 未着手 |
| 5 | 集計 | ⬜ 未着手 |
| 6 | 出力 + バッチ統合 | ⬜ 未着手 |
| 7 | テスト + ドキュメント | ⬜ 未着手 |

## 動作例

### Frankfurter API のレスポンス
ブラウザで `https://api.frankfurter.dev/v2/rates` にアクセスした結果。

![Frankfurter API のレスポンス](docs/images/api_response.png)

### Extract の実行結果（STEP 2）
`extract.py` を実行し、為替レートを JSON配列で取得できたところ。

![extract.py の実行結果](docs/images/extract_run.png)

## ドキュメント

- [設計ドキュメント (docs/design.md)](docs/design.md) — 背景・技術選定理由・アーキテクチャ・STEP分解
- [開発ログ (Notion)](https://www.notion.so/b421864d51b24570a0ec352cedade572) — 日々の作業記録・設計判断

## セットアップ

```bash
# 1. リポジトリをクローン
git clone <repository-url>
cd exchange-rate-pipeline

# 2. 依存ライブラリをインストール
pip install -r requirements.txt

# 3. 環境変数を設定（.env.example をコピーして MySQL 接続情報を記入）
cp .env.example .env
```

※ 実行方法は実装の進行に応じて追記します。
