# Issue #189 Phase 2 — PIT vintage reconstruction & validation — Finding v2

- Branch: `research/issue-189-deep-history-pit`（原獨立 worktree）
- Base `5864f68`；prereg `190f3a6`、Phase 1/1B/1C 設計文件皆未動
- 本文件取代 v1（v1 檔保留不動；差異全列於文末 §7，直接原因見獨立
  `issue-189-phase2-correction-addendum.md`，GPT-6 複核兩 bug 皆已確認修復）
- Phase 2 判決：**Phase 3 full PIT replay → No-Go**（九象限 as-of 路徑不可辨識；
  G5 缺席是硬阻斷）。可用產品是 10/11 成分級 as-of 審計＋完整 Inflation_DH。
- 本輪零資產報酬回測、零模型修改、未進 Phase 3。
- `production_authorized=false`. Research only. No merge. No Pine change.

## 六個繁體中文必答（修正後數字）

**第一，十條候選資料有多少真正通過 L3 數值與版本驗證？——10/11 通過版本存在性＋跨度驗證，0/11 達到定義完全確認，G5 零 vintage。**
3130/3130 pulls（313 月底×10 feeds，中斷 3 筆 504 同 worker 續傳補回）。
每個 vintage 的觀測上限皆早於 vintage 月（全集無未來觀測，測試硬斷言；
快照隔離修復後重驗：staleness 2430 筆 `vintage_as_of ≤ decision_at`
零違反——修前 2420 筆違反）。
2000-08-01 版 10 條全含完整歷史（INDPRO 回到 1921、PPI 回到 1913）；
2006-06-01 版同樣到源頭。L3 在此定義為「該 vintage 真實存在且含所需觀測」：
10/11 達成；定義完全確認僅 G1/G2/G3/G4/I1/I2 六條，
I3/I4/I5 因 TV 原始定義不明維持 partial 上限（fail-closed）。

**第二，哪些成分容易受到事後修訂影響？——G3 建屋許可最甚，G1 工業生產次之，CPI 近乎零修訂。**
YoY 層級修訂帶寬（同觀測跨 vintage，2002–2026 年抽樣，中位數）：
G3 **3.14pp**（最大 8.82）、G1 **1.38pp**（最大 3.51）、I5 0.49pp、
I2 0.31pp、I4 0.18pp、I3 0.12pp、I1 **0.06pp**（最大 0.17）。
Level 層級另見 rebasing 階梯（INDPRO 38%、PCE 系 ~30%——YoY 內抵消，
跨 vintage 水平比較則斷裂，已披露）。SA 因子年修對 G5 spot 月約 ±0.5pp
（2009-02 初值 33.1→修訂 32.8 即其例）。

**第三，2006–2026 能否完整重建 Inflation_DH？——能，241/243 決策月 scored，另 2 個月 partial。**
243 決策月：241 scored（九個非 G5 角色全 finite）＋ 2 partial
（2026-01、2026-03，缺 G2/I1/I5——2025 關廠潮所致，角色具名）＋ 0 gaps。
as-of vs revised：band 一致 **184/241（76.3%）**，平均 |ΔI| 8.55；
as-of 轉換 68 次 vs revised 78 次（修訂憑空多出 10 次穿越）。
混淆集中在 Low|Neutral 25（as-of 更偏鴿）與 Neutral|High 12 兩格。
注意：這是通膨單軸，不是九象限——Growth 永遠缺 G5。

**第四，G5 缺失下 Growth_DH 哪些不可辨識？——全部：九象限月份 0/243。**
G1–G4 as-of 分數可重建（241/243 決策月四角色全 finite；partial mean 與
revised 均差 13.9，僅描述性——缺 G5 的 partial mean 不是 Growth_DH，
不得使用）。引擎 fail-closed：G5 欄永為 NaN 佔位（parser 缺失值語言，
零資訊注入），five-finite 規則拒絕完整 Growth，`nine_state` 全為 null
（243/243 實測）。B-2 換倉序列、九象限配置訊號：皆不可產生。

**第五，公布延遲與修訂的影響分別有多大？——延遲：BEA 三條腿把共同月份再推後一個月（D−2 vs 樸素 D−1）；修訂：上見第二問。**
保守時鐘實測：月頻腿資訊年齡 ~1.0 個月，BEA（G4n/G4d/I2）~2.0 個月
（最大值 G3 4.07、G4/BEA 3.07——關廠拉回的共同月份所致）；
共同可用月恆為決策月前 2 個月（2006-06-30→2006-04），樸素時鐘則為前 1 個月。
BEA 月底邊界案按保守規則計入 staleness，ledger 逐月記錄各腿 vintage/age。
結論：延遲把可交易資訊再推後一個月，但不斷鏈（243 決策月 scored/partial，
0 gaps）；修訂改變分數水平（G3/G1 最大數 pp 級），但 band 一致率仍 76.3%。

**第六，完整 PIT 配置回測還缺什麼？——缺 G5 vintage 資料庫（唯一硬缺口）。**
其餘：月 vintage 密度未窮舉（端點抽樣＋慣例，需 key 做 vintage_dates 全表
才算完備）、I3/I4/I5 TV 定義溯源、G1 清單、日內 timestamp（永遠 date-only，
保守次日規則已凍結）。G5 合法路徑只剩兩條：ISM 授權歷史庫（價格/條款未驗證）
或 episode 抽查（2008-03：46.5、2009-02：33.1/32.8、2020-03：42.2、
2022-09：47.1，均已引證；僅作對照，不得插值成月序列）。

## Phase 3 Go / No-Go：**No-Go（full replay）**

完整 240 個月 ETF 九象限 PIT 回測不具可辨識性（G5 無 vintage → 無 as-of
九象限路徑），依 prereg 必須判 No-Go，不得用 10/11 替代配置宣稱成功。
可用交付：10/11 as-of ledger（243 月逐月 vintage/age/分數）、完整
Inflation_DH as-of 路徑、逐成分修訂/延遲審計、G5 spot 對照。建議的唯一後續：
取得 ISM 授權庫（或立項記錄排除分析）＋key 窮舉 vintage 密度後，再議 Phase 3。

## §7 v1→v2 差異表（v1 檔原樣保留）

| 項目 | v1（錯誤） | v2（修正） | 原因 |
|---|---|---|---|
| staleness vintage 違規 | 未檢查（實 2420/2430） | 0/2430 | 快照別名 bug＋修復 |
| 2019-02 common | 2018-12（含未來 vintage 值） | 2018-11 | 同上（關廠月 genuine 缺值） |
| ledger 狀態 | 243 scored-partial | 241 scored＋2 partial＋0 gaps | 五 null-I 月正名（關廠缺值） |
| I 一致率分母 | 182/240＝75.8% | **184/241＝76.3%** | 同上 |
| mean dI | 8.588 | **8.549** | 同上 |
| G1–G4 finite | 238/243 | **241/243** | 同上 |
| 簡體字串 | 2 處 | 已改為繁體 | 撰寫疏失 |
| Q4 重複句 | G-partial 兩句重疊 | 合併為一句 | 撰寫疏失 |

另修（開發期、未進任何已提交輸出）：G3 double-YoY、contiguity 誤判、
ledger 非法 NaN、空字串崩潰——v1 §方法錨點已披露，v2 不贅。

## 方法錨點與誠實披露

- 3130 pulls 全 200、中斷 3 筆 504 續傳補回；raw 未提交（span/hash manifest 可重拉）。
- 暖機 74 offsets/75 obs（frozen code 實測；Phase 1C 已證）。
- 測試：Python 12 項＋Node mirror（獨立 pressure_score 交叉 maxdiff 2.6e-13、
  全 pulls 無未來觀測、無報酬引用掃描、ledger 九象限全拒）全綠；
  analyzer＋engine 重跑位元組一致。
- 停在 Phase 2。未 merge、未動 main/Pine/模型。交 GPT-6 再次審查。

`production_authorized=false`