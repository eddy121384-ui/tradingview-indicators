# Issue #185 — C1 historical discovery, first independent shadow replay (2026-10-16)

**Status: STRONG NEGATIVE HARVEST SIGNAL / FORMAL REPLICATION STILL REQUIRED.**
This is **an independent causal reimplementation** of the frozen C1 mechanism,
not a verified execution of the byte-identical `ptm_territory.py` and
`ptm_addon_policy.py`. Therefore it is **not** the definitive registered
PASS/FAIL adjudication. No new candidate or threshold has been introduced;
OOS5 remains untouched. No code, thresholds or market observations were
changed on the frozen branch. The raw files and individual event rows remain
local/private, never committed.

## Inputs and parity

- **9/9** original Issue #76 CSV files exactly match the committed frozen
  SHA-256/byte-size manifest, 50,459,542 total bytes.
- **13** supplemental Issue #185 absolute OHLC Pine Logs CSVs, nine symbols
  across the original FX and 10Y yield markets. Without seam bridges:
  77,593 direct source bars; with three **explicitly inferred**, flagged
  seam candles: 77,596. Of 68,118 original events, 68,113 have independently
  confirmed one-bar source parity. The five remaining source identities require
  one of three *inferred* seam candles; never describe them as independent
  OHLC observations.
- The #78 parent logic is reconstructed with the *original relative
  `PRICE_LOG`/yield coordinate convention*, not substituted absolute levels,
  and reproduces exactly: 68,118 events, 1,624 formal episodes, 997 B3
  events; paths P0=411, P1=110, P2=126, P3=350.
- 647 of the B3 events earned a 75% parent add-on. The independently
  reproduced **strict pre-probe 120-bar `width_atr`** descriptor is available
  on 661 of 997 B3 events and returns the original feature-only
  tertile split: **NARROW 221 / MID 219 / WIDE 221**.
  `WIDTH_ATR_EDGES=(7.368,11.9931)` is unchanged.
  Of the parent-eligible group, **447** have this descriptor, **159 WIDE**.

## Same-clock experimental method (exploratory)

- B0: 25% Probe; P0/P1/P2 eligible at `B3_break_t + 3`.
  A decision at completed close t changes exposure no earlier than next
  bar (the replay conservatively applies the new exposure to the subsequent
  forward `move1` interval).
- B1: B0 plus the frozen *Warning-First* 2/4-entry-ATR
  latched giveback reduction; no second challenger.
- C1: fixed reference of 120 actual **absolute** OHLC bars before the first
  fresh trend probe, Q10/Q90 radius `w=(Q90−Q10)/20`, A1 cycle/envelope/gap
  guard, A3 `w/|median_close|<=0.05`, prior reference range touch episodes
  R<=1, and sticky one-bar ratio-break screen. Only a trusted new-territory
  claim can release the earned 75% add-on. Invalid reference stays at 25%
  until release or baseline exit.
- Market outcome `MFE` groups are retrospective labels only; never used
  to place an order. All measures below are signed `move1 / entry_scale`
  ATR-like **unrealised/gross diagnostic** contributions, *not executable
  net cash PnL*. No trade-fee model/DV01 conversion is fitted from outcomes.

## Findings on the frozen WIDE parent-eligible group

| Registered WIDE subset | N | C1 released add-on within stage | B0 negative-episode gross add-on contribution (ATR-like) | B1 negative-episode gross add-on contribution | C1 corresponding contribution | B0 positive-bar add-on harvest retained | B1 positive-bar add-on harvest retained |
|---|---:|---:|---:|---:|---:|---:|---:|
| Retrospective `MFE < 4 ATR` | **40** | **0** | 99.566192 | 64.937810 | **0** | not the registered success metric | not the registered success metric |
| Retrospective `MFE >= 8 ATR` | **72** | **1** | 97.311942 | 56.604175 | **0** | **4.37%** | **3.79%** |

For large trends, the **gross positive directional per-bar add-on
contributions** are B0=1,960.601218, B1=1,283.979106,
C1/B0=85.675728, C1/B1=48.707289 ATR-like units.
The harvest retention diagnostic is thus 4.37% versus B0 and 3.79%
versus B1: **much lower than the approved >=90% minimum**.

The `MFE<4` group's apparent 100% reduction in negative gross
episode contributions reflects that **C1 added zero positions**, and should
not be celebrated alone. The formal 20% gate requires a pre-fixed *net
75%-add-on trading-cost* calculation, which is not completed.

In a simple paired episode bootstrap (10,000 resamples, seed 185),
the descriptive 95% percentile range for wide `MFE>=8` harvest
retention was [0%, 13.38%] relative to B0 and [0%, 11.78%] relative to
B1. This is a **descriptive resampling diagnostic**, not independent holdout
evidence.

**Seam robustness:** inclusion/exclusion of the three source-derived
boundary bars changed **zero** parent B0/B1 economics, **zero** C1
release/definite-withhold decisions, and **zero** C1 gross add-on
contributions across all 647 eligible episodes. Four A3 adequacy results
differed when source coverage was treated as unavailable vs recovered
around seams, but none was promoted or altered the above payoffs.

## Three important limitations before a definitive verdict

1. **Original-module replication.** This is a causal shadow implementation
   independently ported from GitHub source function definitions, not a
   byte-identical execution of the frozen PTM Python package. Its original
   `build_reference`/C1 state machine must be executed and compared
   event-by-event before marking `§6.7 HARVEST_FAIL` as final.
2. **Trade economics.** The original #76 `move1 / entry_scale` is a
   directional price/yield movement normalised by ATR. Government bond
   **yield** moves cannot be treated as actual bond cash PnL without a
   frozen DV01/price convention. Trading costs were not preapproved;
   no definitive 20% negative-**net-PnL** pass or fail can be assigned.
3. **Competing exits and denominator.** The 20% definite
   120-bar withholding gate requires rigorous separation of baseline
   exits, missing observations and completed PTM decision horizons. The
   shadow study reports diagnostic counts but does **not** claim a
   final censoring-aware denominator or permanent-suppression pass.

**Recommendation:** do not rescue C1 by relaxing A1/A3, changing the frozen
90% hurdle, moving the entry clock, or selecting a different subgroup. The
independent negative-harvest finding is substantial and should trigger a
**focused exact-module replication**, not parameter-search. If reproduced,
**reject C1 as an add-on exposure policy for this cohort and retain B0/B1**,
even if the false-trend loss gate is satisfied. OOS5 stays sealed.

**Current verdict: `INDICATIVE_REJECTION / FINAL_FROZEN_MODULE_VERDICT_PENDING`.**
