# Issue #185 — active C1-only empirical preregistration DRAFT

**Status: DRAFT / NO HISTORICAL OUTCOME RUN AUTHORISED / NO OOS5.**
**Design baseline:** `5a20b0e20d692b52ed3072b8b51d9677dc2827ac` (phase-2 accepted),
plus this isolated Sophira specification/horizon-accounting patch.
**Primary issue:** https://github.com/eddy121384-ui/tradingview-indicators/issues/185
**Decision authority:** https://github.com/eddy121384-ui/tradingview-indicators/issues/185#issuecomment-6158215812

This document **supersedes conflicting candidate/cohort/stratum/censoring text**
in the older `issue-185-price-territory-prereg-draft.md`, which is a retained
historical two-challenger working draft, NOT the active study registration.
The existing 216 engineering tests and historical artifacts remain as an audit
trail. Do not use the old synthetic 14/23 headline as an outcome estimate.

## 1. Fixed instrument and single policy challenger

The `ptm_territory.py` v0.2.2 reference, A1–A7 gates, R/O/N, bar semantics,
first-probe frozen anchor and numeric thresholds are **unchanged**. This issue
does not authorise formula retuning, path-based entry, or changing parent
strategy/stop/risk rules.

Compare:
- **B0:** frozen R0 Immediate, 25% Probe, post-probe usable B3,
  P0/P1/P2 eligible for 100% at `B3_break_t + 3`, earliest fill next bar;
  P3/no B3 stay at Probe.
- **B1:** frozen R0 + the *existing* Warning-First defensive overlay as
  actually represented by the parent code; no fictional B1 symbol or newly
  synthesized rule.
- **C1:** an **add-on-only** PTM guard applied to the same earned 75%,
  without modifying entry, B3 eligibility or defense. At and after the
  eligible completed bar, release only on `is_new_territory_claim=True`
  and execute no earlier than the subsequent tradable bar. Otherwise hold
  the 75%; `DEGRADED/UNKNOWN` conservatively withhold as a **chosen C1
  exposure policy**, NOT a forced mathematical fact. Deterioration invokes
  the inherited de-risk/exit, never a promotion. Missing signal/120-bar
  expiry never automatically promotes. An eligible 100% position already
  filled is not reduced by C1.

**Exactly ONE active challenger (`C1_PTM_GUARD`).** The prior C2 changed
the original historical occupancy hypothesis (old-region `O` in [0,1])
into three **consecutive new-territory claim** bars. They are not the same
mechanism, and `o_min=3` is not an occupancy fraction. C2 implementation,
synthetic comparisons and tests are retained as **deprecated research
history only**: not part of the active empirical candidate count, no
parameter sweep, no substitute C2, no ex-post rescue.

## 2. Actual parent event contract (not synthetic B3 guesses)

- Source: Issue #76 forward-logger `ISSUE76|schema=1`.
- Consumer code: `analyze_issue78_retest_path_stage1.py` and
  `analyze_issue78_second_entry_economic_policy.py`.
- Frozen pre-outcome parity: `EXPECTED_EVENTS=68118`;
  `EXPECTED_EPISODES=1624`; `EXPECTED_B3_EVENTS=997`;
  `EXPECTED_P12=236`; path composition from counts-only rehearsal:
  P0=411, P1=110, P2=126, P3=350 (647 eligible / 350 not).
- Existing operator export glob: `/mnt/data/pine-logs-#76 Forward Logger*.csv`.
  These files **are NOT committed** and must not be presumed mounted in
  a future environment. DSH previously reported counts-only parity, which
  is not a substitute for independent file identity verification.

**PENDING INPUT FREEZE, before any forward outcomes:** enumerate the exact
export files in a committed manifest with SHA-256 per raw file, row counts,
FIGI universe hash, complete bar dates/time blocks, missing/split/roll policy
and cohort inclusion rules. Verify parity on the actual frozen inputs before
any MFE/PnL helper is called. If inputs are unavailable or hashes mismatch,
**STOP**, do not guess or replace with another export. No actual forward
outcome has been read by this patch.

## 3. Causal range stratification — BEFORE each probe

Old draft §6.5 mistakenly used `spread/w=20` to define a big box, but this
is an identity of `w=spread/20`, not a classifier. Further, an
episode-level `sustained_escape()` examines future bars, and may only be
an **ex-post RESULT**, never a predecision feature or a cohort filter.

For a completed Probe t0, use exactly 120 bars with index <t0.
Calculate historical `reference_high_low_width = max(high)-min(low)`.
The denominator is **mean True Range of the final 14 completed preprobe bars**
using only their own OHLC and preceding completed closes; valid-reference
coverage and positive finite denominator are mandatory. Call the continuous
feature `width_atr14 = reference_high_low_width / ATR14_preprobe`.
This is a descriptive normalisation, not another entry signal. Use the
frozen A1 `reference_cycle_count` solely as a separate historical
rotational-evidence axis.

Geometry-only *pre-outcome illustrative bins* for prereg stratification:
- `NARROW`: `width_atr14 <4`
- `WIDE_ROTATING`: `width_atr14 >=8` AND
  `reference_cycle_count >=1`
- `WIDE_UNCONFIRMED_ROTATION`: `width_atr14 >=8`
  but no confirmed complete reference cycle
- `MIDDLE`: remaining adequate width ratios
- `UNKNOWN`: absent 120 valid preprobe bars, invalid OHLC, zero/nonfinite
  ATR14, nonfinite ratio or inadequate denominators.

The numerical bins (4/8 in ATR14 units) are **geometry conventions, not
optimized returns thresholds**. The full continuous width and cycle count
MUST be reported to expose any sensitivity to arbitrary bins. Wide and narrow
groups MUST be labeled *using only information known before the Probe*.
No postprobe price, MFE, PnL, future `sustained_escape` or retrospective
peak/trough can assign a trading-stratum label. Independent cross-sleeve
and era breadth is required; unequal asset-count balance cannot be hidden
by pooling all bars.

## 4. Policy disposition and censoring (active C1 meaning)

The historical phase-2 `evaluate_addon` returns a legacy
`WITHHOLD_CENSORED` for *any* sequence that ends without a release, even if
it ends **BEFORE** the parent's eligible bar; therefore its "14/23" cannot
mean 14 proven permanently withheld earned adds.

The active prereg audit uses `ptm_c1_prereg.classify_c1_disposition` with
distinct, mutually exclusive statuses:

| Status | Meaning |
|---|---|
| `PARENT_NOT_ELIGIBLE` | P3/no usable B3, never earned 75%; no PTM cost |
| `OBSERVATION_RIGHT_CENSORED` | Follow-up stopped before a completed 120-bar post-eligible horizon or has missing observations; eventual release **unknown**, never a confirmed missed add |
| `POLICY_WITHHELD_THROUGH_EXPIRY` | Parent earned add; every eligible-through-expiry bar observed, C1 never released; full 120-bar policy horizon complete |
| `BASELINE_DE_RISK_BEFORE_RELEASE` | Inherited benchmark deterioration/exit controls disposition; not a PTM-fabricated promotion |
| `PROMOTED` | Valid C1 release and actual next-bar eligible fill, finite extra delay |
| `ALREADY_FULL` | Ex-ante full exposure; PTM doesn't reduce an already-filled add |

Never compare a right-censored episode with a confirmed policy-expired one,
or count a missing future as realized missed PnL. Right-censored and
policy-expired times should both be **excluded from finite release-delay
means** but reported separately, with eligible-at-risk denominators and
their date/horizon/observation-coverage counts. An episode ending in a
baseline exit is not evidence the guard would never have released afterward.
For full expiry, report *missed potential opportunity*, but actual lost
harvest still requires separately authorized ex-post economics.

Particular sanity fixtures: `gappy_reference` (eligible 126; last bar 123),
`one_tick_breakout` (132 vs 130), and `crossed_but_not_closed` (127 vs
124) MUST be administratively right-censored. Use the same causal rules for
all synthetic cases, and **never extrapolate a synthetic censoring rate to
the market population**.

## 5. Economic falsification plan — future, NOT authorised now

On a later, separately authorised DISCOVERY study only, use the **same**
Issue #76/#78 cohort, exact B3 event clock, fills, costs and exposures for
B0/B1/C1. Measure, **together**:

1. Wide-box/failed-break trading damage (whipsaws, giveback, turnover,
   costs, exposure-days, drawdown and tail risk) and **matched-exposure** /
   matched-latency comparator(s). Reducing exposure alone is not alpha.
2. Genuine trends with frozen `MFE >=8 ATR` label: fraction of **gross
   harvest retained** against the original B0/B1; missed 75% add days,
   earliest executable release, weighted ATR harvest missed and never
   promoted opportunities (with censoring correctly separated).
3. Incremental separation conditional on Core-2
   Structure×Extension, A9 volatility context and a plain predeclared
   Donchian-style 120-day comparator. These are controls, not extra policy
   triggers.
4. Equal-asset and adequate market/sleeve/time-block breadth and
   ex-ante wide/narrow regime stratification; report the continuous
   width/ATR and cycle features.

**PENDING_SOPHIRA_APPROVAL (normative decision):** the specific trade-off
required for ACCEPT versus REJECT — maximal tolerable measured reduction
in MFE>=8 ATR gross harvest versus demonstrable *risk-adjusted* wide-box
damage prevented, plus the minimum acceptable asset/era breadth. Do not
select these by examining outcomes or by using 14/23 synthetic cases.
If this normative decision, raw-file hashes, cohort manifest or event
parity are not frozen, **NO forward historical outcomes may be read.**

The old candidate count 2, `o_min` scan, D1 identity-stratum,
`sustained_escape` ex-ante interpretation, and `14/23=60.9% permanent loss`
are **explicitly not active prereg statements**.

## 6. Exact boundaries and release conditions

Research branch only. No Pine, no production, no parent model changes; no
OOS3/OOS4/OOS5 forward outcomes, no MFE/PnL/backtest run, no PR/merge,
no closing Issue #185. The protected OOS5 holdout is reserved for a
**separate precommitted** validation issue after a survivor exists.

Research artifacts and tests may exercise deterministic artificial paths
only. Historical two-candidate artifacts are frozen *legacy engineering
comparisons*; new `synthetic_c1_audit` is the active reporting layer.

**Next gate:** explicit Sophira signoff after code/tests and full input
identity/normative risk limits are resolved. Keep `PREREG DRAFT —
NOT AUTHORISED` until that time.
