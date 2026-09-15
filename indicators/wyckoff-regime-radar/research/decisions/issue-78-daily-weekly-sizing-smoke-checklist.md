# Issue #78 — Daily × Weekly Sizing Smoke / Export Checklist

## Goal

Collect compact native-weekly context evidence for the nine frozen Issue #76 markets. The existing accepted daily logs do not need to be re-exported.

Generated Pine:

`indicators/wyckoff-regime-radar/research/generated/wyckoff-issue78-weekly-context-logger.pine`

Indicator title:

`Chase Risk Weekly Context Logger｜Issue #78`

## TradingView smoke

For each market:

1. Open the **native 1W chart**.
2. Paste / run the generated logger.
3. Confirm there is no Pine compile/runtime error.
4. Confirm the indicator header is `Chase Risk Weekly Context Logger｜Issue #78`.
5. Confirm Pine Logs contain rows beginning with:
   `ISSUE78WEEKLY|schema=1`
6. Inspect one row and confirm it contains:
   - `ticker=`
   - `tf=1W` (TradingView may render the weekly period using its canonical weekly string)
   - `week_open_time=`
   - `week_close_time=`
   - `formal=`
   - `er13=` / `er26=` / `er52=`
   - `er13r=` / `er26r=` / `er52r=`
   - `wtrend=`
7. Do **not** alter classifier inputs between markets.
8. Keep Auto representation unchanged.

## Frozen market list

- `OANDA:EURUSD`
- `OANDA:GBPUSD`
- `OANDA:USDJPY`
- `TVC:US10Y`
- `TVC:DE10Y`
- `TVC:FR10Y`
- `TVC:GB10Y`
- `TVC:AU10Y`
- `TVC:JP10Y`

## What to export

Export the Pine Logs CSV for each market and upload all nine files together.

The weekly export is intentionally compact: roughly one log row per confirmed week, not one row per daily bar.

## Causal contract

The downstream analyzer uses only the most recent weekly row satisfying:

`week_close_time <= daily_event_time`

This intentionally prevents an incomplete current weekly candle from informing a daily decision.

## What happens after upload

Run:

`analyze_issue78_daily_weekly_sizing.py`

It compares the frozen three-policy set:

1. Daily-only Persistence + Gentle benchmark.
2. Daily + weekly formal-direction sizing cap.
3. Daily + weekly formal-direction + Weekly Trendability sizing cap.

Primary output includes cross-market expectancy, PF, MDD, turnover, exposure, MFE slices, tail stress, friction sensitivity and the already-frozen 2010–2014 / 2015–2019 / 2020–2026 temporal slices.

No threshold tuning is permitted after first results.