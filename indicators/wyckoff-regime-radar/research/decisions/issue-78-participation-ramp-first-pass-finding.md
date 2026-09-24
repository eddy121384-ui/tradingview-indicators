# Issue #78 — Participation Ramp First-Pass Finding

## Scope

This pass tests whether formal Markup / Markdown should begin as a probe position and earn larger exposure before the already-frozen Gentle / Balanced damage-latch layer manages deterioration.

The candidate rules were preregistered before results at commit `ac6ead7cb0ff06e873d2f4e6e671167c6cbc4b7d`.

Accepted discovery sample:

- 9 daily markets from Issue #76;
- 68,118 accepted formal-stage log rows;
- 1,624 completed known-start trend episodes;
- 806 Markup episodes;
- 818 Markdown episodes.

This is in-sample discovery, not OOS validation.

## Frozen participation candidates

- **Full-at-entry:** 100% participation immediately.
- **Persistence Ramp:** 25% for age 0–4, 50% for 5–9, 75% for 10–19, 100% for 20+ bars.
- **Excursion-Proof Ramp:** 25% initially; 50% after >=0.5 ATR favorable excursion, 75% after >=1 ATR, 100% after >=2 ATR.
- **Persistence + Health Gate:** same age ramp, but upward steps require current giveback <1 ATR.

Each ramp is combined separately with the previously frozen Gentle and Balanced damage-latch ladders. Actual exposure is the minimum of the participation cap and damage-latch exposure.

## Result 1 — Probe-to-add materially reduces false-start damage

For episodes whose total favorable excursion never reaches 4 ATR, every preregistered participation ramp improves the equal-market median retained move versus Full-at-entry under the same damage-latch family.

### Gentle + damage latch, MFE <4 ATR

| Stage | Full-at-entry | Persistence | Excursion-Proof | Persistence + Health |
|---|---:|---:|---:|---:|
| Markup | -1.667 ATR | -0.925 | -0.988 | **-0.861** |
| Markdown | -1.630 ATR | -0.979 | **-0.949** | -0.961 |

### Balanced + damage latch, MFE <4 ATR

| Stage | Full-at-entry | Persistence | Excursion-Proof | Persistence + Health |
|---|---:|---:|---:|---:|
| Markup | -1.401 ATR | -0.785 | -0.892 | **-0.757** |
| Markdown | -1.347 ATR | -0.816 | -0.861 | **-0.799** |

Cross-market robustness is unusually clean for this diagnostic:

- all three ramps improve failed-trend median harvest versus Full-at-entry in **9/9 markets** for Markup and **9/9 markets** for Markdown under Gentle;
- the same is true in **9/9 + 9/9** markets under Balanced;
- terminal giveback is also lower in **9/9 markets** for both directions and both latch families.

Interpretation: starting smaller is not merely cosmetic. It consistently reduces the damage from short-lived formal trend labels.

## Result 2 — The cost is lost participation in genuine large trends

For episodes that eventually achieve at least 8 ATR favorable excursion, every ramp gives up some retained move versus Full-at-entry.

### Gentle + damage latch, MFE >=8 ATR

| Stage | Full-at-entry | Persistence | Excursion-Proof | Persistence + Health |
|---|---:|---:|---:|---:|
| Markup | 5.315 ATR | 3.568 | **4.280** | 3.398 |
| Markdown | 5.820 ATR | 4.472 | **4.750** | 4.379 |

### Balanced + damage latch, MFE >=8 ATR

| Stage | Full-at-entry | Persistence | Excursion-Proof | Persistence + Health |
|---|---:|---:|---:|---:|
| Markup | 4.396 ATR | 3.033 | **3.575** | 2.996 |
| Markdown | 4.200 ATR | 2.885 | **3.577** | 2.866 |

The large-trend opportunity cost is also cross-market consistent: under Gentle, the ramp candidates retain less than Full-at-entry in 0/9 markets for both directions; under Balanced there are only isolated 1/9 exceptions.

Interpretation: the participation problem has the same unavoidable frontier as the exit problem. Reducing false-start damage means accepting some delayed participation in true trends.

## Result 3 — Excursion-Proof preserves large trends better than age-only ramps

Among the three ramps, Excursion-Proof consistently keeps the most large-trend harvest.

That is structurally sensible: a strong trend can earn Full exposure before age 20 if price has already demonstrated 2 ATR of favorable excursion.

On MFE >=8 ATR episodes, the Excursion-Proof cap reaches Full in 100% of both Markup and Markdown episodes. By contrast, the age + health-gated ramp still fails to earn Full participation in roughly 5% of these very large episodes.

The cost is that Excursion-Proof protects failed trends slightly less aggressively than the most conservative age / health ramps.

## Result 4 — The Health-Gated age ramp adds complexity but little frontier improvement

The Persistence + Health candidate is best or near-best on small / failed episodes, but the incremental benefit over plain Persistence is modest while its large-trend participation cost is slightly worse.

It also introduces a failure mode where an otherwise large trend remains below Full participation because the health gate blocks an age upgrade.

This does not justify rejecting it permanently, but it is currently the weakest universal research candidate because the extra condition does not clearly buy a better frontier.

## Result 5 — Participation helps the all-episode distribution, but does not solve it

Across all completed formal trend episodes, equal-market median retained move remains negative for every candidate.

Examples:

- Markup, Balanced + latch: Full-at-entry -0.818 ATR -> Persistence -0.568 -> Excursion-Proof -0.659 -> Persistence+Health -0.560.
- Markdown, Balanced + latch: Full-at-entry -0.744 ATR -> Persistence -0.515 -> Excursion-Proof -0.583 -> Persistence+Health -0.495.

So the participation ramp materially reduces damage, but does not turn every formal trend label into a positive-median trade. That is consistent with the product goal: the regime classifier is an environment / position-management framework, not a promise that every fresh trend label is an entry edge.

## Operational implication

The first-pass frontier now has a clear shape:

- **Full-at-entry:** best large-trend participation, worst false-start damage.
- **Persistence Ramp:** strongest simple protection, but delays genuine trends mechanically.
- **Excursion-Proof Ramp:** weaker false-start protection than the most conservative ramp, but materially better large-trend participation; strongest current candidate for “market proves itself, then add.”
- **Persistence + Health:** slightly better protection in some failed episodes, but additional complexity and no clear universal frontier advantage.

No production policy is selected.

## Research decision

Advance **Persistence Ramp** and **Excursion-Proof Ramp** as the two interpretable discovery survivors.

Downgrade **Persistence + Health Gate** for now because it adds complexity without a clear frontier improvement.

## TradingView visual audit

The two surviving ramps are now implemented in the Issue #78 TradingView Position Lifecycle visualizer.

Default visual mode is **Excursion-Proof × Gentle + Damage Latch**, with a single signed final target-exposure staircase to keep the chart readable. Users can switch the Participation Ramp among `Full-at-entry`, `Persistence`, and `Excursion-Proof`, and switch Damage management between `Gentle + Latch` and `Balanced + Latch`.

The chart marks `試 / 加 / 滿 / 減`, while optional component lines expose the Participation cap and Damage cap separately. The final next-bar target remains `min(participation_cap, damage_latch_cap)`.

This visual pass is for causal/manual auditing. It does not upgrade the discovery result to production validation.

Before any production claim:

1. manually compile and visually audit the generated Pine in TradingView;
2. freeze the two surviving ramp definitions;
3. test unchanged rules on new heterogeneous evidence — especially equities, commodities and weekly data;
4. only then decide whether either ramp belongs in the practical exposure state machine.

Refs #78, #80 and #76.
