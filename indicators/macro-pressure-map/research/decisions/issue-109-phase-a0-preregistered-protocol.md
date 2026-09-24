# Issue #109 Phase A0 — preregistered pairwise Action Layer protocol

Status: **PREREGISTERED BEFORE ISSUE #109 PAYOFF RESULTS**

## Research question

Can frozen Macro Pressure Map V6.6 information support stable **pairwise asset tilts** rather than a complete regime-allocation matrix?

Primary legs:

1. Equity vs Duration
2. Duration vs Cash
3. Gold vs Cash
4. Broad Commodities vs Cash

The eventual product may express directional tilts, but this protocol does not authorize production weights or `-2..+2` cutoffs.

---

## Frozen model boundary

Do not change production V6.6:

- GPI;
- IPI;
- FCPI;
- 20/63 time scales;
- thresholds;
- 3x3 state semantics;
- smoothing;
- Risk Note;
- existing alerts.

No Fed-policy variable.
No portfolio optimizer.
No new macro factor after outcomes are viewed.

---

## Modern signal source

Primary modern state source:

- exact Issue #64 V6.6 frozen transition history;
- transition SHA-256:
  `80446bbcb91be8b18eb0b95e62466edf892e4c04087696a04532f0fe214698af`;
- source Pine-log SHA-256:
  `c0220d4974b2fd0154c4cf8f33b4b3effb27a58e21ee96a1b0109011ce638e3d`;
- exact state coverage: 2007-01-04 through 2026-08-14;
- no signal forward-fill after the cutoff.

At each decision date, use only the latest state known **before** the decision return begins.

---

## Decision schedule

Primary decision frequency: **monthly**.

Decision row:

- first common eligible trading row of each calendar month;
- signal state is the one-bar-lagged V6.6 state available on the previous eligible trading row;
- no same-row state/lookahead.

Primary payoff horizon:

- **3M = 63 common trading rows**.

Diagnostics only:

- 1M = 21 common trading rows;
- 6M = 126 common trading rows.

The 3M primary horizon cannot be replaced because a diagnostic horizon looks better.

All forward windows must be fully observed inside the frozen outcome panel.
Incomplete windows are excluded mechanically.

---

## Asset definitions

### Equity vs Duration

`SPY total-return-like adjusted return - TLT total-return-like adjusted return`

### Duration vs Cash

`TLT adjusted return - SHV adjusted return`

SHV is the preregistered #74 cash-like 0-1Y Treasury exposure.

### Gold vs Cash

`GLD adjusted return - SHV adjusted return`

### Broad Commodities vs Cash

`GSG adjusted return - SHV adjusted return`

GSG is the preregistered #74 broad S&P GSCI commodity-futures exposure.

Do not replace SHV with BIL or GSG with DBC after results are viewed.

---

## Phase A1 — exact state-only baseline

A1 may begin only after the exact outcome snapshot is frozen.

For each leg and horizon:

1. report full-sample state-conditioned pairwise spread by the frozen 3x3 state;
2. report temporal splits:
   - pre-2020;
   - 2020-01 through 2022-12;
   - 2023-01 through latest completed frozen 3M origin;
3. report:
   - n;
   - mean;
   - median;
   - standard deviation;
   - positive fraction;
   - 10,000-resample bootstrap 95% interval of the mean;
4. primary inference sample uses non-overlapping starts:
   - candidate monthly decision rows are sorted chronologically;
   - greedily keep a start only if at least 63 common trading rows have elapsed since the last kept start;
5. all monthly starts may be shown as descriptive diagnostics, but they cannot replace the non-overlap primary inference sample.

Primary question:

> Is the **direction** of a pairwise preference stable across the major temporal segments?

No state is required to have a non-zero view.

A state with conflicting signs, sparse observations, or episode concentration remains `no_view`.

---

## Phase A1 episode robustness

For any state/leg that appears directionally useful:

1. group contiguous same-state monthly decision origins into episodes;
2. identify the largest positive-contribution episode;
3. remove that entire episode;
4. recompute the primary mean/sign and temporal interpretation;
5. report the share of total positive contribution attributable to the top episode.

A full-history relationship that flips after one dominant episode is not stable.

Do not choose a different episode-removal rule after inspection.

---

## Absolute-inflation diagnostic for Duration vs Cash

The #91 long-history finding is reused as context only.

For the Duration-vs-Cash leg, additionally report a frozen historical diagnostic split:

- CPI YoY < 4%;
- CPI YoY >= 4%.

The 4% threshold is inherited from #91 as a **diagnostic anchor**.

It is not a production Action Layer threshold.

This diagnostic may not be used to change the primary state-only verdict after the fact.

No 3%, 5%, percentile, or optimized alternative threshold may be introduced inside Issue #109 after payoff inspection.

The monthly CPI source and publication-safe lag must be frozen in the Phase A0 source manifest before this diagnostic is run.

---

## Phase A2 — incremental trajectory test

A2 asks:

> Does frozen GPI/IPI trajectory add stable information beyond current V6.6 state for the 3M pairwise spread?

A2 is **blocked** until a durable full exact-V6.6 GPI/IPI axis series is available.

### Frozen trajectory family

For each axis `X in {GPI, IPI}`:

```
fast_slope_X = (X_t - X_t-20) / 20
mid_slope_X  = (X_t - X_t-63) / 63
acceleration_X = fast_slope_X - mid_slope_X
```

No alternative lookbacks.

### Model ladder

For each pairwise leg separately:

**M0 — state only**

- intercept;
- eight one-hot indicators for the nine frozen V6.6 states.

**M1 — state + trajectory**

M0 plus exactly:

- fast_slope_GPI;
- mid_slope_GPI;
- acceleration_GPI;
- fast_slope_IPI;
- mid_slope_IPI;
- acceleration_IPI.

No interactions.
No feature selection.
No regularization tuning.
No FCPI input.

### OOS discipline

Primary A2 estimation:

- expanding-window OLS;
- monthly origins;
- 3M realized pairwise spread;
- feature standardization uses training-window moments only;
- first forecast occurs only after at least **84 complete monthly training rows**;
- no future data in state, trajectory, normalization, or outcome;
- M0 and M1 use the same complete-case origins.

Primary metrics:

- RMSE;
- MAE;
- Pearson correlation;
- sign agreement of predicted vs realized pairwise spread.

Also report mean realized spread conditional on predicted positive/negative sign as a descriptive diagnostic.

Temporal reporting:

- pre-2020;
- 2020-2022;
- 2023-latest completed origin.

### A2 decision rule

Trajectory earns a future Action Layer role only if M1:

- improves primary OOS error and/or correlation versus M0 in a materially consistent way;
- does not materially degrade sign agreement;
- is not useful only in one temporal segment;
- survives episode-removal diagnostics;
- has economically interpretable coefficient/sign behavior.

If M1 does not pass, the allowed conclusion is:

`state_only_sufficient_trajectory_adds_no_stable_value`

Do not rescue trajectory with new windows, interactions, thresholds, or features.

---

## FCPI

FCPI is **not** a directional predictor in A1/A2.

A later phase may test FCPI as a risk-budget cap only after a stable pairwise direction exists.

No FCPI rule is authorized by this preregistration.

---

## Allowed per-leg verdicts

Each pairwise leg must receive exactly one of:

- `stable_directional_relationship`
- `useful_but_era_dependent`
- `state_only_sufficient_trajectory_adds_no_stable_value`
- `no_material_pairwise_information`
- `inconclusive_insufficient_sample`

A full-sample positive mean with material era reversal cannot receive
`stable_directional_relationship`.

---

## Production gate

No V6.7 Action Layer Pine is authorized by A0.

A later production study may only use pairwise relationships that earned
`stable_directional_relationship`.

Portfolio translation remains separate.

This study does not define:

- +1 / +2 weight sizes;
- DV01;
- equity beta;
- cash percentage;
- commodity percentage;
- maximum portfolio leverage.

---

## Forbidden rescue paths

Do not:

- retune V6.6;
- optimize the nine-cell matrix;
- change the 3M primary horizon;
- change 20/63 trajectory windows;
- swap SHV/GSG to another asset after results;
- optimize the 4% inflation anchor;
- add yield curve, term premium, Fed expectations, FCPI direction, momentum or valuation variables;
- fit weights on CAGR, Sharpe or drawdown;
- call reused modern history untouched OOS;
- convert an era-dependent result into a production tilt.

No Issue #109 payoff result had been viewed when this protocol was committed.


---

## Pre-A1 clarification — frozen before A1 payoff generation

This clarification resolves implementation ambiguity without changing any asset, horizon, state, or source definition.

### Non-overlap grouping

The primary horizon embargo is applied **within each V6.6 state**.

For a given leg / horizon / state:

1. sort eligible monthly decision origins chronologically;
2. keep the first eligible origin;
3. keep a later origin only if at least the horizon's number of common trading rows has elapsed since the last kept origin in that same state.

Temporal segment summaries are then calculated from those already-selected state-level non-overlap origins. The selector is not restarted at each segment boundary.

### Episode definition

An episode is a consecutive run of monthly decision origins carrying the same lagged V6.6 state.

For the 3M primary horizon:

- episode contribution = sum of the pairwise 3M spread across all eligible monthly origins inside that episode;
- largest positive episode = episode with the largest positive contribution;
- top-positive share = largest positive episode contribution / sum of all positive episode contributions for that state/leg;
- leaveout removes every monthly origin belonging to that episode and then reruns the state-level primary non-overlap selector from scratch.

No alternative episode rule may be selected after results.

### State-level A1 classification

Use the primary 3M non-overlap sample.

Sample labels:
- n < 3: `insufficient_sample`;
- n = 3..9: `sparse`;
- n >= 10: `regular`.

A state/leg may be labeled `stable_directional_candidate` only if:

1. full-sample primary n >= 10;
2. the full-sample 10,000-resample bootstrap 95% CI of mean pairwise spread excludes zero;
3. every preregistered temporal segment with n >= 3 has the same mean sign as the full sample;
4. largest-positive-episode leaveout retains the full-sample mean sign;
5. top-positive episode share is <= 50%.

A state/leg is `era_dependent_candidate` if:

- full-sample n >= 10 and full-sample CI excludes zero;
- but at least one temporal segment with n >= 3 reverses sign, or the largest-positive-episode leaveout reverses sign, or top-positive episode share exceeds 50%.

A state/leg is `no_clear_state_edge` if:

- full-sample n >= 10;
- full-sample CI includes zero;
- and there is no stronger preregistered evidence that qualifies it above.

Otherwise it is `inconclusive_insufficient_sample`.

### A1 leg-level summary

Before trajectory is opened, each pairwise leg receives a provisional A1 summary:

- if at least one state is `stable_directional_candidate`: `stable_directional_relationship`;
- else if at least one state is `era_dependent_candidate`: `useful_but_era_dependent`;
- else if at least five states have regular samples and none is stable/era-dependent: `no_material_pairwise_information`;
- otherwise: `inconclusive_insufficient_sample`.

The A1 leg summary does not authorize production. A2 remains separately gated.
