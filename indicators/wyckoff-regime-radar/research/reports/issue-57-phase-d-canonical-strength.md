# Issue #57 — v0.6 Phase D canonical strength audit

Status: **strength_calibration_audit_complete_pending_phase_d_decision**

Development-derived per-pair/per-state terciles applied unchanged to already-observed Exploratory and burned Final segments. Internal calibration-development evidence only; no PnL and no independent validation.

Development defines Low / Medium / High terciles per pair and canonical Formal state. Those cut points are then applied unchanged to the two later, already-observed segments.

The question is deliberately strict: does a higher score reliably mean a more persistent classification and a more directionally aligned Markup/Markdown outcome?

## exploratory_oos

| Metric | Retention: high>low | Retention monotonic | Median high-low retention | Direction: high>low | Direction monotonic | Median high-low aligned return |
|---|---:|---:|---:|---:|---:|---:|
| Formal Support | 26/27 (96.3%) | 15/27 (55.6%) | 0.3064 | 3/15 (20.0%) | 1/15 (6.7%) | -0.0028 |
| Formal Margin | 26/27 (96.3%) | 17/27 (63.0%) | 0.3010 | 3/15 (20.0%) | 2/15 (13.3%) | -0.0030 |
| Weight Concentration | 24/27 (88.9%) | 13/27 (48.1%) | 0.2522 | 8/15 (53.3%) | 3/15 (20.0%) | 0.0010 |

## final_oos

| Metric | Retention: high>low | Retention monotonic | Median high-low retention | Direction: high>low | Direction monotonic | Median high-low aligned return |
|---|---:|---:|---:|---:|---:|---:|
| Formal Support | 26/32 (81.2%) | 20/32 (62.5%) | 0.2990 | 6/24 (25.0%) | 2/24 (8.3%) | -0.0048 |
| Formal Margin | 26/32 (81.2%) | 21/32 (65.6%) | 0.2982 | 6/24 (25.0%) | 3/24 (12.5%) | -0.0047 |
| Weight Concentration | 26/32 (81.2%) | 12/32 (37.5%) | 0.1586 | 7/24 (29.2%) | 1/24 (4.2%) | -0.0024 |

## Metric definitions

- **Formal Support:** four-state weight assigned to the currently confirmed Formal regime.
- **Formal Margin:** Formal Support minus the strongest competing four-state weight. It can be negative when inertia is carrying a stale Formal label.
- **Weight Concentration:** normalized inverse entropy of the four canonical weights; high means the weight vector is concentrated, regardless of which state is Formal.

## Decision boundary

A metric may be called confidence only if Development-derived Low/Medium/High bins show repeatable high>low and preferably monotonic improvement in later observed segments for both state retention and directional Markup/Markdown outcomes. Otherwise retain descriptive names such as Support, Margin, or Concentration and do not present them as probability/confidence.
