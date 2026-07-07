# Provider MCP / Skills 連携仕様

このファイルは、Codex / OpenCode / Antigravity の CLI 連携を扱うプロジェクトでのみ参照する。
共通ルールは `AGENTS.md` に従う。

---

## 1. 設定ファイルの場所

- OpenCode の MCP 設定: `~/.config/opencode/opencode.json` と選択 workspace root の `.mcp/settings.json`
- OpenCode のユーザー共通 skill 配置先: `~/.config/opencode/skills`
- OpenCode / Antigravity の project skill 配置先: 選択 workspace root の `skills/`
- Antigravity の MCP 等の CLI 設定: `C:/Users/seizo/.gemini/settings.json` と選択 workspace root の `.mcp/settings.json`
- Antigravity のユーザー共通 skill 配置先: `C:/Users/seizo/.gemini/skills`

---

## 2. Provider 一覧

| provider | API 経路 | workspace | MCP / skills |
| --- | --- | --- | --- |
| Codex | Codex App Server | Frontend の `workspace_path` を使用 | workspace 基準 |
| OpenCode | ローカル `opencode serve` + 公式 SDK `opencode-ai`（CLI を Backend が起動） | Frontend の `workspace_path` を使用 | tool / MCP は opencode CLI 標準設定に workspace `.mcp/settings.json` を merge。skills は `~/.config/opencode/skills` と workspace root `skills/` を利用 |
| Antigravity | Antigravity CLI (`agy -p`) | Frontend の `workspace_path` を使用 | ターミナルの `agy -p` と同じユーザー設定（MCP 等は `C:/Users/seizo/.gemini/settings.json` に workspace `.mcp/settings.json` を merge、ユーザー共通 skills は `C:/Users/seizo/.gemini/skills`）と workspace root `skills/` を利用 |

---

## 3. OpenCode 運用詳細

- Frontend の `workspace_path` でローカル `opencode serve` を Backend が起動し、公式 SDK `opencode-ai` 経由で会話する（毎ターン新規 session を作成する stateless 運用）。
- `opencode serve` は port 単位で常駐するため、Backend 管理の serve は workspace 変更時に停止して起動し直す。
- 外部起動済みの serve は workspace を保証できないため、workspace 指定時は安全側で拒否する。
- 認証は opencode CLI 標準に委譲する。API キーの env 設定は不要。
- MCP は `~/.config/opencode/opencode.json` と選択 workspace root の `.mcp/settings.json` を起動時 config として merge する。
- skills はユーザー共通 `~/.config/opencode/skills` と選択 workspace root の `skills/` を読む。
- tool 実行（filesystem / MCP / document など）は opencode ネイティブに全委譲し、Backend 自前の tool ループは持たない。
- Gemini API 直呼びは廃止し、旧 `gemini` / `gemini_cli` provider 入力は Antigravity に正規化する。

---

## 4. MCP / skills のマージ規則

- MCP は OpenCode / Antigravity 各 CLI の通常ユーザー設定を正本にしつつ、Frontend で選択した workspace root の `.mcp/settings.json` を project-level MCP として merge する。同名 MCP server は workspace 側を優先する。
- skills は各 CLI のユーザー共通ディレクトリに加え、Frontend で選択した workspace root の `skills/` を project-level skill として読む。

---

## 5. `gws` コマンド詳細

`AGENTS.md` §20 の詳細である。書き込み系の事前確認ルールは `AGENTS.md` §20 を正本とする。

- **基本形**: `gws <service> <resource> [sub-resource] <method> [--params JSON] [--json JSON]`
- **例**:
    - `gws drive files list --params '{"pageSize": 10}'`
    - `gws gmail users messages list --params '{"userId": "me", "q": "is:unread"}'`
    - `gws calendar events list --params '{"calendarId": "primary"}'`
    - スキーマ確認: `gws schema drive.files.list`
- **不明なメソッド**は `gws <service> --help` または `gws schema <service.resource.method>` を先に確認する。

---

## 6. `gws` の自動許可スコープ

- Antigravity: `agy -p` 実行前に PilotBase の shell 承認を通す。
- OpenCode: `~/.config/opencode/opencode.json` の `permission.bash` で `gws *list*` / `*get*` / `*search*` / `schema*` を `allow`、書き込み系は `ask`。
