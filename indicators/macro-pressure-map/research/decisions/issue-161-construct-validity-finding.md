# Issue #161 — Deep-History v0.1 construct validity — macro-cycle benchmarks

- Issue: [#161](https://github.com/eddy121384-ui/tradingview-indicators/issues/161)
- Branch: `research/issue-161-construct-validity` (isolated worktree; shared checkout untouched)
- Frozen model: Issue #160 final `cc331bf11591ab49c6f5a5023cfee39b2cf09fde`
  (DH monthly CSV SHA256 verified `42516418ec8d1ce981d1b4bc05e2ae86809d6acbf5de63dccbad515db507dcfc`
  after LF normalization; worktree checkout uses CRLF on disk, values identical)
- Formal verdict: `deep_history_v01_construct_valid_with_limitations`
- `outcome_data_loaded=false`
- `production_authorized=false`
- This study does NOT compare DH v0.1 with V6.6 again and does NOT rescue Issue #160.
  No asset-return outcome was tested. No merge requested.

## 1. Question and approach

Issue #160 showed DH v0.1 does not clone market-implied V6.6 (Growth Spearman
~0.35, Inflation ~0.45, verdict overlap_failed). This issue tests whether the
frozen axes are nevertheless valid realized-macro state measures against
independent benchmarks: NBER chronology (FRED:USREC monthly), real GDP at native
quarterly frequency (USGDPQQ/USGDPYY), CFNAI from 1967 (secondary, partial
conceptual overlap disclosed), GDP deflator (USGDPD, YoY derived causally),
Michigan expectations from 1978 (1Y) / 1990-monthly (5Y), CPI peak chronology
(USIRYY reuse — timing only, input-circular by construction), and WTI from 1983
(secondary direction only). DH v0.1 was NOT altered: no source, weight,
lookback, threshold, or transformation change. All diagnostics are descriptive;
no thresholds or weights were fit to these benchmarks.

## 2. Growth findings

**Recession/expansion separation (723 full-composition months, 1966-03+):**
85 NBER recession months vs 638 expansion months. Mean Growth_DH −39.9 vs +3.9;
median −37.8 vs +3.7; Cohen's d −2.88. **100% of recession months are negative**
(85/85); 59% of expansion months positive. Separation is unambiguous.

**Peak/trough timing (8 frozen recessions):** Growth_DH is negative at or before
the NBER peak in 7/8 (exception: 1981-07 peak +0.9, decline followed). Trough
months are deeply negative (−10.8 to −55.5). Minima fall inside every
[P−6, T+6] window (−41 to −71). First upward turn around troughs lags
−2..+1 months in all 8 cases (five within ±1). T+3 recovery is positive in 5/8;
the three negatives (1975, 1980, 1991) match historically slow/double-dip
healings, not model artifacts. The 2020 shock reads honestly: +12.8 pre-shock,
−64.8 trough-month low, turn exactly at trough.

**Real GDP at native quarterly frequency (239 quarters):** quarterly-mean
Growth_DH vs GDP YoY Pearson 0.61 — the cycle frequency is captured. QoQ-change
sign agreement is 0.55 (98/178 adjacent pairs) with Δ-correlation 0.27:
high-frequency quarterly changes are weak, as expected for a 60-month
z-score state (levels, not quarterly deltas, are its construct).

**CFNAI cross-check (711 months from 1967-03):** Pearson 0.51, Spearman 0.60,
direction 0.58. Moderate agreement, consistent with partial conceptual overlap
(CFNAI embeds production/employment concepts; it is not an independent
measurement of the same series).

Growth construct: **strongly supported** on separation, timing, recovery, GDP
cycle frequency, and independent activity correlation.

## 3. Inflation findings

**Episode presence (8 frozen windows):** DH-I takes the economically correct
sign/extreme in all 8 — late-60s elevation (window mean +26.9), 1974-01 peak
+66.6, 1980-02 peak +56.1, 1982-04 trough −61.3, 1990-09 peak +45.4, 2007-11
peak +45.2 with 2008-12 trough −84.2, 2021-04 peak +92.6, 2023-06 descent −29.3.
Shock direction matches WTI on all 4 spans (1990 spike, 2008 crash, 2020-22
surge, 2022-23 retreat).

**Peak/trough timing vs CPI and GDP-deflator extremes:** excellent (−2..0 mo)
for 1978-80 and 1990; early leads of −7..−14 mo for 1973-75, 2008 spike/crash,
and the 2021-22 peak (DH 2021-04 vs CPI 2022-06 — surge identified over a year
early with a near-ceiling 92.6, plausibly base-effect-amplified by the 2010s
low-inflation window); early normalization −14..−22 mo for 2023-26; endpoint
misses for the 1981-86 glide (DH bottomed 1982-04 with the Volcker recession,
−55 mo vs the 1986 CPI/deflator trough) and a sample-start edge artifact for
the late-60s peak (window max 1966-02 at series inception; interior max 1968-02
still leads CPI's 1969-12 by ~22 mo; elevation, not peak timing, is the valid
read there). The 2007-Q1 deflator "peak" inside the 2008 window is likewise a
window-edge maximum (deflator YoY was muted throughout 2007-08), not a true
cyclical peak.

**Independent level agreement is weak:** GDP-deflator YoY vs quarterly-mean
DH-I Pearson 0.28 / Spearman 0.29 (n=239); Michigan 1Y 0.28/0.27 with direction
0.48 (n=581 from 1978); Michigan 5Y (monthly from 1990, n=434) diverges
(−0.13/−0.16, direction 0.41), consistent with anchored long-run expectations
vs realized pressure. Partial offsets: deflator quarter-acceleration direction
0.63, and shock-span directions align.

Inflation construct: **partially supported** — episode presence, shock
direction, and acceleration co-movement are good; linear level agreement with
the deflator/expectations is weak and several peak/normalization timings lead
by a year or more.

## 4. Verdict

`deep_history_v01_construct_valid_with_limitations`

Growth validity is strong across separation, NBER timing, recovery, GDP cycle
frequency, and CFNAI. Inflation validity holds for episode identification and
shock direction but is limited in linear agreement and peak-timing precision.
The verdict is about macro construct validity only and authorizes no
asset-outcome testing.

## 5. Artifacts

- `research/decisions/issue-161-construct-validity-finding.md` (this file)
- `research/generated/issue-161/construct-validity-summary.json` (benchmark
  metadata incl. FNV hashes, all headline statistics, verdict)
- `research/generated/issue-161/construct-validity-episodes.csv` (16 frozen
  episodes with DH values, timings, and reference extremes)

## 6. Workflow evidence and verification

- Work was performed in an isolated worktree
  (`tradingview-indicators-161` @ `cc331bf`); the concurrently used Issue #78
  checkout was never touched from this task.
- Frozen DH CSV hash verified before use; benchmark FNV-1a hashes verified
  after fetch (GDPD `ecfb4a8e`, GDPQQ `30c502d5`, GDPYY `077f2d82`, CFNAI
  `a1473415`, MIE1Y `4fb3d108`, MIE5Y `6f2021b5`, USREC `9c3b013e`, CL
  `69325da7`); CPI reuse hash matches the #160 record (`9936e0d6…`).
- Two analysis bugs were caught by verification before finalizing: a truncated
  [P−6,T+6] minimum window and a quarter-to-month lag conversion emitting NaN;
  both fixed and all downstream numbers recomputed. An NBER weekly-sampling
  attempt with month holes was discarded in favor of exact monthly USREC.
- Front-month WTI lacks a December bar in some years (contract roll); affected
  spans use the nearest available month-end, disclosed in the table.
- Michigan 5Y is sparse before 1990 (quarterly-ish); monthly analysis starts
  1990-04. Quarterly DH means require all 3 months (drops 1966-Q1, 2025-Q4,
  2026-Q1). CFNAI overlap is disclosed as partial, not independent.

## 7. Explicit confirmations

- No asset-return outcome was loaded: no SPY/TLT prices or returns, no
  equity-minus-duration spread, no Issue #136 payoff data, no forward-return or
  payoff join of any kind. Only macro benchmarks listed above.
  `outcome_data_loaded=false`.
- No production code was changed and DH v0.1 itself was not altered in any
  parameter, weight, source, or transformation.
  `production_authorized=false`.
- Do not merge.
