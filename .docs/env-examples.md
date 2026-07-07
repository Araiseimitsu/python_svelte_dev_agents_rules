# 環境変数 記入例

`AGENTS.md` §10 の記入例である。分離・秘密情報のルールは `AGENTS.md` §10 を正本とする。
`.env` / `.env.example` の新規作成・変更時に参照する。

---

## backend .env 例

```env
APP_ENV=development
DATABASE_URL=postgresql://user:password@localhost:5432/appdb
SECRET_KEY=change_me
CORS_ORIGINS=http://localhost:5173
NAS_BASE_PATH=\\server\share
```

## frontend .env 例

```env
VITE_API_BASE_URL=http://localhost:8000
```

## .gitignore 必須例

```gitignore
.env
.env.*
!.env.example
```
