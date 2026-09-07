# Issue #74 — Phase C decision

## Question

Does the preregistered broad-commodity sleeve improve the existing Phase B defensive allocation when frozen Macro Pressure Map V6.6 is simultaneously in **lagged Stagflation Pressure** and **lagged raw IPI >= +60**?

Frozen Phase C rule:

- ordinary Stagflation defense: SPY/TLT/SHV/GSG = **20/20/60/0**
- severe-inflation Stagflation: **20/20/40/20**
- the 20% commodity sleeve is GSG and comes entirely from SHV at each target rebalance
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

This satisfies the preregistered `equivalently exact verified reconstruction` path. The gate performs full manifest/SHA/content validation before reporting Phase C ready. Production V6.6 is unchanged.

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

## Realized-weight attribution

The first diagnostic used a fixed `20% × (GSG - SHV)` target-weight approximation. A later version improved this by using realized invested weights, but still summed only the rows where the severe-inflation Phase C state was active.

Codex review identified one remaining accounting detail: when a severe episode ends between month starts, Phase C event-rebalances back to the Phase B target while Phase B itself may not rebalance on that row. The two simulations can therefore retain slightly different realized weights for several subsequent inactive rows.

The reviewed attribution now uses each simulation's **actual invested weights on every row in each evaluation segment**, including:

- drift while Phase C is active; and
- post-activation residual drift on inactive rows until the portfolios reconverge.

Asset-level weight-difference contributions reconcile to the realized gross Phase C-minus-Phase B asset-mix return difference to floating-point precision.

Annualized arithmetic realized gross Phase C-minus-Phase B contribution over each complete segment:

- full history: **-0.114234 pp/year**
- pre-2020: **-0.141959 pp/year**
- post-2019 reused: **-0.059801 pp/year**

Across the full sample, 42 inactive rows retain a nonzero realized gross difference after Phase C deactivation. Their cumulative residual is about **+0.0461%**, partially offsetting the active-state cumulative gross difference of about **-2.2800%**; the complete gross difference is about **-2.2339%**.

The corrected attribution remains negative in every era split. It changes only the attribution accounting, not the primary Phase C strategy metrics or verdict.

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

## Review hardening

The Codex review findings are now addressed in the evidence path:

1. Severe-inflation availability means **full evidence validation**, not mere file existence.
2. Phase C attribution uses **realized invested weights**, not a fixed target-weight approximation.
3. Attribution covers **all segment rows**, including post-activation inactive residual drift, and reconciles to the complete realized gross return difference.
4. GitHub pull-request validation checks out the immutable **`github.event.pull_request.head.sha`** before any checked-out research code executes. The Python SHA guard remains defense in depth.

## Provenance

Latest evidence-producing evaluator head after the post-activation drift correction:

- head: `00dbc6f8035b05e263718e6379741459690f6088`
- GitHub Actions run: `34073743809` — success
- Phase C artifact ID: `10001351985`
- artifact digest: `sha256:4e4cf277f2d6f5bd20b0f4a699ca35e1192a85153aa85cd9e28f01212303f573`

The decision-record commit is documentation-only relative to that evidence-producing evaluator head; it does not alter the frozen Phase C rule, outcome data, or evaluator logic.
