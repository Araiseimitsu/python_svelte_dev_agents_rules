# Backend Python 詳細リファレンス

`AGENTS.md` §6 の詳細（コマンド例・推奨構造）である。必須・禁止ルールは `AGENTS.md` §6 を正本とする。
Backend の実装・構成変更時に参照する。

---

## 1. uv コマンド例

```bash
uv venv
uv add fastapi
uv add --dev pytest
uv run python src/app/main.py
uv run pytest
```

---

## 2. 推奨構造

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
