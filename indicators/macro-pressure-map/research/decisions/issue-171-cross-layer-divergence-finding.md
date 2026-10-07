# Issue #171 — Cross-layer recovery divergence autopsy — finding

- Issue: [#171](https://github.com/eddy121384-ui/tradingview-indicators/issues/171)
- Branch: `research/issue-171-cross-layer-divergence-autopsy` (isolated worktree)
- Base: `b2f82c2311b7d501eb45623bcb668680f8d884db` (Issue #169 final)
- Formal verdict: `cross_layer_divergence_joint_and_rotating`
- `outcome_data_loaded=false`
- `production_authorized=false`
- SIGNAL ONLY: no return file opened at any stage (DH macro CSV + V6.6
  snapshot only). No thresholds, windows, weights, or labels changed. No Pine
  changed. No merge. #167/#169 verdicts unaltered.

## 1. Reconstruction (frozen rules, hashes verified)

- DH CSV SHA256 `42516418…` OK; snapshot SHA256 `1d039235…` OK (388 months,
  1994-05 → 2026-08, zero gaps).
- DH: 801 months, 723 full, 70 episodes, **27 triggers** (matches frozen count).
- Exact: 55 episodes, **14 triggers** (matches frozen count).
- Common valid months: **385** (1994-05 → 2026-08; the 3 DH gap months
  2025-10/11, 2026-01 excluded). DH triggers in common: 15; pre-common
  (1967–1993, no exact coverage): 12, listed separately, not classified.

## 2. Event classification (frozen ±3M greedy matching)

- MATCHED: **5** (lags −3,−3,−2,+2,+3; median −2; DH-first 2, exact-first 3).
- DH_ONLY: **10**. EXACT_ONLY: **9**.
- Divergence labels: both_trajectories 7, state_only 6, growth_only 2,
  inflation_only 2, timing_only 2 (both matched: 2009-01/03 GFC, 2019-08/10),
  state+inflation 2, state+growth 2, state+both 1.

## 3. Which axis dominates (event-level attribution, not correlation)

Over 19 divergent singletons (all determinate, no na):
- Growth-involved: **13/19 (0.68)**; Inflation-involved: **16/19 (0.84)**;
  both: **10/19 (0.53)**.
- DH-only split: Growth 7/10, Inflation 8/10. Exact-only split: Growth 6/9,
  Inflation 8/9. Matched onset agreement: Growth 2/5, Inflation 3/5.
- Verdict rule (documented operationalization of the semantic definitions):
  determinate ≥ 2/3 required; growth ≥ 0.60 with infl < 0.40 (or mirror) for
  single-axis dominance. Observed 0.68 / 0.84 → neither dominance condition
  met → **joint_and_rotating**. The related component and lead/lag evidence
  below corroborates rotation rather than a stable single-axis cause.

## 4. Where the divergence lives (narrative from the event table)

- **State_only (6), all inflation-boundary cases:** five DH-only months where
  market-implied IPI runs hot (> +10: 1999, 2003, 2020, 2023 episodes) while
  realized DH inflation stays cool, plus the mirror image (2001: DH-I > +10
  while breakeven-implied IPI stays calm, exact triggers alone). The ±10
  state boundary cuts the two inflation reads differently.
- **Both_trajectories (7, largest class):** both layers eligible but 3M
  momenta point opposite ways — e.g. 1998-12 (DH recovering +/+ as LTCM
  stress passes in realized data while market ratios still fall −/−);
  2022-12 (mirror: markets rebound while realized data deteriorate).
- **Single-axis trajectory cases (2+2)** and state-plus mixes (2+2+1) are
  scattered across decades with no recurring signature.
- **Timing_only (2)** are genuine cross-episode near-coincidences, not the norm.

## 5. Lead/lag: no stable ordering, slight exact-first tilt

Positive-d3 onsets, common period, complete (no-window) profiles:
- Growth (77 onsets): DH-first 24, same 14, exact-first 39; median **−1**,
  mean −0.43; mass concentrated ±3.
- Inflation (55 onsets): DH-first 11, same 13, exact-first 31; median **−1**,
  mean −0.67.
- Whole-trigger matched pairs: median −2, mean −0.6 (2 DH-first, 3 exact-first).
Neither layer systematically leads; if anything the market-implied layer turns
marginally earlier on both axes, consistent with fast market repricing vs slow
realized data — but the tilt is small (±1 month medians) and rotation across
episodes dominates any sequence claim.

## 6. Component attribution

- DH-side improvements are broad-based: at the 10 DH-only triggers, positive
  3M changes count g5:10, g3:8, g1:7, g2:6, g4:3 on Growth and i3/i5:9,
  i1/i2:8, i4:7 on Inflation. Real disposable income (g4) joins least often;
  no component dominates; energy is not the driver.
- Delayed-DH and matched cases show the same spread (no component signature).
- Exact V6.6 components: **unavailable as frozen artifacts** — checked
  143/145/59 result artifacts (bridge/attribution models, not exact-component
  histories) and the parity-sources pine (input tickers, not histories);
  deterministic reconstruction would require new market data (forbidden).
  Analysis continues at composite GPI/IPI level; per contract this alone is
  not a failure.

## 7. Economic interpretation of the two layers

- **Deep-History** = slow realized-macro state (60-month z-scores of
  output/labor/housing/income/surveys and price/wage/energy YoY on revised
  history): persistent, smooth, turning late.
- **Exact V6.6** = fast market-implied state (z-scores of cross-sectional
  equity/bond/commodity ratios, breakeven, credit/vol): reactive, whipsawing
  around the same episodes.
- Divergence concentrates (a) at the inflation state boundary where the two
  inflation reads disagree, and (b) in transition months where 3M momenta
  oppose. Neither axis, layer order, nor component set is stable across
  episodes — hence joint-and-rotating. No allocation recommendation follows.

## 8. Artifacts

- `research/issue_171_divergence_autopsy.py` (frozen evaluator, pure stdlib)
- `research/test_issue_171_divergence_autopsy.py` (synthetic-only tests +
  frozen-count integration with skip)
- `research/generated/issue-171/divergence-events.csv` (24 events, 22 columns)
- `research/generated/issue-171/growth-axis-attribution.csv`
- `research/generated/issue-171/inflation-axis-attribution.csv`
- `research/generated/issue-171/divergence-components.csv` (event × component rows)
- `research/generated/issue-171/lead-lag-summary.json`
- `research/generated/issue-171/divergence-summary.json` (counts, dominance, verdict)
- This finding.

## 9. Tests / validation evidence; bugs found and fixed

- Python suite: state/d3 boundaries, positional d3 + NaN, first-trigger +
  episode-break semantics, greedy window/tie/reuse matching, all 8 labels +
  na-fallthrough, lead/lag sign convention, onset sign-change rule, verdict
  branches incl. the 2/3 boundary, determinism, snapshot-hash rejection, and a
  repo-file integration asserting 27 DH triggers (skipped when absent).
  Committed without local execution (no Python runtime on this machine); every
  numeric vector was cross-derived through the executed Node mirror, which
  caught and fixed one wrong hand-computed trigger expectation pre-commit.
- Node mirror: frozen counts reproduced exactly (27/14/5/10/9); dominance
  fractions independently recomputed from the events file (identical);
  rerun-determinism holds (pure functions, no RNG in this issue).
- Bugs fixed before finalization: (1) CRLF header parse zeroing the entire I5
  column (phantom "energy exonerated" — caught by the all-5-finite
  composite-consistency check); (2) a group-mean double-count for
  single-member groups; (3) a `kind` vs `event_class` column-name mismatch that
  emptied trigger matching (caught by the 5-match anchor); (4) dead
  stub/parameters removed from committed files.

## 10. Explicit flags

`outcome_data_loaded=false` (no return, wrapper, payoff, or conditioned file
opened; #167/#169 payoff-bearing artifacts never read — triggers recomputed
from macro sources). `production_authorized=false` (research files only).
Do not merge.
