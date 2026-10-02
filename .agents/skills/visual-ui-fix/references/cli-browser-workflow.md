# CLI・IDEからのブラウザ操作

## 実行手段の選択

1. Kimi WebBridge Skillが利用可能なら、その`SKILL.md`を読み、必須のhealth checkを行う。
2. `running: false`ならKimi WebBridgeの運用手順に従ってデーモンを起動する。
3. `extension_connected: true`になった場合は、同梱の`kimi_visual_ui.py`を使用する。
4. Kimi WebBridgeが未導入または拡張機能未接続なら、環境が提供するPlaywright・ブラウザツールを確認する。対話可能な実ブラウザを維持できない場合は、注釈付き画像による代替をユーザーへ説明する。

Kimi WebBridgeのインストールやブラウザ拡張機能の追加は、ユーザーの承認なしに行わない。既に導入済みのデーモン起動は通常の準備として扱う。

## Kimi WebBridge経路

Skillディレクトリを`<skill>`、対象URLを`<url>`とする。

```text
python <skill>/scripts/kimi_visual_ui.py open <url>
```

このコマンドは次を行う。

- Kimi WebBridgeの状態確認と、停止中の場合の起動
- `visual-ui-fix`セッションで新規ブラウザタブを表示
- `assets/visual-ui-overlay.js`の一時注入

ブラウザに表示された`Select element`を有効にし、対象要素をクリックする。テキスト、文字色、背景色、padding、幅、高さ、X・Y方向の移動量、自由コメントを入力し、`Preview`で表示を確認してから`Save`する。複数箇所を続けて指定できる。

ツールバーが対象画面に重なる場合は、`Visual UI Fix`の文字部分をドラッグして移動する。ツールバーはブラウザの表示領域外へ出ないように制限される。

Overlayはユーザーが実際に変更したフィールドだけを変更一覧へ含める。`Move X`と`Move Y`はプレビュー用の相対移動量であり、Agentはその値を恒久的な`translate`へ直結させず、既存のFlex・Grid・gap・配置制約から意図に合う実装を選ぶ。

位置・寸法を記録するため、対象を選択するときはブラウザウィンドウを表示した状態にする。最小化中などでviewportを取得できなかった変更は`collect`が拒否するため、ブラウザを前面に戻して`Discard`後に指定し直す。

ユーザーが指定を終えたら、変更一覧を取得する。

```text
python <skill>/scripts/kimi_visual_ui.py collect
```

返されたJSONは視覚的な意図を示す証拠として扱う。`target.rect`は変更前、`preview.rect`はブラウザ内プレビュー後の寸法である。selectorをそのままコードへ埋め込まず、DOMとリポジトリを対応付けて実装箇所を特定する。

ページを再読み込みするとOverlayと未取得の変更が消える。再読み込みが必要なら、先に`collect`して変更一覧を保持する。

完了時はセッションを閉じる。

```text
python <skill>/scripts/kimi_visual_ui.py close
```

複数タスクを同時に扱う場合は、サブコマンドの前に`--session <固有名>`を指定する。

```text
python <skill>/scripts/kimi_visual_ui.py --session dashboard-review open <url>
python <skill>/scripts/kimi_visual_ui.py --session dashboard-review collect
python <skill>/scripts/kimi_visual_ui.py --session dashboard-review close
```

## Playwrightフォールバック

Kimi WebBridgeを利用できず、実行環境に永続的なPlaywrightブラウザセッションが提供されている場合だけ使用する。同梱OverlayをページのJavaScriptとして評価し、`window.__visualUiFix.exportChanges()`から変更一覧を取得する。このSkillにはPlaywrightランタイムや専用ランナーを同梱していないため、実行環境側のブラウザセッションを利用する限定的なフォールバックである。

単発の`playwright screenshot`や`playwright open`だけではAgentが継続操作できない場合がある。その場合は完全対応と主張せず、スクリーンショット確認へ切り替える。

## 既知の制約

- cross-origin iframe内の要素はトップページから選択できない。必要ならiframeのURLを直接開く。
- アプリ独自のShadow DOM内部は、ページ側のイベント境界によって選択できない場合がある。
- 再読み込みやページ遷移ではOverlayが消えるため、未取得の変更は先に`collect`する。
