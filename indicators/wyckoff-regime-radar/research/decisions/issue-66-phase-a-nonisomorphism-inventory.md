# Issue #66 Phase A — source-level non-isomorphism inventory

Status: **diagnostic only / no formula repair / no PnL**

This inventory compares the frozen v0.6 Phase-B price-only classifier against the reciprocal contract `classifier(P) ≈ mirror(classifier(1/P))`. It records where bull/bear paths are structurally isomorphic, where reciprocal price representation is mathematically non-invariant, and where the source explicitly uses different bull/bear heuristics.

## 1. Raw OHLC / structural range events

### Structurally symmetric

The reciprocal OHLC transform is exact:

```text
O' = 1/O
H' = 1/L
L' = 1/H
C' = 1/C
```

The frozen 20-bar structural break tests are mirror formulas:

```python
range_break_up = close > prior_high and prior_close <= prior_prior_high
range_break_dn = close < prior_low  and prior_close >= prior_prior_low
```

Observed inherited audit result: both reciprocal Jaccards are `100%` on the four frozen FX fixtures.

Interpretation: the first material asymmetry does **not** originate in the raw range-break event definition.

## 2. MA / return / volatility representation

### Log-price return/slope family: algebraically favorable

The core already computes:

```python
log_price = np.log(close)
log_ret = np.log(close_t / close_t-1)
```

Under reciprocal quotation:

```text
log(1/P) = -log(P)
```

so signed log-price displacement is naturally compatible with direction reversal.

### Arithmetic moving averages: representation-level reciprocal mismatch

The classifier also computes arithmetic SMAs directly on price:

```python
ma = rolling_sma(close, ma_len)
maturity_ma = rolling_sma(close, maturity_ma_len)
```

but in general:

```text
SMA(1/P) != 1 / SMA(P)
```

Therefore `close > ma` does not map perfectly to reciprocal `close < ma`, and the same is true for MA crossover/crossunder events. This is an upstream mathematical source of asymmetry even before any unequal bull/bear heuristic constants are applied.

Observed inherited audit result: MA-cross reciprocal Jaccard is only about `92–94%`, versus `100%` for raw range breaks.

### ATR / price normalization: not exactly reciprocal-invariant

The classifier uses arithmetic-price ATR and quantities such as:

```python
dist_atr = (close - ma) / atr
atr_pct = atr / close
```

Under `P -> 1/P`, ATR is not transformed by a constant sign flip or scale factor. Consequently ATR-normalized MA distance, percentile ranks derived from it, low-volatility flags, soft boundary widths, and downstream heat/maturity inputs can inherit quote-direction differences.

Phase-B implication: representation repair should be evaluated before stage-formula repair.

## 3. Directional breakout / breakdown evidence

### Explicit unequal range-evidence scales

Frozen v0.6 uses:

```python
breakout_range_evidence = recent_range_break_up_strength * 0.70
breakdown_range_evidence = recent_range_break_dn_strength * 0.85
```

This is a direct source-level non-isomorphism.

### Explicit unequal recent-range gate scales

Frozen v0.6 uses:

```python
breakout_recent_range_gate = recent_range_break_up_strength / 100 * 0.85
explicit_recent_breakdown_gate = recent_range_break_dn_strength / 100 * 0.90
```

This is also a direct source-level non-isomorphism.

### MA evidence path is not the same function with direction reversed

Bull path:

```python
breakout_ma_evidence = where(recent_ma_cross_up, 70,
                             where(close > ma, 35, 0))
```

Bear path:

```python
breakdown_ma_evidence = where(
    recent_ma_cross_dn
    and panic_heat_dn >= orange
    and structure_weak >= 50,
    55,
    0,
)
```

The downside path requires additional panic/structure qualifiers and uses a different score level. This is semantic asymmetry, not merely reciprocal representation error.

## 4. Trend stage gates: Markup vs Markdown

### Breakout confirmation products are non-isomorphic

Stage-2 breakout component:

```python
breakout_markup_gate = (
    breakout_gate
    * structure_strong_gate
    * non_end_up_gate
)
```

Stage-5 breakdown component:

```python
breakdown_markdown_gate = (
    explicit_breakdown_gate
    * gate(panic_heat_dn, 40, 80)
    * structure_weak_gate
)
```

The downside path has an explicit panic gate; the upside path instead has `non_end_up_gate`. There is no same-form `direction` parameterization here.

### Extension / continuation subpaths are closer to mirror form

The `markup_extension_gate` / `markdown_extension_gate`, `markup_cont_gate` / `markdown_cont_gate`, MA-spread conditions, and extension-score constructions are much closer to explicit bull/bear mirrors. They can still diverge because their upstream arithmetic MA/ATR and evidence inputs are not reciprocal-safe.

Interpretation: Phase A should distinguish **structural formula asymmetry** from **symmetric formulas fed asymmetric representations**.

## 5. Accumulation vs Distribution family

### Raw-score terminal components differ

Accumulation raw score ends with:

```python
low_vol_score * 0.10
```

Distribution raw score ends with:

```python
bear_pressure_rising * 0.10
```

Those are not reciprocal counterparts.

### Gate backgrounds differ

Accumulation uses:

```python
bear_background_acc_gate
```

while Distribution uses:

```python
mature_bull_gate
```

These encode different narrative semantics rather than a single mirrored function.

## 6. Re-accumulation vs Redistribution family

Re-accumulation raw/gate logic and Redistribution raw/gate logic are not simple mirrors. In particular, Redistribution introduces `rebound_failure` / `rebound_failure_gate`, whereas Re-accumulation uses a different combination including `100 - panic_heat_dn` and `100 - bear_pressure_rising`.

This is a source-level family asymmetry and should be redesigned only after the more upstream representation/evidence layers are measured.

## 7. Evidence / candidate logic

### Stage-support asymmetry for Stage 2 vs Stage 5

Stage 2 support includes:

```python
max(breakout_score, structure_strong)
```

Stage 5 support includes:

```python
max(explicit_breakdown_gate * 100, panic_heat_dn)
```

Again, these are not the same function under direction reversal.

### Candidate-conflict asymmetry for Stage 1 vs Stage 4

The Stage-1 conflict clause uses resistance/rebound-failure logic, whereas the Stage-4 clause uses support/downside-exhaustion logic. Other pairs such as Stage 2/5 and much of Stage 3/6 are closer to mirror form.

## 8. Persistence / confirmation shell

The strong/weak candidate classification, fast Markup/Markdown confirmation shape, and imperative formal-state inertia loop are largely stage-agnostic or written as explicit Stage-2/Stage-5 mirrors.

The Issue #57 Phase-B stale-state decay is also direction-neutral in control flow: chaos, weak challenger, and coexistence pressure are handled without a bull-only or bear-only branch.

Working interpretation for Phase A:

> persistence can amplify an upstream mismatch by carrying it forward, but the main directional bias is introduced before persistence.

## Phase-A ordering consequence

The current source evidence supports the preregistered Phase-B order:

```text
1. representation (log displacement / MA / ATR normalization)
2. range-break / continuation evidence
3. structure strength / weakness
4. extension / exhaustion / holding
5. Markup / Markdown
6. Accumulation / Distribution / Reaccumulation / Redistribution
```

Do not equalize isolated constants yet. First use the reciprocal decomposition report to quantify exactly how much error appears at each layer on the unchanged frozen classifier.
