# Claude Code Instructions

@AGENTS.md

Claude Code should treat `AGENTS.md` as the shared repository constitution. This file only adds Claude-specific workflow guidance.

## Working model

TradingView Indicators is an AI-native Pine Script indicator and strategy repository, not a one-off script dump.

The long-term scope includes TradingView Pine Script indicators, strategy prototypes, market-regime tools, Wyckoff-style structure maps, macro pressure maps, fear/greed-style reconstructions, MTF validation, divergence logic, dashboard/UI polish, multilingual release copy, and publish-ready documentation.

Do not attempt to implement the entire vision at once.

## Before coding

Read the smallest relevant set of documents before editing code:

1. `AGENTS.md`
2. `README.md`, if it exists
3. The relevant GitHub issue or spec
4. The Pine Script file being edited
5. Any relevant release note, publishing copy, or prior implementation note

For indicator behavior changes, also read any relevant spec under `docs/`, `specs/`, or issue-linked notes when they exist.

## Execution workflow

For non-trivial changes:

1. Restate the target issue or spec section.
2. Propose a short implementation plan.
3. Identify the files or modules that will change.
4. Implement the smallest useful version.
5. Add or update deterministic checks where practical.
6. Run available checks, linting, or manual chart-review checklist if the environment supports it.
7. Summarize changed files, assumptions, test/check results, and remaining risks.

## Financial and trading correctness rules

Indicator and strategy behavior must come from deterministic Pine Script logic, not LLM reasoning.

LLMs may help with:

- turning rough trading ideas into specs;
- writing Pine Script;
- explaining indicator output;
- drafting TradingView publication copy;
- proposing chart test cases;
- reviewing implementation against a spec;
- identifying repaint, MTF, signal, alert, or UI risks.

LLMs must not fabricate market data, chart screenshots, backtest results, win rates, TradingView publication performance, or trading validation evidence.

## Implementation boundaries

Do not silently change existing indicator behavior.

Do not rename user-facing inputs, plots, alerts, dashboard fields, or labels unless the issue explicitly asks for it.

Do not introduce repainting, future leak, or MTF lookahead behavior unless the spec explicitly allows it and the limitation is documented.

Do not commit secrets, real account data, internal bank data, client information, real positions, or private market data.

## Preferred output style for Claude Code

When responding after code changes, include:

- what changed;
- why it changed;
- how to run, test, or manually check it;
- what assumptions were made;
- what remains unfinished.

Be explicit and boring. In this repo, boring code is a feature.

Always summarize what changed in GitHub itself, not only in chat.

## GitHub PR execution report requirement

After opening or updating any pull request, Claude Code must leave a top-level GitHub PR comment with a self-contained execution report.

Do not rely only on the chat reply. The GitHub PR conversation should contain the audit trail.

The PR comment must include:

1. PR / Branch
   - PR number
   - Branch name
   - Base branch
   - Related issue number, if any

2. Intent
   - What this PR is trying to accomplish
   - Why the change exists

3. Files changed
   - Main files changed
   - One short note per file

4. What changed
   - Specific implementation or documentation changes

5. What intentionally did not change
   - Explicit scope boundaries
   - Anything deferred or intentionally left untouched

6. Tests / checks
   - Exact commands or manual chart checks run
   - Exact results
   - If tests were not run, explain why

7. Review status
   - Whether Codex review was requested
   - Whether prior Codex findings were addressed
   - Whether human review is still needed

8. Issue status
   - Related issue status after this PR
   - Whether the issue should remain open or can be closed

9. Follow-up work
   - What should happen next
   - What remains out of scope

The report should be understandable from GitHub alone, without requiring external chat context.
