# Issue #78 — Classifier Methodology Audit finding

Date: 2026-10-05

## Scope

This finding executes the frozen classifier-methodology audit on the already-inspected OOS3 equity cohort.

It asks whether the current six-regime classifier behaves like six distinct market states, whether Re-accumulation / Re-distribution disappear only in downstream hard-state logic, and whether continuous Markup / Markdown evidence is more informative than the final formal labels.

This is post-outcome methodology work. It does not validate a replacement classifier or a new trading policy.

## Integrity

- 300 frozen OOS3 equities;
- 300 raw Bloomberg files, 0 failures;
- exact FIGI-set SHA:
  `017e9360402afa002dc0970088649e7c411c4f02333dec550f2432be3c0dd701`;
- frozen classifier blob:
  `1eec08e791403453853b589373bb2270c508c3bb`;
- 823,404 classifier-ready daily bars;
- frozen forward horizons: 1 / 5 / 10 / 20 bars;
- primary summaries are one-stock-one-vote.

## Finding 1 — the operational system is not really six-stage

Formal-label occupancy across classifier-ready bars:

| Regime | Formal share |
|---|---:|
| Accumulation | 6.08% |
| Markup | 49.41% |
| Re-accumulation | **0.022%** |
| Distribution | 10.33% |
| Markdown | 30.02% |
| Re-distribution | **0.119%** |
| No clear regime | 4.02% |

Markup + Markdown alone occupy about 79.4% of ready bars.

The two supposed continuation / pause states are almost absent.

Most importantly, they are already scarce at the **raw-score winner** layer:

- Re-accumulation raw winner: **0.145%**;
- Re-distribution raw winner: **0.967%**.

So their disappearance is not primarily caused by confirmation or state inertia. The raw six-score formulation itself almost never lets them lead.

Downstream gating makes the problem worse, especially for Re-distribution, but it does not create the problem.

## Finding 2 — Re-accumulation / Re-distribution are largely shadow copies of trend scores

Equal-stock mean Spearman correlations:

- Markup vs Re-accumulation: **+0.911**;
- Markdown vs Re-distribution: **+0.901**;
- Markup vs Markdown: **-0.914**;
- Re-accumulation vs Re-distribution: **-0.922**.

The continuation states therefore move almost one-for-one with their corresponding trend states rather than forming clearly separate evidence dimensions.

Top-two raw-score pairs reinforce the same diagnosis:

- Markdown winner / Re-distribution runner-up: **16.38%** of ready bars;
- Markup winner / Re-accumulation runner-up: **15.29%**.

Re-accumulation and Re-distribution frequently exist as runner-up shadows underneath Markup / Markdown, but almost never become distinct winning states.

Interpretation:

> the current six-score geometry is closer to a dominant bullish-versus-bearish axis plus transition side-states than to six independent Wyckoff phases.

## Finding 3 — the hard-label pipeline is not destroying a good raw directional signal

The preregistered 10-bar direction-aligned comparison is the decisive result.

### Markup

| Layer | Aligned equal-stock mean |
|---|---:|
| Raw score top quintile | **-0.100 ATR** |
| Probability top quintile | **-0.097** |
| Effective winner | **-0.057** |
| Strong candidate | **-0.066** |
| Formal label | **-0.051** |
| Formal age >=10 | **-0.086** |

### Markdown

| Layer | Aligned equal-stock mean |
|---|---:|
| Raw score top quintile | **-0.123 ATR** |
| Probability top quintile | **-0.194** |
| Effective winner | **-0.132** |
| Strong candidate | **-0.129** |
| Formal label | **-0.127** |
| Formal age >=10 | **-0.170** |

Negative aligned mean means the future move is opposite the intended trend direction.

This pattern persists and generally worsens at 20 bars.

Therefore the original hypothesis:

> “raw trend evidence is good, but six-way competition / confirmation / inertia destroys it”

is **not supported**.

The directional weakness is already visible in the raw and normalized continuous evidence.

Hard labeling sometimes makes the result slightly less bad, but it is not the source of the failure.

## Finding 4 — score strength does not behave like continuation confidence

For both trend directions, the strongest continuous evidence is not better.

At 10 bars:

- Markup probability top quintile: -0.097 ATR aligned;
- Markdown probability top quintile: -0.194 ATR aligned.

For Markdown, stronger normalized probability is materially worse than the broad formal label.

This suggests the current score magnitude is at least partly measuring:

> how strongly the market has **already** moved / extended,

rather than:

> how much directional continuation remains.

That distinction is fundamental for a regime classifier used to manage forward exposure.

The current formulas explicitly mix current trend direction, extension, heat/panic, structure, breakout/breakdown and lifecycle traces inside the same stage scores. The audit result is consistent with that mixture confusing **trend intensity** with **remaining trend life**.

This is an interpretation, not a newly validated formula claim.

## Finding 5 — Markup and Markdown fail in different ways

The signed formal-label results are asymmetric.

At 10 bars:

- Markup mean forward move: **-0.051 ATR**;
- Markup median-stock median: **+0.143 ATR**;
- Markup positive-move fraction: **51.5%**.

So Markup has a weakly positive typical / hit-rate tendency but a sufficiently adverse left tail to make mean expectancy negative.

Markdown is more seriously misaligned:

- Markdown mean forward move: **+0.127 ATR**;
- Markdown median-stock median: **+0.281 ATR**;
- positive-move fraction: **56.1%**.

In other words, a formal Markdown bar is followed by rising prices more often than falling prices in this equity cohort, and the mean is also positive.

At 20 bars the same effect strengthens:

- Markup mean: **-0.250 ATR**;
- Markdown mean: **+0.254 ATR**.

This is not merely a hard-state timing problem.

## Finding 6 — regime age does not rescue the stock result

Earlier heterogeneous nine-market work found that surviving Markup / Markdown could become more credible with age.

That behavior does not transport cleanly to this OOS3 equity cohort.

Examples:

### Markup

10-bar forward mean:

- age 0–4: +0.015 ATR;
- age 5–9: -0.005;
- age 10–19: -0.019;
- age 20+: -0.042.

### Markdown

10-bar forward mean:

- age 0–4: -0.132 ATR;
- age 5–9: -0.181;
- age 10–19: **+0.078**;
- age 20+: **+0.214**.

A mature Markdown state becomes increasingly rebound-prone rather than more continuation-prone.

Thus “the regime just needs to survive longer” is not a universal repair.

## Finding 7 — state inertia is not the main culprit

For formal Markup at 10 bars:

- effective winner agrees with formal label: mean **-0.064 ATR**;
- effective winner disagrees: mean **+0.043 ATR**.

For formal Markdown, both agreement and disagreement remain directionally wrong after alignment:

- agree: **-0.129 ATR**;
- disagree: **-0.105 ATR**.

So stale persistence / inertia is not the primary source of the equity failure.

The underlying directional state evidence is already problematic.

## Finding 8 — collapsing to Up / Transition / Down does not rescue the signal

The frozen three-family collapse gives, at 10 bars:

- Up family: **-0.057 ATR aligned**;
- Down family: **-0.134 ATR aligned**;
- Transition family: +0.120 ATR signed.

This simpler representation does not restore directional continuation.

Therefore the problem is deeper than six-way winner-take-all competition alone.

## Post-hoc sanity check — not a preregistered gate

A supplementary reconstruction of the all-ready-bar forward mean from the mutually exhaustive family partition gives an approximate equal-stock baseline of:

- +0.027 ATR at 10 bars;
- +0.031 ATR at 20 bars.

Relative to that stock drift, formal Markup is even weaker and formal Markdown even more opposite-directional.

Because this baseline-relative reconstruction was not a preregistered audit gate, it is descriptive only and must not be used to select a replacement model.

## Methodology conclusion

The strongest conclusion is:

> **This is not primarily an exposure-policy problem. The current classifier representation itself is structurally suspect for individual equities.**

Two different issues are present:

1. **Six-stage degeneracy**
   - Re-accumulation / Re-distribution are almost absent;
   - their raw scores are highly redundant with Markup / Markdown;
   - the implementation does not behave like six distinct lifecycle states.

2. **Direction-versus-lifecycle conflation**
   - stronger Markup / Markdown evidence does not imply better forward continuation;
   - raw evidence already fails before hard-state confirmation;
   - trend intensity / extension appears mixed together with lifecycle validity and remaining continuation.

The evidence does **not** support simply changing confirmation bars, state inertia, stage thresholds, or adding another filter.

## Recommended redesign direction

Do not edit the existing classifier yet.

A new preregistered architecture study should test a **factorized state representation** rather than another six-way winner-take-all scoring pass.

Candidate conceptual dimensions:

- directional bias: Up / Neutral / Down;
- market structure: Expansion / Range;
- lifecycle: Emerging / Established / Deteriorating;
- supply-demand / acceptance: Demand / Balanced / Supply.

Under such a representation, Wyckoff names become semantic combinations rather than six mutually exclusive competitors.

For example:

- Markup ~= Up + Expansion + Established;
- Re-accumulation ~= Up + Range + Demand/Acceptance;
- Distribution ~= prior Up + Range/Deterioration + Supply;
- Markdown ~= Down + Expansion + Established;
- Re-distribution ~= Down + Range + Supply/Acceptance.

These mappings are hypotheses only. They require a separate preregistration and untouched validation before production use.

## Decision

Pause further policy/filter research on the current formal six-stage labels.

Do not tune the OOS3 cohort.

Next gate should be a classifier-architecture redesign study, not another exposure-management patch.

Refs #78, #147, #138, #135, #132, #131, #80.
