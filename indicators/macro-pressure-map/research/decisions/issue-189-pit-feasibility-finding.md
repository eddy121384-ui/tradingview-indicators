# Issue #189 Phase 1 — PIT source feasibility — Finding

- Branch: `research/issue-189-deep-history-pit`
- Base: `5864f6852042c22594529d8d96d02d73d42c6130` (#188 final)
- Prereg: `190f3a64d38d8f857c349ba9abf041f83266d517` (BEFORE any vintage fetch)
- Verdict: **部分可行（partially feasible）：2000-08 起 10/11 條成立；
  完整五因子 PIT 在 1960–2026 任何月份皆不可驗證（G5 全滅），2000 年以前
  的完整 PIT 亦不可驗證。**
- 本輪止於 Phase 1，未進入 Phase 2/3，未讀取任何資產報酬做來源選擇
  （審計程式經測試不含報酬檔引用；`test_issue_189_feasibility.mjs` 第 1 項）。
- `production_authorized=false`. Research only. No merge. No Pine change.

## 判定方法（凍結 prereg §§1–9）

11 條 feed 逐一對 ALFRED / Philadelphia Fed RTDSM / 官方發布時程做公開目錄
審計（無 key、無憑證、無抓取原始歷史數據；僅引用公開頁面）。
狀態分類凍結五級：本輪**沒有任何一條達到 `exact_verified_PIT`**
（intraday timestamp 無從驗證），6 條 `date_only_conservative_PIT`，
4 條 `partial_PIT`，1 條 `unavailable`（G5）。

## A. 11 條原始資料有多少能精確對應真正的歷史版本？

- 6 條 date-only（定義相符、日精度）：G2 失業率（UNRATE，vintage 自 1960-03；
  1960-03–1967-01 因 14+/16+ 定義拼接降為 partial）、G3 建屋許可（PERMIT，
  vintage 自 1999-08；SAAR 與 TV PSN 對 YoY 無差）、G4n 名目 DPI（DSPI，
  自 1979-12）、G4d PCE 平減（PCEPI，自 2000-08）、I1 CPI（CPIAUCSL，
  自 1972-07；1972 年內截斷 vintage 降為 partial）、I2 核心 PCE（PCEPILFE，
  自 2000-08；1959 年即有觀測值，駁回「核心 PCE 起步晚」之說）。
- 4 條 partial（上限即 partial，主因 TV 定義不明或 vintage 晚）：
  G1 工業生產（INDPRO；RTDSM IPT 月 vintage 自 1962-11，但 ALFRED
  data-vintage 清單未確認，需 key）、I3 PPI（PPIACO 自 1996-12；
  TV 用的是哪個 PPI 指數未知，且 2014 FD-ID 改制）、I4 工資（AHETPI
  自 1999-08；TV 工資概念未知；1960–63 無單一序列）、I5 能源（CPIENGSL
  自 1996-12；TV 能源概念未知）。
- 1 條 unavailable：**G5 ISM 新訂單擴散指數——無任何公開歷史 archive**
  （FRED 無 ISM 擴散序列；ISM 官網僅近期報告；1960 連續性疑為 backfill，
  方法未公開；購買條款未知）。**G5 在所有月份（含 ETF 期間）阻斷完整 PIT。**

## B. 哪些年份能完整重建當時的 Growth_DH 與 Inflation_DH？

- **完整（11/11 可用）：0 個月。** 1960–2026 全區間皆因 G5 缺席而無法滿足
  frozen five-finite 規則——這是本輪最硬的結論，不是年份問題。
- 部分可用（可用角色數，十年代表年）：1960:1、1970:2、1980:4、1990:4、
  2000:10、2010:10、2020:10。2000-08 起除 G5 外 10/11 條成立
  （G4d/I2 自 2000-08 起；年格精度，月界以 manifest 的 vintage_start 月為準）。
- 年表全文見 `vintage-coverage.csv`（11×67 格）；逐格狀態定義凍結於 prereg。

## C. 2006–2026 嚴格 ETF 期間能否完整 PIT 回測？

- **不能（full PIT not identifiable）。** 11/11 門檻卡在 G5（0/21 年可用）；
  另 G4d/I2 的 72 個月暖機史在窗口起點被截（vintage 自 2000-08 起，
  2006-06 決策需 2000-06 起的歷史）。
- 最多是 10/11 的 partial：2000-08 後 G1（partial）、G2、G3、G4、I1–I5
  （I3/I4/I5 帶定義 caveat）成立；G5 全程缺席。
- 發布時程本身不是瓶頸：BLS 8:30am ET（ES 首週五、CPI/PPI 月中）、
  BEA 月底 8:30am（PCE/DPI 約晚 1–2 個月，月底收盤決策屬邊界案，保守規則
  已凍結）、G.17 月中 9:15am、Census 約第 12 個工作日、ISM 次月首個工作日
  10am——現代月份的月底決策時鐘大致可行，缺的是**歷史版本**，不是時刻。

## D. 缺什麼？有無合法解？

缺口清單（`feasibility-summary.json` D_gaps 十項）：G5 全部；G4/I2 2000-08
前；G3 1999-08 前（FRASER PDF 數位化是未驗證的未來工作）；I1 1972-07 前；
I3 1996-12 前＋定義；I4 1960–63＋1999-08 前＋概念；I5 1996-12 前＋概念；
G1 data-vintage 清單（需 key）；G2 1960-01/02。
合法解（皆不動模型、不填修正值、不換代理、不放寬 five-finite）：
ALFRED vintage-date API 拉取（key 只放環境變數，Phase 2）、FRASER/SCB/BLS
檔案館數位化、ISM 歷史授權或有記錄的排除分析（概念若變則另立新 issue）。
**弱化 PIT 標準以求通過是被禁止的——本 finding 維持部分可行，不升級。**

## Phase 2 技術風險與所需資料

1. ALFRED key 的管理與 vintage-date 清單確認（G1/PCEPI 等 metadata-start
   與 data-start 差異）；2. FRASER 1960–1999 許可/CPI/PPI/PCE/薪資 PDF 的
   可機讀性；3. ISM：購買或正式排除（排除＝改概念，需新 issue）；
   4. I3/I4/I5 的 TV 定義溯源（決定 PPIACO/CPIENGSL/AHETPI 能否從 partial
   升格）；5. 薪資 1960–63 拼接決策；6. rebasing 跨 vintage 水平比較；
   7. BEA 綜合修訂深度；8. 共同月份規則與 staleness 計量（prereg §5 已凍結，
   待 Phase 2 實作＋測試）。

## 交付

- Prereg：`research/issue-189-pit-prereg.md`（`190f3a6`）
- 審計引擎：`research/issue_189_feasibility.mjs`（凍結證據表；零報酬引用）
- 測試：`research/test_issue_189_feasibility.mjs`（7 項全過，含重跑一致性）
- 輸出：`generated/issue-189/`（source-manifest.csv、vintage-coverage.csv、
  publication-lag-audit.csv、feasibility-summary.json）
- 本 finding。父工件零修改（測試第 7 項守門）。

`production_authorized=false`
