# Issue #55 — Canonical FX data source qualification

## Decision

Use the committed static D1 files derived from `ejtraderLabs/historical-data` as the **primary reproducible research fixture** for the frozen Issue #55 experiment.

This is a reproducibility decision, not a claim that the upstream repository is the authoritative interbank FX close. Cross-feed behavior remains a separate robustness audit.

The exact upstream source files are pinned by Git blob SHA and the normalized copies are committed into this repository with SHA-256 checksums. The primary fixture therefore does not change when an external API changes, times out, or revises history.

## Primary frozen fixture

Pairs:

- EURUSD
- USDJPY
- GBPUSD
- AUDUSD

Common normalized coverage:

- 2,400 daily bars per pair
- 2012-12-04 through 2022-03-04
- Development: 2012-12-04 through 2018-06-21
- Exploratory OOS: 2018-06-22 through 2020-04-29
- Final OOS: 2020-04-30 through 2022-03-04

Final OOS remains `SEALED_DO_NOT_EVALUATE` until the response map, benchmarks, lag/cost assumptions, and pre-final diagnostics are frozen.

See `data/issue-55-static-fx-canonical-manifest.json` for source blob SHAs, frozen SHA-256 checksums, scaling, and exact row boundaries.

## Why not Yahoo Finance as the primary OHLC fixture?

Yahoo remained useful for the earlier Python-vs-TradingView cross-feed diagnostic, but a dedicated OHLC-envelope audit found provider rows where High/Low failed to contain Open/Close, including large defects and recent dates across all four target pairs. The failure was not confined to old history.

The research code initially attempted a fail-closed freezer and then a very small auditable envelope repair. A full source-quality audit showed that broad repair would be required, which would amount to manufacturing the primary market input rather than freezing it. Yahoo was therefore rejected as the canonical OHLC experiment input.

Evidence:

- `audit_fx_source_quality.py`
- `freeze_fx_canonical_data.py` (retained as research trail, not the active primary freezer)

## Why not Stooq?

The CI qualification probe did not receive the expected CSV payload for the four requested FX symbols; responses were HTML rather than parseable daily OHLC. It was rejected rather than adding brittle scraping behavior.

Evidence: `probe_stooq_daily_feed.py`.

## Why not FXCM public D1 files?

The documented yearly public-candle URL pattern returned unavailable/404 responses for the recent years probed across the four target pairs. It was rejected as a current reproducible source for this experiment.

Evidence: `probe_fxcm_daily_feed.py`.

## Why not Dukascopy as the primary fixture?

Dukascopy's yearly BID daily-candle files were the best live-source candidate on data integrity when requests succeeded: the representative 2024 files showed internally consistent OHLC. However:

1. GitHub Actions access to the public datafeed was intermittent (successful runs mixed with timeouts/503 responses), so a fresh online freeze was not operationally deterministic.
2. The yearly D1 files use calendar-day records. Representative 2024 files contained flat zero-volume Saturday bars and separate Sunday trading bars, requiring an explicit session-normalization / Sunday-to-Monday aggregation policy before they could be treated as the same daily-bar convention used by common five-day FX charts.

That normalization would be a defensible future data-engineering task, but it is unnecessary for the first frozen validation and creates an extra discretionary choice after the experiment has already begun.

Evidence: `probe_dukascopy_daily_feed.py`.

## Known limitation of the chosen static fixture

The upstream README does not establish a dealer/broker provenance sufficient to call the data a universal or authoritative FX close. The fixture is intentionally described as a **static reproducible research dataset**, not as OANDA-equivalent market data.

This limitation is acceptable for the primary frozen experiment because Issue #55 separately records the already-confirmed feed-sensitive hard-threshold risk. A model that only works on one exact feed must ultimately be reported as fragile even if its primary-fixture OOS looks attractive.

## Research boundary

- Do not refresh or replace the committed primary fixture after results are observed.
- Do not tune v0.5.2.1 thresholds to improve agreement with this fixture.
- Keep OANDA/Yahoo/Dukascopy and small-price perturbations as robustness evidence, separate from the primary OOS score.
- A future experiment may preregister a normalized Dukascopy/OANDA-quality dataset, but that would be a new independent evaluation rather than a silent replacement of Issue #55 inputs.
