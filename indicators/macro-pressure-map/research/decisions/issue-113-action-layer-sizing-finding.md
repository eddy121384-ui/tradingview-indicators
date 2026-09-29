# Issue #113 finding — sparse state-only Action Layer sizing gate

Status: **COMPLETE — ECONOMICALLY POSITIVE, NOT ROBUST ENOUGH FOR PRODUCTION**

Workflow:
- run: `36515349227`
- head: `a2d66a1f2dd1a87e47d8dcef4814637f818488ae`
- artifact: `issue-113-action-layer-sizing`
- artifact id: `11010144242`
- artifact digest: `sha256:9d21e45a4d3d88c78f263f04c9f34fe91213c769ee259a50ecaa24d08908d197`

Preregistered verdict:

`economically_positive_but_not_robust_enough`

Production authorization: **NO**

## Frozen design tested

Neutral C0:

- SPY 40%
- TLT 40%
- GLD 10%
- SHV 10%

Sparse +1 overlay:

- Regime 8 — Growth Slowdown / Stable Inflation:
  - SPY +5pp / TLT -5pp
  - GLD +5pp / SHV -5pp
- Regime 7 — Slowdown / Disinflation:
  - GLD +5pp / SHV -5pp
- Regime 9 — Stagflation Pressure:
  - GLD +5pp / SHV -5pp
- Regimes 1–6:
  - no view

Primary tactical transaction cost: 5bp one-way per dollar of target turnover.

Sample:

- 234 completed monthly periods
- 2007-02-01 through 2026-07-01 origins
- 87 active overlay months
- 39 active episodes

## Full-sample result

### Action Layer

- CAGR: **7.7538%**
- annualized vol: 8.8696%
- Sharpe vs SHV: **0.7215**
- max drawdown: **-21.3660%**
- Calmar: 0.3629
- terminal wealth: 4.2898

### C0 neutral 40/40/10/10

- CAGR: **7.3233%**
- annualized vol: 8.7315%
- Sharpe vs SHV: **0.6850**
- max drawdown: **-21.1222%**
- Calmar: 0.3467
- terminal wealth: 3.9677

### Incremental result

- CAGR advantage: **+0.4305 percentage point / year**
- Sharpe advantage: **+0.0365**
- max-drawdown difference: **-0.2438 percentage point**
- terminal wealth difference: **+0.3221**

The overlay is economically positive, but the preregistered Sharpe hurdle was +0.05. The observed improvement is +0.0365 and therefore fails that production gate.

## Exposure-matched control C1

Realized average Action Layer weights:

- SPY: 40.3205%
- TLT: 39.6795%
- GLD: 11.8590%
- SHV: 8.1410%

C1 static metrics:

- CAGR: 7.5149%
- Sharpe vs SHV: 0.6952
- max drawdown: -21.2153%

The dynamic Action Layer beats C1 on both CAGR and Sharpe, so the full-sample benefit is not explained solely by carrying a different average exposure.

## Temporal validation

All three preregistered periods show positive CAGR advantage versus C0.

### Pre-2020

- Action CAGR: 8.2511%
- C0 CAGR: 7.8430%
- CAGR advantage: **+0.4081pp**
- Sharpe advantage: +0.0314
- drawdown difference: +0.8527pp better

### 2020–2022

- Action CAGR: 1.3379%
- C0 CAGR: 1.0495%
- CAGR advantage: **+0.2885pp**
- Sharpe advantage: +0.0242
- drawdown difference: -0.2438pp worse

### 2023+

- Action CAGR: 11.5693%
- C0 CAGR: 10.9260%
- CAGR advantage: **+0.6433pp**
- Sharpe advantage: +0.0574
- drawdown difference: approximately flat (-0.0023pp)

There is no pre/post-2020 sign reversal in CAGR advantage.

## Episode robustness

Strongest positive episode:

- 2007-08-01 through 2008-02-01
- 7 months
- contribution sum: +1.8592%
- share of all positive episode contribution: **17.73%**

After reverting that entire episode to C0 and recomputing target turnover:

- leaveout Action CAGR: 7.6521%
- leaveout CAGR advantage vs C0: **+0.3287pp**

The result is not dependent on one winning episode.

## Cost sensitivity

Primary 5bp tactical cost:

- annualized tactical turnover: 21.54%
- total tactical cost across sample: 0.2100%
- annualized cost drag: approximately **1.15bp/year**

0bp Action CAGR: 7.7653%

10bp Action CAGR: 7.7423%

Transaction costs are not the reason the production gate fails.

## Sleeve attribution diagnostic

Gross additive monthly relative-return contribution:

### Equity-duration sleeve

Regime 8 only:

- cumulative arithmetic contribution: +1.1819%
- annualized mean contribution: approximately +0.0606pp/year

### Gold-cash sleeve

Regimes 7/8/9:

- cumulative arithmetic contribution: +7.1115%
- annualized mean contribution: approximately +0.3647pp/year

Most of the gross historical contribution comes from Gold > Cash rather than Equity > Duration.

Per preregistration, this diagnostic **does not authorize deleting or resizing a sleeve inside Issue #113**.

## Production gate

1. CAGR advantage >= +0.25pp: **PASS**
2. Sharpe advantage >= +0.05: **FAIL**
3. max DD not worse by >1.5pp: **PASS**
4. at least 2/3 periods positive CAGR advantage: **PASS** — 3/3
5. no period worse than -0.50pp CAGR: **PASS**
6. strongest-episode leaveout keeps positive CAGR advantage: **PASS**
7. beats C1 on CAGR and Sharpe: **PASS**

Result: **6 / 7 gates PASS**

Under the frozen deterministic verdict rule:

`economically_positive_but_not_robust_enough`

## Product implication

Do **not** implement the Action Layer as a production portfolio-sizing rule yet.

The state-only map has substantially more support than the prior full 3x3 allocation matrix:

- positive full-sample incremental CAGR;
- positive CAGR advantage in all three eras;
- survives strongest-episode removal;
- beats the exposure-matched static control;
- low turnover and low cost sensitivity.

But the preregistered risk-adjusted improvement is not large enough to clear the production bar.

Do not rescue this result by:

- increasing 5pp to 10pp;
- lowering the +0.05 Sharpe hurdle;
- removing the Equity/Duration sleeve after seeing attribution;
- adding trajectory or FCPI;
- adding Reflation;
- changing the neutral portfolio.

The research result is:

> **The sparse state-only Action Layer is economically promising, but has not earned production sizing authority.**

A future study, if pursued, must be separately preregistered and answer a genuinely new question rather than retune this failed gate.
