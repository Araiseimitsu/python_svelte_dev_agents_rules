---
name: app-idea-map
description: Turn a fuzzy new-app or feature idea into a lightweight requirements map and short brief through a one-question-at-a-time conversation. Use when the user wants to clarify what to build before implementation; do not use when a detailed specification is already complete or when the request is simply to implement it.
license: MIT
metadata:
  category: development
  summary: 曖昧なアプリ案や機能案を対話形式で整理し、軽量な要件マップと概要を作成する
  summary_en: Turn fuzzy app or feature ideas into a lightweight requirements map and brief through dialogue.
---

# App Idea Map

Clarify an app idea without turning the conversation into a long interview. Keep the map useful to both the person requesting the work and the person implementing it.

## Start

Begin from the user's own description. If none exists, ask only: 「何を作りたいですか？」

Infer whether the request is a new app or a feature for an existing app. Ask which only when the conversation does not make it clear. For a feature, distinguish the current behavior from the requested change.

Before asking anything, fill every state field supported by the existing conversation or project evidence. Read [references/state-schema.md](references/state-schema.md) when creating or updating the state.

## Interview

- Ask exactly one question per turn.
- Prefer a short, easy-to-answer question. Offer two or three concise choices when that reduces effort, while allowing a free-form answer.
- Never ask for information that is already known or can be safely inferred from provided project context.
- Choose the unanswered item most likely to change the finished product. Typical priority is audience, problem, desired outcome, main flow, screens or information, scope, then constraints.
- Aim for four to eight user-facing questions in total. Do not ask filler questions to reach a count, and do not exceed eight unless the user explicitly asks to continue.
- After each answer, summarize only the newly settled decision, update the state, generate the next version of the map, show it, and then ask the next question.

Stop the ordinary interview when the idea, audience, problem, desired outcome, and at least one main flow are clear and no open issue would cause two implementers to build materially different products. Screens, constraints, and exclusions are conditional: ask about them only when they affect the result.

## Map Versions

Use a task-owned writable working directory such as `work/app-idea-map/<session-name>/`. Keep one predictable current file while every version stays recoverable:

- `map.html` is the current map. It is overwritten on every update.
- `history/state-vNN.json` and `history/map-vNN.html` are the immutable record of each version.

For each update:

1. Write normalized UTF-8 JSON as `history/state-vNN.json`, setting `version` to the same number.
2. Run `python scripts/render_map.py history/state-vNN.json history/map-vNN.html --live map.html` from this skill directory, using the absolute script path when the current directory differs.
3. On the first version, provide a clickable link to `map.html`. Afterwards say that the same file was updated and ask the user to reload the page if it is already open. Do not automate or control a browser.

Never reuse a version number or overwrite an existing state or history map. Only `map.html` is ever replaced. If rendering fails, keep the state and earlier maps, explain the useful cause briefly, and continue the interview only when the user's answer is safely preserved.

The HTML has no live-reload script and works as a local file. Never assume an open viewer notices file changes automatically.

## Ordinary Finish

Produce both:

- `map.html`, the latest self-contained HTML requirements map, plus its immutable snapshot in `history/`;
- a short Markdown brief covering the idea, audience, problem, desired outcome, main flow, relevant screens or information, scope, constraints, and any explicitly accepted open questions.

Keep the brief compact enough to scan before implementation. Then ask once whether the user wants to deepen it into an implementation specification. End unless they explicitly opt in; do not begin implementation automatically.

## Optional Deepening

When the user opts in, continue one question at a time only for implementation-critical details such as acceptance criteria, failure states, data boundaries, integrations, or rollout constraints. Preserve the ordinary map and brief as the agreed product intent, and create separate deeper artifacts rather than rewriting them in place.
