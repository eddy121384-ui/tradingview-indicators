# Macro Pressure Map — 資產配置研究證據地圖（2026-10-15）

**定位：既有 findings 的決策摘要，不是新回測或交易建議。** 研究北極星見 [MPM README](../README.md)。優先回答「股票 vs 長債、長債 vs 現金、轉折、金融條件」，不強迫九象限各有一個買賣指令。

## 已經知道什麼？

| 研究問題 | 目前最有用的歷史發現 | 證據等級／不能推論什麼 |
|---|---|---|
| **何時偏好長債？** | 1966+ Deep-History 3×3 狀態中，**低通膨**尤其低成長／低通膨時，2Y、10Y、長天期國債均列為相對較佳；**高通膨**的三種成長狀態，長天期國債皆為低偏好。 | **描述性、有跨期線索**。這是相對現金及其他資產的歷史分類，**不等於已證明可以在高通膨一律清倉長債**；還缺通膨的絕對水準、方向、期限報酬及反例的專項驗證。[#177](https://github.com/eddy121384-ui/tradingview-indicators/blob/1fabf0f9c94c391a7c2d302caff6bbdf56062d95/indicators/macro-pressure-map/research/decisions/issue-177-state-allocation-policy-finding.md) |
| **股票相對長債何時有利？** | 高成長／通膨中性時，三類股票被列高偏好，公債低偏好；低成長／低通膨則國債高偏好。**反例：高成長／低通膨時，長天期國債也可能是高偏好**。 | **方向性值得保留，不是通用交易規則**。同一「成長強」不足以獨立決定股票或 Duration，必須看通膨背景與風險。[#174](https://github.com/eddy121384-ui/tradingview-indicators/blob/1fabf0f9c94c391a7c2d302caff6bbdf56062d95/indicators/macro-pressure-map/research/decisions/issue-174-nine-sleeve-map-finding.md)、[#177](https://github.com/eddy121384-ui/tradingview-indicators/blob/1fabf0f9c94c391a7c2d302caff6bbdf56062d95/indicators/macro-pressure-map/research/decisions/issue-177-state-allocation-policy-finding.md) |
| **長歷史狀態配置是否比固定配置有用？** | 修正 #183 的權重讀取 bug 後，結構配置在 1966+ 樣本仍改善風險／回撤；#188 對公平靜態基準，在 P-MAX 約 **CAGR +0.53 個百分點／年、Sharpe +0.095、最大回撤改善 7pp**，8 個凍結歸因檢驗全過。 | **歷史樣本內支持，實盤尚未證明**：權重本來就在相同樣本設計；獲益集中於少數時期，2020+ 衰退，並使用事後修訂宏觀資料。應以 #183 的**修正後**結果解讀 #178/#180/#182。[#183](https://github.com/eddy121384-ui/tradingview-indicators/blob/1fabf0f9c94c391a7c2d302caff6bbdf56062d95/indicators/macro-pressure-map/research/decisions/issue-183-lineage-repair-finding.md)、[#188](https://github.com/eddy121384-ui/tradingview-indicators/blob/1fabf0f9c94c391a7c2d302caff6bbdf56062d95/indicators/macro-pressure-map/research/decisions/issue-188-edge-attribution-finding.md) |
| **成長／通膨改善能否抓到股市落底？** | #167 的長歷史恢復訊號 Equity−10Y 增量 **+2.35pp／3M**，但 95% CI 跨 0；#169 在現代 exact V6.6 翻譯反而 **−1.57pp**。#186 發現結構策略的加股動作通常在底部後 **4 個月**；#187 提早加股 60 年僅 **8 次**、6/8 次虧損出場，對績效幾乎沒有改善。 | **轉折預測／提早加倉尚未成立**。#187 的「pass」是因為小部位傷害有限，**不是擇時 alpha 通過**。兩層歷史指標也不能互換。[#167](https://github.com/eddy121384-ui/tradingview-indicators/blob/1fabf0f9c94c391a7c2d302caff6bbdf56062d95/indicators/macro-pressure-map/research/decisions/issue-167-recovery-outcomes-finding.md)、[#169](https://github.com/eddy121384-ui/tradingview-indicators/blob/1fabf0f9c94c391a7c2d302caff6bbdf56062d95/indicators/macro-pressure-map/research/decisions/issue-169-exact-v66-recovery-finding.md)、[#186](https://github.com/eddy121384-ui/tradingview-indicators/blob/1fabf0f9c94c391a7c2d302caff6bbdf56062d95/indicators/macro-pressure-map/research/decisions/issue-186-turning-lag-finding.md)、[#187](https://github.com/eddy121384-ui/tradingview-indicators/blob/1fabf0f9c94c391a7c2d302caff6bbdf56062d95/indicators/macro-pressure-map/research/decisions/issue-187-early-recovery-finding.md) |
| **FCPI 能讓配置更準嗎？** | 現代 exact V6.6 的 FCPI 作為風險情境描述有價值；#59 沒證實其獨立或交互的穩健預測增量。#182 的現代 Equity↔Cash overlay 雖稍改善回撤，#184 顯示**用相同平均股票曝險的固定減碼，大致就能重現風險改善**。 | **增量價值未驗證，尤其缺超長歷史 FCPI 代理**。不能說「FCPI 收緊就有可交易的超額報酬」。[#59](https://github.com/eddy121384-ui/tradingview-indicators/blob/1fabf0f9c94c391a7c2d302caff6bbdf56062d95/indicators/macro-pressure-map/research/decisions/issue-59-final-verdict.md)、[#184](https://github.com/eddy121384-ui/tradingview-indicators/blob/1fabf0f9c94c391a7c2d302caff6bbdf56062d95/indicators/macro-pressure-map/research/decisions/issue-184-v66-specificity-finding.md) |

## 三條不可省略的限制

1. **不是同一個指標的 60 年回測**：1966+ 的 Deep-History 是經濟結構模型，現代 V6.6 是另一套市場／總經混合訊號。#160 兩者重疊對照**未通過**，#161 只支持 Deep-History 的部分經濟構念有效。1928+ 年資料亦須與 1966+ 月資料分開陳述。[#160](https://github.com/eddy121384-ui/tradingview-indicators/blob/1fabf0f9c94c391a7c2d302caff6bbdf56062d95/indicators/macro-pressure-map/research/decisions/issue-160-deep-history-v01-finding.md)、[#161](https://github.com/eddy121384-ui/tradingview-indicators/blob/1fabf0f9c94c391a7c2d302caff6bbdf56062d95/indicators/macro-pressure-map/research/decisions/issue-161-construct-validity-finding.md)
2. **資產報酬尚有語意限制**：#176 改善 S&P 含息與石油投資性報酬，但 S&P 重建只到 2023-06；Nasdaq／Russell 超長歷史仍部分是**不含股息價格**；石油期貨可投資代理始於 2000 年。ETF 僅作現代 QA，不作超長歷史骨幹。[#176](https://github.com/eddy121384-ui/tradingview-indicators/blob/1fabf0f9c94c391a7c2d302caff6bbdf56062d95/indicators/macro-pressure-map/research/decisions/issue-176-allocation-backbone-finding.md)
3. **不等於當時能照做**：#189 找不到 G5（ISM 新訂單）完整歷史 vintage，九象限 **PIT replay No-Go**。通膨軸的 as-of 與 revised 狀態僅約 **76.3%** 一致（241 個可評月份），可見資料修訂會改變判斷。這不是證明策略無效，而是**不能宣稱有已驗證的即時交易優勢**。[#189](https://github.com/eddy121384-ui/tradingview-indicators/blob/1fabf0f9c94c391a7c2d302caff6bbdf56062d95/indicators/macro-pressure-map/research/decisions/issue-189-phase2-finding-v2.md)、[補正](https://github.com/eddy121384-ui/tradingview-indicators/blob/1fabf0f9c94c391a7c2d302caff6bbdf56062d95/indicators/macro-pressure-map/research/decisions/issue-189-phase2-closeout-addendum.md)

## 缺口與下一步（只做一件事）

**優先問題：高通膨下，什麼時候應減少長 Duration、轉向短債或 Cash？**

先用 #174／#176 **現有非 ETF 長歷史資產報酬**，盤點是否已充分回答「長債−Cash、10Y−Cash、長債−10Y」的風險／報酬；再檢查研究有沒有拆分「通膨絕對水準」與「通膨正在升／降」。**只補尚未回答的最小缺口**；未預先凍結定義前不做新回測，也不加 Pine／Action Layer。

**目前允許的結論：**有些配置偏好值得深入研究；**目前不允許的結論：**已找到何時「一定該賣光長債」或可以自動切換配置的可靠訊號。

`production_authorized=false`；本文件不更改任何原始 finding、凍結門檻或研究證據。
