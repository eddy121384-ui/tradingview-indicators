# Issue #158 — Deep-history growth/inflation source feasibility (1960s+)

- Issue: [#158 — [Research] Deep-history growth/inflation source feasibility — 1960s+](https://github.com/eddy121384-ui/tradingview-indicators/issues/158)
- Branch: `research/issue-158-deep-history-feasibility`
- Role: Research Engineer — source feasibility and architecture research only
- Date (UTC): 2026-10-06
- Verdict: `deep_history_architecture_feasible_with_limitations`
- Modern anchor: frozen Macro Pressure Map V6.6 (exact reference only; deep-history layer is NOT exact V6.6)
- Firewall: no asset returns, no SPY/TLT payoff, no equity-minus-duration, no Issue #136 payoff tables, no weight optimization, no production Pine change

Companion artifacts:

- `indicators/macro-pressure-map/research/generated/issue-158/deep-history-source-matrix.csv`
- `indicators/macro-pressure-map/research/generated/issue-158/deep-history-source-summary.json`

This document is the research contract record. The CSV is the coverage matrix. The JSON is the machine-readable summary. All three must agree; where they differ in wording, this document governs semantics and the JSON governs the verbatim verdict string.

---

## 1. Objective and research philosophy

Determine whether Macro Pressure Map can support a true half-century monthly Growth / Inflation research layer extending to the 1960s/1970s without relying on late-inception ETF proxies.

Principles applied throughout:

1. Prefer original long-history economic or market series over ETF proxies.
2. Never choose SPY, IWM, RSP, sector ETFs, DBC, etc. merely because they are easy to fetch. ETFs are documented only as modern confirmation layers.
3. Modern V6.6 remains the modern exact anchor. The deep-history layer must NOT be called exact V6.6.
4. No asset-return outcome inspected. No weights optimized. No source choice tuned against later performance. No production Pine modified.

Three layers are kept explicitly separate (see §7):

1. Modern exact V6.6 layer.
2. Transitional historical bridge layer (roughly late-1980s/1990s onward).
3. Deep-history structural growth/inflation layer (1960s/1970s onward) proposed here.

---

## 2. Modern V6.6 semantic reference (frozen; not modified)

Source of truth read for this issue (no edits):

- `indicators/macro-pressure-map/research/v6_6_core.py` (frozen Python mirror)
- `indicators/macro-pressure-map/research/macro-pressure-map-v6.6-parity-sources.pine` (parity helper)

V6.6 semantics relevant to deep-history role design:

- GPI market (default weight 0.70 when macro enabled; 1.00 by default with `use_macro_data=false`): 5 component scores — `iwm/spy`, `rsp/spy`, `xly/xlp`, `xli/xlu`, `copper/gold`. All are ETF/futures ratios with late inception by construction. None can support a 1960s backbone. They define what “growth tilt / cyclicals-vs-defensives / breadth” means in modern language, not the deep-history implementation.
- GPI macro (0.30 when enabled): `pmi`, `cfnai`, `building_permits`, `initial_claims` (inverted), `unemployment` (inverted). This is the closest modern semantic bridge to deep history: output/survey + housing + labor stress. Deep-history Growth roles mirror this logic with 1960-continuous replacements.
- IPI market (0.70): breakeven pressure (T10YIE; optional T5YIE), commodity basket (DBC), energy pressure (mean of oil + gasoline scores). Modern market inflation language. DBC/oil/gasoline futures and breakeven have no 1960s history; deep history replaces them with CPI/PCE/PPI/wage/energy-inflation economics.
- IPI macro (0.30): `cpi`, `core_cpi`, `pce`, `core_pce`, `ppi`, `wage`. This is the direct modern semantic bridge to deep-history Inflation. All six concepts have 1960-continuous ECONOMICS counterparts investigated here.
- FCPI market: credit stress (HY OAS + HYG/IEF reversed; optional KRE), rates-dollar (real yield + DXY), vol shock (VIX + MOVE). Official overlay: NFCI + STLFSI. For deep history, yields/curve/NFCI/DXY are secondary cycle inputs only, never primary Growth/Inflation backbone.
- Component scoring (`f_componentScore`): level z + momentum z + tanh direction, scaled by `100*tanh(raw/2)`, with daily/weekly/macro lookbacks (252/156/60) and thresholds 10/60. Deep-history work does NOT replicate these exact parameters; it proposes simple monthly constructions (native YoY, inverted rates, 12m changes, diffusion centered at 50) and leaves exact scoring to a future preregistered bridge study.

No V6.6 thresholds, weights, or lookbacks were changed. No V6.6 outcome was inspected.

---

## 3. Phase A — TradingView source scan (primary tool)

### 3.1 Method

TradingView Official MCP was the primary source-discovery and historical-data tool:

- `mcp-tv-get-economic-symbols` (overview + per-category US tickers + targeted `search=` for industrial production, unemployment, claims, payrolls, retail, permits, income, CPI/PCE/PPI, wages, gasoline, expectations, PMI/ISM/CFNAI/leading, etc.).
- `mcp-tv-get-economic-data` with `date_from=1960-01-01`, `date_to=2026-10-06` for full-history first/last/count/unit/description, plus gap analysis via maximum calendar-month gap. Note: the API returns the trailing ~120 observations without dates, full history only when `date_from` is deep with `date_to` near present; historical sub-windows ending in the past return empty, so continuity was assessed from the full 1960→present series.
- `mcp-tv-search-symbols` to resolve FRED/ETF/futures tickers.
- `mcp-tv-get-ohlcv` with `interval=M` (monthly; `1M` is 1-minute and was avoided after verification) and `count=5000` for market depth, plus `1D`/`1W` for FRED series that reject monthly resolution. `summary=true` was used only for aggregate checks; first/last bars give depth. No return series were constructed.

Official public long-history knowledge (FRED concepts, BLS/BEA/Census revision practice) was used only for verification of revision/frequency semantics, not as a substitute for TradingView discovery.

For every candidate the CSV records: exact ticker, description, family, frequency, first/last observation, count, unit, signal type (level/rate/YoY/MoM/yield/spread/price/diffusion), monthly support without interpolation, revision status, tier, decade coverage, economic role, and missing-history notes. Key rows are summarized below; the CSV is authoritative for the full list.

### 3.2 Growth families investigated

Industrial production / manufacturing:

- `ECONOMICS:USIPYY` — Industrial Production YoY — monthly 1960-01-01→2026-08-01 — 800 obs — `%` YoY — monthly native — revised (Fed G.17) — Tier A backbone.
- `ECONOMICS:USIPMM` — IP MoM — same window — 800 — `%` MoM — Tier A redundant (noisier; excluded from backbone to avoid double-count).
- `ECONOMICS:USMPRYY` / `USMPRMM` — Manufacturing Production YoY/MoM — 1960-01→2026-08 — 800 each — Tier A redundant (narrower than IP; excluded as redundant).
- `ECONOMICS:USCU` — Capacity Utilization — 1967-01→2026-08 — 716 — `%` level — Tier A extension from 1967.

Employment / unemployment / claims / payrolls:

- `ECONOMICS:USUR` — Unemployment Rate — 1960-01→2026-09 — 800 — `%` level rate (invert) — Tier A backbone. One 2-month gap 2025-09→2025-11 (federal shutdown release delay); otherwise max gap 1m.
- `ECONOMICS:USEMP` — Employed Persons — 1960-01→2026-09 — 800 — `PSN` level (needs 12m % change) — Tier A alternate (trending; overlaps UR/NFP).
- `ECONOMICS:USIJC` — Initial Jobless Claims — 1967-01→2026-09 — 717 — `PSN` level (invert) — Tier A extension. Same start for `USCJC` (continuing) and `USJC4W` (4-week avg); both Tier A redundant with `USIJC`.
- `ECONOMICS:USNFP` — Nonfarm Payrolls net change — 1960-01→2026-09 — 801 — `PSN` flow — Tier A backbone/alternate. `USNPP` (private) and `USMP` (manufacturing) same window, Tier A redundant. `USGPA` (government) same window but Rejected as semantically weak (acyclical policy-driven).

Income / spending:

- `ECONOMICS:USPI` — Personal Income (MoM %) — 1960-01→2026-08 — 800 — `%` MoM — Tier A backbone leg (noisy MoM disclosed).
- `ECONOMICS:USDPI` — Disposable Personal Income level — 1960-01→2026-08 — 800 — `USD` level → 12m % change causally (usable 1961-01) — Tier A backbone.
- `ECONOMICS:USRCNSMSPND` (Real Consumer Spending QoQ, 266 quarterly) and `ECONOMICS:USCS` (level, 266 quarterly) — Rejected for monthly backbone (quarterly; interpolation would be non-causal).
- `ECONOMICS:USRSYY` (Retail YoY from 1993-01, 404) and `ECONOMICS:USRSMM` (Retail MoM from 1992-02, 415) — Tier B (1990s onward). No 1960s–1980s retail exists in ECONOMICS. `USRSCG` (control group, 13 obs from 2025-08) — Rejected (insufficient).

Housing:

- `ECONOMICS:USBP` — Building Permits level — 1960-01→2026-08 — 800 — `PSN` → 12m % change (usable 1961-01) — Tier A backbone. `USBPMM` (MoM from 1960-02, 799) Tier A redundant.
- `ECONOMICS:USHST` — Housing Starts — 1960-01→2026-08 — 800 — `UNIT` → 12m % change — Tier A alternate (overlaps permits; choose one).
- `ECONOMICS:USEHS` — Existing Home Sales — 1968-01→2026-08 — 704 — Tier A extension from 1968.

Business surveys / composites:

- `ECONOMICS:USMNO` — ISM Manufacturing New Orders diffusion — 1960-01→2026-09 — 801 — `POINT` diffusion (50 neutral) — Tier A backbone survey. Monthly continuous (max gap 1m). Pre-1980 backfill plausibility must be disclosed, but continuity qualifies it as the only 1960-continuous monthly forward-diffusion series.
- `ECONOMICS:USMEMP` — ISM Manufacturing Employment — same window — 801 — Tier A redundant (labor overlap).
- `ECONOMICS:USCFNAI` — Chicago Fed National Activity Index — 1967-03→2026-08 — 714 — `POINT` composite — Tier A extension. Overlaps IP/labor/sales by construction; extension/overlay only, never double-counted with its inputs.
- `ECONOMICS:USPFMI` — Philadelphia Fed Manufacturing Index — 1968-05→2026-09 — 701 — Tier A extension (regional; cross-check only).
- `ECONOMICS:USLEI` (described by MCP as “Coincident Economic Activity Index” despite LEI code; 1960-01→2026-07, 799) and `ECONOMICS:USCLI` (Composite Leading, 1960-01→2026-08, 800) — Tier A secondary composites with label-quality flag on `USLEI`; secondary only.
- `ECONOMICS:USDGO` (Durable Goods Orders from 1992-03, 414), `ECONOMICS:USFO` (Factory Orders from 1991-08, 420), `ECONOMICS:USNO` (New Orders level from 1992-02, 415) — Tier B.
- `ECONOMICS:USNYESMI` (NY Empire from 2001-07, 303) and ISM Prices diffusion `ECONOMICS:USMPR` (from 2003-01, 285; inflation-side; do not confuse with `USMPRYY` production) — Tier C.
- `ECONOMICS:USCCI` — Consumer Confidence — 1960-05→2026-09 — 656 — quarterly-sparse early (max gap 3m; May/Aug/Nov/Feb pattern), monthly continuous only from 1980-01 — Tier B (1980+ monthly). Cannot support 1960s monthly without interpolation.
- `ECONOMICS:USAHE` / `USAHEYY` (Average Hourly Earnings MoM/YoY from 2006-04/2007-03, 246/235) — Tier C; deep wage role uses `USWG`/`USWAG` instead.

Yield curve / financial conditions (secondary only):

- `TVC:US10Y` — 10Y yield monthly — 1912-06-03→2026-09-30 — 1273 bars — Tier A secondary.
- `FRED:DGS10` — 10Y weekly — 1962-01→2026-10 — 3379 weekly bars — Tier A secondary.
- `FRED:DGS2` — 2Y weekly — 1976-06→2026-10 — 2627 — Tier A-late secondary. `TVC:US02Y` monthly only from 1988-02 (464) — Tier B.
- `FRED:T10Y2Y` — 10Y-2Y spread — 1976-06→2026-10 — 2628 — Tier A-late secondary. Curve signal only from 1976.
- `FRED:NFCI` — National Financial Conditions Index weekly — 1971-01→2026-10 — 2908 — Tier A secondary from 1971.
- `FRED:STLFSI` / `STLFSI2` — 1993-12→2022-01 (338; discontinued/stale endpoint) — Rejected for backbone (Tier C stale).
- `FRED:BAMLH0A0HYM2` — HY OAS monthly — 1996-12→2026-10 — 359 — Tier B/C modern credit.
- `CBOE:VIX` monthly from 1990-01 (442) — Tier B. `TVC:MOVE` from 2002-11 (288) — Tier C.
- `TVC:DXY` monthly from 1967-01 (718) — Tier A secondary/confirmation from 1967.

Broad equity (optional confirmation only; never primary backbone):

- `TVC:SPX` monthly from 1871-02 (1599 bars; covers 1960s fully) — Tier A confirmation only.
- `AMEX:SPY` from 1993-01 (406) — Rejected as backbone (Tier C confirmation only). Same logic applies by construction to IWM/RSP/XLY/XLP/XLI/XLU/HYG/IEF and V6.6 ratios (late inception; philosophy forbids convenience sampling; modern exact layer only). No return series were built for any of them.
- `DJ:DJI` on this feed only 124 months from 2016-07 — Rejected (feed-truncated; use `TVC:SPX`).

Unresolved / insufficient (Rejected):

- `ECONOMICS:USUC`, `USBPYY`, `USPMCE`, `USCPYY`, `USENP`, `USMGDPYY`, `USMGDPMM` — empty via MCP. `USCIRMM` (11 obs), `USRSCG` (13 obs) — insufficient. Construct YoY from levels instead (e.g., USBP→YoY) rather than using empty YoY tickers.

### 3.3 Inflation families investigated

CPI / Core CPI:

- `ECONOMICS:USCPI` — CPI level — 1960-01→2026-08 — 799 — `POINT` → 12m % change (usable 1961-01) — Tier A level leg.
- `ECONOMICS:USIRYY` — CPI YoY — same window — 799 — `%` YoY native — Tier A backbone (no transform).
- `ECONOMICS:USIRMM` — CPI MoM — 1960-01→2026-08 — 798 — `%` MoM — Tier A alternate (noisy).
- `ECONOMICS:USCCP` — Core CPI level — 1960-01→2026-08 — 799 — Tier A level leg.
- `ECONOMICS:USCIR` — Core YoY — 1960-01→2026-08 — 799 — Tier A backbone.
- `ECONOMICS:USCCPI` — Core CPI YoY alternate — 1968-01→2026-08 — 703 — Tier A extension/cross-check (starts 1968; overlaps `USCIR`; keep one in backbone).
- `ECONOMICS:USCIRMM` — Core MoM — 2025-08→2026-08 — 11 obs — Rejected (insufficient).

PCE / Core PCE:

- `ECONOMICS:USPCEPI` (level, 800), `USPCEPIAC` (annual change YoY, 800), `USPCEPIMC` (monthly change, 800) — all 1960-01→2026-08 — Tier A. `USPCEPIAC` is the headline-PCE backbone candidate.
- `ECONOMICS:USCPCEPI` (level, 800), `USCPCEPIAC` (annual change, 800), `USCPCEPIMM` (MoM, 800) — all 1960-01→2026-08 — Tier A. `USCPCEPIAC` is the persistent-core backbone role (Fed-preferred concept).

PPI:

- `ECONOMICS:USPPIYY` — Producer Prices YoY — 1960-01→2026-08 — 800 — Tier A backbone (native YoY; level ticker `USPPI` only from 2009-11, 202 obs, Tier C, so the YoY ticker is required).
- `ECONOMICS:USPPIMM` (MoM from 2009-12, 201), `USCPPI` (core level from 2010-04, 197), `USCPPYY` (core YoY from 2011-04, 185), `USCPPMM` (core MoM from 2010-05, 196) — all Tier C modern. Limitation: no long-history core PPI.

Wages / earnings:

- `ECONOMICS:USWG` — Wage Growth YoY — 1960-01→2026-08 — 800 — Tier A backbone (native YoY, causal).
- `ECONOMICS:USWAG` — Average Hourly Wages level — 1964-01→2026-09 — 753 — `HOUR` → 12m % change (usable 1965-01) — Tier A cross-check from 1964.
- `ECONOMICS:USAHE`/`USAHEYY` (2006/2007+, 246/235) — Tier C. `ECONOMICS:USEMCI`/`USEMCIW` (ECI quarterly from 1982-06, 177 each) — Tier B-quarterly; rejected for monthly backbone. `ECONOMICS:USLC` (Labour Costs quarterly from 1960-03, 266) — Rejected (quarterly).

Commodities / oil / energy / gasoline:

- Broad commodity `ECONOMICS:USCPYY` — empty — Rejected. `AMEX:DBC` ETF monthly from 2006-02 (249) — Rejected as backbone (late inception; Tier C modern confirmation only).
- `ECONOMICS:USEI` — Energy Inflation — 1960-01→2026-08 — 799 — `%` — Tier A backbone energy leg (native, causal).
- Market oil: `FRED:DCOILWTICO` weekly spot from 1986-01 (2127 weekly), `NYMEX:CL1!` monthly futures from 1983-03 (524) — both Tier B confirmation from the 1980s.
- Gasoline: `ECONOMICS:USGASP` retail level from 1991-02 (428, `LTR`) and `NYMEX:RB1!` futures from 1984-12 (503) — both Tier B.

Metals / gold:

- `COMEX:GC1!` gold futures monthly from 1975-01 (622) — Tier A-mid70s secondary only if economically justified. Gold is not CPI; it is a crisis/hedge secondary, disclosed as weak CPI link.
- `COMEX:HG1!` copper futures from 1988-07 (460) — Tier B. Industrial-metal demand overlaps modern copper-gold logic; not a 1960s inflation backbone.

Expectations / breakeven:

- `ECONOMICS:USMIE1Y` (Michigan 1Y from 1978-01, 585) and `USMIE5Y` (from 1979-02, 480) — Tier B expectations from late 1970s. No 1960s expectations exist in ECONOMICS. This is a structural limitation: 1960s–1970s inflation must be measured from realized price/wage/energy series, not expectations.
- `ECONOMICS:USIE` (generic expectations from 2013-06, 159) — Tier C.
- `FRED:T10YIE` (breakeven weekly from 2003-01, 1241) and `FRED:DFII10` (real yield from 2003-01, 1240) — Tier C modern market breakeven/real. No deep history.

Money (context only):

- `ECONOMICS:USM1`/`USM2` levels from 1960-01 (800 each) — Rejected as primary inflation backbone (semantic weak for monthly pressure; documented as context only).

---

## 4. Phase B — coverage matrix and tiering

Tier definitions (frozen on coverage + semantics; never tuned on outcomes):

- Tier A: monthly-continuous enough for 1960/1970+ backbone (native monthly, or weekly/daily with causal month-end sampling, or monthly from 1967–1968/1971–1979 flagged as late-60s/70s extension). Includes secondary/confirmation-only Tick A where noted.
- Tier B: useful from 1980s/1990s onward (monthly from 1978–1996, or quarterly ECI). Transitional bridge only.
- Tier C: modern-only validation/confirmation (2000s+ or <300 obs or stale endpoint).
- Reject: insufficient (empty or <~50 obs), redundant (narrower duplicate kept as alternate), quarterly-needing-interpolation for a monthly backbone, stale/discontinued, feed-truncated, or semantically weak.

Decade coverage (summary; see CSV for per-ticker `cov_*`):

- 1960s: full monthly from 1960-01 for IP, manufacturing production, UR, employed, NFP/private/manufacturing payrolls, income/DPI, permits/starts, LEI/CLI, ISM new orders/employment, CPI headline/core, PCE headline/core, PPI headline YoY, wage growth, energy inflation. Partial-late-60s from 1967-01 (claims, capacity utilization, DXY), 1967-03 (CFNAI), 1968-01 (existing sales, alternate core CPI), 1968-05 (Philly Fed), plus 1964-01 (hourly-wage level). No retail, no expectations, no breakeven, no core PPI in the 1960s.
- 1970s: all 1960s roles continue; plus NFCI weekly from 1971-01, gold futures from 1975-01 (secondary), 10Y-2Y/DGS2 curve from 1976-06 (secondary), Michigan 1Y/5Y from 1978-01/1979-02 (Tier B expectations). CCI remains quarterly-sparse through the 1970s.
- 1980s: adds CCI monthly from 1980-01, ECI quarterly from 1982-06, oil futures 1983-03, gasoline futures 1984-12, WTI spot 1986-01, copper 1988-07, 2Y TVC 1988-02. Retail/durables/factory still absent until 1991–1993.
- 1990s: adds gasoline prices 1991-02, factory orders 1991-08, retail MoM/new orders 1992-02, durables 1992-03, retail YoY 1993-01, STLFSI 1993-12 (later stale), HY OAS 1996-12, VIX 1990-01.
- 2000s: adds NY Empire 2001-07, MOVE 2002-11, breakeven/real 2003-01, ISM prices 2003-01, AHE 2006-07, DBC 2006-02, PPI level 2009-11.
- 2010s: adds core PPI 2010–2011, generic expectations 2013-06.
- 2020s: adds sparse control-group/core-MoM tickers with <15 obs (rejected); 2025-10 shutdown gap affects some CPI-family series (2-month gap disclosed, not a deep-history break).

Net assessment: both axes have 1960-continuous monthly Tier A coverage with multiple independent roles. The binding constraints are not existence but composition: Growth lacks 1960s retail/orders (must use output/labor/housing/income/surveys); Inflation lacks 1960s expectations/breakeven/core-PPI (must use headline + core + upstream + wages + energy). Revisions (TradingView notice: latest point lags; values subject to revision) apply to all ECONOMICS/FRED series; TradingView serves revised history, so any future monthly signal must disclose revision lookahead versus real-time vintage.

---

## 5. Phase C — proposed architecture (proposed, NOT optimized)

No weights were fitted. Where aggregation is mentioned, it is provisional equal weighting with available-role averaging, labeled as such. A future study may preregister justified role weights, but this issue does not.

### 5.1 Growth backbone — 5 source roles (all usable from 1960–1961)

Provisional aggregation: equal weight 0.20 each; before full coverage use available-role mean; no smoothing beyond the native YoY/diffusion semantics; invert labor roles for growth direction.

| Role | Ticker | Why it belongs | Exact usable start | Transformation | Causal? | Overlap | Revisions |
|---|---|---|---|---|---|---|---|
| G1 Output growth | `ECONOMICS:USIPYY` | Broad coincident output; the 1960s growth backbone; 800 monthly obs, max gap 1m | 1960-01-01 | None (native YoY %) | Yes | Low with labor/housing/income; defines output leg | Yes — Fed G.17; disclose vintage |
| G2 Labor-market slack (inverted) | `ECONOMICS:USUR` | Level rate avoids population trend; 800 obs; complements flow payrolls | 1960-01-01 | Invert sign; no smoothing | Yes | Correlated with NFP/claims by construction; rate-vs-flow distinction retained | Yes — CPS annual revisions minor |
| G3 Housing authorization | `ECONOMICS:USBP` | Forward housing supply; 800 obs; 1960s housing cycle essential for 1970s context | 1960-01-01, usable 1961-01-01 | 12m % change causally (12 prior months) | Yes after 12m warmup | Low with output/labor; leads construction employment | Yes — Census revisions |
| G4 Household resource base | `ECONOMICS:USDPI` | Disposable income funds demand; 800 obs | 1960-01-01, usable 1961-01-01 | 12m % change causally | Yes after warmup | Moderate via income-spending loop; distinct resource semantics | Yes — BEA revisions |
| G5 Forward manufacturing demand | `ECONOMICS:USMNO` | Only 1960-continuous monthly forward diffusion; 801 obs | 1960-01-01 | None (diffusion; center at 50) | Yes | Moderate with G2 (labor); diffusion orders distinct from realized output | Minor; disclose pre-1980 backfill plausibility |

Earliest usable Growth backbone date: 1960-01-01 (partial 3-role: G1+G2+G5 with no warmup); 1961-01-01 (full 5-role after DPI/permits 12m warmup).

Alternates documented (Tier A, not double-counted): `USNFP` flow (1960-01) as labor-flow alternate to `USUR`; `USHST` (1960-01) as housing alternate to `USBP`; `USMPRYY`/`USCU`/`USMEMP` as output/labor alternates (redundant).

Extended optional roles from 1967 (not required for 1960s start; available-role averaging can incorporate them when available): G6 claims stress inverted (`USIJC`, 1967-01-01); G7 cycle composite (`USCFNAI`, 1967-03-01; `USPFMI` 1968-05-01 regional cross-check). Secondary-only overlays: `TVC:US10Y` (1912), `FRED:DGS10` (1962 weekly), `FRED:NFCI` (1971 weekly), curve `T10Y2Y`/`DGS2` (1976), `TVC:DXY` (1967), `TVC:SPX` confirmation only (1871). `USLEI`/`USCLI` (1960) are secondary composites with a label-quality flag on `USLEI`.

What was deliberately excluded from Growth backbone: retail/orders (Tier B, no deep history); quarterly spending/GDP/ECI/labour-costs (non-causal interpolation); government payrolls (semantically weak); all ETFs and V6.6 market ratios (late inception; modern exact only); confidence pre-1980 (quarterly); manufacturing-production narrow duplicate.

### 5.2 Inflation backbone — 5 source roles (all usable from 1960-01-01, no warmup)

Provisional aggregation: equal weight 0.20 each; no fitted weights.

| Role | Ticker | Why it belongs | Exact usable start | Transformation | Causal? | Overlap | Revisions |
|---|---|---|---|---|---|---|---|
| I1 Headline pressure | `ECONOMICS:USIRYY` | Direct headline CPI; 799 obs; defines 1970s shocks | 1960-01-01 | None (native YoY %) | Yes | Overlaps I2/I3/I5 by construction; retained to isolate energy-shock episodes from persistence | Yes — BLS |
| I2 Persistent core (Fed-preferred) | `ECONOMICS:USCPCEPIAC` | Core PCE ex food-energy; 800 obs | 1960-01-01 | None (native annual %) | Yes | Subset of I1 by construction; paired to separate persistence from volatility; do not double-weight without disclosure | Yes — BEA |
| I3 Upstream pass-through | `ECONOMICS:USPPIYY` | Only long upstream series; 800 obs (core PPI only 2010+) | 1960-01-01 | None (native YoY; level ticker modern-only so YoY ticker required) | Yes | Leads CPI/PCE; moderate correlation disclosed | Yes — BLS |
| I4 Labor-cost push | `ECONOMICS:USWG` | Wage growth; 800 obs; 1960s–1970s wage-price dynamics require this leg (companion `USWAG` level from 1964-01, usable 1965-01, as cross-check) | 1960-01-01 | None | Yes | Moderate via wage-price loop; distinct cost-push semantics | Yes — BLS |
| I5 Energy shock | `ECONOMICS:USEI` | Energy-price shock leg; 799 obs; 1973/1979 uninterpretable without it | 1960-01-01 | None | Yes | Component of I1 but isolated as shock identifier | Yes — BLS component |

Earliest usable Inflation backbone date: 1960-01-01 (all five natively YoY; no warmup).

Alternates: `USCIR` (core CPI YoY, 1960-01) as core alternate to core PCE; `USCCPI` (1968-01) as cross-check; `USPCEPIAC` (headline PCE, 1960-01) as headline alternate; `USWAG` YoY (1965-01) as wage cross-check. Secondary/context: Michigan expectations (1978/1979, Tier B), oil/gasoline market确认 from 1983–1991 (Tier B), gold from 1975 (secondary only if justified), breakeven/real from 2003 (Tier C), core PPI from 2010–2011 (Tier C limitation), money supply (rejected as primary).

Both backbones use simple interpretable monthly constructions. No z-score windows, thresholds, or smoothing are specified here; those belong to a future preregistered bridge study.

---

## 6. Phase D — future overlap-validation design (designed, NOT executed)

No bridge metrics were computed in this issue. The following design must be preregistered before any future comparison of the deep-history architecture with modern V6.6.

- Overlap window (report all three; do not select the best ex post): primary 2007-01→2026-08 (V6.6 parity/breakeven era); sensitivities 1993-01 onward (retail/VIX era) and 2003-01 onward (breakeven era).
- Monthly sampling: one observation per calendar month at month-end, causal (last-available release concept; disclose that TradingView history is revised, so this is not a real-time vintage test unless vintages are sourced).
- Level agreement: Pearson + Spearman between deep-history Growth and V6.6 GPI, and deep-history Inflation and V6.6 IPI, with 95% CIs; no fitting.
- Direction agreement: sign agreement of monthly first-differences (diffusion centered) plus Cohen kappa; no threshold tuning on overlap.
- Regime agreement: map each axis to 3 states via preregistered thresholds (e.g., >+10 / −10…+10 / <−10 on z-scored axes; thresholds fixed from V6.6 10/60 or deep-history z-equivalents preregistered, not tuned) and report confusion matrix, accuracy, kappa.
- Turning-point agreement: preregistered peak/trough rule (e.g., 12m rolling extrema with 3m causal confirmation); report lead-lag distribution and hit rate within ±3 months; no ex-post peak redefinition; optionally reference NBER chronology for Growth only as context, never as a fitted target.
- Minimum pass criteria (proposed; must be frozen before computation; all gates must pass jointly; failure means bridge rejected or limited-scope claim only):
  - Level: Spearman ≥ 0.50 per axis over full overlap and ≥ 0.40 in each half-split (early/late).
  - Direction: monthly sign agreement ≥ 0.60 per axis.
  - Regime: 3-state accuracy ≥ 0.55 with kappa ≥ 0.30 per axis.
  - Turning-point: median absolute lag ≤ 3 months on preregistered peaks.
- Anti-tuning rules: no asset returns inspected; no source added/dropped after seeing agreement; no gate adjustment after computation; no relabeling deep-history as exact V6.6; no production parameter recalibration on overlap data; any future predictive use requires genuinely unseen observations after the preregistration cutoff.

---

## 7. Key distinction — three layers

1. Modern exact V6.6 layer: frozen Pine + Python mirror; ETF/futures/breakeven market legs; exact reference for modern regime language. Authorization: none for changes in this issue.
2. Transitional historical bridge layer (late-1980s/1990s onward): where Tier B joins and overlap validation is meaningful (retail, durables/factory, VIX, oil futures/spot, Michigan expectations, ECI quarterly with monthly bridge method preregistered separately). Not built here.
3. Deep-history structural growth/inflation layer (1960s/1970s onward): the 5+5-role architecture in §5; provisional equal weights; native YoY/diffusion/rate semantics; NOT exact V6.6 and must never be labeled as such.

---

## 8. Verdict

`deep_history_architecture_feasible_with_limitations`

Rationale: a true 1960s-to-present monthly Growth/Inflation research layer can be built from original TradingView economic series without late-inception ETFs — Growth from 1960-01-01 (full 1961-01-01) via IP + UR + permits + DPI + ISM orders, Inflation from 1960-01-01 via CPI headline + core PCE + PPI + wages + energy — with continuous monthly support (max gap 1m except disclosed 2025 shutdown gaps) and 1967–1979 extensions (claims, CFNAI, NFCI, curve, expectations, gold). Limitations are material and disclosed: no 1960s retail/orders; no 1960s expectations/breakeven/core-PPI; quarterly concepts rejected; all ECONOMICS/FRED history is revised (not real-time vintage); ISM pre-1980 backfill and `USLEI` label mismatch require documentation; housing/income YoY need 12m warmup; 2025-10 release gap; ETFs/market ratios forbidden as backbone. Hence feasible, but only with limitations — not unconditional, and not infeasible.

---

## 9. TradingView data families investigated (for final report)

- ECONOMICS US categories via `mcp-tv-get-economic-symbols`: gdp (25), lbr (67), prce (91), bsnss (141 codes), cnsm (35), hse (54), mny (39), enrg/trd/gov searched; targeted searches for industrial production, unemployment, claims, payrolls, retail, permits, starts, income, CPI/PCE/PPI, wages, gasoline, expectations, PMI/ISM/CFNAI/leading/confidence/manufacturing/capacity/durables/orders/employment-cost/hourly.
- ECONOMICS full-history fetch via `mcp-tv-get-economic-data` (`1960-01-01`→`2026-10-06`) for ~60 tickers; first/last/count/unit recorded; max month-gap continuity verified.
- Market OHLCV via `mcp-tv-get-ohlcv`: monthly `M` depth for `TVC:SPX`, `TVC:DXY`, `TVC:US10Y`, `TVC:US02Y`, `CBOE:VIX`, `TVC:MOVE`, `COMEX:GC1!`/`HG1!`, `NYMEX:CL1!`/`RB1!`, `AMEX:DBC`/`SPY`, `DJ:DJI`; daily/weekly for `FRED:DGS10`/`DGS2`/`T10Y2Y`/`DCOILWTICO`/`NFCI`/`T10YIE`/`DFII10`/`BAMLH0A0HYM2`/`STLFSI`.
- Symbol discovery via `mcp-tv-search-symbols` (FRED/ETF/futures disambiguation; `USMPR` production vs ISM-prices disambiguation).
- Modern V6.6 reference via `v6_6_core.py` + parity Pine (read-only).

Earliest usable dates: Growth backbone 1960-01-01 partial / 1961-01-01 full (extended 1967-03-01 with claims/CFNAI); Inflation backbone 1960-01-01.

Tier A sources: see §3–§5 and CSV/JSON (Growth: IPYY, UR, NFP, BP, DPI, MNO, HST-alt, CLI/LEI-secondary, US10Y/DGS10-secondary, SPX-confirmation; extension: claims, CU, CFNAI, EHS, PFMI, DXY, NFCI, GC-secondary, curve-1976; Inflation: IRYY, CIR, CCP, PCEPIAC, CPCEPIAC, PPIYY, WG, EI, plus CCPI-1968/WAG-1964 cross-checks).

Major rejected: ETFs as backbone (late inception + philosophy); retail/orders Tier B (1991–1993); quarterly spending/GDP/ECI/labour-costs (non-causal interpolation); empty tickers (USUC/BPYY/PMCE/CPYY/ENP/MGDP/CIRMM-11/RSCG-13); modern-only core-PPI/PPI-level/AHE/ISM-prices/IE/breakeven/MOVE/NY-Empire/HYOAS-1996/STLFSI-stale; government payrolls (weak semantics); DJ:DJI feed (truncated); DBC/copper as inflation backbone; pre-1980 confidence quarterly.

Proposed architectures: §5.1 Growth 5-role equal-weight (IPYY + UR-inv + BP-YoY + DPI-YoY + ISM-orders); §5.2 Inflation 5-role equal-weight (CPIYY + core-PCE-YY + PPIYY + wage-YY + energy); provisional only, no fitting.

---

## 10. Tests / validation performed

- Source discovery + full-history fetch for ~60 ECONOMICS tickers with first/last/count/unit + max month-gap continuity (monthly backbone requires max gap 1m; disclosed exceptions: 2025 shutdown 2m in CPI-family/UR/EMP; CCI quarterly-early 3m → Tier B).
- Market monthly/weekly depth checks listed above; interval semantics verified (`M` vs `1M`; FRED monthly rejection → weekly/daily fallback).
- CSV well-formedness: header + 90+ data rows, per-row tier/decade/role populated; JSON parses as one object with required keys (`verdict`, `earliest_*`, `growth_architecture`, `inflation_architecture`, `overlap_validation_design_not_executed`, `anti_tuning_rules`).
- No asset-return series constructed; no payoff inspected; no weights fitted; no Pine modified (verified via `git status --short` showing only new research files).

Validation was performed with TradingView MCP as the primary tool plus local file checks. No Python test suite exists for this issue by design (architecture study only); a future bridge study must add preregistered tests before computing overlap metrics.

---

## 11. Explicit confirmations

- No asset-return outcome was inspected (no SPY/TLT/returns, no equity-minus-duration, no Issue #136 payoffs, no forward-return conditioning of source choices).
- No production code was changed (no edits to `src/*.pine`, `research/v6_6_core.py`, parity helpers, or any indicator; only new files under `research/decisions/issue-158*` and `research/generated/issue-158/`).
- No weights were optimized; any aggregation mentioned is provisional equal weighting, clearly labeled.
- No source was selected after seeing market outcomes; tiering is on coverage/frequency/semantics only.
- Deep-history layer is NOT called exact V6.6 anywhere in these artifacts.
- Push target is `research/issue-158-deep-history-feasibility`; no merge is requested.

---

## Appendix — Reproducibility notes

- TradingView ECONOMICS series carry the notice “latest point lags the official release; recent values are subject to revision.” Treat all first/last/counts as revised-history snapshots as of 2026-10-06, not real-time vintages.
- `USLEI` description mismatch (“Coincident” vs LEI code) is recorded in CSV/JSON; use as secondary only.
- `USMNO`/`USMEMP` 1960-continuous diffusion should cite ISM backfill methodology in any future bridge preregistration.
- `TVC:SPX` 1871 origin reflects Shiller-style long history on that feed; deep-history use is confirmation-only regardless.
- `FRED:STLFSI` endpoint 2022-01 is stale/discontinued on this feed; rejected for backbone.
- CSV uses grouped ETF row for modern V6.6 legs to avoid return inspection; individual ETF inception logic follows the same late-inception exclusion.
