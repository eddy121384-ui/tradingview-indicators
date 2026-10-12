# Issue #188 — Deep History edge attribution — Finding

- Branch: `research/issue-188-deep-history-edge-attribution`
- Starting HEAD: `e61b9a31feb08ab757d34d77cc841fda70c77bcc` (#187 final)
- Prereg commit: `0d28ba13b0f37333a954619a043999e252545761` (BEFORE any candidate outcome)
- Final commit: (this finding's commit; see log)
- Verdict: **`deep_history_macro_information_supported`** — with the four
  printed caveats below (in-sample weights, revised macro, E4 fade,
  concentrated gains). Support means the frozen policy's edge survives every
  preregistered control; it does NOT mean production-ready.
- `production_authorized=false`. Research only. No merge. No Pine change.

## Gate table (frozen §8; P-MAX net-2bp unless noted; all 8 pass)

| gate | result | figure |
|---|---|---|
| G1 raw edge | PASS | DH−C **+0.53pp/yr** P-MAX (8.747 vs 8.214); **+0.63pp** P-ETF (8.158 vs 7.524) |
| G2 risk-adjusted | PASS | Sharpe +0.095 (0.588 vs 0.493); MaxDD **+7.0pp** (−17.05 vs −24.05) |
| G3 timing placebo | PASS | Sharpe pct **98.5**, MaxDD **98.8** (720 shifts); P-ETF Sharpe **97.5** |
| G4 ablation resistance | PASS | DH Sharpe − E1-infl **+0.083**, − E1-growth **+0.097** |
| G5 mechanism | PASS | common-309m: DH 6.63/0.670/−17.05 vs E2 6.27/0.568/−26.83 |
| G6 beyond exposure | PASS | DH−D **+0.65pp** CAGR, +0.115 Sharpe (D carries +1.68pp MORE equity) |
| G7 availability honesty | PASS | Shapley policy **+0.43pp (97% share)** vs availability −0.01pp |
| G8 robustness | PASS | bootstrap 90% CI **[+0.06, +0.98]**; LOOO all > +0.46pp |

## 給非技術 PM 的六個繁體中文答案

1. **同等資產可得性、同等風險下，Deep History 贏靜態配置嗎？——贏。**
   對最公平的靜態對照（C：同名目權重、缺失轉現金）：60 年 +0.53pp/年，
   Sharpe 0.588 vs 0.493，最大回撤少 7 個百分點（−17.05 vs −24.05），
   Ulcer 3.28 vs 4.40，CDaR95 10.97 vs 15.10。ETF 可交易期間亦贏 +0.63pp/年。
   風險匹配對照 E（回顧性降波動版靜態）亦全敗：7.866/0.477/−21.00。
   唯一輸的是只比報酬不比風險的 60/40（9.145 vs 8.747，但回撤 −30.44）。

2. **超額是真的經濟訊號擇時嗎？——在樣本內，是；日曆對齊檢驗非常強。**
   凍結 9 態權重序列打亂 720 種，DH 的 Sharpe/MaxDD/CAGR 分位 **98.5/98.8/97.6**，
   Ulcer/rolling-12m/CDaR 亦 97+；ETF 期間 97.5/97.1。打亂後風險調整全部崩掉，
   表示權重與報酬的日曆對應不是偶然。但**權重本身就是用這段歷史調出來的**
   （sample-in-sample），這是診斷、不是 OOS 證明——已在每份 placebo 輸出加註。

3. **多少來自通膨 vs 成長、現金/存續期 vs 股票？——股票擇時是大頭，現金次之。**
   歸因（DH−C，稅前）：股票 **+0.217**、現金 **+0.125**、利率 +0.042、
   實質資產 −0.104（黃金/石油低配是拖累）。Opus 的“只是通膨現金開關”**不成立**：
   通膨單因子极简版 E1R 只有 8.486/0.505/**−26.06**（回撤慘），成長單因子 E1G
   8.176/0.491/−18.60，都複製不了 DH 的 0.588 Sharpe。
   2008 機制審計：2007 全年已因通膨 High 處於 E37/現金38，雷曼當月 E22.5/
   現金48.5——防守主要靠通膨狀態沒錯，但“通膨單獨”不夠，成長軸的股票降倉
   （22.5 vs 中性 45）才是回撤差 9pp 的關鍵。

4. **更簡單的通膨-only 固定股票策略夠嗎？——不夠。**
   E2（股票鎖 45% + 通膨防守籃）在共同 309 個月：6.27/0.568/−26.83，
   全面輸 DH（6.63/0.670/−17.05），回撤多近 10pp。固定股票救不了 2008。

5. **有足夠證據拿去實盤嗎？——沒有。** 四個保留：
   (a) 樣本內建模，無 pristine-OOS；(b) 宏觀是修正後重構數，
   +1/+2/+3 stress 雖仍為正（+0.32/+0.36/+0.33），但**不是** vintage 驗證；
   (c) 增益集中：1972–80 與 2007–13 兩段佔全部正貢獻近八成（top3 79%），
   E4（2020+）DH−C 累計反而 **−1.86pp**，2020 年單年 −6.3pp；
   (d) ETF 期間 bootstrap CI 含零（[−0.15, +1.47]，樣本小）。
   結論是“模型有真東西”，不是“可以上線”。

6. **下一步只做一件事的話？——做 vintage PIT。**
   用發布時點可得的宏觀 vintage（非修正值）在 P-ETF 上重跑凍結 9 態政策，
   另立 preregistered 專項；在本 issue 不調任何參數（已凍結）。

## 方法錨點與誠實披露

- A/B 兩條基線 0 mismatch（1e-12）；D 名目目標與 prereg 表 ±0.001；
  P-MAX 上 D 實際比 DH 多 1.68pp 股票（redistribution vs subset 規則差，
  §2 tolerance MISS 已披露）——G6 是在 D **更高**暴露下贏的，結論更強而非更弱；
  P-FULL/P-ETF 的 D 匹配精確為 0。
- E2 在 P-MAX 僅 309 個月（石油缺失丟月，1986 前防守不可測——投資性限制
  已披露）；G5 用共同月比較。
- 中性投影 I_Low/I_High 違反 zero-cell，按 prereg 標 NONPOLICY（只算不稱為組合）。
- 十字驗證：13 Python tests OK；12 Node mirror PASS；重跑 16 個生成檔位元組一致；
  main/Pine/父工件未動；成本 10bp 假設性拖累僅 A 3.4bp/年——數量級可忽略。

## 交付

- Prereg：`research/issue-188-edge-attribution-prereg.md`（`0d28ba1`）
- 審計/原語/測試：`issue_188_pre_audit.mjs`、`issue_188_primitives.py`、
  `test_issue_188_primitives.py`、`test_issue_188_mirror.mjs`
- 引擎：`research/issue_188_build.mjs`
- 輸出：`generated/issue-188/`（manifest、reproduction、monthly×6、performance、
  placebo.json/csv、attribution、audit-2008、bootstrap、stress、summary）
- 本 finding。

`production_authorized=false`
