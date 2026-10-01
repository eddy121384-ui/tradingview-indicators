# Issue #78 — Equity Proof-Policy OOS3 universe freeze

Date: 2026-09-30

## Status

The untouched second 300-stock OOS3 cohort is now frozen **before any OOS3 price history, classifier output, or policy economics are inspected**.

Universe SHA-256:

`9d4a14d163ed308238737647b94e722c62fd023b641e1015e6d97679f9ba3b44`

This hash is the identity of the OOS3 stock cohort for all subsequent downloads and policy tests.

---

## Selection provenance

Candidate snapshot:

`artifacts/issue119_bbg_oos2/issue119_bbg_oos2_candidates.csv`

Prior OOS2 universe excluded:

`artifacts/issue119_bbg_oos2/issue119_bbg_oos2_universe_manifest.csv`

Deterministic seed:

`issue78-equity-proof-policy-oos3-v1`

Selection logic:

- same frozen Issue #119 metadata eligibility rules;
- exclude every FIGI in the first 300-stock OOS2 cohort;
- exclude AAPL / JPM / XOM calibration fixtures;
- same equal-sector-within-size-sleeve deterministic allocation;
- 100 large / 100 mid / 100 small.

---

## Freeze diagnostics

- candidate rows: **1,506**
- prior OOS2 universe rows: **300**
- prior FIGIs excluded: **300**
- calibration candidate rows excluded: **3**
- remaining candidate rows before eligibility: **1,203**
- selected rows: **300**
- unique selected FIGIs: **300**
- overlap with prior OOS2 FIGIs: **0**

Sleeves:

- large: **100**
- mid: **100**
- small: **100**

Current-sector counts:

- Communication Services: 19
- Consumer Discretionary: 29
- Consumer Staples: 23
- Energy: 27
- Financials: 35
- Health Care: 28
- Industrials: 36
- Information Technology: 28
- Materials: 28
- Real Estate: 28
- Utilities: 19

---

## Firewall

At freeze time:

- no OOS3 price history had been downloaded or inspected;
- no OOS3 classifier output had been computed;
- no OOS3 R0 / proof-policy / WarningFirst economics had been computed;
- no selected security had been replaced;
- no proof threshold or exposure state had been changed.

From this point onward, failed / sparse securities are retained as fixed cohort members and may not be replaced after outcomes are visible.

Refs #78, #135, #132, #131, #80.
