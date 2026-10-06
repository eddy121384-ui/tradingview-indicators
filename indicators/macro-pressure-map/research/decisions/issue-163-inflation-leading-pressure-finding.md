# Issue #163 — Deep-History inflation axis — leading-pressure validation

- Issue: [#163](https://github.com/eddy121384-ui/tradingview-indicators/issues/163)
- Branch: `research/issue-163-inflation-leading-pressure` (isolated worktree; shared checkout untouched)
- Frozen model: Issue #160 final `cc331bf11591ab49c6f5a5023cfee39b2cf09fde`
  (DH monthly CSV SHA256 verified `42516418ec8d1ce981d1b4bc05e2ae86809d6acbf5de63dccbad515db507dcfc`)
- Formal verdict: `inflation_pressure_leading_not_supported`
- `outcome_data_loaded=false`
- `production_authorized=false`
- DH v0.1 was not altered in any source, weight, transformation, lookback,
  threshold, or scoring rule. No asset-return outcome was tested. No merge requested.

## 1. Question and frozen method

Is frozen Inflation_DH a systematic LEADING pressure measure rather than a
coincident realized-inflation measure? Primary benchmarks: CPI YoY
(`ECONOMICS:USIRYY`) and GDP-deflator YoY (causal, native quarterly, no
interpolation). Secondary: Core PCE (input-circular, disclosed) and Michigan 1Y
expectations. Frozen horizons 3/6/9/12M; no best-lag selection.

Frozen definitions applied exactly as written in the issue:

- Future change: `CPI[t+h] − CPI[t]`, h ∈ {3,6,9,12}; predictors DH level,
  DH 1M change, DH 3M change at t (all require finite inputs; CPI missing
  2025-10 drops affected pairs automatically).
- Direction: sign agreement plus balanced accuracy (TPR/TNR over nonzero
  actuals; exact-zero predictions count as misses; zeros are near-absent in
  these float series).
- Turning rule (both sides, identically): turn at t iff first differences
  reverse sign with both legs nonzero AND the t+1 difference confirms the new
  sign (retrospective dating; disclosed). Detected date = first month of the
  new direction leg.
- Greedy matching: chronological realized turns; each takes the nearest
  preceding unmatched DH turn with lead in [0,15] months (lead 0 = same month).
  Hit rate, median/mean lead, unmatched realized turns, false (unmatched) DH
  turns, and peak-peak / trough-trough / mixed composition reported.
- Deflator quarterly: quarterly-mean DH-I (complete quarters) vs deflator YoY;
  association at 1/2/3/4Q; quarterly turns matched 0–15 months.
- Episodes: the 8 frozen #161 windows; reference = sign-reversal CPI turn in
  window nearest the #161 CPI extremum (deflator fallback if none); DH turn =
  earliest DH turn within [ref−15, ref]; pass iff lead ∈ [0,15]. For 2008,
  peak and trough sub-checks were evaluated and the episode passes if either
  passes (disclosed leniency: all other episodes have a single reference).

## 2. Future-change association (A) and direction (B), n≈723

| h | DH level P/S | DH 1M P/S | DH 3M P/S | dir agree d1 (BA) | dir agree d3 (BA) |
|---|---|---|---|---|---|
| 3M | 0.16/0.16 | 0.19/0.15 | 0.18/0.15 | 0.519 (0.555) | 0.501 (0.535) |
| 6M | 0.12/0.11 | 0.15/0.13 | 0.19/0.166 | 0.526 (0.547) | 0.523 (0.544) |
| 9M | 0.06/0.03 | 0.18/0.16 | **0.28/0.261** | 0.541 (0.556) | **0.571 (0.587)** |
| 12M | −0.05/−0.09 | 0.16/0.15 | 0.15/0.13 | 0.533 (0.555) | 0.529 (0.550) |

(P=Pearson, S=Spearman.) A genuine but modest 9-month association exists for
DH 3M change (Spearman 0.26, direction 0.57); 3M/6M/12M horizons are near-null.
Level associations decay to zero/negative by 9–12M.

## 3. Turning points (C): high hit rate, zero median lead

- DH turns: 182 (≈ one per 4 months). CPI turns: 105. Matched: 100.
- Hit rate **0.952**. Median lead **0 months**, mean 1.58.
- Lead histogram: 0:53, 1:19, 2:7, 3:7, 4:3, 5:2, 6:2, 7:2, 10:1, 11:3, 13:1.
- Composition: 39 peak-peak, 45 trough-trough, 16 mixed.
- Unmatched CPI turns (5): 1982-11, 1992-11, 1993-02, 2007-02, 2009-08.
- False DH turns: 82 unmatched of 182.
- Independently recomputed with separate code: identical counts and leads.

Interpretation: realized turns are almost always preceded-or-accompanied by a DH
turn within 15 months, but the mass is coincident (53 same-month pairs), not
leading. Same-month coincidence is partly mechanical — CPI YoY is a 20% DH
input, so shared wiggles turn together — and partly genuine co-movement. Either
way it does not demonstrate systematic leadership: the frozen bar requires the
median lead at 2–12 months.

## 4. GDP-deflator quarterly cross-check (D)

Quarterly association (n≈241/240): modest, strongest at 1–2Q for DH level/change
(full table in summary JSON). Quarterly turns: 51 deflator turns, 63 DH
quarterly turns, 41 matched → hit rate 0.80, **median lead 3 months**, mean 3.7.
Taken alone this suggests a short quarterly lead, but frozen gate 7 compares
its sign to the CPI median lead (0): sign(3)=+1 vs sign(0)=0 → gate fails as
written. The deflator result is reported as a secondary positive, not a rescue.

## 5. Episode audit (E): 8/8 pass with caveats

| episode | DH turn (dir) | ref turn (src) | lead |
|---|---|---|---|
| late-60s | 1966-03 (−) | 1967-02 deflator fallback | 11 |
| 1973-75 | 1973-10 (+) | 1975-01 CPI | 15 (boundary; direction-mixed) |
| 1978-80 | 1979-07 (+) | 1980-04 CPI | 9 |
| 1981-86 trough | 1984-08 (+) | 1985-10 CPI | 14 |
| 1990 | 1988-12 (+) | 1990-03 CPI | 15 (boundary) |
| 2008 peak | 2007-09 (+) | 2008-08 CPI | 11 |
| 2008 trough | 2008-05 (+) | 2009-08 CPI | 15 (boundary) |
| 2021-22 | 2021-05 (−, peak-peak) | 2022-07 CPI | 14 |
| 2023-26 trough | 2024-02 (+) | 2025-05 CPI | 15 (boundary) |

Every major extremum has a preceding DH turn within the window, but 4 of 8
passes sit exactly at the 15-month boundary and one pairs mismatched turn
directions. At principal cyclical extrema DH usually leads by roughly a year;
across all high-frequency turns it coincides (Section 3). Leadership is
episode-selective, not systematic.

## 6. Secondary profiles (F, G)

- Full −18…+18 lead-lag profile (summary JSON): level-Spearman peaks at lag +3
  (0.38), positive through +18, negative at −18/−12 (realized CPI does not lead
  DH); change-Spearman spikes contemporaneously (0.63 at lag 0, partly
  mechanical via the CPI input) with a secondary 9M bump (0.25).
- Michigan 1Y 6M (n=575): level-Spearman 0.01, d3-Spearman 0.08, direction 0.50
  — no leading read on expectations.
- Core PCE 6M (n=725, input-circular): level 0.36, d3 0.20, direction 0.56 —
  reported for completeness only.

## 7. All frozen gates (no rescue)

| # | gate | result |
|---|---|---|
| 1 | ≥500 CPI obs evaluable at 6M (723) | PASS |
| 2 | d3 Spearman ≥0.20 at 6M (0.166) or 9M (**0.261**) | PASS |
| 3 | d3 direction ≥0.55 at 6M (0.523) or 9M (**0.571**) | PASS |
| 4 | CPI turn hit rate ≥0.60 (0.952) | PASS |
| 5 | median CPI lead ∈ [2,12] (**0**) | FAIL |
| 6 | ≥5/8 episodes with DH lead 0–15 (**8/8**) | PASS |
| 7 | deflator median-lead sign == CPI median-lead sign (+1 vs 0) | FAIL |

Formal verdict: `inflation_pressure_leading_not_supported` (sample sufficient,
so not inconclusive; two gates fail, so not supported).

## 8. Reading of the result

The evidence does not support calling Inflation_DH a systematic leading
measure: turns coincide far more than they lead, and the median lead is zero.
It remains what Issues #160–161 showed — a coincident-to-episodically-early
realized-pressure index (strong recession/inflation-episode identification,
modest 9M association, quarterly deflator lead of ~3 months as a secondary
positive). Any attempt to reframe, rescale, or selectively window these
results into a leading claim would violate the frozen gates; a different
leading-pressure construction needs a new issue.

## 9. Artifacts

- `research/decisions/issue-163-inflation-leading-pressure-finding.md` (this file)
- `research/generated/issue-163/inflation-leading-pressure-summary.json`
  (associations, turns, matches, deflator quarterly, episodes, full −18…+18
  profile, secondary 6M checks, gates, verdict)
- `research/generated/issue-163/inflation-leading-pressure-episodes.csv`
  (per-episode reference/DH turns, leads, pass/fail)

## 10. Workflow evidence and verification

- Isolated worktree at the frozen base; shared checkout untouched.
- DH CSV hash verified; USIRYY/CorePCE reuse hashes match #160 records;
  GDPD/Michigan FNV hashes verified against the fetch-time values.
- Turn-matching was re-implemented independently with identical outcomes
  (182/105/100, median 0, mean 1.58, same unmatched/false sets verified by count).
- Direction-agreement coincidence (0.5216 twice in #160-style checks) does not
  recur here; all reported fractions were recomputed from raw pairs.

## 11. Explicit confirmations

- No asset-return outcome was loaded: no SPY/TLT prices or returns, no
  equity-minus-duration spread, no Issue #136 payoff data, no forward-return
  or payoff join of any kind — CPI/PCE/deflator/Michigan macro benchmarks only.
  `outcome_data_loaded=false`.
- No production code was changed and DH v0.1 was not altered in any parameter,
  weight, source, transformation, lookback, threshold, or turning logic.
  `production_authorized=false`.
- Do not merge.
