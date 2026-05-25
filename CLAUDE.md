# 為替レートETLパイプライン — Claude Code 向け補足

このファイルは、Claude Code が新セッションで本プロジェクトを扱うときに参照する**定常情報**です。プロジェクトの進捗や方針は別途、メモリ機能（`~/.claude/projects/.../memory/`）側にあります。

## プロジェクト概要

為替レートETLパイプライン。Frankfurter API から日次レートを取得し、pandas で整形・品質チェックして MySQL に蓄積するバッチ処理。データエンジニア転向用ポートフォリオ。

詳細: [README.md](README.md) / [docs/design.md](docs/design.md)

## 開発環境

### 仮想環境（PowerShell）

```powershell
.\.venv\Scripts\Activate.ps1
```

※ 新しいターミナルを開くたびに必要。プロンプト先頭に `(.venv)` が付けば有効。

### 依存ライブラリのインストール

```powershell
pip install -r requirements.txt
```

## 実行

| コマンド | 用途 |
|---|---|
| `python -m src.<モジュール名>` | 各モジュール単体実行（例: `python -m src.extract`） |
| `python main.py` | パイプライン全体（STEP 6 で配線予定。現在は空） |

## 品質チェック（Ruff）

```powershell
ruff check .              # リント
ruff check --fix .        # 自動修正できる箇所を修正
ruff format .             # フォーマット
```

`ruff` は pip でも VSCode 拡張でも導入済み。VSCode 拡張は既定で venv 内の Ruff を使う設定。

## GitHub

- リポジトリ: https://github.com/yuki-kuro/exchange-rate-pipeline （public）
- `gh` の場所: `C:\Program Files\GitHub CLI\gh.exe`
  - PowerShell では `& "C:\Program Files\GitHub CLI\gh.exe" <コマンド>` の形で呼ぶ
- コミットメッセージに `Closes #N` を入れて push すると、対応 Issue が自動クローズされる

## データベース（MySQL）

- DB 名: `exchange_rate_db`
- 接続情報: `.env`（Git管理外、`.env.example` がテンプレート）
- 接続URL組み立て: [config.py](config.py) の `DATABASE_URL`
- スキーマ DDL: [sql/schema.sql](sql/schema.sql)
- 主テーブル: `raw_rates`（生データ）
- 操作には A5M2（A5:SQL Mk-2）を使用

## 開発ログ（Notion）

- DB 名: 「為替レートETLパイプライン 開発ログ」
- ページテンプレート（**3項目構成**）:
  - やったこと・判断（なぜ）
  - つまずき・解決
  - 学び・キーワード
- 詳細はメモリの `reference-notion-dev-log` を参照

## 進め方の方針（重要）

- **コードはなるべく自分（ユーザー）で書く**。AI の活用は設計方針のアドバイスやエラー解決の補助に留める（[docs/design.md](docs/design.md) 2章参照）
- **完成最優先・最小スコープ**で進める
- 各 STEP の完了時に Issue を `Closes #N` でクローズしてコミット
- ラベル・文言は日本語、技術固有名詞は英語のまま

### コメント駆動ワークフロー（設計文書・コーディング共通）

設計文書もコーディングも **コメント駆動**で進める。AI は **思考の足場（scaffold）だけを提供** し、本体（本文・実装）はユーザーが書く。

**基本フロー:**

1. **AI**: 骨格 + ヒント/質問コメントを用意する（本体は書かない）
2. **ユーザー**: コメントを読みながら本体を埋める
3. **AI**: まとめてレビュー（抜け・誤り・命名・スタイル不一致を指摘）
4. **ユーザー**: 修正 → 必要に応じてループ

**設計文書（`docs/design.md` など）の場合:**

- AI はセクション骨格を書き、各論点に `<!-- HINT: ... -->` / `<!-- Q: ... -->` でヒントと質問を入れる
- 論点候補の取捨選択は最初にユーザーと合意してから着手

**コーディング（`src/*.py` など）の場合:**

- AI は関数・クラスのシグネチャ（引数・戻り値・型注釈）と docstring だけ書き、本体は以下のようなコメントで方針を示す:
  - `# HINT: ...` — 実装方針のヒント
  - `# Q: ...` — 設計判断が必要な箇所
  - `# TODO: ...` — 埋めるべきブロック
- ロジック分割・関数の切り方も最初にユーザーと合意してから着手
- ボイラープレート（import 文、`if __name__ == "__main__"` 等）はコメント駆動の対象外。AI が普通に書いて OK

**例外的に AI が実装を書いてよい場合:**

- ユーザーが明示的に「実装まで書いて」と依頼したとき
- エラー解決の補助でピンポイントに数行直すとき
