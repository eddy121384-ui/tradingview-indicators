# Issue #91 Phase 0 — source audit boundary

Phase 0 exists to stop us from repeating the 2007-present sample mistake.

It is deliberately boring: establish what underlying, non-ETF history actually exists, what each series means, how far back it goes, whether it is a price/yield/total-return concept, and whether its provenance can be frozen before any regime-conditioned outcome is inspected.

Hard boundary:

- no SPY / TLT / GLD or other ETF as a primary long-history outcome;
- no historical analogue state labels yet;
- no regime-conditioned returns;
- no portfolio performance;
- no tuning based on outcomes;
- no calling a proxy-spliced pre-2007 series “V6.6”.

Primary source candidates are Damodaran's U.S. annual underlying asset returns (1928+), JST Macrohistory Release 6 (1870+ annual cross-check), and official FRED macro series. Shiller 1871+ is recorded as a secondary extension candidate and is not yet part of the required automated evidence path.

The JST dataset is CC BY-NC-SA 4.0. Phase 0 therefore does not commit its raw workbook. The audit stores only retrieval metadata, source hash, schema, coverage and license notes. Any later persistence of derived JST data requires an explicit license/attribution decision.

The next gate after Phase 0 is **not** a backtest. It is a preregistered definition of Historical Macro Regime Analogue v0.1: exact Growth axis, Inflation axis, frequency, lag, normalization and thresholds must be frozen before asset-conditioned results are generated.

## Live-source accessibility finding

The first two live audit attempts established a useful infrastructure constraint:

- Damodaran: GitHub Actions retrieval succeeds after making the HTML-table parser robust.
- JST R6: GitHub Actions retrieval succeeds and raw bytes are hashable.
- FRED web metadata is available and independently verifiable, but repeated GitHub Actions requests to both `fredgraph.csv` and the static table-data URL timed out.
- Shiller's Yale documentation endpoint refused the GitHub Actions runner connection.

This is treated as a **retrieval-path limitation**, not as evidence against the underlying official series. FRED remains an official cross-check and is not replaced with a lower-quality mirror merely to satisfy CI. The Phase 0 automated gate therefore requires the reproducible Damodaran + JST backbone, while recording FRED/Shiller accessibility separately.
