# Issue #78 — A5 untouched OOS4 validation preregistration (causal Core-2)

Date: 2026-10-07 (frozen BEFORE any OOS4 universe output, raw bar, or
outcome is inspected; before the OOS4 builder runs; before any download)

Status: FIRST authorized OOS4 contact. All prior OOS4 gates deferred until
this preregistration lands. `oos4_touched=false` as of this commit.

## Frozen architecture under validation (verbatim from A4, reused by import)

- `dir_structure` = frozen A1 definition (never redefined)
- `dir_velocity` = frozen A1 definition (never redefined)
- `extension = abs(dir_velocity)`
- prior-only expanding same-stock percentile:
  `pct = (count_less + 0.5·count_equal) / N_prior`, current bar excluded
- minimum 252 prior ready observations, else state unavailable
- hard cells 80/20; relaxed robustness 70/30 (never replaces 80/20)
- primary horizon h10 (h1/h5/h20 supporting)
- aligned sign bull +1 / bear −1
- No Supply-Demand axis. No new factors/weights/thresholds. No sign-flips.
  No ML/regression/optimizer. No six-stage labels. No Pine/production.

Hard cells (causal prior-only ranks): bull_low (struct≥.80, ext≤.20),
bull_high (struct≥.80, ext≥.80), bear_low (struct≤.20, ext≤.20),
bear_high (struct≤.20, ext≥.80).

## OOS4 universe freeze rules (before any outcome)

- Builder: `build_issue78_factorized_classifier_oos4_universe.py` unchanged
  unless a pure engineering bug is proven; frozen seed
  `issue78-factorized-classifier-oos4-v1`.
- Exactly 300 unique FIGIs; 100 large / 100 mid / 100 small; zero OOS2
  overlap; zero OOS3 overlap; exclude AAPL/JPM/XOM calibration fixtures.
- Record universe CSV SHA256 and FIGI-set SHA256 at freeze; no
  outcome-aware replacement after freeze (short/missing histories retained
  and reported).

## Historical data contract (formal source only)

- Existing automated Bloomberg/blpapi pipeline from Issue #119; no manual
  one-by-one export. Event window 2000-01-03 through 2026-08-31; request
  earlier history for warmup where available; daily OHLCV; existing
  normalization/missingness/repair rules preserved.
- TradingView only for symbol/data sanity checks; never a silent
  truncated-history substitute for the formal snapshot.
- If Bloomberg automation is genuinely unavailable: STOP, report the exact
  blocker, change nothing about source or window.

## Evaluation (frozen)

Horizons h1/h5/h10(PRIMARY)/h20; four cells bull_low/bull_high/bear_low/
bear_high with equal-stock mean, median-stock median, positive-stock
fraction, stock/bar counts, p5/p10/ES5, sleeves, sectors where adequate,
fixed blocks 2000–04/2005–09/2010–14/2015–19/2020–26/ALL, breadth/
concentration, tails, 70/30 robustness. No entry/exit/sizing research.

## Primary verdict (frozen; no near-pass rescue)

`CORE2_OOS4_VALIDATED` only if ALL hold: (1) universe/raw provenance frozen
before outcomes; (2) ≥200 stocks adequate hard-cell h10 evaluation;
(3) h10 ALL bull-cell mean average > bear-cell mean average; (4) bear_high
worst or tied-worst h10 ALL; (5) ordering in ≥4/5 adequate blocks;
(6) 70/30 does not reverse interpretation; (7) not one tiny subset/sleeve/
sector/tails only; (8) no OOS4-driven tuning/replacement/source change.

Else `CORE2_OOS4_NOT_VALIDATED` (economic gates fail) or
`CORE2_OOS4_INCONCLUSIVE` (provenance/coverage insufficient).

## bull_low secondary verdict (frozen A4 rule, verbatim)

Paired low-minus-high h10: SUPPORTED if ALL mean>0 AND ≥55% positive AND
≥3/5 adequate blocks positive; CONTRADICTED if ALL mean<0 AND <45%;
else NEUTRAL. Does not determine the primary verdict.

## Integrity tests (frozen)

A4 definition hashes verified; zero OOS2/OOS3 overlap asserted by builder;
no-lookahead, append-future invariance, exact 252 boundary, exact 80/20
and 70/30 masks, deterministic rebuilds, A0–A4 artifacts unchanged.

## Boundary

Even a PASS validates only transport of the causal Structure × Extension
context ordering — not a profitable strategy. No entry/exit/sizing work
inside A5.

Refs #78 #170 #168 #162 #159 #156 #153 #148 #147 #138 #119 #80.
