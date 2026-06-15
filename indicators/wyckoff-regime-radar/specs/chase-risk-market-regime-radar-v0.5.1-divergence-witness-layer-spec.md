# Chase Risk Market Regime Radar v0.5.1｜Divergence Witness Layer Patch Spec

> 本文件是 v0.5 完整規格書的 patch spec。  
> 目的：在不重寫主模型的前提下，新增「追價風險背離 / 共振」判斷，作為 Volume 與 MTF 之外的第三個 witness layer。

---

## 0. 版本定位

v0.5.1 目標是加入：

```text
Divergence Witness Layer｜追價風險背離層
```

這一層使用價格高低點與既有追價風險序列：

```text
bullChaseRisk = endRiskUp
bearChaseRisk = endRiskDn
```

判斷價格創高 / 創低時，追價風險是否同步創高，或出現背離。

它回答的問題是：

```text
價格還在創新高 / 新低，但原方向追價風險是否開始不確認？
```

這一層不是買賣訊號，不是 RSI / MACD 類傳統震盪指標背離，也不是威科夫階段投票器。

它只是一個 witness layer，用來提醒：

- 高位追多品質是否下降。
- 低位追空品質是否下降。
- 原趨勢是否進入過熱 / 恐慌共振。
- Flat Action 是否應降級。
- Pace Guide 是否應加入「不追價 / 保護利潤」語氣。

---

## 1. 核心設計原則

### 1.1 Divergence layer 是證人，不是主引擎

Divergence layer 不得直接改寫：

```text
formalId
candidateDisplayId
confirmedId
candidateId
```

它只能低權重影響：

```text
upsideExhaustion / downsideExhaustion 語意
candidateConflict
highClueObservation / lowClueObservation
Pace Context Downgrade
Flat Action No Chase
Dashboard / Debug / Alerts
```

若未來要讓 divergence 參與 effective score，只能透過小權重 multiplier，且預設應為 Observe Only。

### 1.2 背離不是反轉

頂背離不等於做空。  
底背離不等於做多。

正確語意是：

```text
頂背離 = 追多品質下降 / 高位供給觀察
底背離 = 追空品質下降 / 低位承接觀察
```

### 1.3 共振不是背離

v0.5.1 不只看背離，也要看共振。

同樣是創新高 / 新低，應分成四種狀態：

```text
價格創新高 + 多頭追價風險也創新高
→ 多頭過熱共振，不是頂背離。

價格創新高 + 多頭追價風險沒有創新高
→ 頂背離 / 高位供給觀察。

價格創新低 + 空頭追價風險也創新高
→ 空頭恐慌共振，不是底背離。

價格創新低 + 空頭追價風險沒有創新高
→ 底背離 / 低位承接觀察。
```

這個四格語意是本 patch 的核心。

---

## 2. 新增 Input Group

新增：

```pine
groupDivergence = "參數｜Divergence Witness Layer v0.5.1"
```

建議放在 `groupMTF` 之後、`groupRegime` 之前。

---

## 3. 新增 Inputs

```pine
divMode = input.string("Observe Only", "Divergence Mode", options=["Off", "Observe Only", "Auto"], group=groupDivergence)
divPivotLeft = input.int(5, "背離 Pivot Left", minval=1, maxval=20, group=groupDivergence)
divPivotRight = input.int(5, "背離 Pivot Right", minval=1, maxval=20, group=groupDivergence)
divMinPricePct = input.float(0.5, "最小創高 / 破低幅度 %", minval=0.0, maxval=10.0, step=0.1, group=groupDivergence)
divMinRiskGap = input.float(8.0, "最小風險背離差距", minval=0.0, maxval=50.0, step=0.5, group=groupDivergence)
divRiskMin = input.float(55.0, "最低有效追價風險", minval=0.0, maxval=100.0, step=0.5, group=groupDivergence)
divMaxWeight = input.float(10.0, "背離最大參與權重 %", minval=0.0, maxval=20.0, step=0.5, group=groupDivergence)
showDivInCompact = input.bool(true, "Dashboard 精簡模式顯示背離層", group=groupDivergence)
```

### 3.1 divMode 語意

- `Off`：完全關閉 Divergence layer。
- `Observe Only`：預設，只顯示 / 警示，不參與主模型。
- `Auto`：當背離或共振分數足夠明確時，以低權重參與 clue / conflict / downgrade。

v0.5.1 不建議加入 `Force On`。背離訊號在強趨勢中容易過早出現，強制參與會讓模型太敏感。

---

## 4. 追價風險來源

Divergence layer 不另建 RSI、MACD 或外部 oscillator。

它使用指標內既有的追價風險：

```pine
bullChaseRisk = endRiskUp
bearChaseRisk = endRiskDn
```

語意：

- `bullChaseRisk`：多頭追價風險。由上漲熱度與上漲趨勢成熟度共同形成。
- `bearChaseRisk`：空頭追價風險。由下跌恐慌熱度與下跌趨勢成熟度共同形成。

這樣做的好處是背離層仍然沿用本指標自己的語言，不會引入不一致的 RSI / MACD 外部語意。

---

## 5. Pivot 設計

### 5.1 為什麼使用 confirmed pivot

背離如果即時偵測，容易重繪與誤導。

因此使用：

```pine
pricePivotHigh = ta.pivothigh(high, divPivotLeft, divPivotRight)
pricePivotLow = ta.pivotlow(low, divPivotLeft, divPivotRight)
```

當 pivot 確認時，訊號會延遲 `divPivotRight` 根 K 棒，但較穩定。

### 5.2 對應 pivot bar 的 risk

pivot 在確認時，真正的 pivot 發生在 `divPivotRight` 根之前。

因此 risk 也要取同一根：

```pine
bullRiskAtHighPivot = bullChaseRisk[divPivotRight]
bearRiskAtLowPivot = bearChaseRisk[divPivotRight]
```

不得使用當前 bar 的 risk 直接對應歷史 pivot，否則價格與風險時間點會錯位。

### 5.3 保存前一個 pivot

需要保存最近兩個有效高點 pivot：

```text
prevPriceHighPivot
lastPriceHighPivot
prevBullRiskAtHigh
lastBullRiskAtHigh
```

以及最近兩個有效低點 pivot：

```text
prevPriceLowPivot
lastPriceLowPivot
prevBearRiskAtLow
lastBearRiskAtLow
```

---

## 6. 頂背離 / 空頭背離

### 6.1 定義

頂背離成立條件：

```text
lastPriceHighPivot > prevPriceHighPivot
AND lastBullRiskAtHigh < prevBullRiskAtHigh
AND priceHighBreakPct >= divMinPricePct
AND riskGap >= divMinRiskGap
AND max(lastBullRiskAtHigh, prevBullRiskAtHigh) >= divRiskMin
```

其中：

```text
priceHighBreakPct = (lastPriceHighPivot / prevPriceHighPivot - 1) × 100
riskGap = prevBullRiskAtHigh - lastBullRiskAtHigh
```

### 6.2 語意

頂背離代表：

```text
價格創新高，但多頭追價風險沒有同步確認。
```

它應被翻譯為：

- 追多品質下降。
- 高位供給觀察。
- 上攻效率下降。
- 多單續抱可，但不宜無腦加碼。
- 空手者不追多，等待回測或更清楚訊號。

### 6.3 不可翻譯為

頂背離不得直接翻譯為：

- 做空訊號。
- 派發確認。
- 多頭結束。
- 反轉已成立。

---

## 7. 底背離 / 多頭背離

### 7.1 定義

底背離成立條件：

```text
lastPriceLowPivot < prevPriceLowPivot
AND lastBearRiskAtLow < prevBearRiskAtLow
AND priceLowBreakPct >= divMinPricePct
AND riskGap >= divMinRiskGap
AND max(lastBearRiskAtLow, prevBearRiskAtLow) >= divRiskMin
```

其中：

```text
priceLowBreakPct = (prevPriceLowPivot / lastPriceLowPivot - 1) × 100
riskGap = prevBearRiskAtLow - lastBearRiskAtLow
```

### 7.2 語意

底背離代表：

```text
價格創新低，但空頭追價風險沒有同步確認。
```

它應被翻譯為：

- 追空品質下降。
- 低位承接觀察。
- 下跌效率下降。
- 空單續抱可，但應保護利潤。
- 空手者不追空，等待反彈失敗或更清楚訊號。

### 7.3 不可翻譯為

底背離不得直接翻譯為：

- 買進訊號。
- 吸籌確認。
- 空頭結束。
- 反轉已成立。

---

## 8. 多頭過熱共振

### 8.1 定義

多頭過熱共振成立條件：

```text
lastPriceHighPivot > prevPriceHighPivot
AND lastBullRiskAtHigh > prevBullRiskAtHigh
AND priceHighBreakPct >= divMinPricePct
AND riskRise >= divMinRiskGap
AND lastBullRiskAtHigh >= divRiskMin
```

其中：

```text
riskRise = lastBullRiskAtHigh - prevBullRiskAtHigh
```

### 8.2 語意

多頭過熱共振代表：

```text
價格創新高，多頭追價風險也創新高。
```

它不是背離，而是「趨勢與追價風險同向升高」。

正確翻譯：

- 多頭仍強，但追價風險升高。
- 不代表馬上反轉，但代表追高品質變差。
- 對持有多單者：續抱可以，但提高停利 / 停損保護。
- 對空手者：禁止追多或等待回測。

---

## 9. 空頭恐慌共振

### 9.1 定義

空頭恐慌共振成立條件：

```text
lastPriceLowPivot < prevPriceLowPivot
AND lastBearRiskAtLow > prevBearRiskAtLow
AND priceLowBreakPct >= divMinPricePct
AND riskRise >= divMinRiskGap
AND lastBearRiskAtLow >= divRiskMin
```

其中：

```text
riskRise = lastBearRiskAtLow - prevBearRiskAtLow
```

### 9.2 語意

空頭恐慌共振代表：

```text
價格創新低，空頭追價風險也創新高。
```

它不是底背離，而是「下跌趨勢與追空風險同向升高」。

正確翻譯：

- 空頭仍強，但追空風險升高。
- 不代表馬上反彈，但代表追空品質變差。
- 對持有空單者：續抱可以，但提高停利 / 停損保護。
- 對空手者：禁止追空或等待反彈失敗。

---

## 10. 四格判讀總表

| 價格行為 | 追價風險行為 | 狀態名稱 | 語意 | 行動語氣 |
|---|---|---|---|---|
| 創新高 | 多頭追價風險也創新高 | 多頭過熱共振 | 趨勢仍強但追多風險升高 | 續抱可，不追多 |
| 創新高 | 多頭追價風險沒有創新高 | 頂背離 / 高位供給觀察 | 上攻效率下降 | 降低追多、觀察供給 |
| 創新低 | 空頭追價風險也創新高 | 空頭恐慌共振 | 下跌仍強但追空風險升高 | 續抱可，不追空 |
| 創新低 | 空頭追價風險沒有創新高 | 底背離 / 低位承接觀察 | 下跌效率下降 | 降低追空、觀察承接 |

---

## 11. 分數設計

### 11.1 頂背離分數

```text
bearishDivergenceScore = weighted(
    priceHighBreakScore,
    riskGapScore,
    riskRelevanceScore
)
```

建議權重：

```text
priceHighBreakScore 0.30
riskGapScore        0.50
riskRelevanceScore  0.20
```

### 11.2 底背離分數

```text
bullishDivergenceScore = weighted(
    priceLowBreakScore,
    riskGapScore,
    riskRelevanceScore
)
```

建議權重：

```text
priceLowBreakScore 0.30
riskGapScore       0.50
riskRelevanceScore 0.20
```

### 11.3 多頭過熱共振分數

```text
bullChaseClimaxScore = weighted(
    priceHighBreakScore,
    riskRiseScore,
    lastBullRiskAtHigh
)
```

### 11.4 空頭恐慌共振分數

```text
bearChaseClimaxScore = weighted(
    priceLowBreakScore,
    riskRiseScore,
    lastBearRiskAtLow
)
```

### 11.5 有效旗標

```text
bearishDivValid
bullishDivValid
bullClimaxValid
bearClimaxValid
```

有效條件應包括：

- `divMode != "Off"`。
- 已有兩個有效 pivot。
- 對應分數達 `divRiskMin` 或自訂門檻。
- 價格突破幅度達 `divMinPricePct`。
- 風險差距達 `divMinRiskGap`。

---

## 12. 權重接入方式

### 12.1 Observe Only

預設 `Observe Only`：

```text
divWeightApplied = 0
divActive = false
```

只顯示：

- Dashboard。
- Debug。
- Alert。

不影響模型。

### 12.2 Auto

Auto 模式下：

```text
divTopScore = max(
    bearishDivergenceScore,
    bullishDivergenceScore,
    bullChaseClimaxScore,
    bearChaseClimaxScore
)

divWeightApplied = divMaxWeight / 100 × gate(divTopScore, divRiskMin, 90)
```

### 12.3 建議最大權重

```text
divMaxWeight default = 10%
```

理由：背離非常有用，但在強趨勢中容易過早出現，因此權重應小於或等於 MTF layer。

---

## 13. 對主模型的接入位置

### 13.1 不直接改 formal regime

Divergence 不直接改：

```text
formalId
candidateId
candidateBars
confirmedId
```

### 13.2 可加強 clue observation

高位：

```text
highClueObservation 可加入 bearishDivValid
trendClueDispute 可加入 bearishDivValid 或 bullClimaxValid
```

低位：

```text
lowClueObservation 可加入 bullishDivValid
trendClueDispute 可加入 bullishDivValid 或 bearClimaxValid
```

### 13.3 可加強 candidateConflict

多方候選遇到高位背離 / 多頭過熱共振時，可形成供給 conflict：

```text
longSideDivergenceConflict = bearishDivValid OR bullClimaxValid
```

空方候選遇到底背離 / 空頭恐慌共振時，可形成承接 conflict：

```text
shortSideDivergenceConflict = bullishDivValid OR bearClimaxValid
```

### 13.4 可加強 Flat Action No Chase

```text
flatNoChaseLong 可加入 bearishDivValid OR bullClimaxValid
flatNoChaseShort 可加入 bullishDivValid OR bearClimaxValid
```

### 13.5 可加強 Pace Context Downgrade

多方降級：

```text
F3 順勢試多 → F2 小試多
F2 小試多 → F1 等回測
```

觸發：

```text
bearishDivValid OR bullClimaxValid
```

空方降級：

```text
F5 順勢試空 → F4 小試空
F4 小試空 → F1 等反彈失敗
```

觸發：

```text
bullishDivValid OR bearClimaxValid
```

### 13.6 可低權重加強 effective scores

若使用 Auto 模式，可低權重加強：

```text
bearishDivergenceScore → distEff / upsideExhaustion witness
bullishDivergenceScore → accEff / downsideExhaustion witness
bullChaseClimaxScore → no-chase long / end-risk witness，不直接加派發
bearChaseClimaxScore → no-chase short / panic-risk witness，不直接加吸籌
```

注意：climax 共振代表原趨勢仍強但追價風險升高，不應直接視為反向階段加分。

---

## 14. Dashboard 顯示

新增 dashboard 文本：

```text
divStatusText
divClueText
divCompactText
```

### 14.1 狀態文字

```text
Off → 背離關閉
資料不足 → 背離資料不足
Observe Only → 背離觀察
Auto → 背離自動參與
```

### 14.2 線索文字

```text
頂背離｜追多品質下降
底背離｜追空品質下降
多頭過熱｜不追多
空頭恐慌｜不追空
背離中性
```

### 14.3 精簡顯示

```text
背離｜頂背離 / 底背離 / 多頭過熱 / 空頭恐慌 / 無｜W x%
```

---

## 15. Debug 單線

新增 Debug 選項：

```text
頂背離
底背離
多頭追價共振
空頭追價共振
背離權重
```

對應：

```text
bearishDivergenceScore
bullishDivergenceScore
bullChaseClimaxScore
bearChaseClimaxScore
divWeightApplied * 100
```

---

## 16. Alerts

### 16.1 新增 alertcondition

```text
Divergence Witness Layer 重要事件
```

### 16.2 Dynamic alerts

新增 dynamic alert：

```text
頂背離｜追多品質下降
底背離｜追空品質下降
多頭過熱共振｜不追多
空頭恐慌共振｜不追空
```

Alert 文案需避免交易指令：

不使用：

```text
Buy
Sell
Short
Cover
```

使用：

```text
observe
no chase
protect profit
wait for retest
wait for failed rebound
```

---

## 17. 驗收標準

### 17.1 編譯

- Pine v6 編譯通過。
- 不超過 plot count。
- 不造成 table row overflow。
- confirmed pivot 不重繪。

### 17.2 Observe Only

`Divergence Mode = Observe Only` 時：

- 不改 `formalId`。
- 不改 `candidateDisplayId`。
- 不改 `evidenceStrength`。
- 不改 `flatActionLevel`。
- 不改背景。
- 只影響 Dashboard / Debug / Alerts。

### 17.3 語意測試

測試場景：

1. 強多頭一路創高，追價風險也創高：應顯示多頭過熱共振，不是頂背離。
2. 價格創高但追價風險下降：應顯示頂背離 / 追多品質下降。
3. 強空頭一路創低，追價風險也創高：應顯示空頭恐慌共振，不是底背離。
4. 價格創低但追價風險下降：應顯示底背離 / 追空品質下降。
5. 高位背離出現時，Flat Action 不應繼續無條件順勢試多。
6. 低位背離出現時，Flat Action 不應繼續無條件順勢試空。

### 17.4 強趨勢保護

在強趨勢中，背離不得過度提早反轉主模型。

若只有背離但趨勢 continuation / extension 仍強，應優先顯示：

```text
趨勢仍在，但追價品質下降
```

而不是：

```text
反轉成立
```

---

## 18. AI 實作摘要

未來請 Codex 或 AI 實作此 patch 時，使用以下摘要：

```text
請在 Chase Risk Market Regime Radar v0.5 上實作 v0.5.1 Divergence Witness Layer。
此層使用 price pivot 與 endRiskUp / endRiskDn 的 pivot 對應值，偵測頂背離、底背離、多頭過熱共振、空頭恐慌共振。
Divergence layer 是 witness layer，不是交易訊號，不得直接改 formalId / candidateId。
預設 Divergence Mode = Observe Only，只顯示 Dashboard / Debug / Alerts。
Auto 模式才可低權重參與 clue observation、candidate conflict、Flat Action no-chase、Pace Context Downgrade。
頂背離語意是追多品質下降；底背離語意是追空品質下降；共振語意是原趨勢仍強但追價風險升高。
請避免使用 Buy / Sell / Short / Cover 等交易指令文字。
```

---

## 19. 結論

Divergence Witness Layer 應該補上 v0.5 之後最自然的一塊拼圖：

```text
價格是否仍在創高 / 創低？
追價風險是否同步確認？
若沒有同步，是否代表原方向追價品質下降？
若同步創高，是否代表雖然趨勢仍強，但追價風險也升高？
```

這一層的價值不在於預測反轉，而在於讓使用者更早知道：

```text
現在不是不能續抱，而是不能再用原本那種無腦追價心態看待市場。
```
