# Issue #189 — Data Source Feasibility Review (I3/I4/I5 definitions + G5 vintages)

- Branch: `research/issue-189-deep-history-pit`; Phase 1C/Phase 2 evidence only.
- Scope: source identity and vintage availability. No return backtests, no
  optimization, no model changes, no Phase 3. `production_authorized=false`.
- Method per series: TradingView official symbol page → provider/concept/units;
  BLS/BEA definitional docs → concept compatibility; small numeric cross-checks
  from EXISTING Phase 2 scratch vintages only (no new bulk downloads).
  Unverifiable claims stay UNVERIFIED; names alone never pass.

## I3 — ECONOMICS:USPPIYY vs FRED PPIACO → NOT_EQUIVALENT

- TV official page (https://www.tradingview.com/symbols/ECONOMICS-USPPIYY/,
  fetched 2026-10-13): title "United States Producer Prices Index YoY",
  source BLS, monthly, %; description defines it as the **Final Demand**
  index (final-demand goods 33% incl. food+energy, trade services 20%,
  transport 4%, services ex-TTW 41%, construction 2%). Extremes shown:
  high **19.57% Nov-1974**, low **−6.86% Jul-2009**.
- BLS (https://www.bls.gov/ppi/fd-id/, https://www.bls.gov/ppi/faqs/):
  FD-ID became primary only Jan-2014 (history to Nov-2009/Apr-2010);
  pre-2014 headline was SOP Finished Goods. PPIACO is NSA **all-commodities**
  (Index 1982=100), and BLS Technical Note warns all-commodities
  multiple-counts processing stages and "can lead to exaggerated or misleading
  signals" vs FD-ID/industry indexes for general trends.
- Numeric cross-check (existing scratch vintages, recomputation §4):
  PPIACO-implied YoY Nov-1974 = **23.44** vs TV 19.57 (Δ 3.87pp);
  Jul-2009 = **−15.96** vs TV −6.86 (Δ 9.1pp). Decisive mismatch in both
  level and dynamics (all-commodities overstates crashes).
- Verdict **NOT_EQUIVALENT**: different index concepts (FD vs all-commodities),
  different SA (FD SA vs PPIACO NSA), confirmed numerically. Downgrades the
  Phase 1 "partial" cap — no compatible transform exists (no arithmetic turns
  all-commodities into final demand).

## I4 — ECONOMICS:USWG vs FRED AHETPI → NOT_EQUIVALENT

- TV official page (https://www.tradingview.com/symbols/ECONOMICS-USWG/,
  fetched 2026-10-13): title "United States Wage Growth YoY", source listed as
  **Bureau of Economics Analysis** (BEA), monthly, %; description: "yearly
  change in **wages and salaries disbursements** from government, manufacturing
  and service industries." Extremes: high **+15.28% Apr-2021**, low
  **−5.89% Apr-2020**.
- AHETPI is BLS CES **hourly rates** for production/nonsupervisory workers
  (CES0500000008, from 1964); all-employee concept only from 2006 (BLS Handbook
  CES history; official 2010/2011). Rate-concept ≠ disbursement-concept;
  pre-2006 splice across populations is a documented break, not endorsed.
- Numeric cross-check (existing scratch): AHETPI-implied YoY Apr-2020 =
  **+7.67** vs TV −5.89 (OPPOSITE SIGNS — hourly-rate composition effect vs
  payroll collapse); Apr-2021 = **+1.15** vs TV +15.28 (Δ 14pp).
- Verdict **NOT_EQUIVALENT** vs AHETPI. Lawful next lead (UNVERIFIED, new-issue
  work): BEA monthly wages-and-salaries disbursements → computed 12m%
  (concept-matched); no FRED ID verified and no vintage check done here.

## I5 — ECONOMICS:USEI vs FRED CPIENGSL → EXACT_MATCH (stated evidence)

- TV official page (https://www.tradingview.com/symbols/ECONOMICS-USEI/,
  fetched 2026-10-13): title "United States Energy Inflation", source BLS,
  monthly, %; "accounts for more than 9 percent of the consumer price index"
  (CPI-energy concept). Extremes: high **47.13% Mar-1980**, low
  **−28.09% Jul-2009**.
- CPIENGSL: CPI-U Energy, monthly SA, Index 1982-84=100, from 1957 (BLS CPI).
- Numeric cross-check (existing scratch): CPIENGSL-implied YoY Mar-1980 =
  **47.21** vs TV 47.13 (Δ 0.08pp); Jul-2009 = **−28.05** vs TV −28.09
  (Δ 0.04pp). Agreement to <0.1pp at both extremes 29 years apart, same
  provider, same concept, continuous history — SA-basis inference (TV page
  silent on SA) is the sole residual, immaterial at this tolerance.
- Verdict **EXACT_MATCH** (upgraded from partial). Revision seams (1998
  classification, 1999 geometric mean, biennial weights per BLS historical
  changes) remain disclosed limitations, not inequivalence.

## G5 — ISM New Orders vintages 2006–2026: no continuous PIT source exists

1. **ISM official**: history paywalled since 2014-03-01 (subscription notice
   2014-02-12); 2014 public price $2,500/yr (DO NOT quote as current);
   current ROB terms forbid derivatives/tables/archives/redistribution without
   written permission (contact ismresearch@ism.ws). Annual X12-ARIMA factor
   revisions rewrite ~4–7 years (2012/2013/2015 PRs). NO first-reported
   vintage product advertised. Conclusion: licensable **revised-SA history
   only**, terms restrictive, current price unverified.
2. **FRED/ALFRED**: no ISM diffusion series (manufacturing-new-orders tags
   return Census M3 dollar series only: NEWORDER etc.); ALFRED vintages only
   existing FRED series. Nothing to pull.
3. **Press releases as a continuous source**: contemporary values survive
   scattered (2008-03: 46.5; 2009-02: 33.1/32.8; 2020-03: 42.2; 2022-09: 47.1,
   all cited in Phase 1B/2). Gaps of years with no citable release, third-party
   ©, ISM derivative prohibition → NOT a continuous auditable source.
4. **Vendors (Haver USECON/SURVEYS, Moody's Data Buffet NAPMM.IUSA,
   Bloomberg terminals)**: all revised-history only on public evidence;
   composite proven to 1948 (Moody's), New-Orders component continuity
   unconfirmed; pricing quote-only/undisclosed; redistribution unconfirmed.
   **First-reported monthly vintages 2006–2026: NONE FOUND anywhere.**
5. SA subtlety with PIT consequence: today's download of an old month ≠ its
   first-reported value (proven: Feb-2009 33.1→32.8). Any licensed file used
   later must be vintage-typed, not assumed first-reported.

## Answers

- **I3/I4/I5 哪些確認等價？** 僅 **I5 等價**（CPIENGSL，雙極值 <0.1pp 一致）。
  **I3、I4 皆不等價**（I3：FD vs 全商品＋SA 差異，極值差 3.9/9.1pp；
  I4：BEA 薪資總額 vs BLS 小時工資率，COVID 反向）。I3/I4 需另立新 issue
  找 concept-matched 候選（I4 的 BEA 薪資總額路線最有希望，未驗證）。
- **G5 是否存在可實際取得的連續 PIT 資料？** **不存在。** 免費無；付費僅有
  修訂版 SA 歷史（價格未驗證、條款嚴限）；first-reported 連續 vintage 全市場
  無公開供給。2006–2026 連續 PIT 在 G5 這關是死路，除非 ISM 書面授權＋條款。
- **若存在，下一個最小可行驗證步驟是什麼？**（條件式，不適用）——僅記錄：
  需 ISM 書面確認 first-reported 可供性＋授權＋價格後，另立 preregistered
  專項做 2008–09 小樣本对照；此前不得動工。
- **若不存在，是否應停止完整九象限 PIT 回測研究？** **是，停止。**
  Phase 2 No-Go 維持且加固：連付費路徑都無法供給 first-reported vintages，
  完整 240 個月 ETF 九象限 PIT 不具可辨識性。10/11 成分審計與 Inflation_DH
  路徑是本研究的可用終點，不得升級為配置驗證。

## Recomputation (no new downloads; scratch JSONL from Phase 2 pulls)

YoY(m) per vintage column: 100*(P[m]−P[m−12])/P[m−12]; PPIACO Nov-1974 from
vintage 2000-08-01; PPIACO Jul-2009 from 2009-08-31; CPIENGSL Mar-1980 from
2000-08-01; CPIENGSL Jul-2009 from 2009-08-31; AHETPI Apr-2020 from 2020-05-31;
AHETPI Apr-2021 from 2021-05-31. TV extremes from the three official pages
above (19.57/−6.86; −5.89/+15.28; 47.13/−28.09).

`production_authorized=false`
