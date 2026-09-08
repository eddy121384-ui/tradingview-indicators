# Shiori Liquidity Structure Engine v0.1｜ICT-Inspired Market Logic Specification

> 文件狀態：Draft for review  
> 對應 Issue：#11  
> 實作目標：Pine Script v6 overlay indicator  
> 專案定位：ICT-inspired、規則透明、可測試、盡量不重繪；不宣稱為任何官方 ICT 教學、官方指標或未公開演算法的還原。

---

## 0. 一句話定位

Shiori Liquidity Structure Engine v0.1 不是一個看到 FVG 就亮燈的訊號器，而是一套市場事件狀態機：

```text
HTF Context
→ Liquidity Map
→ Sweep / Raid
→ Displacement
→ Market Structure Shift
→ FVG Retracement
→ Qualified / Invalid / Expired Setup
```

它的主要任務不是預測每一段行情，而是回答：

```text
市場正在尋找哪一側流動性？
流動性是否真的被掃掉？
掃蕩後是否出現足以改變短期敘事的價格位移？
目前是否存在可被追蹤、可失效、可回測的 setup？
```

---

## 1. 背景與問題定義

### 1.1 現有 ICT / SMC 指標的常見問題

TradingView 上常見腳本通常能偵測以下一項或多項元素：

```text
FVG
Order Block
BOS / CHoCH
Equal High / Equal Low
Previous Day High / Low
Session Range
Premium / Discount
Liquidity Sweep
```

但單點偵測不等於完整交易邏輯。常見問題包括：

1. 每一個三根 K 棒缺口都被畫成 FVG，未區分尺寸、位移品質、方向背景與生命週期。
2. 只要影線刺過前高前低就標記 sweep，未區分真正拒絕、接受突破或延續突破。
3. BOS、CHoCH、MSS 定義混用，同一根 K 棒可能同時被貼上多個互相矛盾的標籤。
4. 高週期方向使用未確認資料，歷史看起來完美，即時卻反覆改寫。
5. 所有區域永久留在圖上，最後盤面變成資訊垃圾場。
6. 指標只告訴使用者「發生了什麼」，卻不說目前事件順序走到哪一步、缺少什麼、何時失效。
7. 多個概念同時存在時，沒有優先級、權重上限與衝突治理。

### 1.2 v0.1 要解決的核心問題

v0.1 只專注一條可驗證主鏈：

```text
先有 Context，
再辨識 Liquidity，
流動性被 Sweep 後，
必須出現 Displacement 與 MSS，
最後回踩有效 FVG，
才形成 Qualified Setup。
```

任何單一元件都不得獨立產生正式 setup。

---

## 2. 設計原則

### 2.1 Context 先於 Signal

指標必須先建立高週期環境，才解讀低週期事件。

```text
HTF Context = 方向限制與位置資訊
Liquidity Event = 事件起點
Displacement / MSS = 敘事改變確認
FVG Retracement = 執行區域
```

### 2.2 Sweep 不是反轉保證

刺破前高或前低只能證明流動性被觸及，不能單獨推導反轉。

有效 reversal candidate 至少需要：

```text
Liquidity Sweep
AND opposite Displacement
AND opposite MSS
```

### 2.3 FVG 不是天然支撐壓力

FVG 只有在以下條件成立時，才可進入 setup：

```text
由有效 displacement 形成
方向符合 setup
尺寸達最低門檻
尚未完整 mitigation / invalidation
位於允許的 dealing-range 區域
```

### 2.4 所有物件必須有生命週期

Liquidity Pool、Sweep Event、FVG、Setup 都必須具有：

```text
created
active
confirmed
touched
mitigated / swept
invalidated
expired
```

不得無限期保留「曾經有效」的物件。

### 2.5 分數不是勝率

Long Score / Short Score 表示規則完整度與結構品質，不表示歷史勝率、預測機率或保證報酬。

Dashboard 必須使用：

```text
Setup Quality Score
```

不得顯示：

```text
Win Probability
勝率
成功機率
```

### 2.6 Confirmed 與 Developing 必須分離

即時形成中的資訊可以顯示，但必須明確標示為 Developing，不得與 Confirmed 歷史訊號混在一起。

預設模式必須是：

```text
Confirmed
```

---

## 3. v0.1 範圍與非目標

### 3.1 v0.1 必做

```text
1. HTF confirmed context
2. Dealing Range / Equilibrium / Premium / Discount
3. Confirmed internal / external swings
4. Previous Day High / Low
5. Previous Week High / Low
6. Asia / London / New York session high-low
7. Equal High / Equal Low liquidity pools
8. Liquidity sweep / raid classification
9. Breakout acceptance classification
10. Displacement detection
11. Market Structure Shift detection
12. FVG creation and lifecycle
13. Sweep → MSS → FVG Retracement state machine
14. Long / Short independent quality scores
15. Dashboard / Debug / Alerts
16. Four-language UI framework
17. Non-repaint and object-retention controls
```

### 3.2 v0.1 不做

以下概念留待後續版本：

```text
Order Block
Breaker Block
Mitigation Block
Balanced Price Range
OTE
Silver Bullet
Unicorn Model
Judas Swing
Opening Gap / New Week Opening Gap
SMT divergence
Automated strategy order execution
Parameter optimization
Wyckoff integration
```

理由不是否定這些概念，而是避免第一版無法判斷績效究竟來自哪一條規則。

---

## 4. 名詞與本專案操作定義

> 本章定義是本專案的程式化規則，不宣稱是唯一或官方定義。

### 4.1 External Swing

較高敏感度門檻下確認的主要轉折點，用於建立 dealing range 與主要 external liquidity。

預設：

```text
externalPivotLeft  = 5
externalPivotRight = 5
```

以 confirmed pivot 為準：

```pine
externalHigh = ta.pivothigh(high, externalPivotLeft, externalPivotRight)
externalLow  = ta.pivotlow(low, externalPivotLeft, externalPivotRight)
```

Pivot 僅在 `right` 根 K 棒後確認；事件時間應記錄實際 pivot bar，而不是確認 bar。

### 4.2 Internal Swing

較低門檻的短期轉折，用於 MSS 與近端流動性判斷。

預設：

```text
internalPivotLeft  = 2
internalPivotRight = 2
```

### 4.3 Buy-Side Liquidity（BSL）

位於價格上方、可能吸引買停損或突破買盤的價格池。

v0.1 來源：

```text
Confirmed swing high
Equal highs
Previous day high
Previous week high
Session high
```

### 4.4 Sell-Side Liquidity（SSL）

位於價格下方、可能吸引賣停損或突破賣盤的價格池。

v0.1 來源：

```text
Confirmed swing low
Equal lows
Previous day low
Previous week low
Session low
```

### 4.5 Liquidity Sweep / Raid

價格穿越流動性價格後，在同一根或指定確認窗口內重新收回流動性內側。

Buy-side sweep：

```text
high > poolPrice + sweepBuffer
AND close < poolPrice - reclaimBuffer
```

Sell-side sweep：

```text
low < poolPrice - sweepBuffer
AND close > poolPrice + reclaimBuffer
```

若允許多 bar reclaim：

```text
價格先穿越 pool
AND 在 sweepReclaimBars 根內收回
```

預設：

```text
sweepReclaimBars = 1
```

### 4.6 Breakout Acceptance

價格穿越流動性後，沒有收回，反而以收盤接受在流動性外側。

Buy-side breakout acceptance：

```text
close > poolPrice + acceptanceBuffer
AND consecutiveAcceptedCloses >= acceptanceBars
```

Sell-side breakout acceptance：

```text
close < poolPrice - acceptanceBuffer
AND consecutiveAcceptedCloses >= acceptanceBars
```

預設：

```text
acceptanceBars = 1
```

Sweep 與 breakout acceptance 必須互斥；同一事件不能同時標記為兩者。

### 4.7 Displacement

方向明確、實體占比高、相對 ATR 足夠，且最好伴隨結構突破或 FVG 的價格位移。

Bullish displacement candidate：

```text
close > open
AND body >= ATR * displacementAtrMult
AND body / range >= displacementBodyRatio
```

Bearish displacement candidate：

```text
close < open
AND body >= ATR * displacementAtrMult
AND body / range >= displacementBodyRatio
```

預設：

```text
atrLength = 14
displacementAtrMult = 0.80
displacementBodyRatio = 0.60
```

品質加分：

```text
close 接近極值
突破 internal swing
形成同方向 FVG
成交量高於基準（僅作可選 witness，不是必要條件）
```

### 4.8 Market Structure Shift（MSS）

在 sweep 事件後，價格以 opposite displacement 收盤突破最近有效 internal swing。

Bullish MSS：

```text
先發生 sell-side sweep
AND bullish displacement
AND close > lastConfirmedInternalHigh + structureBuffer
```

Bearish MSS：

```text
先發生 buy-side sweep
AND bearish displacement
AND close < lastConfirmedInternalLow - structureBuffer
```

沒有先前 sweep 的結構突破可標記為 BOS / structure break，但不得成為 v0.1 reversal setup 的 MSS。

### 4.9 Fair Value Gap（FVG）

三根 K 棒不平衡區域。

Bullish FVG：

```text
low > high[2]
zoneTop = low
zoneBottom = high[2]
```

Bearish FVG：

```text
high < low[2]
zoneTop = low[2]
zoneBottom = high
```

最低尺寸：

```text
fvgSize >= max(syminfo.mintick * fvgMinTicks, ATR * fvgMinAtrMult)
```

預設：

```text
fvgMinTicks = 2
fvgMinAtrMult = 0.05
```

v0.1 setup FVG 必須與觸發 MSS 的 displacement 相連或位於設定的最大 bar 距離內。

### 4.10 Consequent Encroachment（CE）

FVG 中線：

```text
CE = (zoneTop + zoneBottom) / 2
```

### 4.11 Dealing Range

由最近一對 confirmed external swing high / low 建立。

```text
rangeHigh = activeExternalHigh
rangeLow  = activeExternalLow
rangeMid  = (rangeHigh + rangeLow) / 2
```

若 swing 順序或價格無法形成有效區間，Context 顯示 `Insufficient Range`，不得假裝有 premium / discount。

### 4.12 Premium / Discount

```text
price > rangeMid → Premium
price < rangeMid → Discount
price near rangeMid → Equilibrium
```

Equilibrium buffer：

```text
abs(price - rangeMid) <= rangeWidth * equilibriumPct
```

預設：

```text
equilibriumPct = 0.05
```

---

## 5. 系統架構

v0.1 分為七層：

```text
Layer 1｜Time & Session Engine
Layer 2｜HTF Context Engine
Layer 3｜Swing & Liquidity Map
Layer 4｜Sweep / Acceptance Classifier
Layer 5｜Displacement & MSS Engine
Layer 6｜FVG Lifecycle Engine
Layer 7｜Setup State / Score / UI
```

每一層只可以使用自己之前已完成的資料，不得倒因為果。

例如：

```text
不能因為後來出現 MSS，回頭把原本沒有成立的 sweep 改成成立。
不能因為 FVG 後來反應良好，回頭降低它的最小尺寸門檻。
```

---

## 6. Layer 1｜Time & Session Engine

### 6.1 時區

ICT session 邏輯通常依紐約時間理解，因此 session 預設使用 IANA timezone：

```text
America/New_York
```

不得以固定 UTC offset 取代，以避免夏令時間錯位。

Input：

```pine
sessionTimezone = input.string("America/New_York", "Session Timezone")
```

### 6.2 Session 定義

v0.1 預設只追蹤 session high / low，不直接把 Kill Zone 當進場條件。

建議預設：

```text
Asia      20:00–00:00 New York time
London    02:00–05:00 New York time
New York  07:00–10:00 New York time
```

所有 session 必須允許使用者修改與關閉。

### 6.3 Session Pool 建立

Session 結束後才建立 confirmed session high / low liquidity pool。

Session 尚未結束時可顯示 developing range，但不得加入 confirmed liquidity map。

### 6.4 Previous Day / Week

使用前一個完整日 / 週的 confirmed high-low：

```text
PDH / PDL
PWH / PWL
```

不得使用當前尚未完成的日線或週線高低作為 previous period level。

---

## 7. Layer 2｜HTF Context Engine

### 7.1 Context Timeframe

Input：

```text
Auto
Manual
```

建議 Auto mapping：

```text
Chart <= 5m   → HTF 1h
Chart <= 15m  → HTF 4h
Chart <= 1h   → HTF 1D
Chart <= 4h   → HTF 1W
Chart > 4h    → HTF 1M
```

Manual 可由使用者指定。

### 7.2 Confirmed HTF 原則

預設只使用上一根已確認 HTF bar 的資料。

所有 `request.security()` 必須：

```text
明確控制 lookahead
不使用未確認 HTF close 改變歷史 Context
Dashboard 顯示 Active HTF 與 confirmed / developing 狀態
```

### 7.3 HTF Structure Bias

HTF bias 不做複雜預測，只分類：

```text
Bullish
Bearish
Neutral
Insufficient Data
```

建議規則：

Bullish：

```text
最近 confirmed external high 高於前一個 external high
AND 最近 confirmed external low 不低於前一個 external low
```

Bearish：

```text
最近 confirmed external low 低於前一個 external low
AND 最近 confirmed external high 不高於前一個 external high
```

其餘 Neutral。

### 7.4 HTF Location Bias

```text
Discount → long context 加分
Premium  → short context 加分
Equilibrium → 雙方不加分
```

位置不得單獨決定方向。

### 7.5 Draw on Liquidity

v0.1 以最近仍 active 的 HTF liquidity pool 作為候選 draw：

```text
上方最近 active BSL
下方最近 active SSL
```

若 HTF structure bullish，優先上方 draw；若 bearish，優先下方 draw；若 neutral，僅顯示最近距離，不建立強方向。

Dashboard 必須說明：

```text
HTF Bias
Range Location
Nearest BSL
Nearest SSL
Preferred Draw
```

---

## 8. Layer 3｜Swing & Liquidity Map

### 8.1 Liquidity Pool 類型

v0.1 支援：

```text
EXT_SWING_HIGH
EXT_SWING_LOW
INT_SWING_HIGH
INT_SWING_LOW
EQUAL_HIGH
EQUAL_LOW
PDH
PDL
PWH
PWL
ASIA_HIGH
ASIA_LOW
LONDON_HIGH
LONDON_LOW
NEWYORK_HIGH
NEWYORK_LOW
```

### 8.2 Pool 優先級

預設品質權重：

```text
PWH / PWL                 5
PDH / PDL                 4
External Swing            4
Equal High / Equal Low    3
Session High / Low        2
Internal Swing            1
```

此權重只影響事件品質，不表示價格必然反應。

### 8.3 Equal High / Equal Low

兩個 confirmed pivots 價差在 tolerance 內：

```text
tolerance = max(equalToleranceTicks * syminfo.mintick,
                ATR * equalToleranceAtrMult)
```

預設：

```text
equalToleranceTicks = 4
equalToleranceAtrMult = 0.10
```

Equal High：

```text
abs(highPivotA - highPivotB) <= tolerance
```

Equal Low：

```text
abs(lowPivotA - lowPivotB) <= tolerance
```

同一區域若新增第三個以上 pivot，應更新 pool touch count，而不是建立多個重疊 pool。

### 8.4 Pool 去重

新 pool 若與同 side、同類型或相容類型舊 pool 距離小於 merge tolerance，應合併。

合併後價格可採：

```text
平均值
或最外側價格
```

v0.1 預設採最外側價格，以符合實際 sweep 門檻：

```text
BSL 取最高
SSL 取最低
```

### 8.5 Pool Lifecycle

狀態：

```text
ACTIVE
TOUCHED
SWEPT
BROKEN_ACCEPTED
EXPIRED
```

規則：

- 僅觸及但未穿越：`TOUCHED`，仍可保留。
- 有效 sweep：`SWEPT`，不得再次觸發新 sweep。
- 有效 breakout acceptance：`BROKEN_ACCEPTED`。
- 超過最大保存 bars：`EXPIRED`。

### 8.6 Pool Retention

Input：

```text
maxActivePoolsPerSide = 20
maxHistoricalPools = 60
poolMaxAgeBars = 1500
```

超過上限時優先刪除：

```text
已失效
已過期
低優先級
最舊
```

---

## 9. Layer 4｜Sweep / Acceptance Classifier

### 9.1 Buffer

避免單一 tick 雜訊：

```text
sweepBuffer = max(sweepBufferTicks * syminfo.mintick,
                  ATR * sweepBufferAtrMult)
```

預設：

```text
sweepBufferTicks = 1
sweepBufferAtrMult = 0.00
```

Reclaim buffer 預設為 0，可選擇要求收盤深入 pool 內側。

### 9.2 Same-Bar Sweep

Buy-side sweep：

```text
high > poolPrice + sweepBuffer
AND close < poolPrice - reclaimBuffer
```

Sell-side sweep：

```text
low < poolPrice - sweepBuffer
AND close > poolPrice + reclaimBuffer
```

### 9.3 Multi-Bar Sweep

若 `sweepReclaimBars > 1`：

1. 第一次穿越 pool 時建立 developing sweep event。
2. 在窗口內收回則 confirmed sweep。
3. 窗口內沒有收回，且收盤持續在外側，轉為 breakout acceptance 或 expired penetration。

### 9.4 Sweep Quality

Sweep 品質 0–25：

```text
Pool quality        0–8
Penetration quality 0–5
Reclaim quality     0–6
HTF location match  0–6
```

例：bearish setup 中的 buy-side sweep，若發生在 HTF premium，location 加分。

### 9.5 Breakout Acceptance

Breakout acceptance 後：

- 原 pool 標記 `BROKEN_ACCEPTED`。
- 不建立 opposite reversal setup。
- 可作為 continuation context，但 v0.1 不建立 continuation entry model。

### 9.6 同 bar 衝突

若超大 K 棒同時掃到上下兩側：

```text
標記 Dual-Side Liquidity Event
不立即建立方向 setup
等待後續 displacement + MSS
```

Dashboard 顯示：

```text
Two-sided sweep / indecision
```

---

## 10. Layer 5｜Displacement & MSS Engine

### 10.1 Displacement 基礎分數

每根 candidate bar 計算：

```text
Body ATR score       0–8
Body ratio score     0–5
Close location score 0–4
Structure break      0–5
FVG formation        0–3
Total                0–25
```

最低 confirmed displacement：

```text
displacementScore >= 14
```

Input 可調。

### 10.2 Close Location

Bullish：

```text
(close - low) / range
```

Bearish：

```text
(high - close) / range
```

越接近方向極值，分數越高。

### 10.3 MSS Reference Swing

Sweep 發生時，鎖定最近有效 opposite internal swing 作為 MSS reference。

Bullish setup：

```text
reference = last internal swing high before / at SSL sweep
```

Bearish setup：

```text
reference = last internal swing low before / at BSL sweep
```

之後新形成的 internal swing 不得偷偷替換 reference，使條件變容易。

### 10.4 MSS Window

Sweep 後必須在限定 bars 內出現 MSS：

```text
mssMaxBarsAfterSweep = 12
```

超過窗口：

```text
setup state → EXPIRED_NO_MSS
```

### 10.5 MSS Confirmed

Bullish：

```text
close > lockedInternalHigh + structureBuffer
AND bullish displacement confirmed
```

Bearish：

```text
close < lockedInternalLow - structureBuffer
AND bearish displacement confirmed
```

Wick-only break 不算 confirmed MSS。

### 10.6 Developing MSS

Developing 模式可顯示：

```text
intrabar price crossed reference
```

但 label 必須是：

```text
Developing MSS
```

收盤未成立時不得留在歷史圖上。

---

## 11. Layer 6｜FVG Lifecycle Engine

### 11.1 FVG 建立條件

所有 FVG 都可選擇顯示，但只有符合以下條件者可成為 setup FVG：

```text
方向與 MSS 相同
形成時間距 MSS <= fvgLinkMaxBars
尺寸達門檻
中間 candle 或相鄰 candle 屬 confirmed displacement
尚未被完整填補
```

預設：

```text
fvgLinkMaxBars = 2
```

### 11.2 FVG 狀態

```text
OPEN
TOUCHED
CE_TOUCHED
PARTIALLY_MITIGATED
FULLY_MITIGATED
INVALIDATED
EXPIRED
```

### 11.3 Bullish FVG Lifecycle

Zone：

```text
bottom = high[2]
top    = low
CE     = (top + bottom) / 2
```

狀態：

```text
low <= top             → TOUCHED
low <= CE              → CE_TOUCHED
low < top and low > bottom → PARTIALLY_MITIGATED
low <= bottom          → FULLY_MITIGATED
close < bottom - invalidationBuffer → INVALIDATED
```

### 11.4 Bearish FVG Lifecycle

Zone：

```text
bottom = high
top    = low[2]
CE     = (top + bottom) / 2
```

狀態：

```text
high >= bottom         → TOUCHED
high >= CE             → CE_TOUCHED
high > bottom and high < top → PARTIALLY_MITIGATED
high >= top            → FULLY_MITIGATED
close > top + invalidationBuffer → INVALIDATED
```

### 11.5 Mitigation 模式

Input：

```text
Touch
CE
Full Fill
```

這只影響 setup entry-ready 判斷，不改變 zone 的客觀狀態紀錄。

預設：

```text
CE
```

### 11.6 FVG Expiry

```text
fvgMaxAgeBars = 100
```

Setup FVG 若超過最大年齡仍未回踩：

```text
EXPIRED_NO_RETRACE
```

### 11.7 FVG 去重與物件限制

同方向重疊 zone 若 overlap ratio 超過門檻：

```text
fvgMergeOverlapPct = 0.70
```

v0.1 不強制合併 setup FVG；一般觀察 FVG 可合併或只保留最近高品質 zone。

預設：

```text
maxActiveFvgsPerSide = 12
maxHistoricalFvgs = 40
```

---

## 12. Layer 7｜Setup State Machine

### 12.1 Setup Model

v0.1 只實作：

```text
Liquidity Sweep → Opposite MSS → Same-direction FVG Retracement
```

Long setup：

```text
HTF 不強烈 bearish
價格位於 discount 或 neutral
SSL 被 sweep
Bullish displacement
Bullish MSS
有效 bullish FVG
價格回踩設定 mitigation level
```

Short setup：

```text
HTF 不強烈 bullish
價格位於 premium 或 neutral
BSL 被 sweep
Bearish displacement
Bearish MSS
有效 bearish FVG
價格回踩設定 mitigation level
```

### 12.2 狀態枚舉

```text
IDLE
CONTEXT_READY
LIQUIDITY_TARGETED
SWEEP_DEVELOPING
SWEEP_CONFIRMED
WAITING_MSS
MSS_CONFIRMED
FVG_ARMED
RETRACE_DEVELOPING
SETUP_QUALIFIED
SETUP_TRIGGERED
INVALIDATED
EXPIRED
```

### 12.3 狀態轉移

Long：

```text
IDLE
→ CONTEXT_READY
→ SSL pool selected
→ SSL sweep confirmed
→ WAITING_MSS
→ bullish MSS confirmed
→ bullish FVG selected
→ FVG_ARMED
→ retracement reaches selected mitigation level
→ SETUP_QUALIFIED / SETUP_TRIGGERED
```

Short 對稱。

### 12.4 一次只保留有限 active setup

預設：

```text
maxActiveSetupsPerSide = 1
```

若同方向新 sweep 出現：

- 舊 setup 尚未 MSS：新事件可取代舊事件，但需記錄 `REPLACED_BY_NEW_SWEEP`。
- 舊 setup 已 FVG_ARMED：預設不取代，除非舊 setup invalidated。

### 12.5 Setup Invalidation

Long invalidation：

```text
價格收盤跌破 swept liquidity extreme - invalidationBuffer
OR selected bullish FVG invalidated
OR opposite BSL sweep + bearish MSS confirmed
OR setupMaxAgeBars exceeded
```

Short 對稱。

預設：

```text
setupMaxAgeBars = 60
```

### 12.6 Trigger 定義

v0.1 指標不送出策略訂單，只標記 setup trigger。

Trigger input：

```text
FVG Touch
FVG CE
FVG Full Fill
```

Trigger 是研究事件，不是買賣建議。

---

## 13. Setup Quality Score

### 13.1 Long / Short 分開計算

```text
longQualityScore  0–100
shortQualityScore 0–100
```

不得先合併後只顯示單一方向，避免雙方資訊被遮蔽。

### 13.2 分數構成

```text
HTF Context & Location  0–25
Liquidity Event Quality 0–25
Displacement & MSS      0–30
FVG Quality & Retrace   0–20
Total                   0–100
```

### 13.3 Context 分數

Long 例：

```text
HTF bullish structure +10
HTF neutral             +4
Discount                +8
Equilibrium             +3
Preferred draw upward   +7
HTF bearish             +0 and context conflict flag
```

Short 對稱。

### 13.4 Liquidity 分數

```text
Pool priority           0–8
Clean penetration       0–5
Strong reclaim          0–6
Location alignment      0–6
```

### 13.5 Displacement / MSS 分數

```text
Displacement body/ATR   0–8
Body ratio              0–5
Close location          0–4
Locked swing close break 0–8
FVG formed              0–5
```

### 13.6 FVG 分數

```text
Size quality            0–5
Linked to displacement  0–5
Correct range location  0–5
Retrace quality         0–5
```

### 13.7 Grade

```text
0–39   Observe
40–59  Candidate
60–74  Qualified B
75–89  Qualified A
90–100 Exceptional / Research Only
```

`Exceptional` 不得使用誇張語言如「必勝」或「強烈買進」。

### 13.8 Formal Setup Gate

即使分數高，Formal Qualified 仍需硬條件：

```text
sweepConfirmed
AND mssConfirmed
AND setupFvgActive
AND retracementReached
AND notInvalidated
```

分數不能取代硬條件。

---

## 14. Conflict Governance

### 14.1 HTF Conflict

Long setup 遇到 confirmed bearish HTF：

```text
預設降級為 Countertrend Candidate
不得顯示 Qualified A
```

Short 對稱。

Input：

```text
allowCountertrendSetups = true
```

若關閉，直接阻止 formal setup。

### 14.2 Dual-Side Setup

若 long / short 都在 active 狀態：

```text
顯示 Two-Sided / Range Conflict
不使用單一強方向底色
```

### 14.3 Context Insufficient

HTF range 不足或 request 資料不足：

```text
contextScore 降低
但 liquidity / structure 仍可顯示
formal setup 最高 Grade 限制為 Qualified B
```

### 14.4 Developing Data

Developing 事件只能：

```text
畫淡色
顯示 D 標記
提供 observation alert
```

不得進 confirmed score。

---

## 15. Pine Script 資料結構建議

### 15.1 LiquidityPool UDT

```pine
type LiquidityPool
    int id
    string kind
    int side
    float price
    int formedBar
    int confirmedBar
    int priority
    int touchCount
    string status
    line levelLine
    label levelLabel
```

Side 建議：

```text
+1 = BSL
-1 = SSL
```

### 15.2 FvgZone UDT

```pine
type FvgZone
    int id
    int side
    float top
    float bottom
    float ce
    int formedBar
    int linkedMssId
    string status
    box zoneBox
    line ceLine
```

### 15.3 SetupState UDT

```pine
type SetupState
    int id
    int side
    string state
    int sweepPoolId
    int sweepBar
    float sweepExtreme
    float lockedMssLevel
    int mssBar
    int fvgId
    float score
    string grade
    string invalidReason
```

### 15.4 Pine 限制

實作必須控制：

```text
max_lines_count
max_labels_count
max_boxes_count
array size
historical loop length
```

不得每根 K 棒對完整歷史陣列做無界迴圈。

---

## 16. Inputs 規格

### 16.1 General

```text
Language
Engine Mode: Confirmed / Developing
Show Dashboard
Dashboard Size
Object Retention Mode: Compact / Standard / Extended
```

### 16.2 HTF Context

```text
Context TF Mode: Auto / Manual
Manual Context TF
External Pivot Left / Right
Equilibrium Percent
Allow Countertrend Setups
```

### 16.3 Internal Structure

```text
Internal Pivot Left / Right
Structure Buffer Ticks
MSS Max Bars After Sweep
```

### 16.4 Liquidity

```text
Show External Swings
Show Internal Swings
Show Equal High / Low
Show PDH / PDL
Show PWH / PWL
Show Session High / Low
Equal Tolerance Ticks
Equal Tolerance ATR Mult
Pool Max Age Bars
```

### 16.5 Sessions

```text
Session Timezone
Asia Session
London Session
New York Session
Show Developing Session Range
```

### 16.6 Sweep

```text
Sweep Buffer Ticks
Reclaim Buffer Ticks
Sweep Reclaim Bars
Acceptance Bars
```

### 16.7 Displacement

```text
ATR Length
Displacement ATR Mult
Minimum Body Ratio
Minimum Displacement Score
```

### 16.8 FVG

```text
Show All FVG / Setup FVG Only
FVG Minimum Ticks
FVG Minimum ATR Mult
FVG Link Max Bars
Mitigation Mode
FVG Max Age Bars
Show CE
```

### 16.9 Setup

```text
Setup Trigger Mode
Setup Max Age Bars
Minimum Qualified Score
Show Setup Labels
Show Background State
```

### 16.10 Debug

```text
Show Repaint Diagnostics
Show Active Pool Count
Show Locked MSS Level
Show State Code
Show Long / Short Raw Score
Show Active FVG ID
```

---

## 17. UI 與視覺規格

### 17.1 視覺優先級

```text
1. Active setup FVG
2. Swept liquidity source
3. Locked MSS level
4. Preferred draw on liquidity
5. Other active liquidity pools
6. Historical inactive objects
```

### 17.2 顏色語意

不得讓一般 active pool 與 qualified setup 使用相同強度。

建議：

```text
Developing 低透明度
Confirmed 中透明度
Qualified 高辨識度
Invalidated 灰色或刪除
Historical muted
```

使用者可自訂顏色；預設需兼容深色與淺色圖表。

### 17.3 背景

背景只反映 setup state，不反映每一個微小事件。

```text
No setup       無背景
Long candidate 淡多方背景
Short candidate 淡空方背景
Long qualified 較清楚多方背景
Short qualified 較清楚空方背景
Conflict       中性背景
```

### 17.4 Dashboard

Compact Dashboard：

```text
HTF Bias
Range Location
Preferred Draw
Last Liquidity Event
MSS State
FVG State
Long Score / Grade
Short Score / Grade
Engine Mode
```

Full Dashboard 增加：

```text
Active HTF
Nearest BSL / SSL distance
Sweep source & quality
Locked MSS level
Displacement score
Selected FVG / CE
State age
Invalidation level / reason
Data diagnostics
```

### 17.5 說人話

Dashboard 不得只顯示代碼。

可接受：

```text
等待掃蕩
已掃前日低，等待多方 MSS
多方 MSS 成立，等待回踩 FVG 中線
回踩完成，Long Qualified B
FVG 已失效
超過 12 根未出現 MSS，事件過期
```

不可接受：

```text
S3
FLAG 7
ERR_CTX
```

Debug 模式可顯示代碼，但主 Dashboard 必須是自然語言。

---

## 18. 四語架構

Language options：

```text
繁體中文
English
日本語
한국어
```

核心術語保留英文縮寫並翻譯語意，例如：

```text
流動性掃蕩 Liquidity Sweep
市場結構轉移 MSS
公允價值缺口 FVG
溢價區 Premium
折價區 Discount
```

避免把 ICT 專有術語翻譯得無法辨識。

所有 Dashboard、label、alert message 應通過集中式文字函數，不得散落硬編碼。

建議：

```pine
f_text(key) =>
    // return localized string
```

---

## 19. Alerts

### 19.1 Observation Alerts

```text
BSL swept
SSL swept
Dual-side liquidity event
Developing MSS
FVG touched
```

### 19.2 Confirmed Alerts

```text
Bullish MSS confirmed
Bearish MSS confirmed
Long FVG armed
Short FVG armed
Long setup qualified
Short setup qualified
Setup invalidated
Setup expired
```

### 19.3 Alert Payload

至少包含：

```text
Symbol
Chart timeframe
Context timeframe
Direction
State
Liquidity source
Sweep price
MSS level
FVG top / bottom / CE
Score / Grade
Engine mode
Bar close confirmation
```

Confirmed alert 預設 `Once Per Bar Close`。

---

## 20. Non-Repaint Contract

### 20.1 Confirmed Mode

Confirmed Mode 必須遵守：

```text
confirmed pivots only
confirmed HTF data only
bar-close sweep confirmation
bar-close MSS confirmation
historical events reload-stable
```

### 20.2 允許的延遲

Pivot 需要 right bars 才確認，因此標記具有結構性延遲。這是可信度成本，不得為了讓歷史圖更漂亮而提前繪製。

### 20.3 Developing Mode

Developing Mode 可使用當前 bar 高低與未收盤狀態，但：

```text
不得寫入 confirmed history
不得觸發 confirmed setup alert
必須使用不同樣式
Dashboard 必須標記 Developing
```

### 20.4 Repaint Diagnostics

Debug 至少顯示：

```text
Context confirmed?
Current HTF bar developing?
Pivot confirmation delay
Sweep confirmed / developing
MSS confirmed / developing
Selected FVG confirmed?
```

---

## 21. Manual Test Matrix

### 21.1 商品

```text
ES / MES
NQ / MNQ
TY / ZN
CL
EURUSD
USDJPY
BTCUSD（補充壓力測試）
```

### 21.2 時間框架

```text
5m
15m
1h
4h
```

### 21.3 必測情境

```text
1. 前日高被影線掃過後收回，之後 bearish MSS。
2. 前日高被收盤突破並延續，不得誤判 sweep reversal。
3. Equal lows 多次聚集後被 sweep。
4. Sweep 後無 displacement，setup 應過期。
5. Sweep 後有 displacement 但未突破 locked swing，不得標 MSS。
6. MSS 後 FVG 未回踩並過期。
7. FVG 先被完整填補再回到區域，不得重複觸發。
8. 同一根 K 棒掃上下兩側，應顯示 conflict。
9. HTF bullish，但低週期出現 bearish countertrend setup。
10. 圖表 reload 後 confirmed event 不位移。
11. Session 跨夏令時間仍正確。
12. 長歷史資料下物件數不爆炸。
```

### 21.4 視覺驗收

```text
不縮放時仍可辨識主要事件
縮到長歷史時不形成方塊牆
已失效物件會淡化或刪除
Dashboard 可說明狀態與失效原因
```

---

## 22. v0.1 驗收標準

### 22.1 功能

- [ ] 能建立 confirmed dealing range 與 premium / discount。
- [ ] 能建立並去重主要 liquidity pools。
- [ ] 能區分 sweep 與 breakout acceptance。
- [ ] 能鎖定 sweep 當下的 MSS reference swing。
- [ ] 能以 bar close + displacement 確認 MSS。
- [ ] 能建立與管理 FVG lifecycle。
- [ ] 能完整運行 Sweep → MSS → FVG Retracement state machine。
- [ ] Long / Short 分數可被逐項解釋。
- [ ] Dashboard 可顯示缺少條件與失效原因。

### 22.2 穩定性

- [ ] Confirmed 模式重載後主要歷史事件穩定。
- [ ] 不使用 future leak。
- [ ] 不依賴 `calc_on_every_tick` 才能成立。
- [ ] 陣列與繪圖物件有硬上限。
- [ ] 無資料或週期不適用時不產生假訊號。

### 22.3 可維護性

- [ ] 核心偵測、狀態、繪圖、翻譯分區清楚。
- [ ] 重要門檻集中於 inputs / constants。
- [ ] 每個 setup 可追溯 pool id、sweep bar、MSS level、FVG id。
- [ ] 後續 Strategy 腳本可重用相同事件定義。

---

## 23. 建議檔案結構

```text
indicators/ict-liquidity-structure-engine/
├── README.md
├── specs/
│   └── shiori-liquidity-structure-engine-v0.1-spec.md
└── src/
    └── shiori-liquidity-structure-engine-v0.1.pine
```

後續：

```text
strategy/
└── shiori-liquidity-structure-strategy-v0.1.pine
```

Indicator 與 Strategy 必須分檔，避免觀察工具和成交假設互相污染。

---

## 24. 開發順序

### Phase A｜Skeleton

```text
Inputs
Language framework
Session engine
Dashboard skeleton
Debug framework
```

### Phase B｜Context & Liquidity

```text
Confirmed pivots
Dealing range
Premium / discount
PDH / PDL / PWH / PWL
Session pools
Equal highs / lows
Pool lifecycle
```

### Phase C｜Event Logic

```text
Sweep classifier
Breakout acceptance
Displacement
Locked MSS reference
MSS confirmation
```

### Phase D｜FVG & State Machine

```text
FVG creation
FVG lifecycle
Setup state machine
Invalidation / expiry
Scores / grades
```

### Phase E｜UI & Validation

```text
Object cleanup
Alerts
Four-language text
Manual test matrix
Reload stability test
```

---

## 25. 後續 Roadmap

### v0.2｜PD Array Expansion

```text
Order Block
Breaker Block
Mitigation Block
Balanced Price Range
Opening Gaps
Kill Zone filters
```

### v0.3｜Strategy Validation

```text
獨立 strategy() 腳本
只測 Sweep → MSS → FVG Retracement
明確 next-bar / limit-fill 假設
手續費、滑價、session filter
R-based stop / target
MAE / MFE 與 setup grade 分層
```

### v0.4｜Regime Integration

```text
Wyckoff Regime Radar = market phase / background
Liquidity Structure Engine = execution path / setup state
```

整合原則：

```text
Wyckoff 可以限制或調整 ICT setup grade，
但不得回頭改寫 sweep、MSS、FVG 的客觀事件定義。
```

---

## 26. 最終產品語意

本指標不應對使用者說：

```text
現在一定會漲。
這裡是機構訂單。
Smart Money 正在買進。
這是高勝率反轉。
```

它應該說：

```text
前日低已被掃蕩。
掃蕩後出現多方位移並收盤突破鎖定的 internal high。
目前存在一個仍有效的 bullish FVG，價格尚未回踩中線。
Long setup 狀態：FVG Armed；品質 68，Qualified B 尚未觸發。
若收盤跌破 sweep extreme，setup 失效。
```

這就是 v0.1 的核心：

> 不賣神話，只把市場事件、順序、條件與失效點說清楚。
