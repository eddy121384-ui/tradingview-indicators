# Issue #64 Phase C — Stagflation gold-over-equity robustness checkpoint

## Verdict

`stagflation_override_has_historical_risk_management_value_but_is_episode_concentrated`

Phase C kept the preregistered templates unchanged:

- neutral SPY/TLT/GLD = 40/40/20;
- Reflation = 60/20/20;
- Stagflation = 20/40/40.

No V6.6 parameter, threshold, or portfolio weight magnitude was tuned after results were viewed.

## Primary result

Relative to the already-frozen Phase B Reflation-only strategy, adding the Stagflation override improves full reused-history results at 5 bp costs:

- CAGR: 9.06% -> 9.30% (+0.24%/yr);
- Sharpe: 0.942 -> 0.962 (+0.020);
- maximum drawdown: -25.43% -> -23.07% (+2.36 percentage points);
- Calmar: 0.356 -> 0.403 (+0.047);
- annualized turnover rises from about 1.78x to 3.14x.

The full-history advantage remains positive at 10 bp costs, although it narrows.

## Portfolio contribution audit

Phase C now emits the Issue #64-required average allocation by regime, asset contribution, regime contribution, transaction-cost residual, and exact reconciliation tables from the frozen outcome-price snapshot. Regime attribution uses the prior-bar V6.6 state that was actually available to the portfolio on each return row.

For the full reused history, Phase C's annualized arithmetic contribution is:

- SPY: +5.87 percentage points;
- TLT: +1.54 percentage points;
- GLD: +2.12 percentage points;
- transaction-cost residual: -0.16 percentage points;
- total annualized arithmetic net return: +9.37%.

Within executed Stagflation Pressure rows, realized average allocation is approximately 19.87% SPY / 39.79% TLT / 40.34% GLD, confirming that the intended 20/40/40 template is actually expressed after drift. Importantly, the Stagflation regime remains a negative absolute contributor: about -0.56 percentage points per year. Under the Phase B Reflation-only strategy the same Stagflation rows contributed about -0.79 percentage points, so Phase C improves those rows by roughly +0.24 percentage points per year rather than turning them into a profit center.

That distinction strengthens the risk-overlay interpretation: the Stagflation rule historically acted more like drawdown mitigation / damage reduction than a standalone return engine. The largest positive regime contribution in Phase C remains Slowdown / Disinflation at about +4.04 percentage points per year; Reflation contributes about +2.58 percentage points.

The contribution tables reconcile to the portfolio arithmetic net return to floating-point precision. Maximum absolute asset-plus-cost reconciliation error and regime reconciliation error are both `2.78e-17` across full/pre-2020/post-2019 segments and all Phase C comparison strategies.

These diagnostics do not overturn the existing Phase C verdict. They make the mechanism more auditable while the leave-largest-episode-out robustness failure still stands.

## Realized-exposure attribution

A post-hoc noncausal control preserves the Phase B Reflation timing rule and shifts its neutral/Reflation templates only enough to match Phase C's realized average SPY/TLT/GLD exposure. This removes the simple explanation that Phase C wins merely because it carries more GLD and less SPY on average.

Timing residual versus that exposure-matched control:

- full history: +0.26% CAGR, +0.018 Sharpe, +0.045 Calmar;
- 2007–2019: +0.15% CAGR and only +0.002 Sharpe; drawdown/Calmar are worse than the exposure-matched control;
- post-2019 reused history: +0.45% CAGR, +0.036 Sharpe, +0.052 Calmar.

So the recent Stagflation effect is not explained away by average gold exposure alone.

## Episode concentration

The robustness gate fails, however, because the benefit is highly dependent on one large Stagflation episode in each era.

### 2007–2019

Largest winning Stagflation episode: **2007-09-17 -> 2008-01-17**.

- normal Phase C minus Phase B active log return: +0.01325;
- after removing that one episode's Stagflation override: -0.04835;
- incremental CAGR after leaveout: -0.41%/yr;
- incremental Sharpe after leaveout: -0.049.

### Post-2019 reused exploratory history

Largest winning Stagflation episode: **2021-12-29 -> 2022-06-06**.

- normal Phase C minus Phase B active log return: +0.02949;
- after removing that one episode's Stagflation override: -0.00319;
- incremental CAGR after leaveout: -0.05%/yr;
- incremental Sharpe after leaveout: -0.004.

Thus the attractive recent result is indeed strongly tied to the 2021-22 inflation episode, and the older-era result is also concentrated in one large episode.

## Interpretation

Phase C is stronger as a **historical risk-management / crisis-overlay candidate** than as evidence for a robust production allocation rule. The contribution audit sharpens that interpretation because the Stagflation state remains negative in absolute return contribution even after the defensive override; the improvement comes from losing less in those rows. The exposure-matched attribution says the state contains some timing information, especially after 2019, but the leave-largest-episode-out test says that information has not been broadly distributed across episodes.

Do not tune the 20/40/40 weights or thresholds to rescue the result. All history used here has already been inspected and remains development/reused exploratory evidence, not untouched OOS confirmation.

## Provenance

Contribution-audit source workflow: Actions run `33492086706` on code head `51a9998ac0b370bdda8e2ccb5dc6e0e5e79e8b0e`, conclusion `success`.

Phase C artifact: `9794326632`, digest `sha256:a2185cc603fafbdba6dc61bde43f05ca6f2ca8337b9ee0997d1ce0265dccb159`.

The artifact contains `phase-c-asset-contribution.csv`, `phase-c-regime-allocation-contribution.csv`, `phase-c-contribution-reconciliation.csv`, and `phase-c-contribution-manifest.json` together with the existing Phase C primary and robustness evidence. The contribution manifest confirms `committed_frozen_snapshot`, frozen CSV SHA-256 `3a7f590c146f9eda5920b6968fe86c9c3cc1887db35597f2d639a1c76b6e5a57`, and maximum reconciliation error `2.78e-17`.

## Decision

- Do not call V6.6 a validated production allocator.
- Keep the Reflation and Stagflation relationships as distinct exploratory allocation/risk-overlay findings.
- Treat the Stagflation result primarily as historical loss mitigation, not evidence that Stagflation rows are positively returning after the override.
- Do not optimize nine regime weights.
- The next useful research question should test whether a simpler, explicitly defensive **risk-overlay interpretation** can generalize without relying on one historical crisis episode, or wait for genuinely unseen future observations for confirmation.
