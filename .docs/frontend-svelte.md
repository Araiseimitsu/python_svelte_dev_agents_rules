# Frontend — Svelte / Vite / SvelteKit

該当技術の作業時に参照する。共通方針と安全確認は `AGENTS.md` に従う。

## 1. 起動・検証

`frontend/` の `package.json` と設定済みスクリプトを確認して `pnpm` で実行する。`dev`、`build`、`test`、`check`、`lint` などの存在を確認し、未定義のコマンドを前提にしない。
依存追加は `pnpm add`（開発用は `pnpm add -D`）。承認範囲は `AGENTS.md` §14。

## 2. 構成

通常の Svelte + Vite は既存の `main.ts` 等を起点とし、SvelteKit は `src/routes/` とその規約を使う。両者の起動ファイルを混ぜて生成しない。
新規構成では、必要に応じて `src/lib/` に `presentation/`、`state/`、`application/`、`infrastructure/`、`shared/` を置く。空の階層を先に作らず、既存プロジェクトの構造を尊重する。

## 3. 責務と依存

| 責務 | 内容 |
| --- | --- |
| Presentation | 表示、入力、イベント、一時的な UI 状態 |
| State | 複数箇所で共有する状態、画面の状態遷移 |
| Application | ユースケース、業務処理の流れ、必要な変換 |
| Infrastructure | API 通信、外部 I/O |
| Shared | 複数箇所で使う型・定数・純粋な共通処理 |

依存は `Presentation → State → Application → Infrastructure` を基本とする。状態共有が不要なら Presentation から Application を呼んでよい。業務処理や変換が無い単純取得は State から Infrastructure を呼んでよい。空のラッパーを強制しない。
Presentation から業務 API を直接呼ばない。コンポーネントの表示・フォーカス・サイズ計測に必要な DOM / ブラウザ API は、そのコンポーネント内で扱ってよい。
Shared は上位層に依存させず、何でも集める置き場にしない。

## 4. コンポーネントと状態

- 単一コンポーネントだけで使う短い型・定数・一時状態・表示補助は同居してよい。
- 複数箇所で共有する処理・状態、複雑な業務ロジック、API 通信は責務に応じて分離する。
- 型はまず責務の近くに置き、共有が必要なものだけ共通化する。API 型と UI 型は必要な場合に分ける。
- 既存の Svelte バージョンと状態管理方式を確認し、新旧記法の移行を依頼外で行わない。
- コンポーネントの分割基準は `AGENTS.md` §11。行数だけを減らす分割をしない。

## 5. API と環境変数

API クライアントは `infrastructure/api/` 等の既存の正本に集約し、URL や共通エラー処理を画面ごとに重複させない。
入力検証の Backend / Frontend の役割は `AGENTS.md` §8 に従う。
環境変数は使用するフレームワークと既存設定の公開方式を確認する。Vite の公開値は `VITE_` を基本とするが、SvelteKit に機械的に同じ方式を強制しない。秘密情報の扱いは `AGENTS.md` §9。

## 6. スタイルと検証

固有のスタイルはコンポーネント、共有するものは既存の共通スタイルに置く。UI ライブラリや CSS 方式を依頼なく置き換えない。
検証対象は `AGENTS.md` §12、完了条件は `.docs/workflow.md` §2 を参照する。変更した画面は必要な画面幅で確認し、操作変更は正常時だけでなく関連する読み込み・空状態・エラー時も確認する。
