# Issue #68 — HARD Production Candidate Static / Deterministic Finding

## Decision

**STATIC / DETERMINISTIC GATE: PASS.**

This is not final production authorization. The next mandatory gate is TradingView runtime compile/load followed by the frozen six-market 1D regression.

## Candidate provenance

Generated artifact:

`indicators/wyckoff-regime-radar/research/generated/wyckoff-issue68-hard-current-context-production-candidate.pine`

Deterministic diff artifact:

`indicators/wyckoff-regime-radar/research/generated/wyckoff-issue68-hard-current-context-production-candidate.diff`

Generator:

`indicators/wyckoff-regime-radar/research/generate_issue68_hard_current_context_production_candidate_pine.py`

The candidate is mechanically derived from the immutable `v0.5.2.1` source, applies the accepted full Issue #57 / Issue #66 C-2 lineage without forcing price-only witness modes and without stripping production visuals/alerts, then applies only the frozen Issue #68 symmetric HARD routing.

GitHub Actions successfully generated and committed the candidate and diff as commit:

`0d30a5aac560bd635029445f11cfcaa564becb5c`

## Exact deterministic diff

The full C-2 baseline → HARD candidate diff contains only:

1. four new symmetric current-context lines:
   - `currentBearGate = f_gate(bearBg, 35.0, 75.0)`
   - `currentBullGate = f_gate(bullBg, 35.0, 75.0)`
   - `ctxDownExGate = math.min(downsideExhaustionGate, currentBearGate)`
   - `ctxUpExGate = math.min(upsideExhaustionGate, currentBullGate)`
2. S1 direct gate reroute:
   - `downsideExhaustionGate` → `ctxDownExGate`
3. S4 exact-mirror direct gate reroute:
   - `upsideExhaustionGate` → `ctxUpExGate`
4. one traceability comment identifying the Issue #68 HARD production candidate.

No other C-2 source line is changed.

## Frozen invariants confirmed statically

- S1/S4 RAW calculations unchanged.
- S2/S3/S5/S6 RAW, gates, witness multipliers, and pre-normalization effective calculations unchanged.
- Volume mode remains production `Auto` input.
- MTF mode remains production `Observe Only` input.
- Divergence mode remains production `Observe Only` input.
- Witness Stage Bias remains production `Balanced` input.
- Production `request.security_lower_tf` MTF implementation remains present.
- Production Visuals section remains present.
- Production alertcondition layer remains present.
- Plot-generating call footprint is identical to full C-2 baseline.
- No `strategy.entry`, `strategy.close`, price-only parity export, Fresh cohort, or Stateful/grace logic is present.
- The Issue #68 patch adds no lookback/indexed path condition, no `request.*`, no input/tuning parameter, and no state variable.

## Runtime gate — preregistered acceptance criteria

The candidate must now be loaded directly in TradingView as the full generated Pine above.

Runtime PASS requires all of the following before any six-market interpretation:

1. Pine compiles with zero errors.
2. Indicator loads on chart with no runtime error.
3. No TradingView `too many plot counts` / 64-count error.
4. Dashboard, production plots/background, and alerts remain available; the candidate must not look like a stripped parity/audit harness.
5. Normal chart warmup may show unavailable history, but there must be no new persistent NA/runtime failure attributable to Issue #68.
6. No source edit is allowed to make the candidate compile except a clearly non-semantic syntax fix. Any semantic change invalidates this preregistration and requires a new deterministic diff.

## Six-market regression — frozen panel

Only after runtime compile/load PASS, review full-history 1D charts for:

- US10Y
- DE10Y
- FR10Y
- GB10Y
- AU10Y
- JP10Y

The regression is semantic/classifier validation, not PnL evaluation.

Required review:

- confirm the motivating FR10Y 2022–2023 stale-S1 pathology is materially reduced;
- inspect whether S1/S4 exits now track current context rather than historical maturity memory;
- confirm no obvious catastrophic deletion of legitimate S1/S4 regimes;
- confirm S2/S3/S5/S6 behavior changes only as downstream competition/normalization consequences, not because their own logic changed;
- inspect warmup and recent-history behavior on every market;
- reject any proposal to retune 35/75, add market exceptions, revive Stateful grace, or optimize PnL based on this review.

## Authorization boundary

PR #73 remains Draft / Open. Issue #68 remains Open.

Do not modify the formal production source, mark PR ready, merge, or close #68 until TradingView runtime and the six-market regression pass.
