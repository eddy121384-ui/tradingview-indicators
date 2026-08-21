# Issue #61 — Phase B Early-Damaged overlay decision

Status: **MIXED INCREMENTAL RISK VALUE; KEEP AS OPTIONAL WARNING, NOT CORE ENGINE**.

The Early-Damaged mechanics were frozen before PnL and evaluated as the third preregistered variant on the same four reused FX D1 fixtures.

## Result

Median-pair metrics:

| Variant | Gross ann return | Gross Sharpe | Gross max DD | Exposure | Turnover / yr |
|---|---:|---:|---:|---:|---:|
| stage_lifecycle_base | -1.72% | -0.271 | -16.41% | 43.43% | 8.28 |
| stage_lifecycle_plus_early_damage | -1.57% | -0.287 | -14.95% | 40.45% | 8.12 |

Incremental pair consistency versus base:

- gross return better: 3/4;
- gross Sharpe better: 2/4;
- gross max drawdown better: 2/4;
- net 2bp return better: 3/4;
- net 2bp Sharpe better: 2/4;
- net 2bp max drawdown better: 2/4.

The overlay generated 31 Early-Damaged pulses after warm-up, causing 7 long exits and 9 short exits. It also blocked 9 fresh entry attempts during the still-active damaged watch.

Per-pair behavior was mixed:

- EURUSD return/Sharpe improved slightly but max drawdown worsened;
- USDJPY improved materially in return, Sharpe, and drawdown;
- GBPUSD return/drawdown improved slightly while Sharpe worsened;
- AUDUSD worsened in return, Sharpe, and drawdown.

## Decision

Early Damaged retains evidence as a **transition-quality / risk-warning feature**, but it does not show enough uniform incremental performance to become a mandatory core lifecycle rule.

For Issue #61:

- keep `stage_lifecycle_base` as the core position-lifecycle candidate;
- retain Early Damaged as a separately switchable / descriptive risk overlay candidate;
- do not use Healthy +3 for entry or automatic re-risk;
- do not tune Early-Damaged severity, block duration, or weight thresholds from this result.

## Next phase

The base lifecycle has survived sufficiently as a development candidate to justify the preregistered Phase-C risk-management research.

Before choosing a partial-profit fraction, first audit whether Formal Stage 3 / Stage 6 actually occur often enough **while the base lifecycle is holding exposure** to support the user's intended semantics:

- Stage 3 = hold long core, candidate partial profit / risk reduction;
- Stage 6 = hold short core, candidate partial profit / risk reduction.

This next audit is event/occupancy only and must not inspect PnL. If Stage 3/6 are structurally sparse, do not invent partial-profit rules that cannot materially operate.

## Boundary

All evidence remains reused development evidence. No validation or production-trading claim is made.
