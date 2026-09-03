# Issue #74 — Phase C decision

## Question

Does the preregistered broad-commodity sleeve improve the existing Phase B defensive allocation when frozen Macro Pressure Map V6.6 is simultaneously in **lagged Stagflation Pressure** and **lagged raw IPI >= +60**?

Frozen Phase C rule:

- ordinary Stagflation defense: SPY/TLT/SHV/GSG = **20/20/60/0**
- severe-inflation Stagflation: **20/20/40/20**
- the 20% commodity sleeve is GSG and comes entirely from SHV
- one-bar signal lag
- monthly plus lagged-template-change rebalance
- 5 bp primary one-way-turnover cost
- no threshold tuning, weight sweep, commodity momentum filter, oil-only rescue test, or production V6.6 modification

All history is reused/development evidence, not untouched OOS confirmation.

## Signal evidence gate

The operator supplied a new TradingView source capture, `pine-logs-MPM V6.6 PHASE C SRC.csv`.

- SHA256: `6c5aa03419d2e5325d28fb33bf9c83a9744d7170da84f72a614676a7fc1aad4d`
- 5,458 raw rows; 5,451 unique source dates
- raw IPI reconstruction finite on 5,137 dates
- 194 source dates have raw IPI >= +60
- all 51 frozen Issue #64 axis-audit checkpoints matched
- maximum absolute IPI difference: `2.0430569236395968e-08`
- frozen parity gate: `5e-08`

This satisfies the preregistered `equivalently exact verified reconstruction` path. Production V6.6 is unchanged.

## Outcome window

Frozen SPY/TLT/SHV/GSG adjusted-price panel:

- evaluation: 2007-01-12 through 2026-08-14
- 4,928 common return rows
- price CSV SHA256: `eba5c4d82c647536a23856e091b874f7a82940d7358bc5235ed066a20ae9566c`
- archive SHA256: `e2a76e4aa6c43f64c9574000723ebf96309f7f129d148b805e26123c11643398`

The combined lagged Stagflation + lagged IPI >= +60 rule activates on **74 outcome rows across 11 episodes**.

## Primary result — Phase C fails

At 5 bp, Phase C minus Phase B on full reused history:

- Delta CAGR: **-0.1362 percentage points/year**
- Delta Sharpe: **-0.0228**
- Delta maximum drawdown: **-0.8831 percentage points** (worse)
- Delta Calmar: **-0.0254**
- Delta annualized turnover: **+0.144x/year**

The result is negative in both era splits:

- pre-2020: Delta CAGR **-0.1598 pp**, Delta Sharpe **-0.0243**, max drawdown **-0.8831 pp** worse
- post-2019 reused: Delta CAGR **-0.0898 pp**, Delta Sharpe **-0.0182**, max drawdown **-0.2977 pp** worse

This is not a transaction-cost artifact. At **0 bp**, full-history Phase C minus Phase B still has Delta CAGR **-0.1287 pp**, Delta Sharpe **-0.0222**, and maximum drawdown **-0.8312 pp** worse.

## Direct sleeve attribution

Because Phase C changes only 20% SHV into 20% GSG during the activation state, the direct commodity-versus-cash sleeve can be read cleanly.

Annualized arithmetic contribution of the 20% GSG-minus-SHV sleeve over the corresponding segment:

- full history: **-0.0956 pp/year**
- pre-2020: **-0.1384 pp/year**
- post-2019 reused: **-0.0116 pp/year**

The commodity sleeve therefore did not add historical value under this exact V6.6 severe-Stagflation condition.

## Episode evidence

There is one important positive episode: **2022-03-02 through 2022-04-04**, where Phase C contributes about **+0.9965% active log return** versus Phase B.

But the full active result is **-2.4770% log return**. Removing that largest winning episode makes the result even more negative at **-3.4735%**.

The pre-2020 active result is negative (**-1.9243%**) and the post-2019 reused active result is also negative (**-0.5527%**). The 2022 commodity success is therefore not evidence for a stable general rule.

## Decision

Verdict:

`preregistered_gsg_satellite_does_not_add_historical_value_over_deep_cash_in_v66_severe_stagflation`

Interpretation:

- Phase C **does not pass**.
- Broad commodities are **not supported as a default 20% satellite** under the frozen `Stagflation + IPI >= +60` rule.
- The earlier Phase A evidence for **cash / very-short Treasuries as the cleaner core defensive role** remains intact.
- This does **not** rescue Phase B into a universal 60% Cash rule; Phase B remains highly 2021-22-sensitive as previously documented.
- This also does **not** prove commodities are useless. It rejects this specific preregistered GSG sleeve and conditioning rule.
- No momentum filter, threshold change, weight sweep, oil-only replacement, or extra asset may now be added to rescue Phase C inside Issue #74.
- Macro Pressure Map V6.6 is still **not a validated production allocator**.

## Provenance

GitHub Actions run: `33724590524` on head `c0c32921e9c4ba42491b6da3198a7109e48f649c` — success.

Phase C artifact:

- ID `9881524569`
- digest `sha256:079c3dd3e5cd378d1cda36634bd2ea08573ec2d49e84cee1a6bf99c520e53b98`
