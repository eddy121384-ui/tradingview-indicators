# Issue #109 A2 — TradingView exact trajectory export instructions

Use this only with:

`indicators/macro-pressure-map/research/issue-109-v66-a2-trajectory-export.pine`

## 1. Chart

Open:

- symbol: **SPY**
- timeframe: **1D**

The export needs history back to at least **2007-01-04**.

If the CSV later starts after that date, the acceptance gate will fail and no A2 payoff model will run.

## 2. Add the frozen production V6.6

Add:

`Macro Pressure Map V6.6 [Tiered GPI/IPI/FCPI]`

Use the same frozen/default research configuration.

Critical settings:

- Market Proxy Timeframe = `D`
- Fast Momentum Length = `20`
- Mid Momentum Length = `63`
- Smooth Main Pressure Lines = **ON**
- Pressure Line Smoothing Length = **5**

Do not alter weights, symbols, optional component toggles, macro-data toggles, thresholds, or other V6.6 research settings for this export.

## 3. Add the A2 helper

Paste/add:

`issue-109-v66-a2-trajectory-export.pine`

The helper has two source inputs.

Set:

- **Frozen V6.6 plot: GPI - Growth Pressure**
  → choose the `GPI - Growth Pressure` plot from the production V6.6 indicator.

- **Frozen V6.6 plot: IPI - Inflation Pressure**
  → choose the `IPI - Inflation Pressure` plot from the production V6.6 indicator.

Do not leave either source pointed at SPY close.

The helper's top-right status table should show:

- GPI source: `OK`
- IPI source: `OK`
- Raw axes: `READY`
- Trajectory: `READY`

## 4. Export

Use TradingView:

**Export chart data**

Export the full available SPY 1D history as CSV.

Do not edit the CSV.

Upload the raw exported CSV to ChatGPT.

## 5. Acceptance before payoff research

The CSV will be hash-frozen first.

Then `issue_109_a2_export_validation.py` must pass:

- date uniqueness/order;
- raw-axis reconstruction;
- 20/63 trajectory recomputation;
- 51 frozen #64 GPI/IPI checkpoints;
- exact regime mapping against #64 transition history.

Only after that gate passes may A2 compare:

`M0 = state only`

versus:

`M1 = state + exact GPI/IPI trajectory`

on the already-frozen pairwise asset outcomes.

No production V6.7 Action Layer is authorized by merely exporting the data.


## Essential plan fallback — Pine Logs instead of chart-data export

If the TradingView plan does not provide **Export chart data**, do not upgrade the plan and do not change the research source.

The helper now emits one compact `MPM_A2|...` Pine Log message per confirmed historical daily bar.

TradingView documents that Pine Logs work on historical bars and the Pine Logs pane keeps the most recent 10,000 historical log messages. Essential charts expose at least 10,000 historical bars when available, so one daily log per bar is sufficient for the required 2007-present SPY history.

### Steps

1. Use the same SPY / 1D / frozen V6.6 setup above.
2. Add the latest `issue-109-v66-a2-trajectory-export.pine`.
3. Bind the GPI and IPI source inputs to the production V6.6 plots.
4. Leave `Pine Logs start year = 2007`.
5. Open **Pine Logs** from the Pine Editor More menu or from the helper indicator's More menu.
6. Confirm the messages contain payloads beginning with:

   `MPM_A2|date=...`

7. Copy the Pine Logs text into a plain `.txt` file. It is fine if TradingView UI timestamps / labels are included around each message; the parser ignores unrelated text.
8. Upload the raw `.txt` file to ChatGPT without editing individual payload values.

The repo parser:

`issue_109_a2_pine_log_parser.py`

extracts the `MPM_A2` payloads into a canonical CSV. That CSV must then pass the exact same `issue_109_a2_export_validation.py` gate before any A2 payoff evaluation.

If copying all logs in one operation is awkward, do not manually retype them. Send screenshots / tell us where copying stops; the helper can be temporarily filtered into date chunks without changing any research variable.
