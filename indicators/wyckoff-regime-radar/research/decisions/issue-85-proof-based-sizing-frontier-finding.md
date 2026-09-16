# Issue #85 — Proof-Based Sizing Frontier finding

Date: 2026-09-16

## Executive conclusion

The first preregistered attempt to convert Issue #81 Market Responsiveness into a hard position-sizing gate **does not beat the existing Persistence + Gentle baseline**.

The negative result is economically informative:

> Path efficiency is a strong discriminator of Large vs Failed trends, but using it as a hard participation gate delays too much exposure to the trends that matter most.

The existing age-only **Persistence + Gentle** policy remains the best current risk-managed in-sample survivor among the four frozen policies tested here.

No threshold rescue, asset-specific rule, direction split, or post-hoc policy variant is authorized by this result.

## Data gate

The exact accepted Issue #76 daily sample was reused:

- event rows: **68,118**;
- completed known-start formal trend episodes: **1,624**;
- Markup: **806**;
- Markdown: **818**;
- Failed (`MFE < 4 entry ATR`): **1,058**;
- Large (`MFE >= 8 entry ATR`): **308**;
- Middle: **258**.

The existing Persistence + Gentle baseline reproduces the accepted Issue #78 economic result:

- equal-market mean episode return: **+0.332 ATR**;
- positive-mean markets: **8/9**;
- median profit factor: **1.260**;
- equal-market mean max drawdown: **37.35 ATR**.

This confirms that the new study is operating on the same reconstruction and baseline.

## Frozen policies

- **P0 — Persistence + Gentle**: existing age-only 25% -> 50% -> 75% -> 100% ramp plus unchanged Gentle damage latch.
- **P1 — Excursion-Proof + Gentle**: existing +0.5 / +1 / +2 ATR proof ladder plus Gentle.
- **P2 — Proof + Path-Efficiency Gate + Gentle**: P1 may exceed the 25% probe only while causal direction-aligned path efficiency is >= 0.50.
- **P3 — Proof + Path Efficiency + Favorable Extension + Gentle**: higher tiers can only be newly earned following a fresh favorable cumulative close extreme that also satisfies the efficiency gate.

No new policy was added after outcomes were inspected.

## All-sample economics

| Policy | Eq-market mean return | Positive markets | Median PF | Mean MDD | Bootstrap 95% |
|---|---:|---:|---:|---:|---:|
| P0 Persistence + Gentle | **+0.332** | **8/9** | **1.260** | **37.35** | **+0.137 to +0.541** |
| P1 Excursion-Proof + Gentle | +0.275 | 6/9 | 1.215 | 52.19 | +0.010 to +0.534 |
| P2 Proof + Efficiency | +0.075 | 5/9 | 1.116 | 38.71 | -0.142 to +0.253 |
| P3 Proof + Efficiency + Extension | +0.194 | 6/9 | 1.101 | 49.27 | -0.047 to +0.419 |

### Decision

**P0 remains the current survivor. None of P1/P2/P3 improves the economic frontier enough to replace it.**

P1 participates more aggressively once favorable excursion appears, but pays for that with materially worse Failed-trend damage and drawdown.

P2 successfully suppresses exposure in bad trends, but suppresses too much of the big trends as well.

P3 restores more Large-trend participation than P2, but the Failed-trend protection largely disappears and drawdown remains materially worse than P0.

## Large vs Failed decomposition

### P0 — Persistence + Gentle

- Failed mean return: **-1.026 ATR**.
- Large mean return: **+5.853 ATR**.
- Large episodes ever reaching full actual exposure: **91.8%**.
- Failed episodes ever reaching full actual exposure: **11.4%**.

This is the benchmark.

### P1 — Excursion-Proof + Gentle

- Failed mean return: **-1.271 ATR**.
- Failed damage = **123.9% of P0**.
- Large mean return: **+6.445 ATR**.
- Large harvest = **110.1% of P0**.

P1 captures more of the large trends, but the extra participation is not selective enough: failed-trend damage rises by about 24%, and all-sample MDD rises from 37.35 to 52.19 ATR.

**Decision: REJECT as replacement for P0.**

### P2 — Proof + Path-Efficiency Gate

- Failed mean return: **-0.815 ATR**.
- Failed damage = **79.5% of P0**; about **20.5% less average Failed-trend damage**.
- Large mean return: **+3.401 ATR**.
- Large harvest retained = only **58.1% of P0**.
- Large episodes ever reaching full actual exposure: **72.1%**.

This is the cleanest demonstration of the central problem. The path-efficiency gate really does filter bad trends, but it filters too much valuable exposure as well. The reduction in Failed-trend damage is far smaller than the loss of Large-trend harvest.

All-sample mean return falls from +0.332 to +0.075 ATR, and the bootstrap interval crosses zero.

**Decision: REJECT as hard sizing gate.**

### P3 — Proof + Efficiency + Favorable Extension

- Failed mean return: **-1.061 ATR**.
- Failed damage = **103.4% of P0**; slightly worse than P0.
- Large mean return: **+5.174 ATR**.
- Large harvest retained = **88.4% of P0**.
- Large episodes ever reaching full actual exposure: **72.1%**.

P3 solves part of P2's opportunity-cost problem, but only by giving back the Failed-trend protection. It retains most, but not all, of the large-trend harvest while producing slightly worse Failed-trend damage and materially worse drawdown than P0.

**Decision: REJECT as replacement for P0.**

## Temporal falsification

Equal-market mean episode return:

| Policy | 2010–2014 | 2015–2019 | 2020–2026 |
|---|---:|---:|---:|
| P0 Persistence + Gentle | **+0.727** | **-0.098** | **+0.098** |
| P1 Excursion-Proof | +0.734 | -0.179 | +0.087 |
| P2 Proof + Efficiency | +0.302 | -0.090 | **-0.032** |
| P3 Proof + Efficiency + Extension | +0.425 | -0.133 | +0.055 |

P2 slightly reduces the already-known 2015–2019 loss, but the improvement is tiny and is paid for by much weaker 2010–2014 performance plus a negative 2020–2026 result. This is not a credible temporal improvement.

P3 is worse than P0 in all three frozen eras.

The original conclusion therefore remains: 2015–2019 is not rescued by simply demanding cleaner proof.

## Direction diagnostic

Equal-market mean episode return:

| Policy | Markup | Markdown |
|---|---:|---:|
| P0 Persistence + Gentle | **+0.145** | **+0.496** |
| P1 Excursion-Proof | -0.036 | +0.548 |
| P2 Proof + Efficiency | **-0.202** | +0.325 |
| P3 Proof + Efficiency + Extension | **-0.080** | +0.445 |

The proof gates are especially damaging on Markup episodes. Because direction-specific parameters were forbidden, this is evidence against the universal hard-gate architecture rather than an invitation to create separate long/short rules.

## Friction robustness

At the frozen 0.10 ATR-equivalent friction level per unit turnover:

- P0: **+0.134 ATR**, 6/9 positive markets;
- P1: **+0.057**, 4/9;
- P2: **-0.072**, 3/9;
- P3: **+0.028**, 3/9.

The extra proof gates therefore do not reveal a hidden turnover-adjusted advantage.

## What this teaches us about `盤感`

Issue #81 remains valid: path efficiency and repeated favorable extension contain real information about whether a live trend will become Large.

But Issue #85 adds an equally important distinction:

> **A feature can be useful for recognizing trend quality without being suitable as a hard gate on participation.**

A discretionary expert may use `this market feels right` as a confidence update while still carrying a meaningful base position. The tested P2 architecture instead withholds too much exposure until the path looks clean, and large trends often charge an opportunity cost for that certainty.

So the current evidence supports:

- **Responsiveness as state information:** yes;
- **Responsiveness as a hard universal sizing gate:** no, under the frozen rules tested here;
- **Persistence + Gentle as the current risk-managed baseline:** still yes, but still in-sample and temporally imperfect.

## Research decision

### Keep

- Issue #81 diagnostic finding: progress + path efficiency + favorable extension describe early trend responsiveness.
- P0 Persistence + Gentle as the current in-sample risk-managed baseline.

### Reject for now

- P1 excursion-only sizing as a P0 replacement.
- P2 hard path-efficiency gating.
- P3 hard efficiency + extension gating.

Do **not** rescue these by moving the 0.50 efficiency threshold, changing the proof ladder, splitting Markup/Markdown parameters, or tuning specifically on 2015–2019.

## Next valid research direction

If this line continues, the next hypothesis should be structurally different and separately preregistered. The most defensible question is not another hard gate, but whether responsiveness can add value as a **limited overlay on top of the existing Persistence + Gentle base exposure** — for example, a bounded add-on that never withholds the baseline position.

That question is not tested here and no overlay rule is authorized by Issue #85.

## Method note

The analyzer uses a fixed bootstrap seed of `8501`, frozen in code before the empirical run. The prior Issue #78 audit used seed `7801`; recomputing the headline bootstrap intervals with the older seed does not change policy ordering or any research decision. No seed was selected for favorable outcomes.

Refs #85 #81 #78 #76 #68.
