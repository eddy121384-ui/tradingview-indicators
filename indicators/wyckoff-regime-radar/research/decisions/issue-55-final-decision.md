# Issue #55 — Final research decision

## Verdict

`unstable_across_fx_pairs_or_oos`

This is the final decision for the frozen `Chase Risk Market Regime Radar v0.5.2.1` **price-only** FX validation.

The research execution itself succeeded: the frozen subject was mirrored, TradingView reference checkpoints were collected, canonical research inputs and splits were frozen, Development / Exploratory-OOS diagnostics were completed, the response map and baselines were committed before Final OOS, and the one-shot Final OOS was opened only after those rules were locked.

The price-only core did **not** demonstrate stable enough regime behavior across time/pairs to support a positive validation decision.

## Why this verdict, rather than another allowed outcome?

### Not `parity_or_data_blocked`

Parity/data issues were investigated rather than ignored. The OANDA-vs-Yahoo 2024 divergence localized a genuine feed-sensitive hard threshold in the frozen model. A reproducible static primary fixture was then frozen and used consistently for the primary experiment. The final experiment was therefore executable rather than blocked.

### Not `validated_incremental_utility`

The frozen regime response did not beat the simple price-only baselines in Final OOS.

Final-OOS equal-weight four-pair result:

- Wyckoff frozen response: net annualized return **0.35%**, Sharpe **0.11**
- SMA200: **4.92%**, Sharpe **0.98**
- Momentum60: **0.38%**, Sharpe **0.11**
- Donchian55: **3.45%**, Sharpe **0.70**

Wyckoff Final-OOS pair results:

- EURUSD: +3.46% annualized, Sharpe 0.66
- USDJPY: +0.82%, Sharpe 0.18
- GBPUSD: -4.70%, Sharpe -0.71
- AUDUSD: +1.52%, Sharpe 0.22

There is no robust incremental decision value versus the transparent trend/breakout baselines.

### Why not merely `descriptive_but_not_incremental`?

Because the descriptive behavior itself was not stable enough from one OOS segment to the next.

Before Final OOS:

- Formal Markup vs Formal Markdown had the expected directional ordering in only **4 / 31** comparable Development/Exploratory pair × horizon cases.
- Development→Exploratory formal-state return ranking was weak/unstable (median Spearman approximately -0.15 at 5 bars, +0.10 at 10/20 bars, -0.20 at 60 bars).
- Return-sign stability across Development→Exploratory was only about 42%–61% depending on horizon.
- Exploratory frozen-rule equal-weight trading utility was **-3.19% annualized**, Sharpe **-0.71**.

In the one-shot Final OOS, however:

- Formal Markup mean return exceeded Formal Markdown in **13 / 16** pair × horizon comparisons.
- The same frozen trading response improved to **+0.35% annualized**, Sharpe **0.11**.

The swing from mostly reversed directional ordering before Final OOS to mostly expected ordering in Final OOS is exactly the kind of temporal instability this experiment was designed to detect. A regime label that changes its outcome relationship materially between OOS periods is not yet a stable descriptive state variable.

## Additional failure signals

### Six-state coverage contracts materially on FX

The full six-state taxonomy was not populated in practice.

- In pre-final Exploratory OOS, individual pairs had only about 3–4 materially populated stages.
- Re-accumulation (3) and Redistribution (6) had no complete episodes across the four pairs in the pre-final analysis.
- In Final OOS, the median number of stages occupying at least 1% of bars was **4 / 6**.
- Stage 3 and Stage 6 remained absent from the Final-OOS bar-level horizon tables.

This means the claimed six-stage engine behaves more like a reduced-state classifier on these FX inputs.

### State separation is weak / inconsistent

Pre-final Exploratory median eta-squared for formal state explaining future return was approximately:

- 5 bars: 0.039
- 10 bars: 0.054
- 20 bars: 0.076
- 60 bars: 0.148

The one-shot Final-OOS median forward-return eta-squared fell to **0.034**.

So even when labels are treated merely as anonymous clusters, rather than requiring textbook Wyckoff semantics, future-return separation was not stable.

### Confidence is not calibrated

Exploratory OOS using Development-frozen confidence buckets:

- Evidence: high confidence beat low in **3 / 24** comparable cases (12.5%); strict monotonicity 1 / 24 (4.2%).
- Top Gap: high beat low in **10 / 20** (50.0%); strict monotonicity 1 / 20 (5.0%).

Final OOS:

- Evidence: high beat low in **13 / 32** (40.6%); strict monotonicity 3 / 28 (10.7%).
- Top Gap: high beat low in **6 / 28** (21.4%); strict monotonicity 2 / 28 (7.1%).

Neither field behaved like a reliably calibrated confidence measure.

### Feed-sensitive discontinuity is real

The 2024-04-16 TradingView/OANDA vs Yahoo diagnostic demonstrated that the frozen hard predicate

`close > previous 50-bar low ? 100 : 0`

can flip downstream Markdown gating and the candidate regime when price crosses the boundary by approximately 0.01 pip in the controlled diagnostic. This does not create the temporal-OOS verdict by itself, but it is an independent robustness concern.

## What this result means

The correct conclusion is **not** "Wyckoff is false" and not "the indicator is useless in every possible context."

It means the specific frozen v0.5.2.1 price-only implementation, with its current six-stage scoring, hard structural predicates, confidence fields, and formal-state persistence, did not survive the preregistered FX stability test strongly enough to justify treating its stage label as a stable out-of-sample regime variable.

The existing indicator can still be used as a descriptive/visual discretionary tool, but the current research does not support presenting its six-stage output or confidence fields as a validated predictive regime engine.

## Research consequence

Per Issue #55's decision boundary:

1. Stop before assuming Volume, MTF, or Divergence will rescue the core.
2. Do not tune v0.5.2.1 against the now-opened 2020-04-30..2022-03-04 Final-OOS window.
3. Any redesign must be a new version / new issue and use a new independent evaluation sample.
4. If a redesign is pursued, the first engineering targets should be structural rather than cosmetic:
   - replace brittle 0/100 hard price predicates with continuous/tolerance-aware measures;
   - revisit state persistence / confirmation lag;
   - verify whether six states are identifiable at all on the intended market/timeframe before forcing a six-state taxonomy;
   - redesign Evidence / Top Gap if they are intended to communicate confidence;
   - repeat validation on a higher-provenance normalized FX feed as an independent replication.

## Evidence trail

Primary files:

- `data/issue-55-static-fx-canonical-manifest.json`
- `decisions/issue-55-canonical-data-source-qualification.md`
- `decisions/issue-55-feed-sensitivity-finding.md`
- `decisions/issue-55-final-oos-response-map-and-baselines.md`
- `decisions/issue-55-final-oos-opening.md`
- `reports/issue-55-pre-final-regime-paths.md`
- `reports/issue-55-pre-final-regime-episodes.md`
- `reports/issue-55-pre-final-state-separation.md`
- `reports/issue-55-pre-final-confidence-calibration.md`
- `reports/issue-55-exploratory-trading-utility.md`
- `reports/issue-55-final-oos.md`
- corresponding JSON reports and frozen CSV inputs

## Final boundary

This Final-OOS sample is spent. It must not be reused to claim independent validation of any modified Wyckoff core.
