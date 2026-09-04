# Issue #68 Phase B3.15 — Mechanical PASS / Rates Human-Review Gate

Status: **mechanical PASS; frozen C-2; no parameter change; rates human review next**.

## Mechanical result

B3.15 reproduced the exact B3.14/B3.10 Break-final-blocker population:

- 106 / 106 events;
- reproduction delta 0;
- reciprocal population-label agreement 100%;
- reciprocal uncensored timing agreement 100% (122/122).

The preregistered blocker-clock split is essential:

- `MA_TARGET_AT_BLOCKER`: 20 / 106 (18.9%);
- `PRE_MA_FLIP_AT_BLOCKER`: 86 / 106 (81.1%).

Therefore stale memory after an MA turn is **not** a universal explanation for all Break blockers. Most blockers occur before the MA relation itself has moved to the target side.

## Primary stale-memory population

For the 20 events where MA was already on the target side at `t-1`:

- event-related MA flip found: 20 / 20;
- old range-memory survival, uncensored only: median 11 bars, p75 15, max 16; 7 uncensored / 13 censored;
- target range-evidence delay: median 1 bar, p75 2, max 5; 14 uncensored / 6 censored;
- Break release delay: median 11 bars, p75 15, max 16; 7 uncensored / 13 censored;
- stale-overlap bars (`MA target + old range memory`): 166;
- Break remains old-negative on 105 / 166 stale-overlap bars (63.3%);
- Break is target-positive on only 4 / 166 stale-overlap bars; zero on 57 / 166;
- where both target-range formation and old-memory clearing are observed, target range appears first in 7 / 7 cases.

## Interpretation

B3.15 materially strengthens the **stale old range-memory mechanism for the narrow primary population**.

The strongest evidence is not simply that old memory exists. It is the timing relationship:

1. MA has already moved to the new side;
2. target range evidence, when observable, usually forms quickly;
3. old range memory often remains active much longer;
4. Break continues to vote old or neutral through most of that overlap;
5. uncensored Break-release timing matches old-memory survival timing closely in the aggregate primary summary.

This is consistent with old range evidence mechanically suppressing fresh Break handoff even after other trend context has started to turn.

However this does **not** establish that `breakoutBars=20` is too long. Thirteen of the 20 primary cases are right-censored because the target-side MA run ends before old memory clears. Exact memory lifetime is therefore not identified, and no decay parameter should be changed from this result alone.

It also does not explain the other 86 / 106 blocker events, because those occur before the MA side has flipped. Break remains a partial handoff mechanism, not a universal reversal-lag explanation.

## TradingView audit artifact

Use:

`indicators/wyckoff-regime-radar/research/generated/wyckoff-issue68-phase-b315-event-window-stale-memory-audit.pine`

Bands:

1. `BREAK EDGE` — green target / red old;
2. `MA TARGET SIDE` — green when current MA relation is on the audit target side;
3. `OLD RANGE MEMORY` — red while old-side range-break memory is alive;
4. `STALE OVERLAP` — yellow when MA is target-side but old range memory remains alive;
5. `NEW RANGE EVIDENCE` — green when target range evidence exists;
6. `BREAK OLD DURING OVERLAP` — red only when stale overlap is active and Break still votes old;
7. `MA FLIP` — aqua target-side MA transition pulse;
8. `BREAK FINAL BLOCKER` — orange handoff event.

## Locked human-review cases

Review without changing inputs:

- **FR10Y 1D, 2021–2024, Bull** — primary adverse case;
- **JGB10Y 1D, 2021–2024, Bull** — rates control;
- **EURUSD 1D** — FX/control context if needed.

## Human-review question

Around adverse handoffs, especially orange Break-blocker events:

- after the aqua MA flip, does yellow stale overlap persist for multiple bars?
- while yellow persists, does the red `BREAK OLD DURING OVERLAP` band remain active?
- does green `NEW RANGE EVIDENCE` appear before old range memory clears?
- in mature right-side Bull regimes, do old-memory and red-overlap bands eventually clear cleanly as B3.14 already suggested?

### Interpretation guide

- **Rates show the same sustained yellow + red overlap around adverse handoffs:** stale old range memory remains a credible rates handoff-delay mechanism. Proceed to a later mechanism-design phase, still with no tuning/PnL.
- **Yellow persists but red Break-old overlap clears quickly:** memory may be stale visually but not mechanically decisive; demote the mechanism.
- **Orange blocker events mostly occur before aqua MA flip:** rates behavior resembles the 86-event contextual population; stale-after-turn is not the main adverse mechanism.
- **FR10Y fails to show the mechanism while controls do:** reject stale memory as the primary rates fix, as with B3.13 Structure shadow.

## Hard boundary remains

Do not change `breakoutBars`, Break weight, MA length, thresholds, lifecycle, Core Bias, Exposure, Volume/MTF/Divergence/HMM, or inspect PnL from this phase.

PR #73 remains Draft/Open. Issue #68 remains Open.
