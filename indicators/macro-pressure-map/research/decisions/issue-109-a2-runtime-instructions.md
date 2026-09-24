# Issue #109 A2 — TradingView exact trajectory runtime instructions

## Preferred path — self-contained r4

Use:

`indicators/macro-pressure-map/research/issue-109-v66-a2-selfcontained-export.pine`

This replaces the earlier manual `input.source()` transport. Do **not** use the older source-binding helper for a new attempt.

### 1. Chart

Open:

- symbol: **SPY**
- timeframe: **1D**

The r4 helper fails closed on any other chart symbol or timeframe.

You do **not** need to add the production V6.6 indicator and you do **not** need to bind GPI/IPI source inputs.

### 2. Add r4

Paste/add:

`issue-109-v66-a2-selfcontained-export.pine`

The top-right status table must show:

- Chart symbol: `SPY OK`
- Chart timeframe: `1D OK`
- GPI axis: `READY`
- IPI axis: `READY`
- Trajectory: `READY`
- Pine Logs: `MPM_A2 r4sc`

The script hard-codes the frozen Issue #59/#64 market-axis configuration. Do not edit symbols, weights, lookbacks, or formulas.

### 3. Pine Logs — Essential plan path

Open **Pine Logs** from the Pine Editor More menu or the indicator's More menu.

The payloads must begin with:

`MPM_A2|date=...`

and end with:

`|helper_rev=r4sc`

One compact row is emitted for each confirmed eligible SPY daily bar from 2007 onward.

Copy/save the Pine Logs to a raw `.csv` or `.txt` file and upload it to ChatGPT. Do not edit payload values.

### 4. Acceptance before payoff research

The uploaded log is frozen by SHA-256 first.

Then:

1. `issue_109_a2_pine_log_parser.py` parses the `MPM_A2` payloads;
2. `issue_109_a2_export_validation.py` must pass:
   - unique/increasing dates;
   - exact 20/63 trajectory recomputation;
   - frozen #64 GPI/IPI axis checkpoints;
   - zero regime mismatch against #64 transition history;
   - SPY-calendar historical coverage sufficient for the frozen gate.

Only after this gate passes may A2 compare:

`M0 = state only`

versus:

`M1 = state + exact GPI/IPI trajectory`

on the already-frozen pairwise asset outcomes.

No production V6.7 Action Layer is authorized by data export alone.

---

## Superseded path — manual input.source helper

The earlier:

`issue-109-v66-a2-trajectory-export.pine`

is retained only as an audit trail for the failed pre-outcome transport attempts.

Do not use it for the next runtime attempt. The self-contained r4 helper is the current transport.
