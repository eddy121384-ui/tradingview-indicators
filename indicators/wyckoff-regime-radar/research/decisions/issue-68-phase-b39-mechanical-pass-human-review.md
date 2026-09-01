# Issue #68 Phase B3.9 — Mechanical PASS / Human Review Gate

Status: **MECHANICAL PASS / HUMAN TRADINGVIEW REVIEW REQUIRED / NO PERFORMANCE**

## Mechanical result

Frozen four-FX diagnostics passed all preregistered B3.9 engineering gates:

- usable direction observations: 10,776;
- raw-loss observations: 7,620;
- unexplained exact raw winner: 0;
- exact winner accounting delta: 0;
- minimum reciprocal boolean agreement: 99.480%;
- minimum exact raw-winner-stage mirror agreement: 99.555%;
- fresh target share while target family loses: 46.4%.

## Generic Bull-side baseline

When the Bull target family (S2/S3) loses at the raw layer, exact competitor winners are:

- EURUSD: S1 328 / S4 226 / S5 438 / S6 0;
- USDJPY: S1 335 / S4 300 / S5 375 / S6 0;
- GBPUSD: S1 230 / S4 297 / S5 369 / S6 3;
- AUDUSD: S1 302 / S4 214 / S5 471 / S6 0.

Thus S5 Markdown is a major generic Bull suppressor; S1/S4 range stages are also material; S6 is negligible in this baseline. This is descriptive baseline evidence, not a claim that FR10Y/JGB10Y are caused by S5.

The Bull family is internally led by fresh Stage2 on only 46.4% of target-loss observations; Stage3 continuation/reaccumulation leads slightly more often while the target family is losing.

## Locked human review

Use:

`indicators/wyckoff-regime-radar/research/generated/wyckoff-issue68-phase-b39-raw-formulation-attribution-audit.pine`

Settings:

- Audit Direction = Bull.
- FR10Y 1D, focus 2021–2024 — primary adverse case.
- JGB10Y 1D, focus 2021–2024 — control.

Bands:

1. RAW ADV
2. FRESH TARGET
3. > S1
4. > S4
5. > S5
6. > S6
7. BREAK
8. STRUCTURE

Interpretation:

- >S5 persistent red -> old Markdown raw remains too competitive;
- >S6 persistent red -> Redistribution remains too competitive;
- >S1 or >S4 persistent red -> range-family raw suppresses trend leadership;
- competitors mostly green but FRESH TARGET red -> target family is being expressed mainly as Stage3 rather than fresh Stage2;
- BREAK/STRUCTURE red together with >S5 red -> directional fresh-trend formulation is the leading local suspect;
- BREAK/STRUCTURE green while a range stage suppresses target -> inspect range-family formulation instead.

## Boundary

No classifier formula, weight, threshold, gate, persistence, Core Bias, Exposure, or strategy-performance rule may be changed before FR10Y/JGB10Y B3.9 human review is recorded.

PR #73 remains Draft/open. Issue #68 remains open. No merge/close without explicit Eddy approval.
