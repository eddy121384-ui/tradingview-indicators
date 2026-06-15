# Chase Risk Market Regime Radar v0.5.1｜Divergence Witness Layer Patch Spec

> 本文件是 v0.5 完整規格書的 patch spec。  
> 目的：在不重寫主模型的前提下，新增「追價風險背離 / 共振」判斷，作為 Volume 與 MTF 之外的第三個 witness layer。  
> **v0.5.1-r1 更新重點**：根據實際圖表測試，單純用「價格 pivot 當根的 chase risk」太容易漏判。背離應改成「價格 pivot 附近的 chase-risk peak 對位」，並新增 soft divergence 與 signal hold。

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

## 1. 實測問題與 r1 修正方向

### 1.1 實測問題

使用 v0.5.1 第一版套到實際圖表後，出現以下問題：

```text
價格在高位測高 / 創高，
下方 bullChaseRisk / endRiskUp 的高峰明顯下降，
人眼判讀符合頂背離或高位供給觀察，
但 Dashboard 顯示「背離｜無」。
```

這不是使用者觀察錯，而是第一版偵測邏輯太嚴格。

### 1.2 問題原因

第一版使用：

```pine
bullRiskAtHighPivot = bullChaseRisk[divPivotRight]
bearRiskAtLowPivot = bearChaseRisk[divPivotRight]
```

也就是只取「價格 pivot 那一根」的追價風險。

但真實市場常見狀況是：

```text
chase-risk peak 可能先於 price pivot 出現，
也可能晚於 price pivot 出現，
或在 price pivot 附近幾根內形成峰值。
```

因此背離不應要求 price pivot 與 risk peak 完全同根對齊。

### 1.3 r1 修正方向

v0.5.1-r1 必須新增三個能力：

1. **Risk alignment window**：用價格 pivot 前後 N 根內的 chase-risk peak，對應該價格 pivot。
2. **Signal hold**：背離 / 共振確認後保留 N 根，避免下一個小 pivot 出現後立刻消失。
3. **Soft divergence**：價格接近前高 / 前低，或高位測壓 / 低位測底，即使沒有嚴格創高 / 破低，也能標為高位供給觀察 / 低位承接觀察。

這三項是 v0.5.1 實測修正的必做項目。

---

## 2. 核心設計原則

### 2.1 Divergence layer 是證人，不是主引擎

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

若讓 divergence 參與 effective score，只能透過小權重 multiplier，且預設應為 Observe Only。

### 2.2 背離不是反轉

頂背離不等於做空。  
底背離不等於做多。

正確語意是：

```text
頂背離 = 追多品質下降 / 高位供給觀察
底背離 = 追空品質下降 / 低位承接觀察
```

### 2.3 共振不是背離

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

### 2.4 Strict 與 Soft 必須分層

v0.5.1-r1 必須把背離分成：

```text
Strict Divergence：價格明確創高 / 破低，風險 peak 反向下降。
Soft Divergence：價格接近前高 / 前低，或高位測壓 / 低位測底，風險 peak 已明顯下降。
```

Strict 可用於更高強度的 clue / no-chase。  
Soft 只能用於 observation / dashboard / no-chase，不得直接推動 formal regime。

---

## 3. 新增 Input Group

新增：

```pine
groupDivergence = "參數｜Divergence Witness Layer v0.5.1"
```

建議放在 `groupMTF` 之後、`groupRegime` 之前。

---

## 4. 新增 Inputs

```pine
divMode = input.string("Observe Only", "Divergence Mode", options=["Off", "Observe Only", "Auto"], group=groupDivergence)
divPivotLeft = input.int(5, "背離 Pivot Left", minval=1, maxval=20, group=groupDivergence)
divPivotRight = input.int(5, "背離 Pivot Right", minval=1, maxval=20, group=groupDivergence)
divRiskAlignWindow = input.int(3, "追價風險對位視窗", minval=0, maxval=10, group=groupDivergence)
divSignalHoldBars = input.int(20, "背離訊號保留根數", minval=1, maxval=100, group=groupDivergence)
divMinPricePct = input.float(0.5, "最小創高 / 破低幅度 %", minval=0.0, maxval=10.0, step=0.1, group=groupDivergence)
divNearPricePct = input.float(1.0, "Soft 背離｜接近前高 / 前低容許 %", minval=0.0, maxval=10.0, step=0.1, group=groupDivergence)
divMinRiskGap = input.float(8.0, "最小風險背離差距", minval=0.0, maxval=50.0, step=0.5, group=groupDivergence)
divRiskMin = input.float(55.0, "最低有效追價風險", minval=0.0, maxval=100.0, step=0.5, group=groupDivergence)
divMaxWeight = input.float(10.0, "背離最大參與權重 %", minval=0.0, maxval=20.0, step=0.5, group=groupDivergence)
showDivInCompact = input.bool(true, "Dashboard 精簡模式顯示背離層", group=groupDivergence)
```

### 4.1 divMode 語意

- `Off`：完全關閉 Divergence layer。
- `Observe Only`：預設，只顯示 / 警示，不參與主模型。
- `Auto`：當背離或共振分數足夠明確時，以低權重參與 clue / conflict / downgrade。

v0.5.1 不建議加入 `Force On`。背離訊號在強趨勢中容易過早出現，強制參與會讓模型太敏感。

### 4.2 新增參數語意

#### divRiskAlignWindow

價格 pivot 與 chase-risk peak 不一定同根。此參數定義在價格 pivot 前後多少根內尋找 chase-risk peak。

預設 3，代表：

```text
pivot bar 前後 3 根內，取 bullChaseRisk / bearChaseRisk 最高值作為該 pivot 對應風險。
```

#### divSignalHoldBars

背離 / 共振確認後，Dashboard、Debug 與 alert 狀態應保留 N 根，不要因下一個小 pivot 出現立刻消失。

#### divNearPricePct

Soft divergence 使用。當價格沒有嚴格創新高 / 破低，但仍接近前高 / 前低時，可視為「測壓 / 測底」。

---

## 5. 追價風險來源

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

## 6. Pivot 與 Risk Peak 對位設計

### 6.1 confirmed price pivot

背離若即時偵測，容易重繪與誤導。

因此使用 confirmed pivot：

```pine
pricePivotHigh = ta.pivothigh(high, divPivotLeft, divPivotRight)
pricePivotLow = ta.pivotlow(low, divPivotLeft, divPivotRight)
```

當 pivot 確認時，訊號會延遲 `divPivotRight` 根 K 棒，但較穩定。

### 6.2 不可只取 pivot 當根 risk

以下寫法太嚴格，會漏判：

```pine
bullRiskAtHighPivot = bullChaseRisk[divPivotRight]
bearRiskAtLowPivot = bearChaseRisk[divPivotRight]
```

這只能拿到 price pivot bar 當根的 risk，無法捕捉「risk peak 早於 / 晚於 price pivot」的常見情況。

### 6.3 必須使用 risk alignment window

正確做法：

```text
對每一個 confirmed price pivot，
找到該 pivot bar 前後 divRiskAlignWindow 根內的 chase-risk peak，
作為該 price pivot 對應的 risk peak。
```

概念：

```text
high pivot → 尋找 bullChaseRisk peak
low pivot  → 尋找 bearChaseRisk peak
```

### 6.4 Pine 實作提示

若 Pine 不方便往「未來 bar」看，可在 pivot confirmation 當下，用已知資料重建視窗。

當 `pricePivotHigh` 在目前 bar 被確認時，真正 pivot 位於 `divPivotRight` 根之前。可用：

```text
risk window = [divPivotRight - divRiskAlignWindow, divPivotRight + divRiskAlignWindow]
```

在 Pine 的歷史索引語意下，這些都是目前 bar 已知的過去資料。

需要注意：

- index 不得小於 0。
- `divRiskAlignWindow = 0` 時，退回 pivot 當根 risk。
- 建議寫 helper function，以 loop 取得 window max。

概念函式：

```pine
f_windowMaxRisk(src, pivotRight, win) =>
    float _max = na
    int _from = math.max(pivotRight - win, 0)
    int _to = pivotRight + win
    for i = _from to _to
        _v = src[i]
        if not na(_v)
            _max := na(_max) ? _v : math.max(_max, _v)
    _max
```

此函式只使用當前 bar 可見的歷史資料，不應重繪。

### 6.5 保存最近兩個 pivot 與 risk peak

需要保存最近兩個有效高點 pivot：

```text
prevPriceHighPivot
lastPriceHighPivot
prevBullRiskAtHighPeak
lastBullRiskAtHighPeak
```

以及最近兩個有效低點 pivot：

```text
prevPriceLowPivot
lastPriceLowPivot
prevBearRiskAtLowPeak
lastBearRiskAtLowPeak
```

命名應使用 `Peak`，避免與舊版 `AtPivot` 混淆。

---

## 7. Strict 頂背離 / 空頭背離

### 7.1 定義

Strict 頂背離成立條件：

```text
lastPriceHighPivot > prevPriceHighPivot
AND lastBullRiskAtHighPeak < prevBullRiskAtHighPeak
AND priceHighBreakPct >= divMinPricePct
AND riskGap >= divMinRiskGap
AND max(lastBullRiskAtHighPeak, prevBullRiskAtHighPeak) >= divRiskMin
```

其中：

```text
priceHighBreakPct = (lastPriceHighPivot / prevPriceHighPivot - 1) × 100
riskGap = prevBullRiskAtHighPeak - lastBullRiskAtHighPeak
```

### 7.2 語意

Strict 頂背離代表：

```text
價格明確創新高，但多頭追價風險 peak 沒有同步確認。
```

翻譯：

- 追多品質下降。
- 高位供給觀察。
- 上攻效率下降。
- 多單續抱可，但不宜無腦加碼。
- 空手者不追多，等待回測或更清楚訊號。

### 7.3 不可翻譯為

不得直接翻譯為：

- 做空訊號。
- 派發確認。
- 多頭結束。
- 反轉已成立。

---

## 8. Strict 底背離 / 多頭背離

### 8.1 定義

Strict 底背離成立條件：

```text
lastPriceLowPivot < prevPriceLowPivot
AND lastBearRiskAtLowPeak < prevBearRiskAtLowPeak
AND priceLowBreakPct >= divMinPricePct
AND riskGap >= divMinRiskGap
AND max(lastBearRiskAtLowPeak, prevBearRiskAtLowPeak) >= divRiskMin
```

其中：

```text
priceLowBreakPct = (prevPriceLowPivot / lastPriceLowPivot - 1) × 100
riskGap = prevBearRiskAtLowPeak - lastBearRiskAtLowPeak
```

### 8.2 語意

Strict 底背離代表：

```text
價格明確創新低，但空頭追價風險 peak 沒有同步確認。
```

翻譯：

- 追空品質下降。
- 低位承接觀察。
- 下跌效率下降。
- 空單續抱可，但應保護利潤。
- 空手者不追空，等待反彈失敗或更清楚訊號。

### 8.3 不可翻譯為

不得直接翻譯為：

- 買進訊號。
- 吸籌確認。
- 空頭結束。
- 反轉已成立。

---

## 9. Soft 高位供給背離

### 9.1 設計目的

實際市場常見狀況是：價格沒有精準創新高，但已接近前高、測壓、或形成高位雙頂；同時 bullChaseRisk peak 明顯下降。

這種情況不應叫 Strict 頂背離，但應顯示為：

```text
高位供給觀察 / 追多品質下降
```

### 9.2 定義

Soft 高位供給背離成立條件：

```text
priceNearHigh = lastPriceHighPivot >= prevPriceHighPivot × (1 - divNearPricePct / 100)
AND lastBullRiskAtHighPeak < prevBullRiskAtHighPeak
AND riskGap >= divMinRiskGap
AND max(lastBullRiskAtHighPeak, prevBullRiskAtHighPeak) >= divRiskMin
AND NOT strictBearishDivValid
```

可選擇加入：

```text
uptrendGate > 0.25 OR bullBg >= 50 OR close > maturityMa
```

用來確保這是高位測壓，不是低位亂跳。

### 9.3 語意

Soft 高位供給背離代表：

```text
價格仍在高位測壓，但多頭追價風險 peak 已下降。
```

文字應使用：

- 高位供給觀察。
- 追多品質下降。
- 高位背離觀察。

不應使用：

- 頂背離確認。
- 派發確認。
- 做空。

---

## 10. Soft 低位承接背離

### 10.1 設計目的

實際市場常見狀況是：價格沒有精準破低，但已接近前低、測底、或形成低位雙底；同時 bearChaseRisk peak 明顯下降。

這種情況不應叫 Strict 底背離，但應顯示為：

```text
低位承接觀察 / 追空品質下降
```

### 10.2 定義

Soft 低位承接背離成立條件：

```text
priceNearLow = lastPriceLowPivot <= prevPriceLowPivot × (1 + divNearPricePct / 100)
AND lastBearRiskAtLowPeak < prevBearRiskAtLowPeak
AND riskGap >= divMinRiskGap
AND max(lastBearRiskAtLowPeak, prevBearRiskAtLowPeak) >= divRiskMin
AND NOT strictBullishDivValid
```

可選擇加入：

```text
downtrendGate > 0.25 OR bearBg >= 50 OR close < maturityMa
```

用來確保這是低位測底，不是高位亂跳。

### 10.3 語意

Soft 低位承接背離代表：

```text
價格仍在低位測底，但空頭追價風險 peak 已下降。
```

文字應使用：

- 低位承接觀察。
- 追空品質下降。
- 低位背離觀察。

不應使用：

- 底背離確認。
- 吸籌確認。
- 買進。

---

## 11. 多頭過熱共振

### 11.1 定義

多頭過熱共振成立條件：

```text
lastPriceHighPivot > prevPriceHighPivot
AND lastBullRiskAtHighPeak > prevBullRiskAtHighPeak
AND priceHighBreakPct >= divMinPricePct
AND riskRise >= divMinRiskGap
AND lastBullRiskAtHighPeak >= divRiskMin
```

其中：

```text
riskRise = lastBullRiskAtHighPeak - prevBullRiskAtHighPeak
```

### 11.2 語意

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

## 12. 空頭恐慌共振

### 12.1 定義

空頭恐慌共振成立條件：

```text
lastPriceLowPivot < prevPriceLowPivot
AND lastBearRiskAtLowPeak > prevBearRiskAtLowPeak
AND priceLowBreakPct >= divMinPricePct
AND riskRise >= divMinRiskGap
AND lastBearRiskAtLowPeak >= divRiskMin
```

其中：

```text
riskRise = lastBearRiskAtLowPeak - prevBearRiskAtLowPeak
```

### 12.2 語意

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

## 13. 六格判讀總表

| 價格行為 | 追價風險行為 | 狀態名稱 | 強度 | 語意 | 行動語氣 |
|---|---|---|---|---|---|
| 明確創新高 | 多頭追價風險 peak 也創新高 | 多頭過熱共振 | 強 | 趨勢仍強但追多風險升高 | 續抱可，不追多 |
| 明確創新高 | 多頭追價風險 peak lower high | Strict 頂背離 | 強 | 上攻效率下降 | 降低追多、觀察供給 |
| 接近前高 / 高位測壓 | 多頭追價風險 peak lower high | Soft 高位供給觀察 | 中 | 高位追多品質下降 | 不追多，等回測 |
| 明確創新低 | 空頭追價風險 peak 也創新高 | 空頭恐慌共振 | 強 | 下跌仍強但追空風險升高 | 續抱可，不追空 |
| 明確創新低 | 空頭追價風險 peak lower high | Strict 底背離 | 強 | 下跌效率下降 | 降低追空、觀察承接 |
| 接近前低 / 低位測底 | 空頭追價風險 peak lower high | Soft 低位承接觀察 | 中 | 低位追空品質下降 | 不追空，等反彈失敗 |

---

## 14. 分數設計

### 14.1 Strict 頂背離分數

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

### 14.2 Strict 底背離分數

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

### 14.3 Soft 高位供給分數

```text
softHighSupplyDivScore = weighted(
    priceNearHighScore,
    riskGapScore,
    riskRelevanceScore
)
```

### 14.4 Soft 低位承接分數

```text
softLowDemandDivScore = weighted(
    priceNearLowScore,
    riskGapScore,
    riskRelevanceScore
)
```

### 14.5 多頭過熱共振分數

```text
bullChaseClimaxScore = weighted(
    priceHighBreakScore,
    riskRiseScore,
    lastBullRiskAtHighPeak
)
```

### 14.6 空頭恐慌共振分數

```text
bearChaseClimaxScore = weighted(
    priceLowBreakScore,
    riskRiseScore,
    lastBearRiskAtLowPeak
)
```

### 14.7 有效旗標

```text
strictBearishDivValid
strictBullishDivValid
softHighSupplyDivValid
softLowDemandDivValid
bullClimaxValid
bearClimaxValid
```

---

## 15. Signal Hold 設計

### 15.1 為什麼需要 hold

若背離只在 pivot confirmation 當根顯示，使用者在圖上很容易看不到。若下一個小 pivot 出現，狀態又被覆蓋，Dashboard 會顯示「無」，造成肉眼看到背離但指標不承認。

因此必須新增 signal hold。

### 15.2 必要變數

```text
var int strictBearishDivBarsSince = na
var int strictBullishDivBarsSince = na
var int softHighSupplyDivBarsSince = na
var int softLowDemandDivBarsSince = na
var int bullClimaxBarsSince = na
var int bearClimaxBarsSince = na
```

或等價設計。

### 15.3 Hold flags

```text
strictBearishDivRecent = strictBearishDivBarsSince <= divSignalHoldBars
strictBullishDivRecent = strictBullishDivBarsSince <= divSignalHoldBars
softHighSupplyDivRecent = softHighSupplyDivBarsSince <= divSignalHoldBars
softLowDemandDivRecent = softLowDemandDivBarsSince <= divSignalHoldBars
bullClimaxRecent = bullClimaxBarsSince <= divSignalHoldBars
bearClimaxRecent = bearClimaxBarsSince <= divSignalHoldBars
```

### 15.4 Dashboard 必須使用 recent flags

Dashboard 不應只看當根 valid flags。

正確：

```text
divClueText 使用 recent flags
```

不是：

```text
divClueText 只使用當根 valid flags
```

### 15.5 模型參與仍應保守

Observe Only：recent flags 只顯示，不改模型。  
Auto：可使用 recent flags 參與 no-chase / downgrade，但不要讓過期訊號長期干擾。

---

## 16. 權重接入方式

### 16.1 Observe Only

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

### 16.2 Auto

Auto 模式下：

```text
divTopScore = max(
    bearishDivergenceScore,
    bullishDivergenceScore,
    softHighSupplyDivScore,
    softLowDemandDivScore,
    bullChaseClimaxScore,
    bearChaseClimaxScore
)

divWeightApplied = divMaxWeight / 100 × gate(divTopScore, divRiskMin, 90)
```

### 16.3 建議最大權重

```text
divMaxWeight default = 10%
```

理由：背離非常有用，但在強趨勢中容易過早出現，因此權重應小於或等於 MTF layer。

---

## 17. 對主模型的接入位置

### 17.1 不直接改 formal regime

Divergence 不直接改：

```text
formalId
candidateId
candidateBars
confirmedId
```

### 17.2 可加強 clue observation

高位：

```text
highClueObservation 可加入 strictBearishDivRecent OR softHighSupplyDivRecent
trendClueDispute 可加入 strictBearishDivRecent OR softHighSupplyDivRecent OR bullClimaxRecent
```

低位：

```text
lowClueObservation 可加入 strictBullishDivRecent OR softLowDemandDivRecent
trendClueDispute 可加入 strictBullishDivRecent OR softLowDemandDivRecent OR bearClimaxRecent
```

### 17.3 可加強 candidateConflict

多方候選遇到高位背離 / 多頭過熱共振時，可形成供給 conflict：

```text
longSideDivergenceConflict = strictBearishDivRecent OR softHighSupplyDivRecent OR bullClimaxRecent
```

空方候選遇到底背離 / 空頭恐慌共振時，可形成承接 conflict：

```text
shortSideDivergenceConflict = strictBullishDivRecent OR softLowDemandDivRecent OR bearClimaxRecent
```

### 17.4 可加強 Flat Action No Chase

```text
flatNoChaseLong 可加入 strictBearishDivRecent OR softHighSupplyDivRecent OR bullClimaxRecent
flatNoChaseShort 可加入 strictBullishDivRecent OR softLowDemandDivRecent OR bearClimaxRecent
```

### 17.5 可加強 Pace Context Downgrade

多方降級：

```text
F3 順勢試多 → F2 小試多
F2 小試多 → F1 等回測
```

觸發：

```text
strictBearishDivRecent OR softHighSupplyDivRecent OR bullClimaxRecent
```

空方降級：

```text
F5 順勢試空 → F4 小試空
F4 小試空 → F1 等反彈失敗
```

觸發：

```text
strictBullishDivRecent OR softLowDemandDivRecent OR bearClimaxRecent
```

### 17.6 可低權重加強 effective scores

若使用 Auto 模式，可低權重加強：

```text
strictBearishDivScore / softHighSupplyDivScore → distEff / upsideExhaustion witness
strictBullishDivScore / softLowDemandDivScore → accEff / downsideExhaustion witness
bullChaseClimaxScore → no-chase long / end-risk witness，不直接加派發
bearChaseClimaxScore → no-chase short / panic-risk witness，不直接加吸籌
```

注意：climax 共振代表原趨勢仍強但追價風險升高，不應直接視為反向階段加分。

---

## 18. Dashboard 顯示

新增 dashboard 文本：

```text
divStatusText
divClueText
divCompactText
```

### 18.1 狀態文字

```text
Off → 背離關閉
資料不足 → 背離資料不足
Observe Only → 背離觀察
Auto → 背離自動參與
```

### 18.2 線索文字

Dashboard 必須能區分 strict / soft / climax：

```text
頂背離｜追多品質下降
高位供給觀察｜追多品質下降
底背離｜追空品質下降
低位承接觀察｜追空品質下降
多頭過熱｜不追多
空頭恐慌｜不追空
背離中性
```

### 18.3 優先順序

若多個 recent flags 同時成立，Dashboard 顯示優先順序：

```text
Strict 頂背離 / Strict 底背離
→ Soft 高位供給 / Soft 低位承接
→ 多頭過熱 / 空頭恐慌
→ 中性
```

也可以依當前方向決定優先：

```text
formal/candidate 偏多 → 優先顯示高位相關風險
formal/candidate 偏空 → 優先顯示低位相關風險
```

### 18.4 精簡顯示

```text
背離｜頂背離 / 高位供給 / 底背離 / 低位承接 / 多頭過熱 / 空頭恐慌 / 無｜W x%
```

---

## 19. Debug 單線

新增 Debug 選項：

```text
頂背離
高位供給觀察
底背離
低位承接觀察
多頭追價共振
空頭追價共振
背離權重
```

對應：

```text
bearishDivergenceScore
softHighSupplyDivScore
bullishDivergenceScore
softLowDemandDivScore
bullChaseClimaxScore
bearChaseClimaxScore
divWeightApplied * 100
```

Debug 分數可顯示當根 score；Dashboard 顯示應使用 recent flags。

---

## 20. Alerts

### 20.1 新增 alertcondition

```text
Divergence Witness Layer 重要事件
```

### 20.2 Dynamic alerts

新增 dynamic alert：

```text
頂背離｜追多品質下降
高位供給觀察｜追多品質下降
底背離｜追空品質下降
低位承接觀察｜追空品質下降
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

## 21. 驗收標準

### 21.1 編譯

- Pine v6 編譯通過。
- 不超過 plot count。
- 不造成 table row overflow。
- confirmed pivot 不重繪。
- `divRiskAlignWindow` 不使用未來資料。

### 21.2 Observe Only

`Divergence Mode = Observe Only` 時：

- 不改 `formalId`。
- 不改 `candidateDisplayId`。
- 不改 `evidenceStrength`。
- 不改 `flatActionLevel`。
- 不改背景。
- 只影響 Dashboard / Debug / Alerts。

### 21.3 語意測試

測試場景：

1. 強多頭一路創高，追價風險 peak 也創高：應顯示多頭過熱共振，不是頂背離。
2. 價格明確創高，但追價風險 peak 下降：應顯示頂背離 / 追多品質下降。
3. 價格高位測壓或接近前高，但追價風險 peak 下降：應顯示高位供給觀察，不應顯示無。
4. 強空頭一路創低，追價風險 peak 也創高：應顯示空頭恐慌共振，不是底背離。
5. 價格明確創低，但追價風險 peak 下降：應顯示底背離 / 追空品質下降。
6. 價格低位測底或接近前低，但追價風險 peak 下降：應顯示低位承接觀察，不應顯示無。
7. 背離確認後，Dashboard 應在 `divSignalHoldBars` 內保留訊號，不應下一個小 pivot 出現就變成無。
8. 高位背離出現時，Flat Action 不應繼續無條件順勢試多。
9. 低位背離出現時，Flat Action 不應繼續無條件順勢試空。

### 21.4 實測案例：高位測高但未偵測

若出現以下圖形：

```text
價格在高位測高 / 創高，
bullChaseRisk 的前一段 peak 明顯高於後一段 peak，
但 Dashboard 顯示「背離｜無」
```

則此實作未通過 v0.5.1-r1 驗收。

此情境至少應顯示：

```text
高位供給觀察｜追多品質下降
```

若價格明確創新高，則應顯示：

```text
頂背離｜追多品質下降
```

### 21.5 強趨勢保護

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

## 22. AI 實作摘要

未來請 Codex 或 AI 實作 / 修正此 patch 時，使用以下摘要：

```text
請修正 Chase Risk Market Regime Radar v0.5.1 Divergence Witness Layer。
此層使用 price pivot 與 endRiskUp / endRiskDn 的 pivot 附近 window peak，偵測頂背離、底背離、高位供給觀察、低位承接觀察、多頭過熱共振、空頭恐慌共振。
不要只用 price pivot 當根的 chase risk；必須新增 divRiskAlignWindow，預設 3。
新增 divSignalHoldBars，預設 20，讓 Dashboard / Debug / Alerts 保留近期背離狀態。
新增 soft divergence：高位接近前高但 bullChaseRisk peak lower high → 高位供給觀察；低位接近前低但 bearChaseRisk peak lower high → 低位承接觀察。
Divergence layer 是 witness layer，不是交易訊號，不得直接改 formalId / candidateId。
預設 Divergence Mode = Observe Only，只顯示 Dashboard / Debug / Alerts。
Auto 模式才可低權重參與 clue observation、candidate conflict、Flat Action no-chase、Pace Context Downgrade。
頂背離語意是追多品質下降；底背離語意是追空品質下降；共振語意是原趨勢仍強但追價風險升高。
請避免使用 Buy / Sell / Short / Cover 等交易指令文字。
不要重構整份 Pine Script，只修 Divergence Witness Layer。
```

---

## 23. 結論

Divergence Witness Layer 應該補上 v0.5 之後最自然的一塊拼圖：

```text
價格是否仍在創高 / 創低？
追價風險 peak 是否同步確認？
若沒有同步，是否代表原方向追價品質下降？
若同步創高，是否代表雖然趨勢仍強，但追價風險也升高？
```

v0.5.1-r1 的重點不是讓指標更會猜反轉，而是讓它更貼近真實圖表上的背離語意：

```text
人眼看到的是一段區域的峰與峰，
不是單根 K 棒對單根 K 棒。
```

因此，正確實作應該像市場偵探，而不是只接受完全同根對齊的法院證據。
