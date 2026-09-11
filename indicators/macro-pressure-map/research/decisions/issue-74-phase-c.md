# Issue #74 — Phase C decision

## Question

Does the preregistered broad-commodity sleeve improve the existing Phase B defensive allocation when frozen Macro Pressure Map V6.6 is simultaneously in **lagged Stagflation Pressure** and **lagged raw IPI >= +60**?

Frozen rule:

- ordinary Stagflation: SPY/TLT/SHV/GSG = **20/20/60/0**
- severe-inflation Stagflation: **20/20/40/20**
- one-bar signal lag
- month-start plus lagged-template-change rebalance
- 5 bp primary one-way-turnover cost
- no threshold tuning, weight sweep, commodity momentum, oil-only rescue, extra rescue asset, or production V6.6 change

All history is reused/development evidence, not untouched OOS confirmation.

## Signal evidence gate

The executed Phase C path uses the operator TradingView capture `pine-logs-MPM V6.6 PHASE C SRC.csv`:

- source SHA256 `6c5aa03419d2e5325d28fb33bf9c83a9744d7170da84f72a614676a7fc1aad4d`
- 5,458 raw rows; 5,451 unique dates
- reconstructed raw IPI finite on 5,137 dates
- 194 source dates with raw IPI >= +60
- 51/51 frozen Issue #64 audit checkpoints matched
- maximum absolute IPI difference `2.0430569236395968e-08`, below the frozen `5e-08` gate

This is the preregistered **equivalently exact verified reconstruction** route. Codex review also identified that the code advertised the old exact full-daily artifact as an accepted route without allowing Phase C to execute through it. The reviewed loader and CI now support both preregistered evidence paths:

1. equivalently exact verified reconstruction; or
2. exact prior full-daily artifact with source SHA `c0220d4974b2fd0154c4cf8f33b4b3effb27a58e21ee96a1b0109011ce638e3d`.

Each selected path must fully validate before Phase C can run.

## Primary result — Phase C fails

The rule activates on **74 outcome rows across 11 episodes**.

At 5 bp, Phase C minus Phase B on full reused history:

- ΔCAGR **-0.1362 pp/year**
- ΔSharpe **-0.0228**
- Δmaximum drawdown **-0.8831 pp** worse
- ΔCalmar **-0.0254**
- Δannualized turnover **+0.144x/year**

Both era slices are negative. At 0 bp, full-history ΔCAGR is still about **-0.1287 pp/year** and ΔSharpe **-0.0222**, so the failure is not caused by transaction costs.

## Complete realized attribution: gross, cost, net

The reviewed accounting separates three different objects instead of calling all post-activation effects “gross attribution”:

1. **Gross asset-mix effect:** each asset return times the difference in realized invested weights between Phase C and Phase B.
2. **Transaction-cost residual:** the difference between each simulation's net return and gross asset-mix return.
3. **Net effect:** Phase C net return minus Phase B net return.

Gross plus cost residual reconciles exactly to the arithmetic net-return difference.

Full reused history:

- cumulative gross allocation effect: **-2.2339%**
- annualized arithmetic gross effect: **-0.114234 pp/year**
- active-state gross effect: **-2.2800%**
- inactive post-deactivation gross drift: **+0.0461%**
- cumulative transaction-cost residual difference: about **-0.1407%**
  - active-state cost residual: about **-0.0605%**
  - inactive exit/reconvergence cost residual: about **-0.0802%**
- cumulative arithmetic net difference: about **-2.3746%**
- annualized arithmetic net difference: about **-0.1214 pp/year**

There are 42 inactive rows with nonzero gross allocation difference, 15 inactive rows with nonzero cost difference, and 49 inactive rows with nonzero net difference. Maximum daily gross reconciliation is about `3.47e-18`; net reconciliation is exact to reported precision.

Era-level annualized arithmetic net effects remain negative:

- pre-2020: about **-0.1466 pp/year**
- post-2019 reused: about **-0.0720 pp/year**

This accounting correction does not change the primary Phase C strategy metrics or verdict.

## Preregistered regime reporting

The preregistration explicitly required `average_allocation_by_regime`, `asset_contribution`, and `regime_contribution`. Codex correctly identified that the earlier Phase C artifact did not emit those tables.

The reviewed evaluator now produces:

- `issue-74-phase-c-asset-contribution.csv`
- `issue-74-phase-c-regime-contribution.csv`
- `issue-74-phase-c-reporting-reconciliation.csv`

On all full-history Stagflation rows:

**Phase B**

- 468 observations
- annualized net contribution about **-0.3242 pp/year**
- realized average allocation ≈ 19.88% SPY / 19.90% TLT / 60.23% SHV / 0% GSG

**Phase C**

- 468 observations
- annualized net contribution about **-0.4456 pp/year**
- realized average allocation ≈ 19.93% SPY / 19.89% TLT / 56.96% SHV / 3.22% GSG

The average GSG weight is far below 20% because the +60 severe-inflation condition is active only on a subset of Stagflation rows. The full-sample Stagflation contribution is worse under Phase C than Phase B.

## Episode concentration

Episode concentration remains intentionally **active-state only**. Inactive post-deactivation drift and exit costs are not assigned to an episode; they are represented in the complete gross/cost/net attribution and overall strategy metrics above.

- full active-only log return: **-2.441948%**
- best episode 2022-03-02 → 2022-04-04: **+0.996495%**
- excluding that winner: **-3.438443%**
- pre-2020 active-only: **-1.944501%**
- post-2019 reused active-only: **-0.497446%**

So 2022 was a genuine commodity success, but it does not generalize into a stable `Stagflation + IPI >= +60 → 20% GSG` rule.

## Decision

Verdict:

`preregistered_gsg_satellite_does_not_add_historical_value_over_deep_cash_in_v66_severe_stagflation`

Interpretation:

- Phase C **does not pass**.
- Broad commodities are not supported as a default 20% satellite under this frozen severe-Stagflation rule.
- Phase A's Cash / very-short Treasury core defensive evidence remains intact.
- Phase B does not become a universal 60% Cash rule.
- This result rejects this specific GSG allocation and conditioning rule; it does not prove commodities are useless in every portfolio or inflation shock.
- No rescue tuning is permitted inside Issue #74.
- V6.6 remains a risk-overlay candidate, not a validated production allocator.

## Review hardening

Current code and CI now enforce the Codex findings:

1. Severe-inflation readiness requires full validation, not file existence.
2. Both preregistered severe-evidence routes can actually drive Phase C.
3. Realized gross attribution uses actual invested weights.
4. Gross allocation, transaction-cost residual and net effects are explicitly separated and reconciled.
5. Episode concentration is active-only.
6. Average allocation by regime, asset contribution and regime contribution are emitted for Phase B and Phase C.
7. PR validation checks out immutable `github.event.pull_request.head.sha` before checked-out research code executes.
8. Focused regression tests protect the reviewed episode scopes and legacy evidence fallback.

## Reviewed provenance

Reviewed research code head `5765b2304bf128b74b8bcce902334ee483c8f46c`, pinned GitHub Actions run `34077133711` — success.

Phase C artifact `10002497479`, digest `sha256:e25c47f42e48215af872662b58159ed387c03db3c17639d6e648d0836abfbf25`.

This artifact contains the corrected active-only episode analysis, complete gross/cost/net attribution, and preregistered regime reporting. Subsequent decision/test-only heads should reproduce the same evidence under pinned PR validation.
