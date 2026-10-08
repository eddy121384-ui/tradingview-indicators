# Issue #78 — A9 market-structure dimension audit preregistration

Date: 2026-10-08 (frozen BEFORE any A9 forward-path outcome is computed).
Discovery on recovered OOS3 ONLY. No OOS4 mining for D3/D4 design (OOS4 may
serve ONLY as a preregistered secondary confirmation IFF OOS3 yields a
KEEP candidate — it is already inspected for Core-2 and never pristine).
No OOS5. No triggers, entries, sizing, production, Pine. PRs #80/#148
unmerged.

## Frozen Core-2 (reused by import, never modified)

D1 = dir_structure (frozen A1), D2 = extension = |dir_velocity|, causal
prior-only ranks, 252 minimum, hard 80/20, 70/30 robustness. Core-2 is a
conditioning input and the redundancy baseline — never a gate in A9.

## D3 — Compression/Expansion (frozen)

- TR[t] = max(high−low, |high−close[t−1]|, |low−close[t−1]|), causal.
- ATR20[t] = Wilder RMA (α=1/20, SMA seed over first 20 TRs) of TR.
- NATR20[t] = ATR20[t] / close[t] (requires close>0, finite OHLC window).
- Causal percentile vs previous 252 D3-ready values (same philosophy as
  A4): pct=(less+0.5·equal)/N_prior, self excluded, 252 minimum.
- LOW ≤0.20 (compressed), MID (0.20,0.80), HIGH ≥0.80. No threshold tuning.
- Robustness ONLY: 20-day close-to-close log-return stdev (closes t−20..t),
  same causal percentile. Never chosen over NATR post-hoc.

## D4 — Path Efficiency/Chop (frozen)

- ER20[t] = |close[t]−close[t−20]| / Σ_{i=t−19..t}|close[i]−close[i−1]|
  (0..1; 0/0 → NaN). Causal; no lookback scan (20 only, ever).
- Same causal 252-percentile, bins LOW/MID/HIGH at 0.20/0.80.

## Q1 — novelty (frozen tests)

Per dimension vs Structure, vs Extension, and D3 vs D4: within-stock
Spearman; discrete mutual information (10 rank-bins per variable, natural
log, Miller-Madow-corrected, per-stock then equal-stock mean); 5 fixed
blocks; sleeves. No MI estimator shopping.

## Q2 — future path (frozen outcomes, h1/h5/h10/h20)

Per bar t (causal): signed raw log-return; absolute move; realized forward
volatility (std of log-returns over t+1..t+h); MFE/MAE normalized by
ATR20[t] (known at t): max/min of (logclose−logclose[t])/ATR20[t] over the
next h bars; continuation fraction sign(fwd_h)==sign(close[t]−close[t−20]);
future ER over next 20 bars (h=20 only). Purpose is path description
("what road comes next"), never return ranking.

## Conditional maps (frozen, no 81-cell table)

2D fixed LOW/MID/HIGH maps: Structure×Extension, Extension×Compression,
Structure×Efficiency, Compression×Efficiency. Conditioning test: inside
each hard Core-2 cell (bull_low/high, bear_low/high), D3 LOW-vs-HIGH and
D4 LOW-vs-HIGH paired per-stock deltas on future-path properties.
A dimension that separates only via Extension correlation is redundant.

## KEEP_AS_ATLAS_DIMENSION gates (frozen; one of
## KEEP_AS_ATLAS_DIMENSION / KEEP_AS_DESCRIPTIVE_ONLY / REJECT_REDUNDANT /
## REJECT_UNSTABLE / INSUFFICIENT; no rescue)

Requires ALL: causally computable; equal-stock mean |Spearman| < 0.50 vs
BOTH Structure and Extension (MI consistent); same-sign separation in
≥4/5 adequate blocks and all sleeves; ≥1 future-path property separated
(LOW-vs-HIGH, majority of stocks same sign); separation survives Core-2
conditioning (paired same-sign majority); not tiny-subgroup/tail-only.

## HMM benchmark (frozen; Atlas primary, HMM benchmark only)

- Inputs: frozen causal coordinates D1–D4 only (standardized with
  TRAINING pooled mean/std). No future returns in features, K-selection,
  naming, or fitting.
- Sequences: pooled across stocks with explicit per-stock boundaries
  (never concatenated as one series).
- Fit: diagonal-Gaussian EM (own implementation, numpy only) on bars with
  date < 2015-01-01; decode all histories without refit.
- K-selection: K ∈ {2,3,4,5,6} by BIC on TRAINING data only; ties →
  smaller K. Deterministic init (fixed seed + quantile starts).
- State names from D1–D4 centroids only. Report prevalence, duration,
  transitions, centroids, temporal/sleeve stability, future-path
  distributions, Atlas-overlap.
- Final: exactly one of HMM_CONVERGES_WITH_ATLAS / HMM_ADDS_STABLE_
  STRUCTURE / HMM_UNSTABLE / HMM_INSUFFICIENT. Never promoted.

## OOS4 secondary (conditional, preregistered)

Runs IFF ≥1 dimension is KEEP-candidate on OOS3, reusing frozen
definitions verbatim on the existing OOS4 snapshot. Still discovery
(OOS4 inspected for Core-2). If no KEEP candidate, skipped by rule.

## Tests (frozen = issue's 14 proofs, incl. MFE/MAE windows, HMM
## boundaries/no-future-leak/K-without-outcomes, deterministic rebuild)

Refs #78 #181 #175 #173 #170 #168 #162 #159 #156 #153 #148 #147 #138 #119 #80.
