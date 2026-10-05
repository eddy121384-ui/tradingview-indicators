# Issue #78 — Factorized classifier architecture preregistration

Date: 2026-10-05

Parent finding: `2d018f2fe83c0a9c7073d3c357b4e60ab0ba6ad9`

## Why this study exists

The classifier-methodology audit rejected the working explanation that a useful six-stage raw signal was mainly being damaged by hard-label confirmation or persistence.

The observed problem is earlier:

- Re-accumulation and Re-distribution are already almost absent at the raw-winner layer;
- their raw scores are highly redundant with Markup and Markdown;
- stronger Markup / Markdown raw evidence is not associated with better forward continuation in the inspected OOS3 equity cohort;
- a simple Up / Transition / Down collapse does not repair the result.

Therefore the next study must not be another threshold, confirmation, persistence, filter, or exposure-policy patch.

The preregistered question is:

> **Can a factorized representation separate current direction, expansion-versus-range structure, lifecycle durability, and local supply-demand pressure without forcing them to compete as six mutually exclusive Wyckoff stages?**

This is a classifier-architecture study. It does not authorize a replacement production classifier or a trading policy.

---

## Research firewall

The OOS3 cohort and all of its economic outcomes are already inspected.

Accordingly:

1. OOS3 may be used only for implementation smoke checks, contemporaneous factor geometry, missingness, and static diagnostics.
2. No OOS3 forward-return, MFE, episode-economics, policy, or trade outcome may be used to choose or revise any factor formula below.
3. Primary economic evaluation must occur on a new untouched OOS4 security cohort.
4. Once the OOS4 universe is frozen, no security may be replaced.
5. Once any OOS4 forward outcome is inspected, none of the factor formulas, bins, horizons, or interpretation gates below may change to rescue the result.

PR #80 remains Draft / open / unmerged. Existing classifier branches remain research artifacts and are not overwritten.

---

## OOS4 universe freeze

Use the frozen Issue #119 Bloomberg candidate snapshot.

Before any OOS4 price history is downloaded:

- exclude every FIGI in the first OOS2 300-stock cohort;
- exclude every FIGI in the OOS3 300-stock cohort;
- exclude AAPL / JPM / XOM calibration fixtures;
- preserve the Issue #119 metadata eligibility rules;
- preserve equal-sector-within-size-sleeve deterministic allocation;
- select 300 stocks total:
  - 100 large;
  - 100 mid;
  - 100 small.

Frozen seed:

`issue78-factorized-classifier-oos4-v1`

The resulting 300-FIGI manifest and its SHA-256 become immutable before price history is read.

This is a cross-sectional untouched-security test, not a prospective-time test.

---

## Architecture principle

Do not define six competing stage scores.

Instead compute separate continuous factors from already-frozen primitive measurements.

The first pass intentionally avoids:

- optimized weights;
- machine learning;
- clustering;
- new technical indicators;
- asset-specific parameters;
- direction-specific parameter sets;
- stage-specific gates;
- probability normalization across Wyckoff labels;
- confirmation/inertia.

The point is to test whether the representation itself becomes cleaner when conceptually different questions are kept separate.

---

## Frozen primitive set

The primary factorization may use only the following price-based primitives already present in the frozen Issue #78 Python mirror:

- `speed_rank`
- `ma_bull_spread`
- `ma_bear_spread`
- `range_score`
- `breakout_score`
- `explicit_breakdown_score`
- `range_cont_up`
- `range_cont_dn`
- `downside_exhaustion`
- `upside_exhaustion`
- `support_holding`
- `resistance_holding`

Primary factor scores must not use:

- old six-stage raw scores;
- old stage gates;
- effective stage scores;
- normalized six-stage probabilities;
- top-stage identity;
- strong/weak candidate state;
- formal stage;
- regime age;
- persistence;
- WarningFirst or any exposure policy.

Volume is excluded from the primary factor scores so the first architecture remains portable to markets where volume is missing or not directly comparable. Existing volume witnesses may be reported only as secondary descriptive diagnostics.

---

# Frozen factor definitions

All scores below are contemporaneous and causal at bar `t`.

## F1 — Direction

Short directional component:

`dir_short = 2 * speed_rank - 100`

Structural directional component:

`dir_structure = ma_bull_spread - ma_bear_spread`

Primary direction score:

`direction = clip((dir_short + dir_structure) / 2, -100, +100)`

Interpretation:

- positive = Up bias;
- near zero = Neutral / disputed;
- negative = Down bias.

No hard runtime threshold is selected in this study.

## F2 — Range versus Expansion

Reuse the frozen range measure directly:

`range_factor = range_score`

and for reporting:

`expansion_factor = 100 - range_factor`

Interpretation:

- high `range_factor` = range / compression-like structure;
- low `range_factor` = expansion / directional structure.

This factor is unsigned.

## F3 — Supply versus Demand

Demand score:

`demand = (downside_exhaustion + support_holding) / 2`

Supply score:

`supply = (upside_exhaustion + resistance_holding) / 2`

Net supply-demand score:

`sd = clip(demand - supply, -100, +100)`

Interpretation:

- positive = demand / downside absorption dominates;
- negative = supply / upside rejection dominates.

This dimension is intentionally separate from trend direction.

## F4 — Lifecycle channels

Lifecycle is not forced into one scalar because Emerging, Established, and Deteriorating need not lie on one linear axis.

The active directional side is selected mechanically by the sign of `direction`.

For `direction >= 0`:

- `emerging = breakout_score`
- `established = (range_cont_up + ma_bull_spread) / 2`
- `deteriorating = (upside_exhaustion + resistance_holding) / 2`

For `direction < 0`:

- `emerging = explicit_breakdown_score`
- `established = (range_cont_dn + ma_bear_spread) / 2`
- `deteriorating = (downside_exhaustion + support_holding) / 2`

For descriptive occupancy only, the largest lifecycle channel may be reported as the lifecycle winner.

No lifecycle winner is converted into a formal regime in this study.

---

## Why these definitions are frozen this way

The factorization is deliberately mechanical:

- Direction uses one short directional component and one slower structural component with equal weight.
- Range uses the already-frozen unsigned range measure.
- Supply-demand uses mirrored price-only exhaustion / holding primitives with equal weight.
- Lifecycle separates fresh break evidence, continuing acceptance/structure, and opposing deterioration.

No weight above was selected from OOS3 forward returns.

The architecture is intended to remove the specific failure mode identified in the methodology audit: one score should not simultaneously answer “which way?”, “trend or range?”, “how mature?”, and “who is absorbing whom?”

---

# Static OOS3 implementation audit

Before OOS4 history is inspected, the implementation may be run on already-inspected OOS3 data for static checks only.

Allowed outputs:

- missingness;
- score ranges;
- NaN propagation;
- factor occupancy;
- within-stock pairwise Spearman correlations among the factor scores;
- lifecycle-winner occupancy;
- deterministic reproducibility.

Forbidden OOS3 outputs:

- forward returns;
- favorable/adverse excursion;
- Failed<4 / Large>=8 outcomes;
- policy economics;
- PnL;
- any table that allows factor formulas to be selected by future performance.

No formula may change because an OOS3 static distribution looks aesthetically inconvenient.

---

# OOS4 economic validation

## Forward move

Frozen horizons:

- 1 bar;
- 5 bars;
- 10 bars;
- 20 bars.

Forward move:

`(log_close[t+h] - log_close[t]) / symATR[t]`

Direction-aligned move:

- for Up-bias observations: use the forward move as-is;
- for Down-bias observations: multiply the forward move by -1.

## Analytical bins

Bins are evaluation tools only, not runtime classifier thresholds.

Within each stock:

- Direction Up extreme = top quintile of `direction`;
- Direction Down extreme = bottom quintile of `direction`;
- High Range = top quintile of `range_factor`;
- High Expansion = bottom quintile of `range_factor`;
- High Demand = top quintile of `sd`;
- High Supply = bottom quintile of `sd`;
- High / Low lifecycle channel = top / bottom quintile of that channel.

Whole-sample within-stock quintiles may be used only for retrospective evaluation. They are not proposed as live thresholds.

Primary summaries are one-stock-one-vote.

For any stock × cell × horizon:

- require at least 5 eligible bars before that stock contributes;
- aggregate cells with fewer than 30 contributing stocks are descriptive only.

---

# Primary preregistered tests

## Test A — lifecycle must add information conditional on direction

For Up-extreme observations compare at 10 bars:

- High Established + Low Deteriorating
versus
- High Deteriorating.

For Down-extreme observations run the mirrored comparison.

Primary statistic:

`delta_lifecycle = aligned_mean(good_lifecycle) - aligned_mean(deteriorating)`

Expected sign:

`delta_lifecycle > 0`

Report:

- equal-stock mean delta;
- median stock delta;
- fraction of contributing stocks with positive delta;
- 5- and 20-bar supporting horizons.

This is the central test of whether separating lifecycle from direction solves a real representational problem.

## Test B — supply-demand must add information inside Range states

Inside Up-extreme + High-Range observations compare:

- High Demand
versus
- High Supply.

Inside Down-extreme + High-Range observations compare:

- High Supply
versus
- High Demand.

Primary statistic is the 10-bar difference in direction-aligned mean.

Expected sign:

`delta_range_sd > 0`

This is the factorized analogue of Re-accumulation / Re-distribution semantics. It does not require those labels to beat Markup / Markdown in a six-way contest.

## Test C — Emerging evidence is not enough if deterioration is high

Within Up-extreme observations compare:

- High Emerging + Low Deteriorating
versus
- High Emerging + High Deteriorating.

Mirror for Down-extreme observations.

Expected sign at 5 and 10 bars:

`low_deteriorating > high_deteriorating`

This directly challenges the prior “early proof alone is sufficient” failure without turning proof into a new policy.

## Test D — factor redundancy

Compute within-stock Spearman correlations among:

- direction;
- range_factor;
- sd;
- emerging;
- established;
- deteriorating.

Report equal-stock mean and median correlations.

A mean absolute correlation above 0.85 between conceptually distinct primary factors is a structural warning.

No factor is deleted or reweighted from this OOS4 result.

## Test E — semantic occupancy

Report the prevalence of the following descriptive combinations:

- Up extreme + High Expansion;
- Up extreme + High Range + High Demand;
- Up extreme + High Range + High Supply;
- Down extreme + High Expansion;
- Down extreme + High Range + High Supply;
- Down extreme + High Range + High Demand.

Also report lifecycle-winner shares inside each combination.

This test has no economic pass/fail threshold. It asks whether continuation/pause/deterioration combinations can exist without being structurally suppressed.

---

# Robustness slices

For Tests A-C report:

- Up / Down separately;
- large / mid / small;
- sector;
- five fixed calendar blocks where sample permits;
- leave-one-sector-out equal-stock result.

Do not create sector-specific or size-specific formulas.

---

# Frozen interpretation gate

## Architecture Strong / Encouraging

Require all of the following:

1. Test A 10-bar lifecycle delta is positive for both Up and Down.
2. At least 60% of adequately represented stocks have positive Test A delta in each direction.
3. Test B 10-bar range supply-demand delta is positive for both Up and Down.
4. At least 55% of adequately represented stocks have positive Test B delta in each direction.
5. Test A has the expected sign in at least 4 of 5 adequate temporal blocks in each direction.
6. No conceptually distinct primary factor pair has equal-stock mean absolute Spearman above 0.85.

## Architecture Mixed

Use when aggregate factor interactions are directionally useful but one or more breadth / temporal / redundancy requirements fail.

## Architecture Failed

Use when either central conditional mechanism fails in aggregate:

- Test A lifecycle delta is non-positive in Up or Down; or
- Test B range supply-demand delta is non-positive in Up or Down.

A failed result may not be rescued by changing weights, quintiles, factor ingredients, or horizons on OOS4.

---

# What this study does not test

This study does not select:

- a six-stage replacement labeler;
- production thresholds;
- confirmation bars;
- state inertia;
- exposure size;
- WarningFirst thresholds;
- an entry rule;
- a stop;
- a portfolio.

Even a Strong result means only that the factorized representation deserves a later frozen translation study.

---

# If the factorized architecture passes

The next separate preregistered study may translate factor combinations into semantic Wyckoff labels, for example:

- Markup ~= Up + Expansion + Emerging/Established + not Supply-dominant;
- Re-accumulation ~= Up + Range + Demand + not Deteriorating;
- Distribution ~= prior Up + Range + Supply + Deteriorating;
- Markdown ~= Down + Expansion + Emerging/Established + not Demand-dominant;
- Re-distribution ~= Down + Range + Supply + not Deteriorating;
- Accumulation ~= prior Down + Range + Demand + Deteriorating-down ending.

These mappings are hypotheses only and are not frozen classifier rules in the present study.

A later cross-asset / prospective validation remains mandatory before production consideration.

---

# Guardrails

After OOS4 outcomes are visible, do not:

- change factor ingredients;
- change factor weights;
- add a factor;
- delete a factor;
- change the sign-selection rule;
- change the 1/5/10/20 horizons;
- change the quintile definitions;
- change the 5-bar / 30-stock adequacy rules;
- change the Strong / Mixed / Failed gate;
- invent a stock/sector/size-specific exception;
- use OOS4 to optimize a formal label mapping;
- restart exposure-policy research on the old six-stage formal labels.

The old classifier remains frozen as a benchmark, not a template to patch.

Refs #78, #147, #138, #135, #132, #131, #80.
