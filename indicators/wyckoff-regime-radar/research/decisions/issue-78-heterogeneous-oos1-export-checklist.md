# Issue #78 — Heterogeneous OOS1 Export Checklist

This checklist is operational only. It does not change the preregistered research design.

## Use this generated Pine logger

`indicators/wyckoff-regime-radar/research/generated/wyckoff-issue78-heterogeneous-oos1-forward-logger.pine`

Run the exact generated file without editing classifier parameters.

## Chart timeframe

Use native **1D** bars.

Do not use Heikin-Ashi, Renko, or another synthetic chart type.

## Export exactly these six feeds

1. `TVC:SPX`
2. `NASDAQ_DLY:NDX`
3. `OANDA:XAUUSD`
4. `OANDA:XAGUSD`
5. `BITSTAMP:BTCUSD`
6. `BITSTAMP:ETHUSD`

Do not substitute another exchange / broker feed without a new preregistration.

## Logger settings

Keep:

- Enable Issue #76 Pine Logs = on;
- Event start time = 1970 / all available history;
- Event end time = 2100 / all available history;
- Representation Mode = Auto;
- all classifier parameters = generated defaults.

The logger reuses the accepted `ISSUE76|schema=1` row format but adds:

`cohort=HET_OOS1`

This is intentional schema reuse, not discovery-sample reuse.

## Files

Export one Pine-log CSV per market.

Suggested names:

- `pine-logs-#78 HET OOS1 SPX.csv`
- `pine-logs-#78 HET OOS1 NDX.csv`
- `pine-logs-#78 HET OOS1 XAUUSD.csv`
- `pine-logs-#78 HET OOS1 XAGUSD.csv`
- `pine-logs-#78 HET OOS1 BTCUSD.csv`
- `pine-logs-#78 HET OOS1 ETHUSD.csv`

The analyzer accepts any filenames when supplied explicitly, but these names match its default glob.

## Before analysis

The analyzer will stop if:

- any preregistered market is missing;
- any non-preregistered ticker is present;
- any feed resolves to a representation other than `PRICE_LOG`;
- no completed formal Markup / Markdown episodes are available.

It will **not** require the old discovery counts of 68,118 events / 1,624 episodes.

## Analysis command

From:

`indicators/wyckoff-regime-radar/research`

run:

`python analyze_issue78_heterogeneous_oos1.py /path/to/pine-logs-#78\ HET\ OOS1*.csv --out /mnt/data/issue78-heterogeneous-oos1`

Do not inspect / tune individual-market results before the complete six-market cohort has been loaded.

Refs #78, #80, #76.
