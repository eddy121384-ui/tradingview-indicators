# Issue #57 — Consensus formation / Formal-lag decision

Status: **BURNED-DATA HYPOTHESIS NOT SUPPORTED AS A DIRECTIONAL SIGNAL**

Decision tag:

`consensus_formation_descriptive_lag_only_no_directional_edge`

This decision uses only the seven already-burned FX fixtures and remains price-only. It does not validate or reject performance on any future untouched sample.

## Question A — Does stronger actionable Top-2 agreement improve monotonically?

**No.**

For both frozen v0.5.2.1 and current v0.6, the continuous relation between actionable Top-2 consensus strength and aligned forward return is negative at every tested horizon.

Pair-median Spearman rho:

| Engine | 5 bars | 10 bars | 20 bars | 60 bars |
|---|---:|---:|---:|---:|
| v0.5 | -0.122 | -0.186 | -0.257 | -0.329 |
| v0.6 | -0.157 | -0.134 | -0.186 | -0.267 |

The `90-<95%` bin is locally better-looking, especially at 20/60 bars, but this is not monotonic evidence. The `>=95%` bin contains by far the most observations and is negative across all four horizons in both engines. Therefore the `90-<95%` pocket must not be promoted into a new threshold after seeing burned data.

## Question B — Does Top-2 consensus lead Formal in a useful directional sense?

There is a **descriptive timing lead**, but not a directional trading edge.

When v0.6 Top-2 consensus is `>=90%` while Formal is transition/neutral, Formal adopts the Top-2 direction quickly: median pair adoption is 100% within 5/10/20 bars, with median adoption lag about 1.25 bars. When Formal is initially opposite, adoption is about 75% within 5 bars, 91.67% within 10 bars, and 100% within 20 bars, with median lag about 1 bar.

However, the aligned forward returns from those non-aligned origins are negative. For v0.6:

| Formal relationship | 5 bars | 10 bars | 20 bars | 60 bars |
|---|---:|---:|---:|---:|
| transition / neutral | -0.23% | -0.38% | -0.54% | -0.04% |
| opposite | -0.16% | -0.49% | -0.91% | -1.19% |

The v0.5 engine shows the same qualitative conclusion. Therefore Candidate + Secondary can precede Formal as a classification transition, but this diagnostic does not support treating that lead as a directional price signal.

## Question C — Does 1/2/3-bar persistence improve the 90% signal?

**No stable improvement appears.**

Episode-level scoring avoids repeated-bar inflation. In v0.6, the median aligned return remains negative for all 1/2/3-bar streaks at 5/10/20 bars, and longer persistence does not produce a consistent improvement at 60 bars. v0.5 shows the same lack of stable persistence benefit.

Therefore persistence must not be selected from this burned-data sweep.

## Interpretation

The user's live observation is partially recovered in one narrow sense: Candidate + Secondary often move into an actionable family before Formal follows. But the preregistered diagnostic does not show that stronger consensus, Formal disagreement, or short persistence produces a stable positive directional edge.

The locally attractive `90-<95%` bin is treated as a post-observation curiosity only, not a rule. No threshold is changed from the preregistered design.

## Research decision

- Keep the v0.6 engineering robustness work intact.
- Keep the four-state macro mapping and six-stage diagnostic substructure intact.
- Do **not** add Volume, MTF, Divergence, HMM, or witness bias to rescue this result.
- Do **not** consume a new untouched sample merely to validate `Top2 >=90%` or a fitted `90-<95%` variant.
- Treat Top-2/Formal timing as descriptive regime-transition information only unless a separately preregistered hypothesis identifies a different mechanism.
- PR #58 remains Draft and Issue #57 remains open.

Potential next research, if pursued separately, should focus on a different mechanism rather than threshold tuning—for example formation dynamics or transition-path structure—because the static consensus-strength hypothesis failed its burned-data monotonicity test.
