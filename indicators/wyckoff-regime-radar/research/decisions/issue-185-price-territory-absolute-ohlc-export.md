# Issue #185 — Absolute OHLC supplemental export (research-only)

**Status: EXPORTER AND LOCAL PARITY VALIDATOR READY; REAL TRADINGVIEW EXPORT NOT YET RECEIVED.** This document is NOT a historical C1 pass/fail claim. It does not alter prereg commit `066a8270`, C1 frozen gates (20%/90%/20%), source universe, OOS5 or production/Pine.

## Why one independent export?

The original #76 `ISSUE76|schema=1` Pine Logs intentionally encode `PRICE_LOG` moves for FX and 100x **yield-level changes** for government 10Y markets. They do not encode the actual **absolute source price/yield** of the bars. For PTM's A3 `w / abs(median close)` gate and its one-bar scale-break screen, arbitrary zero-anchoring of the original logs is mathematically invalid.

The new, standalone `research/issue185_absolute_ohlc_logger.pine` logs **absolute daily OHLC levels** for the same feed; it never recomputes the classifier, uses no indicator signals, reads no outcomes and cannot trade. Do not modify the original #76 generator or official indicator.

## How to export on TradingView

1. Open a **standard candlestick 1D** chart, **same exact feed** as the original #76 capture, one of the nine symbols below. No Heikin Ashi, Renko, synthetic charts, or changed adjustment/session settings.
2. Open **Pine Editor**; create a **new** indicator and paste the complete `research/issue185_absolute_ohlc_logger.pine` file. Save it as `#185 OHLC Research Export` and **Add to chart**. Do NOT replace #76 or the production indicator.
3. From the indicator's menu, open **Pine Logs**. Select this script's logs (not the previous #76 script), export as CSV, and save with a recognizable symbol and date interval name, e.g. `issue185-OANDA-EURUSD-2010-2019.csv`. Repeat for **all nine feeds**:

   - OANDA:EURUSD, OANDA:GBPUSD, OANDA:USDJPY
   - TVC:US10Y, TVC:DE10Y, TVC:FR10Y, TVC:GB10Y, TVC:AU10Y, TVC:JP10Y

4. **Important: TradingView caps historical Pine Logs at 10,000 messages per script execution.** If a feed has more bars, set the script Inputs `Bar start time` and `Bar end time` to successive **nonoverlapping intervals** (for example 2010–2014, 2015–2019, 2020–2026), re-run/log/export each interval. The validator deduplicates exact overlapping bars but does not hide a gap. Make sure the chart actually loads the *oldest needed historical bars*; the input date range cannot make earlier unloaded candles magically available. Essential/Plus historical limits can be material for pre-2000 bonds. If old price levels cannot be loaded under the plan, **stop** and report source not available rather than approximating them.
5. Upload the new #185 CSV exports (or ZIP of those CSVs) to the research conversation. Retain the **original nine #76 CSVs unchanged**. All 1D bars, including non-trend bars needed for pre-probe history, should be exported. Do not filter to B3 only. Don't publish raw pricing data to GitHub.

Every line should contain the marker `ISSUE185OHLC|schema=1` plus exact `ticker`, `repr`, `time` (Unix milliseconds), source `bar` (diagnostic only), and **native absolute o/h/l/c**. Cross-file alignment uses `ticker + time`, **NOT `bar_index`**, which can shift if a chart loads different historical depth. Output format is specified in the standalone script.

## Independent, fail-closed source audit (only after exports arrive)

From `indicators/wyckoff-regime-radar/research`:

```bash
python validate_issue185_absolute_ohlc.py \
  --old-glob '/private/old76/*.csv' \
  --new-glob '/private/new185/*.csv' \
  --out '/private/issue185_absolute_ohlc_audit.json'
```

The validator (standard library only):
- Verifies all **nine original #76** bytes and SHA-256 hashes against the frozen `issue185_real_cohort_manifest.json`, regardless of user-assigned CSV filenames.
- Requires nine matching symbols and matches each original #76 event by ticker and event-time to a new absolute-price bar; also requires its **next actual consecutive bar** to exist.
- Checks native OHLC envelope integrity and applies the original identities to **move1, mfe1, mae1**: for FX, `log(P_{t+1}/P_t)`; for yields, `100*(Y_{t+1}-Y_t)`. Text-rounding tolerances are fixed for **source parity only** (FX 5e-8, yields 5e-5 basis-point units); discrepancies, missing symbols, gaps, mixed `repr`, or conflicting duplicate candles **fail**. A changed vendor price series (e.g. some TVC bond periods) is **not** silently substituted.
- Writes a **counts-only private report**, with no raw OHLC or per-trade PnL; exit 0 only if all marker rows align and all parity checks pass. User-provided exports are untrusted until this succeeds.

**Passing one-bar parity is necessary, not sufficient.** The next, independently reviewed study stage must establish 120 contiguous *absolute* pre-probe bars per B3, correct baseline stage exit, frozen PTM C1 `evaluate_episode/evaluate_addon` semantics and a defensible net-trading-cost convention. Only then compare B0/B1 and C1 against the preapproved 20/90/20 outcome gates. **OOS5 remains untouched.**

## Reversibility / scope

These three standalone research files and one test do not modify original Issue #76 Pine logs, the frozen classifier, PTM mathematical code, data, or any production indicator. No new branch or merge is required. GitHub CI tests only small synthetic source-contract fixtures; **a green CI does not replace a real TradingView Pine compile/run or private-market parity verification**.
