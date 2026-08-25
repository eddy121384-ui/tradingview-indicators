# Issue #66 Phase D-1 — Static Pine↔Python Readiness

Status: **STATIC READY / TRADINGVIEW RUNTIME EVIDENCE PENDING**

This note does not claim TradingView runtime parity. It records that the accepted C-2 price-only reference has an auditable Pine parity harness and comparator that pass repository-side contracts, and that the critical formula lineage has been manually cross-checked against the Python generators.

## Repository-side result

Workflow: `Wyckoff Issue 66 Phase D1 Parity`

Latest validated D-1 contract run after source-anchor and CSV-roundtrip test fixes: **SUCCESS**.

Repository-side gates passed:

- Phase C-3 parent contract;
- frozen-source anchored Pine generator contract;
- C-2 comparator self-consistency contract;
- deliberate Formal-ID corruption is correctly rejected;
- deterministic Issue #66 C-2 parity Pine generation.

Generated harness:

`indicators/wyckoff-regime-radar/research/generated/wyckoff-issue66-phase-d1-c2-parity.pine`

The harness exposes exactly 36 Data Window plots and stays below TradingView's 64-plot limit.

## Static lineage audit

The generated Pine was manually checked against the accepted Python generator chain.

### Issue #57 v0.6 boundary primitives

- no-break-low/high geometry matches the Python 0/50/100 ATR-scaled transition;
- breakout/breakdown strength matches the one-sided 0→100 ATR-scaled ramp;
- N-bar soft hold uses `ta.lowest(..., bars)`, matching Python `soft_hold_strength`, which returns the weakest value in an all-finite rolling window.

### Issue #66 B-1 representation

- geometric MA = `exp(SMA(log(price)))`;
- log true range is `max(logH-logL, |logH-prevLogC|, |logL-prevLogC|)`;
- log ATR uses Wilder/RMA, matching Python `atr(log_high, log_low, log_price)`;
- distance, maturity distance, low-vol representation, MA cross, range width and MA spread use the registered log-space forms.

### B-2 break evidence

Both directions use the same structure:

- range component = clipped recent soft range-break strength;
- MA component = 70 on recent MA cross, else 35 on directional MA side, else 0;
- score = 100 in mode, otherwise max(range, MA);
- classifier-facing gate = score / 100.

### B-3 fresh trend entry

Both directions use `break gate × structure gate × non-end gate`.

### B-5 / B-6 / B-7

- Stage 3/6 raw counter-pressure uses `100 - opposite heat` symmetrically;
- Stage 1/4 raw quiet-range context uses the same low-vol score;
- Stage 1/4 background/maturity gate uses the same `gate(max(background, maturity_trace), 35, 75)` primitive.

### C-2 candidate conflict

The generated Pine Stage-1 clause matches the accepted C-2 Python clause:

`Stage 1 = resistance holding + upside exhaustion + NOT markdown continuation override`

and is the reciprocal mirror of canonical Stage 4:

`Stage 4 = support holding + downside exhaustion + NOT markup continuation override`.

Stage 2/5 and Stage 3/6 clauses remain the accepted mirrored pairs.

### Issue #57 Phase-B persistence

The Pine state machine matches the Python reference:

- strong candidate uses the existing confirmation path;
- stale pressure resets on a strong candidate;
- stale-pressure reason priority is chaos (1), weak challenger (2), coexistence (3), otherwise 0;
- unsupported Formal state clears after `2 × confirmBars`;
- weak challengers are never promoted directly.

## Known boundary

The repository cannot execute TradingView Pine runtime. Therefore this phase is not complete until the generated harness is compiled/run in TradingView and chart data is exported.

The preregistered runtime gate remains unchanged:

- Formal stage agreement >= 99.5%;
- Candidate-display agreement >= 99.0%;
- core continuous-field P99 absolute error <= 0.50 points.

TradingView OHLC from the export must be reused as Python input so feed differences cannot masquerade as implementation differences.

## Next evidence

Load `wyckoff-issue66-phase-d1-c2-parity.pine` in TradingView, add it to a chart, export chart data containing OHLC plus all `PARITY ...` columns, and feed that CSV to:

`compare_issue66_phase_d1_tradingview_parity.py`

A failure may authorize implementation/runtime-semantic fixes only. C-2 formulas and thresholds remain frozen.
