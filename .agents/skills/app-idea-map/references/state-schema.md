# State Schema

Use one UTF-8 JSON object per map version. Keep keys stable so the renderer and later versions remain compatible.

## Fields

```text
title: string
mode: "new_app" | "feature"
idea: string
audience: string | null
problem: string | null
outcome: string | null
current_behavior: string | null
flows: string[]
screens: string[]
constraints: string[]
scope_in: string[]
scope_out: string[]
unknowns: string[]
question_count: integer >= 0
version: integer >= 0
```

`current_behavior` is useful only for feature work. Omit no keys in a normalized state; use `null` or an empty list for unanswered optional fields.

## Meaning

- `title`: Short human-readable name for the idea.
- `idea`: One-sentence description of what will be built or changed.
- `audience`: Primary person or group using it.
- `problem`: Current difficulty or unmet need.
- `outcome`: Observable improvement the user wants.
- `flows`: Main user journeys, written as short ordered statements.
- `screens`: Essential screens, views, or information surfaces only.
- `constraints`: Real technical, operational, safety, privacy, cost, or time boundaries.
- `scope_in` and `scope_out`: Explicit product boundaries when they prevent misunderstanding.
- `unknowns`: Unresolved questions that still matter. Do not hide uncertainty.
- `question_count`: Number of user-facing interview questions asked so far.
- `version`: Version number shared by `history/state-vNN.json` and `history/map-vNN.html`.

## Artifact Layout

Keep the current render at `map.html`. Replace this file after each answer and tell the user to reload an already-open page. Do not add browser automation or live-reload code.

Keep every source state and matching HTML snapshot under `history/`:

```text
<session-name>/
|-- map.html
`-- history/
    |-- state-v01.json
    |-- map-v01.html
    |-- state-v02.json
    `-- map-v02.html
```

Never replace files inside `history/` or reuse a version number.

## Ordinary Completion

Ordinary completion requires non-empty `idea`, `audience`, `problem`, and `outcome`, plus at least one entry in `flows`. It also requires that `unknowns` contain no issue likely to make two implementers build materially different products.

Do not manufacture values to satisfy completion. Keep an item unknown or ask one concise question.

## Example

```json
{
  "title": "店舗予約アプリ",
  "mode": "new_app",
  "idea": "小さな店舗が電話対応を減らせる予約アプリ",
  "audience": "個人経営の店舗とその顧客",
  "problem": "予約を電話と紙台帳で管理している",
  "outcome": "顧客が空き時間を確認して自分で予約できる",
  "current_behavior": null,
  "flows": ["顧客が日時を選び、連絡先を入力して予約を確定する"],
  "screens": ["空き時間一覧", "予約確認"],
  "constraints": ["営業時間外の予約は受け付けない"],
  "scope_in": ["一店舗の予約受付"],
  "scope_out": ["オンライン決済"],
  "unknowns": [],
  "question_count": 6,
  "version": 1
}
```
