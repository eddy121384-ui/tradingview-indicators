# AGENTS.md

This repository is designed to be maintained with AI coding agents such as Codex, Claude Code, or other assistants. Follow these rules when editing the project.

## Project identity

Project name: TradingView Indicators

Purpose: build and maintain a private, AI-readable Pine Script indicator and strategy laboratory for TradingView indicators, specs, release notes, multilingual publishing copy, and review workflows.

The project focuses on TradingView Pine Script indicators and strategies, including market-regime tools, Wyckoff-style structure maps, macro pressure maps, fear/greed-style reconstructions, MTF validation, divergence logic, dashboard/UI polish, and publish-ready documentation.

Do not turn this repository into a generic quant platform, brokerage system, Bloomberg clone, or full pricing workbench. Keep the scope centered on TradingView scripts, indicator specifications, chart behavior, testable logic, and publishable documentation.

## Source of truth

GitHub is the source of truth for executable specs, Pine Script code, issues, tests/checklists, release notes, and architecture decisions that affect implementation.

Notion or chat may be used as a discussion hub, draft space, and cross-AI handoff layer, but drafts must be converted into GitHub docs, issues, or PR notes before implementation.

## Required reading map

Before coding, read the smallest relevant set of files.

Always start with:

1. `README.md`, if it exists.
2. The relevant issue or spec document.
3. The Pine Script file being edited.
4. Any related release note, publishing copy, or prior implementation notes.

Then read the relevant domain material if present:

- Indicator behavior or user-facing requirements: `docs/`, `specs/`, or issue body.
- TradingView publication copy: release or publishing docs.
- Backtest or strategy behavior: strategy-specific spec and source file.
- UI/dashboard/color/translation changes: visual or i18n-related spec sections.
- Review process: any PR review rubric or agent review instructions in the repo.

Prefer the newest explicit GitHub issue/spec over older chat-derived notes.

## Current priority

The current priority is not maximum feature count.

The durable milestone is a clean AI-agent workflow for TradingView indicator development:

- clear issue and spec before non-trivial changes;
- small scoped Pine Script edits;
- deterministic indicator logic;
- explicit assumptions and limitations;
- chart behavior that matches the spec;
- simple review and test checklist;
- publish-ready documentation when releasing public indicators.

## Engineering rules

1. Keep indicator logic explicit and readable.
2. Do not add broad refactors unless requested.
3. Do not change user-visible behavior silently.
4. Do not rename inputs, plots, labels, alerts, or dashboard fields unless the spec requires it.
5. Preserve backward compatibility where reasonable, especially for published indicators.
6. Add or update comments only when they explain trading assumptions, Pine Script constraints, MTF mechanics, divergence logic, or non-obvious implementation choices.
7. Do not fabricate market data, screenshots, TradingView behavior, backtest performance, or publication results.
8. Do not commit secrets, real account data, internal bank data, client information, real positions, or private market data.
9. Keep examples synthetic unless the user explicitly provides public data.
10. For MTF logic, avoid future leak/repainting unless the spec explicitly allows it and the limitation is documented.
11. For signals, backgrounds, alerts, or strategy entries, state whether behavior is confirmed-bar, intrabar, repaint-prone, or non-repainting.
12. For dashboards and labels, keep text compact enough for TradingView chart use.
13. For multilingual content, keep Chinese, English, Japanese, and Korean versions aligned in meaning.
14. For public TradingView release copy, avoid promising profit, win rate, predictive certainty, or financial advice.
15. Prefer boring, explicit Pine Script over clever code golf.

## Financial and trading correctness rules

Indicators and strategies must come from deterministic script logic, not LLM reasoning.

LLMs may assist with:

- turning rough trading ideas into specs;
- writing or editing Pine Script;
- explaining indicator output;
- drafting publication copy;
- proposing chart test cases;
- reviewing implementation against a spec;
- identifying repaint, MTF, signal, or UI risks.

LLMs must not fabricate:

- TradingView screenshots or chart outcomes;
- backtest results;
- live market data;
- profit expectations;
- risk metrics;
- user adoption or publication performance.

If a change affects trading interpretation, explicitly state the assumption, limitation, and expected chart behavior.

## Suggested workflow for agents

Before coding:

1. Restate the target issue or spec section.
2. Identify the relevant Pine Script file and docs.
3. State the expected user-visible chart behavior.
4. State assumptions that may affect trading interpretation, repainting, MTF behavior, alerts, or strategy results.

When implementing:

1. Start with the smallest useful version.
2. Keep logic, visual output, alerts, inputs, and documentation consistent.
3. Avoid broad style churn.
4. Preserve existing behavior unless the issue asks to change it.
5. Update docs or release notes when behavior changes.
6. Use explicit names for intermediate calculations when readability helps review.

When proposing larger changes:

1. Create or update an issue first.
2. State the trading/interpretation assumption affected.
3. State expected chart behavior.
4. State test coverage or manual chart-check coverage.
5. State remaining risks.

When opening or updating a pull request:

Leave a self-contained GitHub PR conversation comment that is understandable without reading the private chat session. Include the target issue/scope, changed files, implementation summary, tests and chart checks run with results, known limitations, explicitly deferred work, and any assumptions that affect trading interpretation, repaint behavior, MTF behavior, alerts, or strategy results.

## Reviewing a pull request

When reviewing with Codex, Claude, or any AI reviewer:

- Ground every finding in the actual diff. Do not comment on code the PR does not change, and do not invent problems.
- Apply only the review lenses relevant to the diff: Pine Script correctness, trading interpretation, MTF/repaint behavior, UI/readability, documentation, and publication safety.
- Prefer concrete blockers, edge cases, missing chart checks, broken contracts, misleading output, repaint risk, and publication-risk issues over generic advice.
- Use severity consistently: P0/P1 for wrong signal logic, future leak, repaint not disclosed, broken published behavior, fake results, data leakage, or safety issues; P2 for missing edge cases, unclear failures, missing checks, likely maintenance risk; P3 for naming, docs, and small cleanups.
- Keep reviews short by default. A clean PR can be approved briefly.

## Style preference

The codebase should be boring, explicit, and easy for another AI to edit. This is a feature, not a weakness.
