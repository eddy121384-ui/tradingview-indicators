# Chase Risk Market Regime Radar v0.5｜MTF Effort / Result Layer 規格書

> 文件目的：這份 spec 不是發佈文案，而是給人類與 AI 協作者共同使用的「設計契約」。  
> 任何後續修改 Pine Script 前，應先讀本文件，確認是否符合本指標定位、資料流與語意邊界。

---

## 0. 一句話定位

**Chase Risk Market Regime Radar** 是一個用於 TradingView 的市場結構 / regime 雷達。它用價格行為、趨勢成熟度、區間結構、吸收 / 派發線索、成交量品質與 MTF effort/result 來判斷市場較可能處於哪一種威科夫式階段。

它的目的不是產生進出場訊號，而是協助使用者避免站錯邊、避免在趨勢末端追價、避免把高位鈍化誤認成安全多頭、也避免把低位承接誤認成可以無腦抄底。

---

## 1. 核心使用哲學

### 1.1 本指標是什麼

本指標是：

- 市場階段判讀工具。
- 風險語氣翻譯器。
- 趨勢 / 橫盤 / 末段風險 / 吸收 / 派發線索整合器。
- 空手者、持有多單者、持有空單者的節奏提醒工具。
- 用於觀察「現在是否適合追價、等待、續抱、減碼、提高停利」的輔助雷達。

### 1.2 本指標不是什麼

本指標不是：

- 買賣訊號產生器。
- 高低點預測器。
- 自動交易策略。
- 期望每次標示都事後完美的分類器。
- 用來單獨決定下單、加碼或反手的工具。

### 1.3 修改守則

後續 AI 或人類修改程式時，必須遵守以下守則：

1. **價格行為是主引擎。** 成交量與 MTF 都只能作為 witness layer，不可接管主模型。
2. **狀態不是指令。** `formalId`、`candidateDisplayId`、`flatActionLevel` 都不是直接下單命令。
3. **紅燈不是反向訊號。** 上漲紅燈不是做空訊號；恐慌紅燈不是抄底訊號。
4. **線索不是定罪。** 高位鈍化、低位承接、MTF 反駁，只能提升警覺，不可直接命名為正式反轉。
5. **Observe Only 要保持不改主行為。** v0.5 的 MTF 預設是觀察，不應改寫主導狀態、候選、Evidence、Flat Action 或背景。
6. **修改前先定位：是核心模型、輔助證人、顯示層、還是 alert 層。** 不同層不可混在一起改。

---

## 2. 版本脈絡

### 2.1 v0.3.8 系列

v0.3.8 系列建立了本指標的主要語意框架：

- 六階段威科夫 regime：吸籌、拉升、再吸籌、派發、崩跌、再出貨。
- Flat Action Level：空手者不再只有等待，而是有行動分級。
- Pace Guide：把複雜 Dashboard 翻譯成三種持倉視角。
- Pace Context Downgrade：當主節奏與鈍化 / 分歧線索互相衝突時，將行動降級。
- Dual Layer Background：背景可同時顯示正式主導與候選狀態。

### 2.2 v0.4

v0.4 新增 Volume Quality Layer。

核心思想：成交量不是必要條件，也不是無條件可信。它必須先通過品質檢查，才能成為輔助證據。

成交量層提供：

- Volume Mode。
- Volume Quality。
- Effort vs Result。
- Volume Absorption / Distribution。
- Volume Breakout / Breakdown Confirmation。
- Volume clues for demand / supply / breakout / breakdown。

當 Volume Mode = Off，或成交量品質不足時，模型應回到 price-only 架構，不應懲罰價格主模型。

### 2.3 v0.5

v0.5 新增 MTF Effort / Result Layer。

核心思想：次一級 time frame 不是投票器，而是 effort 證人。它回答的不是「4H 是多還是空」，而是：「4H 已經用了多少力？主週期有沒有產生對應結果？」

這一版的新增功能包括：

- `MTF Mode`。
- lower timeframe effort array。
- 主週期 result 評分。
- 四種 MTF 語意分數。
- MTF witness support。
- Dashboard / Debug / Alerts 的 MTF 顯示。
- MTF 對 Pace / Flat Action / clue observation 的低權重輔助。

---

## 3. 檔案與版本資訊

### 3.1 Pine Script 來源檔

```text
indicators/wyckoff-regime-radar/src/chase-risk-market-regime-radar-v0.5.pine
```

### 3.2 Spec 文件

```text
indicators/wyckoff-regime-radar/specs/chase-risk-market-regime-radar-v0.5-mtf-effort-result-spec.md
```

### 3.3 TradingView 指標名稱

```pine
indicator("Chase Risk Market Regime Radar v0.5｜MTF Effort Result Layer", shorttitle="ChaseRisk Radar v0.5", overlay=false, precision=1, max_labels_count=50)
```

### 3.4 Pine Script 版本

```pine
//@version=6
```

---

## 4. 系統總架構

本指標可以理解為七層資料流：

```text
價格資料
  ↓
基礎特徵層：heat / maturity / range / support / resistance / extension
  ↓
六階段原始分數：acc / markup / reacc / dist / markdown / redist
  ↓
Gate 與 Effective Score：以背景、區間、突破、延伸、鈍化條件過濾原始分數
  ↓
Witness Layer：Volume + MTF 低權重加強，不接管主模型
  ↓
Regime Decision：正式主導、候選、分歧、線索觀察、證據強度
  ↓
User Translation：Pace Guide、Flat Action、Dashboard、Background、Alerts
```

設計重點是「每一層只做自己的事情」。

- 基礎特徵層負責量測市場狀態。
- 六階段層負責形成威科夫劇本候選。
- Gate 層負責避免不合背景的劇本亂亮。
- Witness 層負責補充證據，不負責主導方向。
- Decision 層負責分類與確認。
- Translation 層負責把結果翻成人看得懂的節奏語言。

---

## 5. 主要輸入參數群組

程式使用以下 input groups：

```text
groupHeat      = 參數｜即時熱度
groupMaturity  = 參數｜趨勢成熟度
groupRange     = 參數｜突破與區間
groupAbsorb    = 參數｜吸收 / 出貨辨識
groupTrendExt  = 參數｜趨勢延續 / 快速切換
groupVolume    = 參數｜Volume Quality Layer v0.4
groupMTF       = 參數｜MTF Effort / Result Layer v0.5
groupRegime    = 參數｜威科夫權重表 v0.5
groupWeights   = 參數｜權重
groupDisplay   = 顯示｜視覺設定
groupPace      = 顯示｜Pace Guide / Flat Action v0.5
groupColors    = 顯示｜Dashboard 顏色自訂
groupAlert     = 警示｜門檻設定
```

### 5.1 Heat inputs

此組控制短中期價格動能與熱度：

- `speedLen`：速度斜率天期。
- `shortLen`：短斜率天期。
- `longLen`：長斜率天期。
- `volLen`：波動率天期。
- `maLen`：短中期均線。
- `atrLen`：短中期 ATR。
- `rankLen`：歷史百分位回看天期。

### 5.2 Maturity inputs

此組控制趨勢成熟度：

- `maturitySlopeLen`：成熟度長斜率。
- `maturityMaLen`：成熟度長均線。
- `maturityAtrLen`：成熟度 ATR。

### 5.3 Range / Breakout inputs

此組控制區間、突破與下破：

- `rangeLen`：區間偵測天期。
- `breakoutBars`：突破 / 下破觀察期。
- `lowVolLevel`：低波動門檻。
- `useBreakoutExemption`：低波動突破 / 下破豁免。

### 5.4 Absorption / Distribution inputs

此組控制吸收 / 出貨辨識：

- `absorbLen`：吸收 / 出貨觀察天期。
- `absorbThreshold`：吸收 / 出貨有效門檻。

### 5.5 Trend Extension inputs

此組控制趨勢延伸、整理後延續與快速轉正：

- `trendExtThreshold`：趨勢延伸有效門檻。
- `nonRangeGateStart` / `nonRangeGateFull`：非橫盤 gate 的啟動與滿分。
- `continuationHoldBars`：整理後延續確認根數。
- `fastSwitchWeight`：快速轉正候選權重門檻。
- `fastSwitchGap`：快速轉正 Top Gap 門檻。
- `fastSwitchEvidence`：快速轉正證據強度門檻。
- `fastSwitchExt`：快速轉正趨勢延伸門檻。
- `fastSwitchConfirmBars`：快速轉正確認根數。

### 5.6 Volume inputs

Volume layer 的主要設定：

- `volumeMode`：Off / Auto / Force On / Tick Volume Proxy。
- `volumeRankLen`：成交量百分位回看天期。
- `volumeQualityLen`：成交量品質檢查天期。
- `volumeMaxWeight`：正式成交量最大參與權重。
- `tickVolumeMaxWeight`：tick volume proxy 最大參與權重。
- `volumeParticipationThreshold`：成交量參與度門檻。
- `volumeSpikeThreshold`：成交量尖峰污染門檻。
- `volumeQualityMin`：Auto 啟用最低品質。
- `volumeQualityFull`：Auto 滿權重品質。
- `effortResultThreshold`：Volume effort/result 有效門檻。
- `showVolumeInCompact`：Dashboard 精簡模式是否顯示量能層。

### 5.7 MTF inputs

v0.5 新增：

```pine
mtfMode = input.string("Observe Only", "MTF Mode", options=["Off", "Observe Only", "Auto", "Force On"], group=groupMTF)
mtfLowerTf = input.timeframe("240", "次一級 Time Frame", group=groupMTF)
mtfMinIntrabars = input.int(3, "最低有效次級 K 根數", minval=1, maxval=50, group=groupMTF)
mtfEffortThreshold = input.float(60.0, "MTF Effort / Result 有效門檻", minval=0.0, maxval=100.0, step=0.5, group=groupMTF)
mtfMaxWeight = input.float(15.0, "MTF 最大參與權重 %", minval=0.0, maxval=30.0, step=0.5, group=groupMTF)
mtfResultAtrFull = input.float(1.5, "主週期 Result 滿分 ATR 倍數", minval=0.25, maxval=5.0, step=0.25, group=groupMTF)
showMTFInCompact = input.bool(true, "Dashboard 精簡模式顯示 MTF 層", group=groupMTF)
```

#### 5.7.1 MTF Mode 語意

- `Off`：完全關閉 MTF layer。
- `Observe Only`：預設，只顯示 / 警示，不參與主模型。
- `Auto`：MTF 分數足夠明確才依分數漸進參與。
- `Force On`：只要資料可用，就以最大 MTF 權重參與。

#### 5.7.2 重要約束

`Observe Only` 必須滿足：

```text
mtfWeightApplied = 0
mtfActive = false
```

因此在 Observe Only 下，不應改變：

- `accEff`
- `markupEff`
- `reaccEff`
- `distEff`
- `markdownEff`
- `redistEff`
- `formalId`
- `candidateDisplayId`
- `evidenceStrength`
- `flatActionLevel`
- 背景色

但它仍可顯示 Dashboard、Debug 與 alert。

---

## 6. 基礎特徵層

### 6.1 即時熱度

程式先使用 log price 與 log return 計算：

- `speedZ`
- `shortZ`
- `longZ`
- `accelZ`
- `distATR`

再轉成歷史百分位：

- `speedRank`
- `accelRank`
- `distRank`

最後產生：

```text
heatUp      = 上漲即時熱度
panicHeatDn = 下跌即時恐慌熱度
```

語意：

- `heatUp` 高，不代表一定要做多；它可能是健康動能，也可能是末端過熱。
- `panicHeatDn` 高，不代表一定要做空；它可能是健康下跌，也可能是末端恐慌。

### 6.2 趨勢成熟度

趨勢成熟度由長斜率與長均線乖離組成：

- `maturitySlopeZ`
- `longSlopeRank`
- `maturityDistATR`
- `maturityDistRank`
- `maturityUp`
- `maturityDn`

### 6.3 末段風險

上漲末段風險：

```text
endRiskUpRaw = heatUp × maturityUp / 100
```

下跌末段恐慌風險：

```text
endRiskDnRaw = panicHeatDn × maturityDn / 100
```

解釋：

- 熱度高但趨勢不成熟，未必是末段。
- 趨勢成熟但熱度不高，也未必是末段。
- 熱度與成熟度同時高，末段風險才升高。

### 6.4 突破 / 下破與低波動豁免

突破啟動與下破啟動使用：

- `rangeBreakUp`
- `rangeBreakDn`
- `maCrossUp`
- `maCrossDn`
- `recentBreakUp`
- `recentBreakDn`
- `lowVolRecently`

低波動突破豁免的目的：避免把低波動後的有效啟動誤判成末段紅燈。

### 6.5 Range Score

`rangeScore` 用三個因素衡量橫盤 / 收斂：

- 低斜率。
- 低波動。
- 區間寬度窄。

高 `rangeScore` 表示市場更像橫盤、壓縮、吸收 / 派發環境；低 `rangeScore` 表示更像趨勢延伸。

### 6.6 Bull / Bear background

結構背景使用：

- 價格是否在 `ma` 上方。
- 價格是否在 `maturityMa` 上方。
- 上漲 / 下跌成熟度。

產生：

```text
bullStructure
bearStructure
bullBg
bearBg
```

---

## 7. 吸收 / 出貨辨識層

### 7.1 Range position

吸收 / 出貨層使用 `absorbLen` 定義觀察區間：

- `absRangeHigh`
- `absRangeLow`
- `absRangeMid`
- `absRangePos`

`absRangePos` 越高，價格越接近觀察區間上緣；越低，越接近下緣。

### 7.2 Downside exhaustion

`downsideExhaustion` 衡量「賣壓是否逐漸打不下去」。

主要成分：

- `noBreakLowScore`：沒有跌破前低。
- `negSlopeDullScore`：下跌斜率鈍化。
- `panicDullScore`：恐慌熱度降溫。
- `lowVolScore`：低波動。
- `lowZoneStableScore`：低位穩定。

### 7.3 Upside exhaustion

`upsideExhaustion` 衡量「買盤是否逐漸推不上去」。

主要成分：

- `noBreakHighScore`：沒有突破前高。
- `posSlopeDullScore`：上漲斜率鈍化。
- `heatDullScore`：上漲熱度降溫。
- `lowVolScore`：低波動。
- `highZoneStableScore`：高位穩定。

### 7.4 Support holding

`supportHolding` 衡量低位承接是否存在。

重要概念：

- 有 probe 到支撐區時，重視是否 reclaim。
- 未明顯 probe 時，也可透過不破低、恐慌不延續、低位穩定判斷。

### 7.5 Resistance holding

`resistanceHolding` 衡量高位壓力是否存在。

重要概念：

- 有 probe 到壓力區時，重視是否 reject。
- 未明顯 probe 時，也可透過不破高、熱度不延續、高位穩定判斷。

### 7.6 Gate 化

吸收 / 出貨層不是直接決定階段，而是轉成 gates：

```text
downsideExhaustionGate
upsideExhaustionGate
supportHoldingGate
resistanceHoldingGate
nonAbsorptionGate
nonDistributionGate
```

---

## 8. Volume Quality Layer

### 8.1 設計原則

成交量層是 witness，不是主引擎。

成交量資料在不同市場品質差異很大。股票、期貨、ETF、crypto、FX CFD 的 volume 意義不同，因此 v0.4 設計中先評估品質，再決定是否採用。

### 8.2 Volume quality

Volume quality 使用以下因素：

- `volPresenceScore`：是否有成交量。
- `volContinuityScore`：成交量資料是否連續。
- `volumeStabilityScore`：成交量分布是否穩定。
- `volumeDistributionReasonableScore`：成交量 CV 是否合理。
- `nonSpikePollutionScore`：是否避免尖峰污染。

產生：

```text
volumeQualityScore
volumeWeightApplied
volumeActive
```

### 8.3 Volume effort/result

量價 effort/result 觀念：

- 成交量參與高，但價格上漲結果弱，可能是上攻無效 / 供給。
- 成交量參與高，但價格下跌結果弱，可能是下跌無效 / 承接。

產生：

```text
effortResultUp
effortResultDown
volumeAbsorptionScore
volumeDistributionScore
volumeBreakoutConfirmation
volumeBreakdownConfirmation
```

### 8.4 Volume clues

```text
volumeDemandClue
volumeSupplyClue
volumeBreakoutClue
volumeBreakdownClue
volumeSpikePolluted
volumeForceLowQuality
```

語意：

- `volumeDemandClue`：量能承接線索。
- `volumeSupplyClue`：量能供給線索。
- `volumeBreakoutClue`：量能支持突破。
- `volumeBreakdownClue`：量能支持下破。
- `volumeSpikePolluted`：尖峰污染，需降低可信度。
- `volumeForceLowQuality`：Force On 使用低品質量能，需警示。

---

## 9. MTF Effort / Result Layer

### 9.1 設計原則

MTF Layer 是 v0.5 的核心新增功能。

它不做：

```text
次級週期 bullish → 主週期看多
次級週期 bearish → 主週期看空
```

它做的是：

```text
次級週期 effort 強 + 主週期 result 弱 → 反向吸收 / 派發線索
次級週期 effort 強 + 主週期 result 強 → 同向趨勢確認
```

### 9.2 LTF effort helper

#### 9.2.1 空方努力

`f_ltfBearEffortBar()` 衡量單根 lower timeframe K 棒的空方努力。

成分：

- 紅 K 實體占 range 比例，權重 0.50。
- 收盤位置靠近低點，權重 0.30。
- 收盤低於前一根，權重 0.20。

語意：空方是否在該根 lower timeframe bar 內真的有推動。

#### 9.2.2 多方努力

`f_ltfBullEffortBar()` 衡量單根 lower timeframe K 棒的多方努力。

成分：

- 綠 K 實體占 range 比例，權重 0.50。
- 收盤位置靠近高點，權重 0.30。
- 收盤高於前一根，權重 0.20。

語意：多方是否在該根 lower timeframe bar 內真的有推動。

### 9.3 Lower timeframe array

使用：

```pine
request.security_lower_tf(syminfo.tickerid, mtfLowerTf, f_ltfBearEffortBar(), ignore_invalid_timeframe=true)
request.security_lower_tf(syminfo.tickerid, mtfLowerTf, f_ltfBullEffortBar(), ignore_invalid_timeframe=true)
```

產生：

```text
ltfBearEffortArr
ltfBullEffortArr
ltfCount
```

當 `ltfCount >= mtfMinIntrabars` 時，才視為 MTF 資料足夠。

### 9.4 MTF data availability

```text
mtfDataOk = mtfEnabled
         AND ltfCount >= mtfMinIntrabars
         AND ltfBearEffortRaw is not na
         AND ltfBullEffortRaw is not na
```

若 `mtfDataOk = false`，所有 MTF 分數應歸零或顯示資料不足，不應參與主模型。

### 9.5 主週期 result

主週期 result 不來自 lower timeframe，而是來自主圖 bar：

```text
htfCloseLoc
htfUpMoveATR
htfDnMoveATR
htfUpResult
htfDownResult
```

上漲 result：

- close-to-close 上漲幅度 / ATR。
- 收盤位置靠近高點。

下跌 result：

- close-to-close 下跌幅度 / ATR。
- 收盤位置靠近低點。

### 9.6 四個 MTF 分數

#### 9.6.1 MTF Absorption

```text
mtfAbsorptionScore =
    lower timeframe bear effort 高
    + 主週期 down result 弱
    + 主週期收盤位置偏高
```

交易語意：

次級空方努力很強，但主週期沒有跌出結果，甚至收得不差。這代表賣壓可能被吸收。

常見情境：

- 下跌末段承接。
- 假跌破。
- 空方努力後價格不再有效下跌。
- 低位買盤開始吸收賣壓。

#### 9.6.2 MTF Distribution

```text
mtfDistributionScore =
    lower timeframe bull effort 高
    + 主週期 up result 弱
    + 主週期收盤位置偏低
```

交易語意：

次級多方努力很強，但主週期沒有漲出結果，甚至收得不好。這代表買盤可能被供給吸收。

常見情境：

- 高位上攻無效。
- 假突破。
- 多方努力後價格不再有效上漲。
- 派發或高位供給開始出現。

#### 9.6.3 MTF Markup Confirm

```text
mtfMarkupConfirmScore =
    lower timeframe bull effort 高
    + 主週期 up result 高
    + 主週期收盤位置偏高
```

交易語意：

次級多方 effort 與主週期 result 同向一致，上漲推進較健康。

#### 9.6.4 MTF Markdown Confirm

```text
mtfMarkdownConfirmScore =
    lower timeframe bear effort 高
    + 主週期 down result 高
    + 主週期收盤位置偏低
```

交易語意：

次級空方 effort 與主週期 result 同向一致，下跌推進較健康。

### 9.7 MTF Valid flags

四個 valid flags 必須同時確認：

- MTF 資料可用。
- 對應 effort 達門檻。
- 對應 score 達門檻。

```text
mtfAbsorptionValid
mtfDistributionValid
mtfMarkupConfirmValid
mtfMarkdownConfirmValid
```

### 9.8 MTF top score

```text
mtfTopScore = max(
    mtfAbsorptionScore,
    mtfDistributionScore,
    mtfMarkupConfirmScore,
    mtfMarkdownConfirmScore
)
```

`mtfClueText` 由 top score 決定，依序命名為：

- MTF吸收。
- MTF派發。
- MTF拉升確認。
- MTF崩跌確認。
- MTF中性。
- MTF資料不足。

### 9.9 MTF 權重

```text
Off / Observe Only / data not ok → 0
Force On → mtfMaxWeight / 100
Auto → mtfMaxWeight / 100 × gate(mtfTopScore, mtfEffortThreshold, 90)
```

語意：

- `Observe Only`：只看，不投票。
- `Auto`：有明確分數才開始低權重參與。
- `Force On`：只要資料可用就固定參與，較適合研究，不建議作為實戰預設。

### 9.10 MTF clues

```text
mtfDemandClue    = mtfActive AND mtfAbsorptionValid
mtfSupplyClue    = mtfActive AND mtfDistributionValid
mtfBreakoutClue  = mtfActive AND mtfMarkupConfirmValid
mtfBreakdownClue = mtfActive AND mtfMarkdownConfirmValid
```

注意：在目前 v0.5 程式中，只有 `mtfActive` 時這些 clue 才會參與模型邏輯。Observe Only 下仍可顯示 MTF 分數與 dynamic alert，但不應透過 clue 改寫主模型。

---

## 10. Trend Extension / Continuation Layer

### 10.1 Trend extension

趨勢延伸分數分成：

```text
markupExtensionScore
markdownExtensionScore
```

它們衡量市場是否脫離橫盤，進入方向性推進。

### 10.2 Continuation after range

整理後延續分數分成：

```text
markupContinuationScore
markdownContinuationScore
```

核心判斷：

- 是否站上 / 跌破前區間。
- 是否維持一定根數。
- 均線是否發散。
- 趨勢延伸是否夠強。
- 反向鈍化或壓力是否太強。

### 10.3 Override concept

當趨勢延續證據夠強時，不應被單純橫盤中的反向鈍化線索過度壓制。

```text
markupContinuationOverride
markdownContinuationOverride
```

這是為了避免強趨勢中，指標太早把正常整理誤判成反轉。

---

## 11. 六階段 Raw Scores

六個原始階段分數：

```text
accRaw0       吸籌
markupRaw0    拉升
reaccRaw0     再吸籌
distRaw0      派發
markdownRaw0  崩跌
redistRaw0    再出貨
```

### 11.1 吸籌 accRaw0

吸籌由下列要素組成：

- 空頭成熟 trace。
- Range score。
- Downside exhaustion。
- Support holding。
- Low volatility。

語意：低位橫盤、賣壓衰竭、支撐守住。

### 11.2 拉升 markupRaw0

拉升由下列要素組成：

- Breakout score。
- Heat up。
- Bull structure。
- Markup extension。
- Markup continuation。
- 過去吸籌 trace。

語意：吸籌後突破、趨勢延伸、整理後續行。

### 11.3 再吸籌 reaccRaw0

再吸籌由下列要素組成：

- Bull background。
- Range score。
- Support holding。
- 非恐慌延續。
- 非 upside exhaustion。

語意：上升趨勢中的整理，支撐守住，供給不強。

### 11.4 派發 distRaw0

派發由下列要素組成：

- 多頭成熟 trace。
- Range score。
- Upside exhaustion。
- Resistance holding。
- Bear pressure rising。

語意：高位橫盤，上攻鈍化，壓力壓回，供給上升。

### 11.5 崩跌 markdownRaw0

崩跌由下列要素組成：

- Breakdown score。
- Panic heat down。
- Bear structure。
- Markdown extension。
- Markdown continuation。
- 過去派發 trace。

語意：派發後跌破、空頭趨勢延伸、整理後續跌。

### 11.6 再出貨 redistRaw0

再出貨由下列要素組成：

- Bear background。
- Range score。
- Resistance holding。
- Rebound failure。
- 非 downside exhaustion。

語意：下跌趨勢中的反彈失敗 / 空頭中繼。

### 11.7 平滑

六階段 raw score 會經過 `stageSmoothLen` 平滑。

---

## 12. Gate / Effective Score

### 12.1 Gate 的目的

Raw score 代表「這個劇本的素材是否存在」。Gate 代表「這個劇本是否符合當前背景」。

例如：

- 高位橫盤與上攻鈍化可能支持派發。
- 但若同時是強趨勢整理後延續，則不應太早判派發。

### 12.2 主要 gates

```text
accGate
markupGate
reaccGate
distGate
markdownGate
redistGate
```

每個 gate 使用不同背景條件：

- `accGate`：range + bear background + downside exhaustion + support holding。
- `markupGate`：breakout / extension / continuation 三者取最大。
- `reaccGate`：range + uptrend + support + non-distribution + non-markup-continuation。
- `distGate`：range + mature bull + upside exhaustion + resistance + non-markup-continuation。
- `markdownGate`：breakdown / extension / continuation 三者取最大。
- `redistGate`：range + downtrend + resistance + rebound failure + non-absorption。

### 12.3 Effective score

```text
accEffBase      = accRaw × accGate
markupEffBase   = markupRaw × markupGate
reaccEffBase    = reaccRaw × reaccGate
distEffBase     = distRaw × distGate
markdownEffBase = markdownRaw × markdownGate
redistEffBase   = redistRaw × redistGate
```

Effective score 是進入威科夫權重表前的核心分數。

---

## 13. Witness Layer 接入方式

### 13.1 Volume multiplier

Volume 不直接覆蓋分數，而是透過 multiplier 低權重加強。

```text
accVolMult
markupVolMult
reaccVolMult
distVolMult
markdownVolMult
redistVolMult
```

### 13.2 MTF multiplier

MTF 同樣使用 multiplier：

```text
accMtfMult
markupMtfMult
reaccMtfMult
distMtfMult
markdownMtfMult
redistMtfMult
```

對應語意：

- `mtfAbsorptionScore` → 加強吸籌。
- `mtfMarkupConfirmScore` → 加強拉升。
- `mtfAbsorptionScore` 與 `100 - mtfDistributionScore` → 半權重加強再吸籌。
- `mtfDistributionScore` → 加強派發。
- `mtfMarkdownConfirmScore` → 加強崩跌。
- `mtfDistributionScore` 與 `100 - mtfAbsorptionScore` → 半權重加強再出貨。

### 13.3 Final effective scores

```text
accEff      = accEffBase × accVolMult × accMtfMult
markupEff   = markupEffBase × markupVolMult × markupMtfMult
reaccEff    = reaccEffBase × reaccVolMult × reaccMtfMult
distEff     = distEffBase × distVolMult × distMtfMult
markdownEff = markdownEffBase × markdownVolMult × markdownMtfMult
redistEff   = redistEffBase × redistVolMult × redistMtfMult
```

### 13.4 Sharp probability

程式使用 `regimeGamma` 對 effective score 銳化：

```text
scoreSharp = scoreEff ^ regimeGamma
probStage = scoreSharp / sharpTotal × 100
```

注意：這裡的 probability 是「相對權重」，不是統計機率。

---

## 14. Dominant / Secondary Regime

### 14.1 Six probabilities

```text
probAcc
probMarkup
probReacc
probDist
probMarkdown
probRedist
```

轉成：

```text
p1 = 吸籌
p2 = 拉升
p3 = 再吸籌
p4 = 派發
p5 = 崩跌
p6 = 再出貨
```

### 14.2 Top / second / gap

```text
topId
secondId
topVal
secondVal
topGap
```

`topGap` 是主劇本與次劇本的領先差距，是判斷主導是否清楚的重要因子。

---

## 15. Evidence Strength

### 15.1 Evidence 的目的

Evidence Strength 衡量「目前主導劇本是否有足夠證據」。

它不只看 topVal，也看有效分數總量、最高有效分數、top gap 與階段支持因素。

### 15.2 Price-only evidence

```text
priceOnlyEvidenceStrength = weighted(
    effTotalStrength,
    topEffStrength,
    topGapStrength,
    stageSupportStrength
)
```

### 15.3 Witness evidence

當 Volume 或 MTF active 時，Evidence 加入 witness support：

```text
evidenceStrength = weighted(
    effTotalStrength,
    topEffStrength,
    topGapStrength,
    stageSupportStrength,
    witnessSupportStrength
)
```

### 15.4 MTF support mapping

```text
topId == 1 → mtfAbsorptionScore
topId == 2 → mtfMarkupConfirmScore
topId == 3 → weighted(mtfAbsorptionScore, 100 - mtfDistributionScore)
topId == 4 → mtfDistributionScore
topId == 5 → mtfMarkdownConfirmScore
topId == 6 → weighted(mtfDistributionScore, 100 - mtfAbsorptionScore)
```

### 15.5 Evidence labels

```text
低
中低
中高
高
```

---

## 16. 分歧與線索觀察

### 16.1 階段分歧

階段分歧必須由兩個相對階段的權重同時達到門檻，且差距不大。

```text
lowStageDispute  = 吸籌 vs 再出貨
highStageDispute = 再吸籌 vs 派發
trendStageDispute = 拉升 vs 派發 或 崩跌 vs 吸籌
```

### 16.2 線索觀察

線索觀察不是正式階段，也不是正式反轉。

```text
highClueObservation = 高位鈍化 / 供給線索升高，但派發權重未達命名門檻
lowClueObservation = 低位鈍化 / 承接線索升高，但吸籌權重未達命名門檻
trendClueDispute = 趨勢延伸中出現反向鈍化 / 承接 / 供給線索
```

### 16.3 文字語意規則

這是 v0.5 很重要的語意原則：

- 不要把「供給線索」直接寫成「派發確認」。
- 不要把「承接線索」直接寫成「吸籌確認」。
- 不要把「MTF反駁」直接寫成「反轉」。
- 若階段權重未達 `stageNameUseMinWeight`，應使用「觀察」、「線索」、「分歧」等語言。

---

## 17. Candidate / Formal Regime

### 17.1 State raw flags

```text
chaosRaw
coexistRaw
weakCandidateRaw
strongCandidate
```

語意：

- `chaosRaw`：分數不足或主導不明。
- `coexistRaw`：劇本並存或階段分歧。
- `weakCandidateRaw`：top 劇本存在，但證據不足或有 conflict。
- `strongCandidate`：top 劇本權重、gap、evidence 都達標且沒有 conflict。

### 17.2 Fast switch

快速轉正只適用於非常強的拉升 / 崩跌候選。

```text
fastMarkupSwitch
fastMarkdownSwitch
fastSwitchActive
activeConfirmBars
```

### 17.3 Regime inertia

正式主導需要候選連續達標：

```text
confirmedId
candidateId
candidateBars
noRegimeBars
```

這是為了避免每根 K 棒都亂跳。

### 17.4 Final IDs

```text
formalId = confirmedId
candidateDisplayId = strongCandidate or weakCandidateRaw ? topId : 0
secondaryId = hasSharp ? secondId : 0
```

---

## 18. 六階段名稱與子類型

### 18.1 Stage IDs

```text
0 無明確
1 吸籌
2 拉升
3 再吸籌
4 派發
5 崩跌
6 再出貨
```

### 18.2 拉升 subtype

拉升可細分為：

- `拉升｜整理後延續`
- `拉升｜突破初段`
- `拉升｜極端過熱`
- `拉升｜過熱延伸`
- `拉升｜偏熱推進`
- `拉升｜健康推進`

### 18.3 崩跌 subtype

崩跌可細分為：

- `崩跌｜整理後延續`
- `崩跌｜下破初段`
- `崩跌｜極端恐慌`
- `崩跌｜恐慌延伸`
- `崩跌｜恐慌推進`
- `崩跌｜下跌推進`

---

## 19. Pace Guide

### 19.1 定位

Pace Guide 是人類可讀的節奏翻譯層。

它從三種視角輸出：

- 空手。
- 多單。
- 空單。

### 19.2 Pace code

主要語意包括：

- 證據不足，降低動作。
- 低位階段分歧。
- 高位階段分歧。
- 趨勢階段分歧。
- 多頭延伸帶鈍化。
- 空頭延伸帶承接。
- 高位鈍化觀察。
- 低位鈍化觀察。
- 偏多推進。
- 偏多偏熱。
- 多頭極熱。
- 多頭整理。
- 高位供給升高。
- 偏空推進。
- 恐慌延伸。
- 低位吸籌。
- 空頭中繼風險。

### 19.3 Pace wording principle

Pace Guide 應該使用「節奏語言」，不是交易命令。

例如：

- 可以說：不追高，等確認。
- 不要說：立刻放空。
- 可以說：續抱但停止加碼。
- 不要說：買進持有。
- 可以說：等待反彈失敗。
- 不要說：現在做空。

---

## 20. Flat Action Level

### 20.1 定位

Flat Action Level 是給空手者看的「是否具備試單條件」分級。

它不是交易命令。

### 20.2 Levels

```text
0 觀望
1 等待觸發
2 小部位試多
3 順勢試多
4 小部位試空
5 順勢試空
6 禁止追多
7 禁止追空
```

### 20.3 多方條件

偏多 action 需考慮：

- bull formal or candidate stage。
- Evidence strength。
- Top gap。
- 上漲末段風險未過高。
- 非 redUp。
- 突破 / 延伸 / 續行觸發。
- 沒有 supply conflict。
- 順勢試多可能要求 formal 或 fast switch。

### 20.4 空方條件

偏空 action 需考慮：

- bear formal or candidate stage。
- Evidence strength。
- Top gap。
- 下跌恐慌風險未過高。
- 非 redDn。
- 下破 / 延伸 / 續行觸發。
- 沒有 demand conflict。
- 順勢試空可能要求 formal 或 fast switch。

### 20.5 禁止追價

```text
flatNoChaseLong
flatNoChaseShort
```

語意：方向可能仍偏多 / 偏空，但追價品質已經差。

---

## 21. Pace Context Downgrade

### 21.1 設計目的

當 raw Flat Action 給出順勢試單，但 Pace / 線索層顯示供給、承接或分歧，行動應降級。

這是本指標非常重要的風控語意。

### 21.2 多方降級

```text
raw F3 順勢試多 → F2 小試多
raw F2 小試多 → F1 等回測
```

觸發原因可能包括：

- 高位鈍化。
- 高位階段分歧。
- 上漲延伸帶供給線索。
- Volume supply clue。
- MTF supply clue。
- Upside exhaustion + resistance holding。

### 21.3 空方降級

```text
raw F5 順勢試空 → F4 小試空
raw F4 小試空 → F1 等反彈失敗
```

觸發原因可能包括：

- 低位鈍化。
- 低位階段分歧。
- 下跌延伸帶承接線索。
- Volume demand clue。
- MTF demand clue。
- Downside exhaustion + support holding。

---

## 22. Visual Layer

### 22.1 主圖線

本指標 overlay=false，在副圖顯示：

- 上漲末段風險。
- 下跌末段恐慌風險。
- 選配：即時熱度。
- 選配：趨勢成熟度。
- 選配：區間分數。
- 選配：Debug 單線。

### 22.2 水平線

- 紅燈。
- 橘燈。
- 黃燈。
- 50 中性線。
- 0 / 100。

### 22.3 背景模式

```text
關閉
單色｜正式主導
單色｜候選
單色｜Pace Guide
雙層｜上正式 / 下候選
雙層｜上 Pace / 下候選
```

### 22.4 Dual Layer Background

TradingView 的 `bgcolor()` 無法只染副圖上半部或下半部，因此雙層背景使用隱藏 plot + fill：

- 100 到 50：上半部。
- 50 到 0：下半部。

### 22.5 MTF 不直接染背景

v0.5 的 MTF 預設不新增獨立背景層。

若未來要新增 MTF Ribbon 或 MTF background，應在 v0.5.1 或 v0.6 另開 spec，且預設不得覆蓋正式主導背景。

---

## 23. Dashboard

### 23.1 Table modes

```text
極簡
精簡
完整
除錯
```

### 23.2 極簡模式

顯示：

- 正式。
- 候選。
- 證據 / Gap。
- 模式。
- 量能。
- MTF。

### 23.3 精簡模式

顯示：

- 正式主導。
- 候選。
- 次要 / Gap。
- 六階段權重。
- 吸收判讀。
- 出貨判讀。
- 趨勢判讀。
- 證據 / 狀態。
- 末段 / 模式。
- 量能層。
- MTF驗證。

### 23.4 完整模式

除精簡資訊外，顯示更完整的吸收、派發、趨勢、量價與 MTF 分數。

### 23.5 除錯模式

除錯模式應顯示：

- Gate。
- Effective score。
- Extension gate。
- Flat Raw / Final。
- 背景模式。
- Volume Q/W。
- EVR U/D。
- MTF Effort。
- MTF Result。

### 23.6 已知顯示注意事項

目前完整模式與除錯模式的 row index 有重疊風險：完整模式已使用 `rowOffset + 13` 到 `rowOffset + 15` 顯示量能 / MTF，除錯模式又從 `rowOffset + 13` 開始寫除錯列。若未來要改善 Dashboard，應優先整理 row allocation，避免除錯模式覆蓋完整模式列。

---

## 24. Debug 單線

### 24.1 既有 Debug 選項

Debug 單線可顯示：

- 六階段權重。
- 六階段 gates。
- 下跌鈍化。
- 上漲鈍化。
- 支撐守住。
- 壓力壓回。
- 上漲 / 下跌延伸。
- 上漲 / 下跌續行。
- 量能品質與量能證據。

### 24.2 v0.5 新增 Debug 選項

```text
MTF空方努力
MTF多方努力
MTF吸收
MTF派發
MTF拉升確認
MTF崩跌確認
MTF權重
```

Debug 是驗證 MTF 語意最重要的工具。

---

## 25. Alerts

### 25.1 Plot-count safe 原則

TradingView 的 `alertcondition()` 也會占用 plot count，因此 v0.5 仍維持 compact alertcondition，細項訊息用 dynamic `alert()`。

### 25.2 具名 alertcondition

包含：

- 正式主導狀態切換。
- 新候選主導狀態出現。
- 進入分歧狀態。
- 進入不明確狀態。
- 末段風險進入紅燈。
- 突破 / 下破啟動模式。
- 證據強度升至門檻以上。
- 趨勢延伸分數升至門檻以上。
- 強候選快速轉正啟動。
- 吸收 / 出貨分數升至門檻以上。
- Volume Quality Layer 重要事件。
- MTF Effort / Result 重要事件。
- Pace Guide 主節奏切換。
- Flat Action 空手行動切換。
- Flat Action 切換為試多 / 試空 / 禁止追價。
- Flat Action 觸發 Pace Context 降級。

### 25.3 v0.5 MTF dynamic alerts

MTF dynamic alerts 包含：

- MTF 吸收線索。
- MTF 派發線索。
- MTF 拉升確認。
- MTF 崩跌確認。

注意：即使 MTF 是 Observe Only，MTF 分數仍可用於 alert 觀察；但 Observe Only 不應改主模型。

---

## 26. 重要場景語意

### 26.1 高位橫盤：再吸籌 vs 派發

這是最容易誤解的場景。

高位橫盤不自動等於再吸籌，也不自動等於派發。

再吸籌需要：

- 多頭背景仍在。
- 支撐守住。
- 供給 / 上攻鈍化不強。
- 非 markup continuation 已經更強。
- 沒有明顯 volume / MTF supply clue。

派發需要：

- 多頭成熟。
- range 條件成立。
- upside exhaustion。
- resistance holding。
- bear pressure rising。
- 非 markup continuation。

因此，若價格仍在高位但上攻效率下降、壓力壓回、MTF/Volume 供給線索升高，模型偏向高位供給或派發風險是合理的。

但若派發權重未達命名門檻，文字應使用「高位鈍化觀察」、「高位供給升高」或「派發候選」，不要過早說派發確認。

### 26.2 低位橫盤：吸籌 vs 再出貨

低位橫盤不自動等於吸籌。

吸籌需要：

- 空頭背景 / 成熟 trace。
- Range 條件。
- Downside exhaustion。
- Support holding。
- 承接線索。

再出貨需要：

- 空頭背景。
- Range 條件。
- Resistance holding。
- Rebound failure。
- 非吸收。

若低位只是跌不動，但沒有支撐 reclaim，或反彈始終失敗，不能直接視為吸籌。

### 26.3 強上漲趨勢

強上漲趨勢中，upside exhaustion 可能升高，但若 markup continuation、ma spread、range continuation 都很強，不應太早切成派發。

此時應依賴：

- `markupContinuationOverride`
- `markupContinuationScore`
- `markupExtensionScore`
- `mtfMarkupConfirmScore`
- `volumeBreakoutConfirmation`

### 26.4 強下跌趨勢

強下跌趨勢中，downside exhaustion 可能升高，但若 markdown continuation、ma spread、range continuation 都很強，不應太早切成吸籌。

此時應依賴：

- `markdownContinuationOverride`
- `markdownContinuationScore`
- `markdownExtensionScore`
- `mtfMarkdownConfirmScore`
- `volumeBreakdownConfirmation`

---

## 27. 測試與驗收標準

### 27.1 Pine 編譯

必須在 TradingView Pine v6 編譯通過。

檢查：

- 第一行是 `//@version=6`。
- 無超過 plot count 限制。
- alertcondition 數量合理。
- table row 不超過初始化 row 數。
- `request.security_lower_tf()` 在測試 time frame 可用。

### 27.2 向下相容

在下列設定下，v0.5 應接近 v0.4 行為：

```text
MTF Mode = Off
```

以及：

```text
MTF Mode = Observe Only
```

差異應只出現在：

- Dashboard MTF 顯示。
- Debug MTF 顯示。
- MTF alert。
- Pace reason 附加文字。

不應改變主引擎判斷。

### 27.3 MTF 語意測試

應測以下場景：

1. 真 V 轉：`mtfAbsorptionScore` 應比正式吸籌更早出現線索。
2. 假 V 轉 / 二次探底：`mtfAbsorptionScore` 不應長期錯誤維持高檔。
3. 強趨勢下跌：`mtfMarkdownConfirmScore` 應高於 `mtfAbsorptionScore`。
4. 高位上攻無效：`mtfDistributionScore` 應升高。
5. 健康突破：`mtfMarkupConfirmScore` 應升高，而不是派發分數亂亮。
6. 高位橫盤後最後衝高再跌：模型可先顯示高位鈍化 / 供給線索，再等待跌破確認。

### 27.4 Dashboard 測試

測試 table mode：

- 極簡。
- 精簡。
- 完整。
- 除錯。

檢查：

- MTF row 是否顯示。
- Volume row 是否顯示。
- Pace Guide row 是否與 table mode 互相錯位。
- 除錯模式是否覆蓋完整模式的重要資訊。

### 27.5 多市場測試

至少測：

- 指數 ETF / 期貨。
- 商品。
- 債券或利率商品。
- 外匯或無真實 volume 商品。
- 台股 / 美股個股。

觀察：

- Volume quality 是否合理。
- Tick Volume Proxy 是否過度影響。
- MTF lower timeframe 在日線 / 週線 / 4H 是否有足夠 intrabars。

---

## 28. 已知限制與可能修正

### 28.1 MTF lower timeframe 限制

`request.security_lower_tf()` 需要 lower timeframe 確實低於主圖 timeframe，且資料可用。

若主圖是日線而 lower TF 設 240，某些市場可能 intrabar 數不足。此時可降低：

```text
mtfMinIntrabars
```

或改用更低 timeframe。

### 28.2 array helper 型別風險

目前 helper：

```pine
f_arrayAvgOrNa(arr) =>
```

若 TradingView 編譯器要求明確型別，可改為：

```pine
f_arrayAvgOrNa(array<float> arr) =>
```

或改成手動 loop 版本。這是技術修補，不改模型語意。

### 28.3 Dashboard row overlap

完整模式與除錯模式目前可能有 row 覆蓋。未來修正應集中整理 row allocation，不要順手修改模型邏輯。

### 28.4 MTF alert 與 Observe Only

目前 Observe Only 下仍可出現 MTF dynamic alert。這符合「觀察」精神，但若使用者覺得過吵，未來可新增：

```text
MTF Alerts Mode = Off / Observe / Active Only
```

### 28.5 高位供給語意

「派發」這個詞有很強的定罪感。若高位供給線索存在但正式派發未確認，顯示文字應優先使用：

- 高位鈍化觀察。
- 高位供給升高。
- 派發候選。
- 再吸籌 / 派發待辨。

---

## 29. 後續版本建議

### 29.1 v0.5.1 建議

可做小修版：

- 整理 Dashboard row overlap。
- 修正 `f_arrayAvgOrNa` 型別風險。
- 新增 MTF alert mode。
- 新增 MTF Ribbon，但預設關閉。
- 將高位供給與派發確認的文字語意再分層。

### 29.2 v0.6 建議

可做較大版：

- Event-study strategy 版本，用於測試 15 / 20 / 30 天 forward return。
- 針對 Flat Action Level 做回測模板。
- 將指標版與 strategy 版分檔維護。
- 建立不同市場 preset。

---

## 30. AI 協作指令摘要

未來請 AI 修改本指標時，可使用以下摘要作為前置指令：

```text
你正在修改 Chase Risk Market Regime Radar v0.5。
請先閱讀 spec，再閱讀 Pine Script。
本指標是市場 regime / 風險節奏雷達，不是交易訊號。
價格行為是主引擎；Volume 與 MTF 都只是 witness layer。
MTF 是 effort/result layer，不是 lower timeframe direction voter。
Observe Only 不得改寫主模型。
任何修改都要分清楚是模型層、證據層、顯示層、alert 層還是文件層。
不要在沒有要求時重構整份 Pine Script。
```

---

## 31. 最終設計原則

這個指標應該幫使用者回答三個問題：

1. **現在市場比較像哪一種 regime？**
2. **這個 regime 的證據夠不夠？有沒有分歧？**
3. **我現在最容易犯的錯是追高、追空、太早反手、還是無腦抄底？**

只要後續修改仍然服務這三個問題，就是本指標的正確演化方向。
