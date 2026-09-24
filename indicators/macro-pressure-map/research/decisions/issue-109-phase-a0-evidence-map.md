# Issue #109 Phase A0 — evidence map

Status: **PRE-OUTCOME INVENTORY**

This file records what is already known before any new Issue #109 asset-payoff result is generated.

## Reused evidence

### Issue #59 — V6.6 descriptive state engine

Reuse only the established boundary:

- Pine/Python engineering parity is reliable enough for research;
- GPI / IPI / FCPI are defensible descriptive macro-state axes;
- prior transition tests did not establish robust standalone directional alpha;
- V6.6 remains frozen.

Issue #109 must not reinterpret descriptive validity as asset-allocation validation.

### Issue #64 — exact modern V6.6 cross-asset structure

Durable Phase A verdict:

`cross_asset_structure_present_but_regime_specific_and_era_sensitive`

Frozen exact-V6.6 evidence:

- source Pine-log SHA-256: `c0220d4974b2fd0154c4cf8f33b4b3effb27a58e21ee96a1b0109011ce638e3d`;
- derived transition SHA-256: `80446bbcb91be8b18eb0b95e62466edf892e4c04087696a04532f0fe214698af`;
- signal history: 2007-01-04 through 2026-08-14;
- frozen SPY/TLT/GLD outcome CSV SHA-256: `3a7f590c146f9eda5920b6968fe86c9c3cc1887db35597f2d639a1c76b6e5a57`.

Most coherent pairwise result:

**Reflation / Inflation Rising — SPY minus TLT**

- 1M development: +1.41%, nominal 95% CI [+0.01%, +2.74%], n=51 embargoed starts;
- 1M post-2019 reused: +2.31%, [+0.70%, +4.01%], n=22;
- 3M development: +4.17%, [+1.41%, +7.02%], n=23;
- 3M post-2019 reused: +6.42%, [+2.71%, +10.39%], n=11;
- 6M sign remains positive in both eras, but development uncertainty is wide.

This was selected after inspecting a larger comparison grid, so it is **reused hypothesis-generating evidence**, not a fresh confirmation target.

Weaker result:

**Stagflation — GLD over SPY**

SPY minus GLD was negative in both eras at 1M/3M/6M, but development confidence intervals crossed zero. Treat as a defensive candidate only.

Important counterexample:

**Slowdown / Disinflation**

TLT minus GLD changed materially by era. Do not encode “Slowdown = long duration” or “Slowdown = gold” as a production rule from #64.

Phase C later classified the Stagflation gold override as:

`risk_management_value_only`

Its benefit was episode-concentrated; removing one large winning Stagflation episode in either era erased/reversed the incremental effect.

### Issue #89 — full ex-ante 3x3 allocation matrix

Final verdict:

`inconclusive_insufficient_evidence`

Against a realized-exposure-matched static control:

- full history: +1.71pp CAGR, +0.090 Sharpe, but ~2.00pp worse maximum drawdown;
- pre-2020: +2.99pp CAGR, +0.229 Sharpe, drawdown improved ~5.28pp;
- post-2019: -0.43pp CAGR, -0.081 Sharpe, drawdown worsened ~1.80pp.

This is direct evidence **against** turning the nine V6.6 cells into a fixed full-portfolio matrix.

Issue #109 must therefore test pairwise relative-risk decisions, not optimize a complete allocation table.

### Issue #91 — long-history structural mapping

Final structural verdict:

`inflation_regime_dependent_mapping`

Strong reusable findings:

- Reflation Equity minus Treasury: +11.72pp/year, n=22; positive under every leave-one-era-out rerun;
- Goldilocks Equity minus Treasury: +15.31pp/year, n=20; positive under every leave-one-era-out rerun;
- Slowdown / Disinflation Treasury minus Cash: +6.04pp/year, n=15;
- Disinflationary Drift Treasury minus Cash: +6.33pp/year, n=10.

The strongest higher-order result is **absolute inflation context for Duration vs Cash**.

Within Reflation:
- CPI <4%: Treasury minus Cash +2.03pp;
- CPI >=4%: -3.08pp;
- high-minus-low: -5.11pp; bootstrap difference CI [-10.01pp, -0.43pp].

Within Stagflation:
- CPI <4%: +1.40pp;
- CPI >=4%: -4.71pp;
- high-minus-low: -6.11pp; CI [-12.30pp, -0.10pp].

Stagflation Treasury minus Cash remains negative under every eligible leave-one-era-out rerun.

Strict-causal `state_t -> return_{t+2}` did **not** simply reproduce contemporaneous mappings. Therefore long-history structure cannot be copied directly into a mechanical modern trading rule.

Primary long-history source:
- Damodaran U.S. annual return table, 1928-2025;
- raw SHA-256 `127c772f0fea8763391dbf2c1c7d3ecd3a07ca2b23f81ab47af58b529e2b5647`.

Independent cross-check:
- JST Macrohistory R6;
- raw SHA-256 `c1bb91fe56ea50d4f27af5c0fc897d481e89ae38ce41eaecab62134c9354981d`;
- Damodaran/JST Equity-Treasury correlation 0.9625.

### Issue #95 — binary high-inflation Treasury haircut

Final verdict:

`no_material_overlay_value`

The preregistered rule `CPI >=4% -> redirect 50% of Treasury to T-bills` added only about +2.7bp/year CAGR versus the unchanged base policy and did not improve drawdown materially.

Interpretation:

- #91's structural Duration-vs-Cash inflation interaction remains valid;
- a binary 4% threshold plus fixed 50% haircut is too crude as a portfolio rule;
- Issue #109 may retain 4% only as a **historical diagnostic anchor**, not as a production threshold.

### Issue #74 — preregistration only, no durable result

Issue #74 preregistered:

- SHV = 0-1Y Treasury / cash-like exposure;
- GSG = broad S&P GSCI commodity-futures exposure;
- GLD = legacy gold comparator.

No durable #74 outcome/finding is recorded.

Therefore these asset-role choices may be reused as **pre-outcome source definitions**, but #74 contributes no evidence that SHV/GSG rules work.

### Issues #97 / #99 / #101 / #107 — policy-reaction research

These studies did not establish a stable Fed-reaction layer from Growth/Inflation direction/speed.

Issue #109 must not infer from that failure that trajectory is useless for asset payoffs. The outcome domain is different.

It also must not reintroduce Fed prediction as an Action Layer feature.

## What is genuinely new in Issue #109

The following questions have not been durably answered by the prior findings above:

1. Does exact V6.6 **state-only** information support stable 3M pairwise preferences when measured on a monthly decision schedule?
2. Does frozen 20/63 GPI/IPI trajectory add stable incremental information beyond current state for:
   - Equity vs Duration;
   - Duration vs Cash;
   - Gold vs Cash;
   - Broad Commodities vs Cash?
3. Do those incremental effects survive:
   - pre-2020;
   - 2020-2022;
   - 2023-latest;
   - major-episode leaveout?
4. Can the result legitimately return **no view / zero tilt** when the relationship is unstable?

## Critical data gap discovered in A0

The repository contains:

- exact V6.6 regime transitions for the full modern history;
- sparse exact raw-axis audit checkpoints;
- a reproducible path back to the operator-local hash-frozen Pine log.

It does **not** currently commit the full exact daily GPI/IPI axis history.

Therefore:

- exact state-only pairwise research can proceed from the frozen transition history;
- exact state+trajectory research cannot begin until a full exact-V6.6 axis series is durably available;
- a public-feed reconstruction may be used only under a separately frozen screening gate and must not be represented as exact TradingView-feed V6.6.

No trajectory payoff outcome may be inspected before that source gate is resolved.

## A0 interpretation

The evidence supports the Issue #109 decomposition:

1. **Equity vs Duration** is the strongest first leg.
2. **Duration vs Cash** is structurally important and must retain absolute-inflation context.
3. **Gold vs Cash** and **Broad Commodities vs Cash** should be tested separately.
4. A full nine-cell portfolio matrix is not the target.
5. The model must be allowed to say **0 / no view**.

No new Issue #109 asset-payoff result has been viewed in producing this map.
