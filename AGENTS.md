# AGENTS.md — AI Agent Rules

本ファイルは、本プロジェクトにおける AI Agent の最優先ルール（正本）である。
Claude Code は `CLAUDE.md` の `@AGENTS.md` インポート経由で本ファイルを読み込む。
すべてのエージェント（Claude / Codex / OpenCode / Antigravity など）は本ファイルの同一ルールに従う。

---

## 1. ルール優先順位

1. ユーザーの明示指示
2. 本ファイル `AGENTS.md`
3. `.docs/workflow.md`（開発プロセス）および `.docs/frontend-svelte.md`（フロントエンド作業時のみ）
4. 既存コードの設計・命名・構造
5. 各エージェントの Global Rule

ただし、破壊的操作・機密情報・DB操作・外部送信については、上記に関わらず常に安全側を優先する。

---

## 2. 基本方針

- すべての回答・コメントは **日本語** で書く。
- 技術は可変、設計思想は固定。
- 依存は一方向にする。
- 再現性を最優先する。
- AI が迷わない構造にする。
- 小さく分けて、責務を明確にする。
- 「動けばよい」ではなく、後から直せる構造にする。

---

## 3. 開発プロセス

開発は `理解 → 計画 → 実装 → 検証 → 報告` のループで進める。詳細は `.docs/workflow.md` に従う。
以下は最低限の規律である。

- **検証なしに「完了」と報告しない。** テスト・lint・型チェックの実行結果が完了の証拠である。
- 業務ロジック・判定処理・データ変換は **テストファースト** で実装する。
- **同一アプローチで3回失敗したら停止**し、再調査するかユーザーに報告する。
- 独立した複数タスクは並列化し、広範囲の調査や実装後レビューはサブエージェントに委譲してよい（対応エージェントのみ）。
- 影響範囲が想定より大きい場合・仕様の解釈が分かれる場合は、進めずに確認する。

---

## 4. プロジェクト構成

### レイアウト

```txt
project-root/
├─ backend/
├─ frontend/
├─ docker/
├─ tests/
├─ .docs/
├─ README.md
├─ AGENTS.md
└─ CLAUDE.md（@AGENTS.md を参照するのみ）
```

この構造を勝手に崩してはいけない。

### ディレクトリ責務

| パス | 役割 |
| --- | --- |
| `backend/` | FastAPI / Python 側の実装 |
| `frontend/` | Svelte / Vite 側の実装 |
| `docker/` | Docker 関連ファイル |
| `tests/` | 統合テスト、E2Eテスト、横断的なテスト |
| `.docs/` | 設計ルール、変更履歴、開発ドキュメント |
| `README.md` | セットアップ、起動方法、環境変数の説明 |
| `AGENTS.md` | 本プロジェクトの AI Agent ルール（正本） |

### 実装コードの配置

実装コードは必ず各プロジェクト配下の `src/` に置く。

```txt
backend/
├─ src/
└─ tests/

frontend/
├─ src/
└─ tests/
```

プロジェクトルートへの実装コード直置きは禁止する。例外は以下のみ。

- 設定ファイル
- README / ドキュメント
- Docker 関連ファイル
- 起動スクリプト
- AGENTS.md / CLAUDE.md

---

## 5. プロジェクト種別の自動判定

以下のファイルから使用言語・ツールを判断する。

| ファイル | 判定結果 |
| --- | --- |
| `package.json` + `pnpm-lock.yaml` | Node.js（pnpm） |
| `pyproject.toml` / `requirements.txt` | Python |
| `go.mod` | Go |
| `Cargo.toml` | Rust |
| `pom.xml` / `build.gradle` | Java |

---

## 6. Backend ルール

Python バックエンドは FastAPI を基本とする。

### 必須

- Python 管理は `uv` を使用する。
- `pyproject.toml` と `uv.lock` を使用し、`uv.lock` は必ずコミットする。
- 依存追加は `uv add`、実行は `uv run`、テストは `uv run pytest` を使用する。

### 禁止

- `pip` 単独使用
- `poetry` 併用
- `requirements.txt` の手動管理
- 直接 `python` 実行
- グローバル Python 環境への依存
- 仮想環境の手動前提化

### 実行例

```bash
uv venv
uv add fastapi
uv add --dev pytest
uv run python src/app/main.py
uv run pytest
```

### 推奨構造

```txt
backend/
├─ src/
│  └─ app/
│     ├─ main.py
│     ├─ api/
│     ├─ application/
│     ├─ domain/
│     ├─ infrastructure/
│     ├─ core/
│     └─ shared/
├─ tests/
├─ pyproject.toml
├─ uv.lock
├─ .env
└─ .env.example
```

| 層 | 役割 |
| --- | --- |
| `api/` | FastAPI のルーティング、リクエスト、レスポンス |
| `application/` | ユースケース、業務処理の流れ |
| `domain/` | 業務ルール、判定ロジック |
| `infrastructure/` | DB、外部API、ファイル、NAS、メールなど |
| `core/` | 設定、起動、ログ、例外処理 |
| `shared/` | 共通関数、型、定数 |

---

## 7. Frontend ルール

- フロントエンドは `frontend/` 配下で管理する。
- Node.js パッケージ管理は `pnpm` を使用し、`pnpm-lock.yaml` はコミット対象とする。
- Svelte / SvelteKit / Vite 固有のルールは `.docs/frontend-svelte.md` に従う。フロントエンド作業時は必ず参照する。
- 拡張ルール（`.docs/frontend-*.md`）は本ファイルより優先される。拡張ルールが無い場合は本ファイルのみ適用する。
- 拡張ルールが無いのに UI フレームワーク前提の構造を作ってはいけない。

---

## 8. 依存方向

依存関係は一方向にする。

### Backend

```txt
api
↓
application
↓
domain

application
↓
infrastructure

shared は全層から参照可能
```

### Frontend

```txt
Presentation
↓
State
↓
Application
↓
Infrastructure

Shared は全層から参照可能
```

### 禁止

- レイヤー逆流
- 循環依存
- UI から Infrastructure 直呼び
- API 層に業務ロジックを書くこと
- Infrastructure 層に画面都合の処理を書くこと

---

## 9. 二重実装・責務重複の防止

- 同じ責務を複数レイヤー・複数技術で重複実装しない。
- 既存実装がある場合は、追加実装の前に責務の所在を確認する。
- UI層とAPI層、Frontend と Backend、SvelteKit と FastAPI で責務を二重化しない。
- 特に **API呼び出し・入力検証・状態管理・データ変換・認証・ルーティング** は、正本となる実装箇所を1つに固定する。
- FastAPI をバックエンドとする構成では、SvelteKit のサーバー機能を安易に追加して API や業務ロジックを重複実装しない。
- やむを得ず類似処理を追加する場合は、既存実装を共通化・移設できない理由をコメントまたはドキュメントで明示する。

---

## 10. 環境変数

環境変数は用途ごとに分離する。

| ファイル | 用途 |
| --- | --- |
| `backend/.env` | FastAPI 用 |
| `frontend/.env` | Svelte / Vite 用 |
| root `.env` | Docker Compose や全体起動用 |

### 必須ルール

- `.env` は Git 管理しない。`.env.example` は Git 管理する。
- backend の秘密情報を frontend に置かない。
- frontend に置く値は、ブラウザから見えてよいものだけにする。
- frontend の環境変数は `VITE_` 接頭辞を使う。
- DB接続情報、APIキー、秘密鍵、NAS認証情報は `backend/.env` に置く。

### backend .env 例

```env
APP_ENV=development
DATABASE_URL=postgresql://user:password@localhost:5432/appdb
SECRET_KEY=change_me
CORS_ORIGINS=http://localhost:5173
NAS_BASE_PATH=\\server\share
```

### frontend .env 例

```env
VITE_API_BASE_URL=http://localhost:8000
```

### .gitignore 必須例

```gitignore
.env
.env.*
!.env.example
```

---

## 11. Docker ルール

Docker を使用する場合も、依存管理は各技術の標準に従う。

- Backend: Docker 内でも `uv` を使用し、`uv.lock` ベースで依存同期する。
- Frontend: Docker 内でも `pnpm-lock.yaml` ベースで依存同期する。

---

## 12. コード品質

- 1ファイル 1,000行以内。
- 単一責任原則を守り、共通処理は別モジュールへ分離する。
- 重複・冗長な構造を作らない。
- マジックナンバーを使わない。
- 変数名・関数名は意味が明確なものにする。
- 入出力の型を明確にする。
- 例外処理を放置しない。

---

## 13. テスト

テスト導入を前提とし、以下の基準で対象を判断する。

| 区分 | 対象 |
| --- | --- |
| 必須 | 業務ロジック、判定処理、API 入出力、Application 層、データ変換処理、ファイル操作の重要処理 |
| 不要 | UI表示のみ、試作コード、一度きりの処理、スタイルのみの変更 |

### Commands

```bash
uv run pytest   # backend
pnpm test       # frontend
```

---

## 14. ドキュメント

重要な変更履歴は `.docs/update.md` のみに記録する。

| 区分 | 内容 |
| --- | --- |
| 記録する | 仕様変更、重要な設計変更、ディレクトリ構成変更、DB構造変更、API仕様変更、運用上の注意点 |
| 記録しない | 試行錯誤、一時ログ、単なるエラー履歴、作業メモ、その場限りの検証内容 |

### README.md に必ず書くもの

- セットアップ手順
- 実行方法
- テスト方法
- 必要な環境変数
- ディレクトリ構成
- 開発時の注意点

---

## 15. デバッグ・ログ

- エラーは必ずログ出力し、原因特定を最優先にする。
- ログレベルは `info` / `warn` / `error` を使い分ける。
- 秘密情報をログに出してはいけない。
- エラーを握りつぶしてはいけない。

---

## 16. 安全確認（破壊的操作）

DB の削除・初期化・リセットなど破壊的操作は、**影響範囲を明示し、ユーザー承認を得てから** 実行する。承認なしでは実行しない。

本プロジェクトでは特に以下を事前確認対象とする。

- `.env` 変更
- lock ファイル更新
- DB構造変更
- ディレクトリ構成変更
- 大量ファイル生成
- Docker 設定変更

---

## 17. コード簡素化（code-simplifier）

以下の **いずれかに該当する場合、タスク完了前に自動で実行する**。

- 30行以上の変更があった場合
- 新規モジュールを追加した場合
- 可読性の低下、責務の混在、重複の増加、既存構造との不一致が見られる場合

### 実行時の厳守事項

- 仕様を変更しない（API・DB・入出力形式はすべて維持する）。
- 既存テストがすべて通過することを確認する。
- ユーザー承認なしの大規模リファクタは禁止。

---

## 18. Google Workspace CLI（`gws`）

Google Workspace（Drive / Sheets / Gmail / Calendar / Docs / Slides / Tasks / People など）への操作はシェルツールから `gws` コマンドで実行する。

- **基本形**: `gws <service> <resource> [sub-resource] <method> [--params JSON] [--json JSON]`
- **例**:
    - `gws drive files list --params '{"pageSize": 10}'`
    - `gws gmail users messages list --params '{"userId": "me", "q": "is:unread"}'`
    - `gws calendar events list --params '{"calendarId": "primary"}'`
    - スキーマ確認: `gws schema drive.files.list`
- **書き込み系（send/create/update/delete/insert/patch/batchUpdate）は必ず事前確認**。実行前に対象アカウント・対象データ・影響範囲を明示すること。
- **不明なメソッド**は `gws <service> --help` または `gws schema <service.resource.method>` を先に確認する。
- 自動許可スコープの詳細は `.docs/providers.md` を参照する。

---

## 19. 外部 AI CLI 連携（該当プロジェクトのみ）

Codex / OpenCode / Antigravity の MCP・skills 設定や連携仕様は `.docs/providers.md` に記載する。
これらの CLI 連携を扱うプロジェクトでのみ参照すればよい。

---

## 20. 禁止事項まとめ

- 検証（テスト・lint・型チェック）なしに完了報告すること
- 拡張ルールが無いのに UI フレームワーク前提の構造を作ること
- ユーザー承認なしで DB の破壊的操作を行うこと
- 仕様変更を伴う自動リファクタリングを行うこと
- 同じ責務の処理を別レイヤー・別技術に重複実装すること
- FastAPI が存在する構成で、同等の API や業務ロジックを SvelteKit 側に重ねて実装すること
- プロジェクトルートへの実装コード直置き（§4 の例外を除く）
- 秘密情報の frontend 配置・ログ出力・外部送信
- エラーの握りつぶし・テストの skip・lint ルールの安易な無効化で検証を通すこと
