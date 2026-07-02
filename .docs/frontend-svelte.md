
# Frontend Extension - Svelte
このファイルは、Svelte / SvelteKit / Vite を使用するフロントエンドに適用する拡張ルールである。
フロントエンド作業時は、本ファイルを必ず参照すること。



---


## 1. 前提
- フロントエンドは `frontend/` 配下で管理する。
- パッケージ管理は `pnpm` を使用する。
- UI フレームワーク固有のルールは本ファイルに記載する。
- 共通ルールは `AGENTS.md` に従う。


---


## 2. Commands
基本コマンドは以下とする。

```bash
pnpm dev
pnpm build
pnpm preview
pnpm test
```

依存追加は `pnpm add` を使用する。

```bash
pnpm add package-name
pnpm add -D package-name
```



---


## 3. Recommended Structure
```txt
frontend/
├─ src/
│  ├─ lib/
│  │  ├─ presentation/
│  │  │  ├─ components/
│  │  │  └─ pages/
│  │  ├─ state/
│  │  │  └─ stores/
│  │  ├─ application/
│  │  │  └─ usecases/
│  │  ├─ infrastructure/
│  │  │  └─ api/
│  │  └─ shared/
│  │     ├─ types/
│  │     ├─ constants/
│  │     └─ utils/
│  ├─ routes/
│  ├─ app.html
│  └─ main.ts
├─ tests/
├─ package.json
├─ pnpm-lock.yaml
├─ .env
└─ .env.example
```

SvelteKit を使用する場合は `routes/` を優先する。
通常の Svelte + Vite の場合は `main.ts` 起点で構成する。



---


## 4. Layer Rule
Frontend は以下のレイヤー構造を守る。

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

| レイヤー | 役割 |
| --- | --- |
| Presentation | UI表示、イベント受け取り、画面構成 |
| State | UI状態、ストア、画面状態管理 |
| Application | ユースケース、画面から呼ばれる処理 |
| Infrastructure | API通信、外部I/O、ブラウザAPI |
| Shared | 型、定数、共通関数 |



---


## 5. File Policy

### コンポーネント
- コンポーネントは `.svelte` とする。
- `<script>` に表示制御ロジックを書く。
- `<style>` にそのコンポーネント固有のスタイルを書く。
- 複雑なロジックは `.svelte` 内に閉じ込めず、外部ファイルへ分離する。

### 単一コンポーネント制限
- 300行を超える `.svelte` コンポーネントは禁止。
- API通信、状態管理、表示、業務ロジックを全部1ファイルに入れない。


---


## 6. Separation Rules
以下は必ず外部ファイルへ分離する。

- API通信
- 共通関数
- 定数
- 型定義
- 状態管理ロジック
- ビジネスロジック
- データ変換処理
- バリデーション処理
- 複数画面で使う処理


---


## 7. API Communication Rule
API通信は `infrastructure/api/` に置く。

```txt
frontend/src/lib/infrastructure/api/
├─ client.ts
├─ endpoints.ts
└─ userApi.ts
```

禁止事項:

- `.svelte` ファイルから `fetch()` を直接呼ぶこと。
- API URL をコンポーネントに直接書くこと。
- レスポンス形式を UI 側に密結合させること。
- エラーハンドリングを画面ごとに重複させること。


---


## 8. Application Rule
画面から呼ばれる処理は `application/` に置く。

```txt
frontend/src/lib/application/usecases/
├─ loadUsers.ts
├─ createReport.ts
└─ updateSchedule.ts
```

Application 層では以下を行う。

- Infrastructure の API を呼ぶ。
- 必要なデータ変換を行う。
- State に渡しやすい形に整える。
- UI に依存しない処理を書く。


---


## 9. State Rule
状態管理は `state/` に置く。

```txt
frontend/src/lib/state/
└─ stores/
   ├─ userStore.ts
   ├─ reportStore.ts
   └─ uiStore.ts
```

方針:

- UI状態と業務状態を混ぜない。
- 複数画面で使う状態は store 化する。
- 単一コンポーネントだけの一時状態は `.svelte` 内でよい。
- API通信を store に直接書きすぎない。
- 複雑な処理は Application 層へ分離する。


---


## 10. Presentation Rule
Presentation 層は UI に集中する。

やってよいこと:

- props の受け取り
- イベント発火
- 表示分岐
- 軽い UI 状態
- class の切り替え
- フォーム入力の受け取り
やってはいけないこと:

- API通信
- DB 相当の処理
- 複雑な業務判定
- 複雑なデータ変換
- 大量の状態管理
- 環境変数の直接多用


---


## 11. Shared Rule
Shared には全層から参照してよい共通要素を置く。

```txt
frontend/src/lib/shared/
├─ types/
├─ constants/
└─ utils/
```

| 種別 | 配置例 |
| --- | --- |
| 型 | `shared/types/user.ts` |
| 定数 | `shared/constants/routes.ts` |
| 共通関数 | `shared/utils/formatDate.ts` |



---


## 12. Environment Variables
frontend の環境変数は `frontend/.env` に置く。

```env
VITE_API_BASE_URL=http://localhost:8000
```

必須ルール:

- frontend の環境変数は `VITE_` 接頭辞を使う。
- frontend に秘密情報を置かない。
- APIキー、DB接続情報、秘密鍵、NAS認証情報は禁止。
- ブラウザから見えてよい値だけ置く。
- `.env.example` を用意する。


---


## 13. Styling Rule
スタイルは以下の優先順位で扱う。

1. コンポーネント固有の軽いスタイルは `<style>` に書く。
2. 共通スタイルは shared または global 側へ分離する。
3. Tailwind を使う場合は、過剰な class の肥大化に注意する。
4. 複雑なスタイルはコンポーネント分割を検討する。
禁止事項:

- 1つの `.svelte` に巨大な style を書くこと。
- 同じスタイルを複数箇所に重複記述すること。
- 意味不明な class 名を使うこと。


---


## 14. Component Rule
推奨:

- 小さいコンポーネントに分ける。
- props の意味を明確にする。
- 表示専用コンポーネントとロジック持ちコンポーネントを分ける。
- 再利用する UI は `components/` に置く。
- ページ固有の UI は `pages/` または route 配下に置く。
禁止:

- 1コンポーネントに複数責務を持たせること。
- 300行を超える巨大コンポーネント。
- API通信、状態管理、表示、業務ロジックを全部1ファイルに入れること。


---


## 15. Type Rule
TypeScript を使用する場合、型定義は `shared/types/` に置く。

- APIレスポンス型を明確にする。
- UI用型と API 用型を必要に応じて分ける。
- `any` の多用は禁止。
- 変換が必要な場合は Application 層で行う。


---


## 16. Testing
```bash
pnpm test
```

優先してテストするもの:

- Application 層
- データ変換処理
- バリデーション
- APIレスポンスの整形
- 複雑な状態管理
必須でないもの:

- UI表示のみ
- CSSのみ
- 試作画面
- 一度きりの画面
UIテストは必須ではない。
ただし、業務上重要な画面はテスト導入を検討する。



---


## 17. 判断基準
迷った場合は以下を基準に判断する。

| 判断 | 置き場所 |
| --- | --- |
| 表示だけ | Presentation |
| UI状態 | State |
| 業務処理の流れ | Application |
| API通信 | Infrastructure |
| 型 | Shared / types |
| 定数 | Shared / constants |
| 共通関数 | Shared / utils |



---


## 18. 最重要ルール
Svelte コンポーネントは UI のための場所であり、アプリ全体の処理を詰め込む場所ではない。
API通信、状態管理、業務ロジック、型定義、定数、共通関数は必ず外部化する。

