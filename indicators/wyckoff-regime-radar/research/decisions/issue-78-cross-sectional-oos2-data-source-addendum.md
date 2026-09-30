# Issue #78 — Cross-Sectional OOS2 Data-Source Addendum
## Formal provider lock before any OOS2 economic outcome

## Status

This addendum freezes the formal historical provider and data contract **before any Cross-Sectional OOS2 policy economics are run**.

The Pine -> Python parity gate is already closed.

Formal OOS2 economics have not started.

PR #80 remains Draft / open / unmerged.

---

## 1. Formal provider

Formal provider:

> **CRSP US Stock & Indexes — CIZ / Flat File Format 2.0, monthly-updated WRDS product snapshot**

Use a snapshot obtained after the provider's September 2026 monthly update and containing data through at least **2026-08-31**.

Why this provider is selected:

- survivor-bias-free active + inactive U.S. security history;
- permanent security identifier `PERMNO`;
- historical security-information intervals;
- daily OHLCV;
- split/distribution adjustment factors;
- point-in-time exchange / security-type fields;
- point-in-time SIC / industry fields;
- explicit delisting fields / delisting returns.

No other provider may be mixed into the formal result.

If CRSP/WRDS access proves unavailable, any replacement provider requires a new **pre-outcome** amendment before any formal OOS2 economic result is inspected.

---

## 2. Frozen CRSP tables

Required CIZ inputs:

### A. `StkDlySecurityData`

At minimum:

- `PERMNO`
- `DlyCalDt`
- `DlyOpen`
- `DlyHigh`
- `DlyLow`
- `DlyClose`
- `DlyPrc`
- `DlyVol`
- `DlyRetx`
- `DlyDelFlg`

### B. `StkDlyCumulativeAdjFactor`

At minimum:

- `PERMNO`
- `DlyCalDt`
- `DlyCumFacPr`
- `DlyCumFacShr`

### C. `StkSecurityInfoHist`

At minimum:

- `PERMNO`
- `SecInfoStartDt`
- `SecInfoEndDt`
- `PrimaryExch`
- `SecurityType`
- `SecuritySubType`
- `ShareType`
- `IssuerType`
- `USIncFlg`
- `Ticker`
- `TradingSymbol`
- `SICCD`
- `ICBIndustry` or `UESIndustry` when available

### D. Delisting fields

Use the CRSP CIZ daily / delisting fields available in the subscribed product, including where present:

- daily delisting flag;
- delisting return;
- delisting reason / action;
- terminal payment / price information.

The exact exported field names must be captured in the raw manifest.

---

## 3. Frozen date window

Raw extraction window:

- **1998-01-01 through 2026-08-31**

Formal event window remains:

- **2000-01-03 through 2026-08-31**

The 1998–1999 history exists only for causal warm-up and eligibility history.

No event after 2026-08-31 belongs to historical OOS2.

---

## 4. Point-in-time security eligibility

A bar belongs to the eligible security population only when its contemporaneous `StkSecurityInfoHist` row says:

- `PrimaryExch` in **N / A / Q**
  - N = NYSE
  - A = NYSE American
  - Q = Nasdaq;
- `SecurityType = EQTY`;
- `SecuritySubType = COM`;
- `ShareType` is not ADR / SBI / another non-ordinary share type.

REIT common equity remains eligible.

No current-day header field may substitute for the historical information interval.

Ticker is display metadata only.

`PERMNO` is the formal security identity.

---

## 5. Price / volume representation

The classifier must receive a split-consistent daily OHLCV series.

Use:

- adjusted open = `DlyOpen / DlyCumFacPr`
- adjusted high = `DlyHigh / DlyCumFacPr`
- adjusted low = `DlyLow / DlyCumFacPr`
- adjusted close = `DlyClose / DlyCumFacPr`
- adjusted volume = `DlyVol * DlyCumFacShr`

Do **not** construct classifier prices from total-return series.

Ordinary cash dividends are therefore not reinvested into the classifier price path.

Rows with nonpositive / missing adjustment factors or unusable OHLC are excluded from classifier input and counted in the data-quality report.

---

## 6. Frozen entry-time liquidity rule

At a fresh formal Markup / Markdown entry:

- at least 252 prior valid daily bars;
- adjusted close >= **USD 5.00**;
- trailing 60-session median adjusted dollar volume >= **USD 5 million**.

Adjusted dollar volume:

> adjusted close × adjusted volume

All calculations use information available at or before the entry bar.

---

## 7. Delisting treatment

CRSP terminal economics are preferred because the provider carries explicit delisting information.

For an admitted episode that reaches a delisting event:

- use CRSP-provided terminal delisting return / payment economics when available;
- preserve the terminal event causally;
- do not silently drop the episode.

If the provider flags a delisting but no usable terminal economics can be established:

- mark the episode terminally censored;
- include it in the censoring-rate report;
- apply the preregistered >1% limitation rule.

Do not impute an optimistic terminal value.

---

## 8. Sector / industry diagnostics

Use historical `SICCD` / CRSP historical industry fields from the applicable information interval.

Sector labels are diagnostic grouping only; they do not affect admission or classifier behavior.

If a standard 11-sector mapping is applied, the mapping table must be committed and frozen before OOS2 outcomes are inspected.

Do not use a present-day sector label to rewrite historical classification.

---

## 9. Snapshot provenance

Raw licensed data are not committed to Git.

For every formal raw export, record:

- CRSP / WRDS product name;
- retrieval timestamp;
- source table;
- selected fields;
- date filters;
- row count;
- min / max date;
- SHA-256 of the raw file;
- software / query version.

The manifest itself is committed.

No raw file may be replaced after results are inspected without a new manifest entry and rerun disclosure.

---

## 10. Calibration exclusions

The three parity fixtures remain excluded from formal OOS2 economics:

- AAPL
- JPM
- XOM

Exclusion must be enforced by stable security identity where the CRSP mapping is unambiguous.

If symbol history makes identity ambiguous, the mapping is resolved before economics are run and recorded in the manifest.

---

## 11. No-outcome firewall

Before the first formal policy result is calculated, the following must all pass:

1. CRSP snapshot present;
2. required table / column contract PASS;
3. historical security-information interval join PASS;
4. adjustment-factor sanity checks PASS;
5. AAPL / JPM / XOM exclusion mapping frozen;
6. raw SHA-256 manifest written;
7. eligible-universe count and data-quality diagnostics may be inspected;
8. **R0 / Warning-First returns may not yet be inspected until 1–6 are frozen.**

Universe counts and missing-data diagnostics are engineering information, not policy outcomes.

---

## Decision

> **Formal Cross-Sectional OOS2 data source is CRSP CIZ / WRDS.**

Next engineering step:

> ingest the frozen CRSP snapshot, normalize it to the Issue #78 Python classifier schema, build the point-in-time eligible universe, and only then unlock policy economics.

Refs #78, #80.
