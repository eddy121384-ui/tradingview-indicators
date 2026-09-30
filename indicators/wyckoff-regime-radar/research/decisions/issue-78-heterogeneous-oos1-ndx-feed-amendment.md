# Issue #78 — Heterogeneous OOS1 Technical Amendment: NDX TradingView Feed Namespace

## Reason

The preregistered equity-index pair named the Nasdaq-100 feed as `NASDAQ:NDX`.

Before any usable NDX OOS outcome was inspected, TradingView's Pine runtime reported the actual `syminfo.tickerid` for the available native daily NDX chart as:

`NASDAQ_DLY:NDX`

The public TradingView symbol remains Nasdaq-100 / NDX. This amendment corrects the runtime feed namespace used by the export logger; it does not replace the economic instrument.

## Frozen amendment

Replace the OOS1 NDX export feed identifier:

`NASDAQ:NDX`

with:

`NASDAQ_DLY:NDX`

Every other OOS1 market remains unchanged:

- TVC:SPX
- OANDA:XAUUSD
- OANDA:XAGUSD
- BITSTAMP:BTCUSD
- BITSTAMP:ETHUSD

The OOS1 logger title is advanced to `#78 HET OOS1 v4` only to make the feed amendment visually obvious in TradingView.

## What does not change

No change to:

- the Nasdaq-100 underlying market being tested;
- native 1D timeframe;
- frozen Issue #68 RC classifier;
- Price Log representation;
- five-bar causal breakout box;
- t+1 ... t+3 acceptance window;
- P0 / P1 / P2 / P3 definitions;
- R0 participation logic;
- Warning-First 2 / 4 ATR deterioration logic;
- equal-market / equal-asset-class aggregation;
- OOS interpretation gates.

The prior 10,000-bar Pine memory-safety amendment remains in force.

## Research-integrity status

This namespace correction is frozen **before any accepted NDX research rows or NDX policy outcomes are inspected**.

Do not accept a different NDX provider / proxy after seeing results without another explicit amendment.

PR #80 remains Draft / open / unmerged.

Refs #78, #80, #76.
