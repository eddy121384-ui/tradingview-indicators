# Issue #78 — A7 failed-break rejection / reversal mechanism preregistration

Date: 2026-10-07 (frozen BEFORE any A7 forward-return result is computed).
Mechanism discovery on recovered OOS3 ONLY. No OOS4 mining, no OOS5 contact,
no new download, no policy/sizing/production/Pine. PRs #80/#148 unmerged.

## Frozen structural level (A6 verbatim)

Prior 20 completed bars; current bar excluded:
`prior_high_20(t) = max HIGH[t−20..t−1]`,
`prior_low_20(t) = min LOW[t−20..t−1]`. No lookback scan.

## F0 primary event (must reproduce A6 T3 exactly)

Bullish failed breakdown: close[t0] < prior_low_20[t0]; freeze L;
first close > L within next 3 completed bars confirms at tc; timestamp tc.
Bearish mirror: close[t0] > prior_high_20[t0]; first close < L within 3
bars confirms. If A6 T3 is not reproduced exactly, STOP and report.

## Mechanism descriptors (frozen, no tuning afterward)

- M1 speed: reclaim on t0+1 / t0+2 / t0+3 (no cutoff optimization).
- M2 break depth (ATR-normalized, ATR at t0): bull (L−close[t0])/ATR;
  bear (close[t0]−L)/ATR. Strata: shallow ≤0.25, medium (0.25,0.75],
  deep >0.75.
- M3 reclaim strength (ATR at tc): bull (close[tc]−L)/ATR; bear
  (L−close[tc])/ATR. Strata: weak ≤0.25, medium (0.25,0.75], strong >0.75.
- M4 CLV = (close−low)/(high−low) at tc: bull expects HIGH stronger, bear
  expects LOW stronger. Tertiles: LOW <1/3, MID [1/3,2/3], HIGH >2/3.
- M5 follow-through: next completed bar closes beyond close[tc] in the
  reversal direction (diagnostic only, never backdated; tax reported).

ATR = frozen classifier `sym_atr`. No composite score is created.

## Controls (frozen; mutually exclusive where stated)

- CONTROL A (raw break T0): same structural break, evaluated as A6 T0
  (aligned with trigger side = reversal side for the delta: F0 and T0
  outcomes are compared on the SAME forward clock, see timing).
- CONTROL B (non-reclaimed break): same initial break with NO reclaim
  within next 3 completed bars; mutually exclusive with F0 by construction.
- CONTROL C: broad eligible-bar baseline (descriptive).
- Timing: trigger known at close tc; primary forward clock starts next bar
  (e=tc+1); aligned bull +1 / bear −1; horizons h1/h5/h10(PRIMARY)/h20.
  Control outcomes use the identical forward-clock convention anchored at
  their own knowable bar (T0: e=t0+1; non-reclaim: e=t0+1 with t0 the break
  bar), so clocks are comparable, never backdated.

## Core-2 relationship (explanatory only)

F0 evaluated standalone first (no Core-2 required for existence). Then
split by frozen Core-2 (imported, never redefined): bullish vs bearish
structure side; low vs high extension. No four-way over-conditioning;
no threshold changes.

## Hypotheses H1–H6 (frozen; asymmetry retained, never forced)

H1 F0 beats raw-break control. H2 faster rejection stronger. H3 stronger
reclaim better. H4 CLV extremes carry information. H5 bull/bear asymmetry
may be real (kept explicit). H6 failed-break information exists
independently of Core-2 context.

## Reporting (frozen)

Per side, per horizon (primary h10): event/stock counts, frequency,
equal-stock mean, median-stock median, positive-stock fraction, p5/p10/
ES5, repeated-event concentration, blocks 2000–04/05–09/10–14/15–19/
2020–26/ALL, sleeves, sectors where adequate, tails. Mechanism tables h10
by M1/M2/M3/M4/M5 strata. Control deltas (equal/median/positive-fraction,
blocks, sleeves, sectors): F0−raw, F0−non-reclaimed.

## Decision gates (frozen; no near-pass rescue)

Exactly one of FAILED_BREAK_MECHANISM_STRONG / _PARTIAL / _WEAK /
_CONTRADICTED / _INSUFFICIENT. STRONG requires ALL: (1) F0 h10 beats
raw-break control materially; (2) majority of adequate stocks positive
F0−control; (3) advantage in ≥4/5 adequate blocks; (4) not one
sleeve/sector/tails/subset only; (5) usable frequency; (6) causal timing
tests pass; (7) ≥1 descriptor shows coherent ordered evidence without
rescue; (8) asymmetry retained explicitly. PARTIAL if F0 robust and beats
controls but decomposition mixed or strongly one-sided.

## Tests (frozen list = issue's 17 proofs)

Dedup/levels/mirrors/ATR-math/speed/CLV strata/mutual-exclusivity/
post-confirmation timing/Core-2 reuse/deterministic OOS3 rebuild.

Refs #78 #175 #173 #170 #168 #162 #159 #156 #153 #148 #147 #138 #119 #80.
