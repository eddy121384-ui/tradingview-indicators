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

Phase C is stronger as a **historical risk-management / crisis-overlay candidate** than as evidence for a robust production allocation rule. The exposure-matched attribution says the Stagflation state contains some timing information, especially after 2019, but the leave-largest-episode-out test says that information has not been broadly distributed across episodes.

Do not tune the 20/40/40 weights or thresholds to rescue the result. All history used here has already been inspected and remains development/reused exploratory evidence, not untouched OOS confirmation.

## Provenance

- official Phase C primary artifact: Actions run `33038153870`, artifact `9632868973`, digest `sha256:ee0d592cd15f646718337ff26bbf2208a79a21cc9ee372892cda5d3eae7aa1b1`;
- current-head robustness workflow: Actions run `33038423000` on `1dbc8453e8f35cd076cc554c3430c78f12111c7b`, conclusion `success`;
- the three-day artifact retention expired before this follow-up; the official Phase C daily artifact was replayed using the current-head accounting/diagnostic contract with maximum absolute net-return replay error below `6.7e-16`.

## Decision

- Do not call V6.6 a validated production allocator.
- Keep the Reflation and Stagflation relationships as distinct exploratory allocation/risk-overlay findings.
- Do not optimize nine regime weights.
- The next useful research question should test whether a simpler, explicitly defensive **risk-overlay interpretation** can generalize without relying on one historical crisis episode, or wait for genuinely unseen future observations for confirmation.
