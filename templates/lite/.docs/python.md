# Python の既定

既存プロジェクトに別の管理方式があれば、そちらを優先する。

- パッケージ管理は `uv`。`pip` 単独使用、`poetry` 併用、`requirements.txt` の手動管理はしない。
- 継続して使うツールは `pyproject.toml` / `uv.lock` で管理し、lock は Git 管理する。依存追加は `uv add`、実行は `uv run`。
- 単一ファイルのスクリプトは PEP 723 のインライン依存を書き、`uv run script.py` で実行してよい。依存追加は `uv add --script script.py <pkg>`。
- 管理環境を迂回した直接実行はしない（`uv run python` は可）。
- テストを書く場合は `pytest`（`uv run pytest`）。単発スクリプトは実データでの実行結果による確認でもよい。
- Excel・CSV を更新する処理は、元ファイルを上書きせず別名で出力することを既定とする。
