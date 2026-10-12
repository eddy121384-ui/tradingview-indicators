# Issue #187 — Deep-History early-recovery Equity add — Finding

- Branch: `research/issue-187-deep-history-early-recovery-equity`
- Starting HEAD: `a83836ce0453d890c4d00667d50c36767aa9278b` (#186 final)
- Prereg commit: `e2a141fff4d9f3d48643fd289bd673bc90390d6f` (BEFORE any overlay return)
- Final commit: (this finding's commit; see log)
- Verdict: **`early_recovery_equity_overlay_supported`** — with the explicit
  scope warning below:harmless at portfolio scale, weak as timing. Support here
  means “does no material harm while entering months before the structural
  policy”, NOT “profitable market timing”.
- `production_authorized=false`. Research only. No merge. No Pine change.

## Headline numbers (FULL panel, 721 months 1966-05→2026-08, post-cost)

- Activations: **8 in ~60 years** (51 Low episodes; 0 repeats suppressed)；
  median holding 2 months; exits 7×B (inflation guard) + 1×A (caught up).
- Avg added exposure: **+0.10pp** Equity (dFULL weights-only); active 16/721
  months (2.2%); deployed X: 6×5pp + 2×3pp (Low-Low cash floor,
  blocked 4.0pp total, recorded not invented).
- C−A: CAGR **−0.025pp/yr**, MaxDD **−0.18pp**, Sharpe −0.0045,
  turnover +1.2pp/yr. C−D: −0.022pp / −0.0031 (D under-exposed 0.017pp —
  acceptance MISS disclosed, bias bounded ≤0.001pp/yr, immaterial to G6).
- ETF strict (240 months, 1 activation): C−A −0.016pp/yr, MaxDD −0.15pp.
- Worst single activation: **−0.47pp** (1982-01 entry, −11.1% further market
  decline); 6/8 exited at a loss; **7/8 entries saw a lower monthly low after
  entry** (up to −29% after the 2001-12 entry).
- Bear troughs: 4/8 have early entries (months-early 1 and 10 → G5 median 5.5,
  n=2, disclosed thin); rebound-at-entry fractions 0.91–1.80 (price-late even
  when time-early); 4/8 NO SIGNAL (1970, 1987, 2020, 2022).
- Stress +1/+2/+3: incr CAGR −0.003/−0.004/−0.009pp/yr (advantage ≈ zero
  throughout; no sign flip because there was no advantage to lose).

## 七個繁體中文必答（含分母）

1. **Growth 轉好真能找到有用的提早加倉點嗎？——偶爾能，比結構政策早，但價格上經常買貴。**
   8 次熊市底部中 4 次出現早期訊號（1975-02、1982-02、2002-01、2008-12），
   其中 2 次可算 months-early（1974 谷 +1 個月、2009 谷 +10 個月，中位數 5.5，
   n=2）；另 4 次（1970、1987、2020、2022）**無訊號**，如實列為 NO SIGNAL。
   有訊號的 4 次進場後 3 次又創新低（1974 除外），買入後最大再跌 −11% ~ −29%。

2. **能早幾個月加股票？——帳面中位數 5.5 個月（n=2），其餘靠提前觸發、價格未必佔優。**
   2009 一例早 10 個月（2008-12 加 vs 結構 2009-10），1974 一例早 1 個月；
   1982（早 5 個月）與 2002（早 8 個月）因結構政策 12 個月內從未 +5pp 而無
   分母，不計入中位數（定義凍結在前）。定性來看，
   1982/2002 訊號亦早於結構確認（B-2 分別 1983-03/2002-12 才動）。

3. **第一段反彈能吃到多少？——幾乎沒吃到：進場時 20% 反彈目標平均已走完約 91% 以上。**
   四例 rebound 分數：1974 年 1.34、1982 年 0.23（唯一真正吃到前段，但隨後
   又跌且 overlay 虧 −0.47pp）、2002 年 1.80、2009 年 0.91。
   時間提早 ≠ 價格提早：2008-12 加在 900 點，底部是 735 點。

4. **誤判復甦時多虧多少？——單次 overlay 最多虧 −0.47pp，組合層面可忽略；但買入後幾乎必再跌。**
   8 次啟動 6 次虧損出場（B 通膨守衛觸發 7 次），1 個月 overlay P&L 中位數
   −0.03pp、3 個月 −0.24pp（6/12 個月多為 NaN：持有上限 6 個月、最長一次
   僅 4 個月）；進場後 12 個月內市場最大再跌中位數 −9.6%（最大 −29%）。
   苦的是“早買被套”而非“大賠”：tilt 只有 ≤5pp × ≤6 個月，虧損天然有界
   （G4 門檻 −3.0pp 從未接近）。

5. **是整體改善還是只挑危機？——整體幾乎無感（−0.025pp/年），不只挑危機：全部 51 個 Low episode 只觸發 8 次，非危機期 4 次（1967、1989、1991、2001-02），一併列入 false-recovery 表，無隱藏。**
   最好三個 episode 佔全部正 P&L 的 100%（只有 1975-01 的 +0.39pp 與
   2001-02 的 +0.03pp 為正）——集中度註記：正收益本來就沒多少。

6. **資訊延遲後還有用嗎？——本來就幾乎零超額，延遲後仍是零；結論不變。**
   +1/+2/+3 月 stress：C−A CAGR −0.003/−0.004/−0.009pp/yr，觸發數仍 8 次，
   MaxDD 增量 −0.49/−0.27/−0.01pp。注意這只是假設性界限，**不是** vintage
   證據；真實可執行性仍未知，絕不宣稱 PIT。

7. **該留在研究，還是值得做 point-in-time 測試？——留在研究。**
   門檻全過（G1–G8）只因效果太小而“無害”，不是因為擇時有效：
   7/8 提早進場買在後續新低之前、4/8 熊市無訊號、反彈分數多 >0.9。
   若要往 PIT 走，必須先有 vintage 發佈時點資料 + 日內可執行假設，
   另立專項；在本 issue 內不許再加規則“搶救”（已有結論：不搶救）。

## 方法錨點（凍結 prereg e2a141f）

- 訊號四條件（G<−10、連續兩月嚴格改善、I≤10、I 單月加速≤5）一字未改；
  one-per-Low-episode（51→8 觸發，0 重複被壓制）；退出 A–E（7×B、1×A）；
  t 訊號 → t+1 生效；X 鎖定 + 每月可行性重算（Low-Low 只給 3pp，缺口記錄）。
- A 兩條腿 0 mismatch（1e-12）vs #183 凍結檔；dFULL 純權重 0.099861pp，
  D 接受度 0.0174pp 未達 0.01pp —— **已披露不偷修**（144 個 cap/cash 受限月，
  偏誤上界 ≤0.001pp/年，不影響 G6 的 −0.05 門檻判斷）。
- 十字驗證：18 Python tests OK；12 Node mirror PASS（含一次糾正：
  退出條件可共發，順序 A–E 生效）；重跑 13 個生成檔位元組一致；
  main 未動、Pine 未動、父工件未覆寫。

## 交付

- Prereg：`research/issue-187-early-recovery-prereg.md`
- 引擎/測試：`issue_187_overlay.py`、`test_issue_187_overlay.py`、
  `test_issue_187_mirror.mjs`、`issue_187_build.mjs`
- 輸出：`generated/issue-187/`（manifest、policy、exposure、trigger-timeline、
  monthly-full/etf、performance-full/etf、case-cards、false-recovery、
  stress、sensitivity、summary）
- 本 finding。

`production_authorized=false`
