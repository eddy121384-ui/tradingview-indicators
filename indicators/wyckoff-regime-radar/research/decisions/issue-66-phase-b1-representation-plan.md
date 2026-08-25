# Issue #66 Phase B-1 — Reciprocal-Safe Representation Experiment

Status: preregistered before implementation.

## Question

Does repairing only the classifier's price representation materially improve reciprocal symmetry before any directional heuristic or stage formula is touched?

Core invariant:

```text
classifier(P) ≈ mirror(classifier(1 / P))
```

with OHLC reciprocal transform `O'=1/O`, `H'=1/L`, `L'=1/H`, `C'=1/C` and stage mirror `1↔4`, `2↔5`, `3↔6`, `0↔0`.

## Frozen baseline

Phase A clean-branch reproduction on the reused four-FX fixtures:

- raw range-break reciprocal Jaccard: 100% / 100%;
- MA-cross reciprocal Jaccard: 92.43% / 93.64%;
- Candidate-display mirror: 74.32%;
- Formal mirror: 76.11%;
- Candidate transition-pair mirror: 67.84%;
- Formal transition-pair mirror: 73.36%;
- raw-stage vector MAE: 3.880591;
- effective-stage vector MAE: 5.294190;
- probability vector MAE: 9.239240.

No PnL or strategy statistic may be consulted.

## Single experimental slice

Only the representation family may change in B-1.

1. Replace arithmetic SMA price representation with a geometric/log-space moving-average representation:
   - `ma_log = SMA(log(price))`;
   - exposed price-space `ma = exp(ma_log)` only where existing downstream comparisons require a price level.
2. Compute MA-cross events directly in log space.
3. Replace arithmetic `(close - MA) / ATR` heat and maturity distances with signed log-distance divided by log-space ATR.
4. Replace `ATR / close` low-volatility representation with log-space ATR.
5. Replace arithmetic range-width / ATR used only inside the range-score representation with log range width / log-space ATR.
6. Replace MA-spread / ATR continuation representation with signed log-MA spread / log-space ATR.

Log-space ATR is Wilder ATR applied to log OHLC. Under reciprocal OHLC, log highs/lows swap signs and the resulting true range is invariant.

## Explicitly frozen in B-1

Do **not** change:

- raw range-break definitions;
- v0.6 soft boundary functions;
- upside/downside range evidence multipliers (including 0.70 vs 0.85);
- recent range gates (including 0.85 vs 0.90);
- bearish-only MA qualifiers;
- Stage 1/4, 2/5, or 3/6 raw-score/gate products;
- candidate-conflict logic;
- persistence / inertia;
- any trading rule, position rule, PnL metric, or strategy score;
- frozen v0.5.2.1 source.

## Primary engineering gate

B-1 succeeds at its intended layer only if:

- MA-cross up→inverse-down and down→inverse-up Jaccard become effectively exact (`>= 0.999999` on the frozen fixtures); and
- the reciprocal MAE of the Phase-A `representation` numeric layer is lower than baseline.

## Secondary observations

Report, but do not tune against, downstream changes in:

- directional-mode event Jaccard;
- raw/gate/effective/probability stage-vector MAE;
- Candidate/Formal mirror agreement;
- Candidate/Formal transition-pair mirror agreement.

A downstream regression is evidence about the next non-isomorphic layer; it is not permission to tune thresholds or consult profitability.

## Decision rule

If the primary representation gate passes, retain B-1 as the next research baseline and move to one additional primitive family only. If it fails, diagnose the representation construction itself before touching directional heuristics.
