# Issue #68 Phase B3.17 — Mechanical Safety Result / Human Review Gate

Status: **mechanical engineering PASS / direct global release safety REJECTED pending visual confirmation**

## Locked question

B3.17 applied the exact B3.16 stale-range release shadow globally to every eligible `MA target-side + old range memory active` bar. No parameter, weight, MA length, `breakoutBars`, threshold, or non-Break component changed.

The purpose was not to improve performance. It was to determine whether the locally causal B3.16 release semantics is globally safe enough to consider as a production-style semantic change.

## Engineering gate

PASS under the preregistered gate:

- B3.16 Break / observed raw / shadow raw reconstruction retained to numerical tolerance;
- reciprocal stale-overlap eligibility agreement: **100.000%**;
- reciprocal raw-advance agreement: **99.958%**;
- reciprocal episode-outcome agreement on common advance bars: **100.000%**;
- unexplained episode accounting: **0**;
- no performance statistics were used.

Transition-count reciprocity is retained as a diagnostic output, not a preregistered hard gate: **97.619%** minimum agreement.

## Global safety result

Frozen four-FX development basket:

- eligible stale-overlap bars: **1,523**;
- raw-advance bars: **69**;
- distinct raw-advance episodes: **51**;
- followed by observed handoff in the same MA-side run: **25 / 51 (49.0%)**;
- false-release episodes: **26 / 51 (51.0%)**;
- one-bar false releases: **20 / 26 (76.9%)**;
- raw-advance episode duration: median **1 bar**, p75 **1.5 bars**, max **4 bars**;
- observed raw transitions: **746**;
- shadow raw transitions: **793**;
- transition inflation: **1.063x**;
- target NEW RANGE already present on only **20 / 69 (29.0%)** raw-advance bars;
- MA-side runs with more than one advance episode: **5**.

Per-pair false-release counts:

- EURUSD: **3 / 7** advance episodes;
- USDJPY: **13 / 19**;
- GBPUSD: **6 / 16**;
- AUDUSD: **4 / 9**.

## Mechanical interpretation

B3.16 remains valid: stale old range-memory is a confirmed **local causal brake** in the strict event-selected population.

B3.17 rejects the stronger engineering move `remove stale old range-memory globally whenever MA is target-side` as a direct production semantic rule. Globally, false releases slightly outnumber advances that later connect to an observed handoff, most false releases are one-bar events, and raw transition count rises by about 6.3%.

This is exactly the failure mode the B3.17 stop gate was designed to detect: a locally valid causal intervention does not automatically generalize into a safe global rule.

Do **not** respond by tuning `breakoutBars`, adding a durability threshold, searching a new MA length, or adding a new confirmation horizon. Those would convert a safety audit into post-result optimization.

## Final visual confirmation

Generated artifact:

`indicators/wyckoff-regime-radar/research/generated/wyckoff-issue68-phase-b317-global-false-release-churn-audit.pine`

Locked set remains:

- FR10Y 1D Bull — primary adverse case;
- JGB10Y 1D Bull;
- US10Y 1D Bull;
- EURUSD 1D Bull;
- S&P 500 1D Bull.

Existing B3.16 bands remain. B3.17 adds:

- `OBS HANDOFF` — aqua;
- `FALSE RELEASE CONFIRM` — red, confirmed at the end of a target-side MA run when one or more pending raw-advance episodes never connected to observed raw target-positive;
- `FLIPFLOP START` — fuchsia, second-or-later raw-advance episode within one MA-side run.

Human review is **not** allowed to rescue the global rule because a chart looks prettier. It only checks whether the mechanical false-release / churn classification corresponds to visually noisy or premature releases rather than an implementation error.

## Stop-gate direction

Unless the visual audit reveals a mechanical classification bug, B3.17 closes this classifier-forensic detour:

1. retain B3.16 as a documented local causal limitation;
2. reject direct global stale-range invalidation;
3. make **no B3.18 parameter/context search now**;
4. return Issue #68 to the original lifecycle / strategy-semantic research path with the frozen classifier limitation documented.

Production C-2 remains unchanged.
