# Issue #66 — Directional Symmetry Repair preregistered plan

Status: **frozen before any Issue #66 PnL evaluation**

## Research question

Can the Wyckoff Regime Radar price-only classifier be redesigned so reciprocal quotation behaves as direction reversal rather than as a materially different market state?

Required semantic invariant:

```text
classifier(P) ≈ mirror(classifier(1 / P))
```

Stage mirror:

```text
0 ↔ 0
1 ↔ 4
2 ↔ 5
3 ↔ 6
```

Correct reciprocal OHLC transform:

```text
O' = 1 / O
H' = 1 / L
L' = 1 / H
C' = 1 / C
```

## Frozen inherited baseline

From completed Issue #61 reciprocal diagnostics on reused EURUSD / USDJPY / GBPUSD / AUDUSD daily fixtures:

- raw range-break up → inverse down Jaccard: 100%;
- raw range-break down → inverse up Jaccard: 100%;
- MA-cross mirror Jaccard: roughly 92–94%;
- Candidate-display stage mirror: 74.32%;
- Formal-stage mirror: 76.11%;
- human-review lifecycle-position mirror: 86.44%.

These values are the engineering baseline, not an optimization target selected from profitability.

## Known source-level non-isomorphisms to reproduce before repairing

1. upside breakout range-evidence scale `0.70` vs downside `0.85`;
2. upside recent-range gate scale `0.85` vs downside `0.90`;
3. downside MA-breakdown evidence adds `panic_heat_dn` / `structure_weak` qualifiers without an isomorphic upside path;
4. Stage-2 breakout gate and Stage-5 breakdown gate use different confirmation products.

Phase A must confirm where each divergence enters the pipeline before formulas are redesigned.

## Architecture rule

Do not create separate hand-tuned bullish and bearish formulas where a shared directional primitive can express both.

Preferred pattern:

```text
feature(direction = +1)
feature(direction = -1)
```

where reciprocal price maps to direction reversal.

Use log-price or other dimensionless signed representations where they improve inversion invariance naturally:

```text
log(1 / P) = -log(P)
```

This does not require every real-world market outcome to be symmetric. It only requires the classifier to describe the same price path consistently when quotation is inverted.

## Phase A — reproduce and decompose

No PnL.

Measure reciprocal agreement at these layers:

1. raw OHLC/range events;
2. MA / return / volatility representation;
3. directional evidence primitives;
4. stage gates and effective stage scores;
5. Candidate state;
6. Formal state / persistence.

Use sparse-event Jaccard for event pulses and numeric error / mirror agreement for continuous scores. Do not rely on bar-level accuracy alone when the positive event is sparse.

## Phase B — redesign direction-neutral primitives

No PnL.

Work one primitive family at a time, in this order unless Phase A shows a dependency that requires reordering:

1. price displacement / return / slope;
2. range break and continuation;
3. structure strong / weak;
4. extension / exhaustion / holding;
5. Markup / Markdown trend gates;
6. Accumulation / Distribution and re-accumulation / redistribution families.

Do not repair the system by manually equalizing isolated constants without explaining the shared functional form.

## Phase C — symmetry engineering gate

No PnL.

Report:

- numeric mirror error for primitives and stage weights;
- sparse-event Jaccard;
- Candidate mirror agreement;
- Formal mirror agreement;
- transition / persistence mirror agreement.

Current Formal baseline is 76.11%. A practical goal of 95%+ may be used as an engineering checkpoint, but architecture and invariants—not threshold shopping—must explain any improvement.

## Phase D — TradingView parity / visual review

Only after the Python classifier is substantially inversion-safe:

- generate Pine from the same implementation contract;
- compile in TradingView;
- establish Pine ↔ Python parity;
- visually inspect state behavior.

Still no strategy or profitability claim.

## PnL lockout

Until the symmetry + parity gates are satisfied, Issue #66 must not use any of the following to choose formulas or thresholds:

- CAGR / annualized return;
- Sharpe / Sortino;
- drawdown;
- win rate;
- Profit Factor;
- trade expectancy;
- Strategy Tester net profit;
- EURUSD / GBPUSD / USDJPY long-vs-short profitability.

Previously observed apparent USD-strength preference is treated as confounded evidence until symmetry repair is complete.

## Preservation / archive rules

- frozen v0.5.2.1 source remains untouched;
- archived Issue #57 / PR #58 and Issue #61 / PR #63 branches remain unchanged;
- Issue #66 starts from clean `main` and imports only the minimum diagnostic evidence required to reproduce the asymmetry;
- do not delete historical research branches as part of this redesign.

Refs #66, #61, #63, #57, #58.
