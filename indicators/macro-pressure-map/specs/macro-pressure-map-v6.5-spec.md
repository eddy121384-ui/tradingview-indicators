# Macro Pressure Map V6.5 規格書

版本：V6.5 Adjustable Macro Weights  
對應程式：`indicators/macro-pressure-map/src/macro-pressure-map-v6.5.pine`  
前版規格：`indicators/macro-pressure-map/specs/macro-pressure-map-v6.4-spec.md`  
前版程式：`indicators/macro-pressure-map/src/macro-pressure-map-v6.4.pine`  
指標名稱建議：`Macro Pressure Map V6.5 [GPI/IPI/FCPI]`  
Pine Script 版本：v6  
定位：總經壓力與風險姿態儀表板，不是進出場訊號器。

---

## 1. V6.5 修正目標

V6.5 的主要目標，是修正 V6.4 中「總經資料只能開關，不能指定佔分權重」的限制。

V6.4 中，若 `Use Economic Data` 開啟，GPI 與 IPI 固定使用：

```pine
GPI = f_wavg2(gpiMarket, 0.70, gpiMacro, 0.30)
IPI = f_wavg2(ipiMarket, 0.70, ipiMacro, 0.30)
```

若 `Use Official Financial Conditions Data` 開啟，FCPI 固定使用：

```pine
FCPI = f_wavg2(fcpiMarket, 0.80, fcpiOfficial, 0.20)
```

這使使用者只能選擇是否加入總經資料，不能依照市場環境、回測結果或研究目的調整 market proxy 與 macro confirmation 的權重。

V6.5 必須將這一層權重改成使用者可調參數。

---

## 2. 指標定位

Macro Pressure Map V6.5 仍是一個 TradingView 副圖指標，用於觀察市場正在定價的三種宏觀壓力：

- GPI｜Growth Pressure Index｜成長壓力軸。
- IPI｜Inflation Pressure Index｜通膨壓力軸。
- FCPI｜Financial Conditions Pressure Index｜金融條件壓力軸。

本指標不是買賣訊號器，不提供 entry signal，也不應單獨作為交易依據。

核心概念仍是：

> Growth × Inflation 決定市場方向，Financial Conditions 決定油門與煞車。

V6.5 的新增重點是：

> Market proxy 與 Macro confirmation 的權重必須可調整，避免固定 70/30 或 80/20 導致歷史情境解讀失真。

---

## 3. 三大壓力軸定義

### 3.1 GPI｜Growth Pressure Index

GPI 代表 market-implied growth pressure，也就是市場價格正在反映的成長壓力、成長敘事與風險偏好。

GPI > 0：市場偏向定價成長改善或風險承擔改善。  
GPI < 0：市場偏向定價成長惡化或防禦需求上升。

GPI 不是 GDP nowcast，也不是實體經濟成長率預測。

### 3.2 IPI｜Inflation Pressure Index

IPI 代表通膨壓力軸。

IPI > 0：通膨壓力升溫。  
IPI < 0：通膨壓力降溫。

V6.5 仍延續 V6.4 的基礎架構：IPI market proxy 主要由 breakeven、commodity basket、energy pressure 與 optional industrial metals 組成；IPI macro confirmation 則由 CPI、Core CPI、PCE、Core PCE、PPI 與 wage proxy 組成。

重要提醒：V6.5 本次重點是先讓 market / macro 權重可調整。IPI 拆分為 Market Inflation Impulse 與 Realized Inflation Pressure 可列為 V6.6 或 V7.0 的後續結構修正。

### 3.3 FCPI｜Financial Conditions Pressure Index

FCPI 代表金融條件壓力軸。

FCPI > 0：金融條件變緊。  
FCPI < 0：金融條件轉鬆。

FCPI 仍由三個 market stress sub-index 組成：

- Credit Stress。
- Rates / Dollar Constraint。
- Volatility Shock。

若開啟 official FCI，則加入 NFCI / STLFSI4 作為慢速官方確認。

---

## 4. V6.5 新增權重輸入

V6.5 必須在 `groupWeights` 中新增以下 input。

### 4.1 GPI market / macro 權重

```pine
wGpiMarket = input.float(0.70, "GPI Weight: Market Proxy", minval=0.0, step=0.05, group=groupWeights)
wGpiMacro  = input.float(0.30, "GPI Weight: Macro Confirmation", minval=0.0, step=0.05, group=groupWeights)
```

預設仍維持 V6.4 的 70/30，以保留向後相容性。

但使用者必須可以自由改成例如：

- Market 1.00 / Macro 0.00。
- Market 0.80 / Macro 0.20。
- Market 0.50 / Macro 0.50。
- Market 0.30 / Macro 0.70。

### 4.2 IPI market / macro 權重

```pine
wIpiMarket = input.float(0.70, "IPI Weight: Market Proxy", minval=0.0, step=0.05, group=groupWeights)
wIpiMacro  = input.float(0.30, "IPI Weight: Macro Confirmation", minval=0.0, step=0.05, group=groupWeights)
```

預設仍維持 V6.4 的 70/30。

但使用者必須可以提高 macro 權重，以處理類似 2022 年的情境：market inflation impulse 已經降溫，但 realized inflation pressure 仍然高。

### 4.3 FCPI market / official 權重

```pine
wFcpiMarket   = input.float(0.80, "FCPI Weight: Market Stress", minval=0.0, step=0.05, group=groupWeights)
wFcpiOfficial = input.float(0.20, "FCPI Weight: Official FCI", minval=0.0, step=0.05, group=groupWeights)
```

預設仍維持 V6.4 的 80/20。

但使用者必須可以依照研究目的調整官方金融條件資料的影響力。

---

## 5. 權重正規化原則

V6.5 不要求使用者輸入的權重加總必須等於 1。

所有 market / macro / official 合成仍使用 `f_wavg2()`，由函數自動根據有效資料與有效權重重新正規化。

例如：

```pine
GPI = useMacroData ? f_wavg2(gpiMarket, wGpiMarket, gpiMacro, wGpiMacro) : gpiMarket
IPI = useMacroData ? f_wavg2(ipiMarket, wIpiMarket, ipiMacro, wIpiMacro) : ipiMarket
FCPI = useOfficialFCI ? f_wavg2(fcpiMarket, wFcpiMarket, fcpiOfficial, wFcpiOfficial) : fcpiMarket
```

若某個 component 為 `na`，或其權重為 0，則不應納入分母。

若所有有效資料皆為 `na` 或權重皆為 0，則結果為 `na`。

---

## 6. 開關與權重的關係

### 6.1 `Use Economic Data = false`

若 `Use Economic Data` 關閉，GPI 與 IPI 必須完全使用 market proxy：

```pine
GPI = gpiMarket
IPI = ipiMarket
```

此時即使 `wGpiMacro` 或 `wIpiMacro` 不為 0，也不得影響最終結果。

### 6.2 `Use Economic Data = true`

若 `Use Economic Data` 開啟，GPI 與 IPI 使用使用者指定權重合成：

```pine
GPI = f_wavg2(gpiMarket, wGpiMarket, gpiMacro, wGpiMacro)
IPI = f_wavg2(ipiMarket, wIpiMarket, ipiMacro, wIpiMacro)
```

### 6.3 `Use Official Financial Conditions Data = false`

若 `Use Official Financial Conditions Data` 關閉，FCPI 完全使用 market stress proxy：

```pine
FCPI = fcpiMarket
```

### 6.4 `Use Official Financial Conditions Data = true`

若 `Use Official Financial Conditions Data` 開啟，FCPI 使用使用者指定權重合成：

```pine
FCPI = f_wavg2(fcpiMarket, wFcpiMarket, fcpiOfficial, wFcpiOfficial)
```

---

## 7. GPI 組件

GPI market proxy 維持 V6.4 架構：

- `IWM / SPY`：小型股相對大型股。
- `RSP / SPY`：等權重 S&P 500 相對市值權重 S&P 500。
- `XLY / XLP`：可選消費相對必需消費。
- `XLI / XLU`：工業股相對公用事業。
- `Copper / Gold`：銅金比。

`gpiMarket` 仍為上述五項有效 component 的平均。

GPI macro confirmation 維持 V6.4 架構：

- PMI / ISM Proxy。
- CFNAI。
- Building Permits。
- Initial Jobless Claims，反向處理。
- Unemployment Rate，反向處理。

`gpiMacro` 仍為上述五項有效 component 的平均。

V6.5 的唯一必要修改是：`gpiMarket` 與 `gpiMacro` 的最終合成權重改為 input。

---

## 8. IPI 組件

IPI market proxy 維持 V6.4 架構：

- Breakeven Pressure。
- Commodity Basket。
- Energy Pressure。
- Industrial Metals optional。

IPI market 內部權重維持可調：

```pine
wBreakeven = input.float(0.35, "IPI Weight: Breakeven Pressure", minval=0.0, step=0.05, group=groupWeights)
wCommodity = input.float(0.40, "IPI Weight: Commodity Basket", minval=0.0, step=0.05, group=groupWeights)
wEnergy = input.float(0.25, "IPI Weight: Energy Pressure", minval=0.0, step=0.05, group=groupWeights)
wIndustrialMetals = input.float(0.10, "IPI Weight: Industrial Metals Optional", minval=0.0, step=0.05, group=groupWeights)
```

IPI macro confirmation 維持 V6.4 架構：

- CPI。
- Core CPI。
- PCE Price Index。
- Core PCE。
- PPI。
- Average Hourly Earnings proxy。

`ipiMacro` 仍為上述六項有效 component 的平均。

V6.5 的必要修改是：`ipiMarket` 與 `ipiMacro` 的最終合成權重改為 input。

---

## 9. FCPI 組件

FCPI market stress proxy 維持 V6.4 架構。

### 9.1 Credit Stress

包括：

- HY OAS。
- HYG / IEF，反向處理。
- KRE / SPY optional stress add-on，反向處理。

KRE optional 若開啟，內部權重仍為：

```pine
creditStressWithKRE = f_wavg3(scoreHYOAS, 0.45, scoreHygIefReversed, 0.45, scoreKreSpyReversed, 0.10)
```

### 9.2 Rates / Dollar Constraint

包括：

- 10Y real yield。
- DXY。

### 9.3 Volatility Shock

包括：

- VIX。
- MOVE。

### 9.4 FCPI market 內部權重

V6.4 已經可以調整 FCPI market 內部權重，V6.5 繼續保留：

```pine
wCreditStress = input.float(0.40, "FCPI Weight: Credit Stress", minval=0.0, step=0.05, group=groupWeights)
wRatesDollar = input.float(0.35, "FCPI Weight: Rates/Dollar Constraint", minval=0.0, step=0.05, group=groupWeights)
wVolShock = input.float(0.25, "FCPI Weight: Volatility Shock", minval=0.0, step=0.05, group=groupWeights)
```

### 9.5 Official FCI 權重

V6.5 新增 `wFcpiMarket` 與 `wFcpiOfficial`，讓 `fcpiMarket` 與 `fcpiOfficial` 的最終合成可調。

---

## 10. Dashboard 必須新增的資訊

V6.5 dashboard 必須在主面板中新增或調整權重顯示，避免使用者不知道目前 market / macro 權重狀態。

建議新增以下 rows：

- `GPI Wgt`：顯示目前 GPI market / macro 權重。
- `IPI Wgt`：顯示目前 IPI market / macro 權重。
- `FCPI Wgt`：顯示目前 FCPI market / official 權重。

英文顯示建議：

```text
GPI Wgt: Mkt 70 / Macro 30
IPI Wgt: Mkt 70 / Macro 30
FCPI Wgt: Mkt 80 / Official 20
```

中文顯示建議：

```text
GPI 權重：市場 70 / 總經 30
IPI 權重：市場 70 / 總經 30
FCPI 權重：市場 80 / 官方 20
```

日本語顯示建議：

```text
GPI 重み：市場 70 / マクロ 30
IPI 重み：市場 70 / マクロ 30
FCPI 重み：市場 80 / 公式 20
```

韓文顯示建議：

```text
GPI 가중치: 시장 70 / 매크로 30
IPI 가중치: 시장 70 / 매크로 30
FCPI 가중치: 시장 80 / 공식 20
```

若 `Use Economic Data = false`，GPI / IPI 權重顯示可以改為：

```text
Market only
```

若 `Use Official Financial Conditions Data = false`，FCPI 權重顯示可以改為：

```text
Market only
```

---

## 11. Dashboard 多語系需求

V6.5 必須延續 V6.4 dashboard 四語系：

- English。
- 中文。
- 日本語。
- 한국어。

新增的權重 rows 也必須完整支援四語言，不可只顯示英文。

需要新增的 label 建議：

```pine
lblWeight = f_lang("Weight", "權重", "重み", "가중치")
lblGpiWeight = f_lang("GPI Wgt", "GPI 權重", "GPI 重み", "GPI 가중치")
lblIpiWeight = f_lang("IPI Wgt", "IPI 權重", "IPI 重み", "IPI 가중치")
lblFcpiWeight = f_lang("FCPI Wgt", "FCPI 權重", "FCPI 重み", "FCPI 가중치")
lblMarket = f_lang("Mkt", "市場", "市場", "시장")
lblMacro = f_lang("Macro", "總經", "マクロ", "매크로")
lblOfficial = f_lang("Official", "官方", "公式", "공식")
lblMarketOnly = f_lang("Market only", "僅市場", "市場のみ", "시장만")
```

---

## 12. 權重顯示格式函數

建議新增權重顯示函數。

### 12.1 百分比格式

```pine
f_pctWeight(w) =>
    str.tostring(w * 100.0, "#.0")
```

### 12.2 GPI / IPI 權重句

```pine
f_marketMacroWeightText(wMarket, wMacro, enabled) =>
    enabled ? lblMarket + " " + f_pctWeight(wMarket) + " / " + lblMacro + " " + f_pctWeight(wMacro) : lblMarketOnly
```

### 12.3 FCPI 權重句

```pine
f_marketOfficialWeightText(wMarket, wOfficial, enabled) =>
    enabled ? lblMarket + " " + f_pctWeight(wMarket) + " / " + lblOfficial + " " + f_pctWeight(wOfficial) : lblMarketOnly
```

注意：這裡顯示的是使用者輸入權重，不一定是實際有效權重。若某些資料為 `na`，`f_wavg2()` 會自動重新正規化。未來版本可再加入 actual effective weight 顯示。

---

## 13. Symbol Health 與資料可用性

V6.5 必須保留 V6.4 的 Symbol Health 模式。

使用者應能透過：

```text
Show Component Diagnostics = true
Diagnostic Group = Symbols
```

檢查每個資料源是否為 OK / NA。

V6.5 不要求新增有效資料計數，但建議列為後續優化：

- `GPI Macro available: x/5`
- `IPI Macro available: x/6`
- `FCPI Official available: x/2`

這可以避免使用者以為已經調高 macro weight，但實際上 macro series 都是 NA。

---

## 14. 標準化方法

V6.5 沿用 V6.4 的 `f_componentScore()`：

1. Level z-score。
2. Fast / mid momentum z-score。
3. Direction score。
4. Raw score 合成。
5. 自訂 `f_tanh()` 壓縮至約 -100 到 +100。

合成概念：

```pine
raw = 0.5 * level + 0.3 * momentum + 0.2 * direction
scaled = 100 * tanh(raw / 2)
```

由於 Pine Script 不支援 `math.tanh()`，仍使用 V6.4 的自訂 `f_tanh()`。

---

## 15. 視覺化需求

V6.5 必須保留 V6.4 的雙層視覺架構：

1. Historical Pressure Lines：三條歷史壓力線。
2. Current Regime Dashboard：右側目前狀態儀表板。

主線包括：

- GPI。
- IPI。
- FCPI。

參考線包括：

- 0。
- +30 / -30。
- +60 / -60。

FCPI 背景風險提示繼續保留。

Dashboard 顏色、文字大小與語言切換繼續保留。

---

## 16. Regime 判斷

V6.5 沿用 V6.4 regime 判斷。

GPI / IPI threshold：

```pine
growthThreshold = input.float(10.0, "Growth Threshold")
inflationThreshold = input.float(10.0, "Inflation Threshold")
```

基本象限：

- GPI > +10 且 IPI < -10：Goldilocks / Disinflationary Expansion。
- GPI > +10 且 IPI > +10：Reflation / Overheating Risk。
- GPI < -10 且 IPI < -10：Slowdown / Disinflation。
- GPI < -10 且 IPI > +10：Stagflation Pressure。
- 其他：Mixed / Transition。

FCPI threshold：

```pine
fcThreshold = input.float(30.0, "Financial Conditions Threshold")
stressThreshold = input.float(60.0, "Stress Threshold")
```

- FCPI > +60：Stress rising / Defensive posture。
- FCPI > +30：Conditions tightening / Risk budget reduced。
- FCPI < -30：Conditions easing / Risk-on allowed。
- 其他：Neutral conditions / Standard risk budget。

---

## 17. V6.5 程式修改清單

相對 V6.4，V6.5 程式至少需要做以下修改。

### 17.1 新增 input

在 weights group 加入：

```pine
wGpiMarket = input.float(0.70, "GPI Weight: Market Proxy", minval=0.0, step=0.05, group=groupWeights)
wGpiMacro  = input.float(0.30, "GPI Weight: Macro Confirmation", minval=0.0, step=0.05, group=groupWeights)
wIpiMarket = input.float(0.70, "IPI Weight: Market Proxy", minval=0.0, step=0.05, group=groupWeights)
wIpiMacro  = input.float(0.30, "IPI Weight: Macro Confirmation", minval=0.0, step=0.05, group=groupWeights)
wFcpiMarket   = input.float(0.80, "FCPI Weight: Market Stress", minval=0.0, step=0.05, group=groupWeights)
wFcpiOfficial = input.float(0.20, "FCPI Weight: Official FCI", minval=0.0, step=0.05, group=groupWeights)
```

### 17.2 修改 composite indices

把 V6.4 的固定權重：

```pine
GPI = useMacroData ? f_wavg2(gpiMarket, 0.70, gpiMacro, 0.30) : gpiMarket
IPI = useMacroData ? f_wavg2(ipiMarket, 0.70, ipiMacro, 0.30) : ipiMarket
FCPI = useOfficialFCI ? f_wavg2(fcpiMarket, 0.80, fcpiOfficial, 0.20) : fcpiMarket
```

改成：

```pine
GPI = useMacroData ? f_wavg2(gpiMarket, wGpiMarket, gpiMacro, wGpiMacro) : gpiMarket
IPI = useMacroData ? f_wavg2(ipiMarket, wIpiMarket, ipiMacro, wIpiMacro) : ipiMarket
FCPI = useOfficialFCI ? f_wavg2(fcpiMarket, wFcpiMarket, fcpiOfficial, wFcpiOfficial) : fcpiMarket
```

### 17.3 新增 dashboard 權重顯示

新增：

- `lblGpiWeight`
- `lblIpiWeight`
- `lblFcpiWeight`
- `lblMarket`
- `lblMacro`
- `lblOfficial`
- `lblMarketOnly`

新增 dashboard rows 顯示：

- GPI market / macro 權重。
- IPI market / macro 權重。
- FCPI market / official 權重。

---

## 18. V6.5 驗收標準

完成 V6.5 程式後，至少需檢查以下項目。

1. `Use Economic Data = false` 時，調整 `wGpiMacro` 與 `wIpiMacro` 不應影響 GPI / IPI。
2. `Use Economic Data = true` 時，調整 `wGpiMarket / wGpiMacro` 必須改變 GPI。
3. `Use Economic Data = true` 時，調整 `wIpiMarket / wIpiMacro` 必須改變 IPI。
4. `Use Official FCI = false` 時，調整 `wFcpiOfficial` 不應影響 FCPI。
5. `Use Official FCI = true` 時，調整 `wFcpiMarket / wFcpiOfficial` 必須改變 FCPI。
6. 權重不必加總為 1，`f_wavg2()` 應自動正規化。
7. 若 macro data 為 NA，調高 macro weight 不應導致整個指標崩潰，但結果可能接近 market proxy。
8. Dashboard 必須正確顯示目前權重設定。
9. Dashboard 四語系切換時，權重 rows 不可出現半英文半中文的破碎 UI。
10. Symbol Health 模式必須仍能正常顯示。

---

## 19. V6.5 已知仍未處理事項

V6.5 只處理 market / macro / official 權重可調問題。

以下事項暫不在 V6.5 強制範圍內：

1. IPI 拆分為 Market Inflation Impulse 與 Realized Inflation Pressure。
2. CPI / Core CPI / PCE / Core PCE 改用 YoY 或 3M/6M annualized。
3. 顯示各 macro component 的實際有效資料數量。
4. 顯示因 NA 重新正規化後的 actual effective weights。
5. 新增 policy pressure / Fed hawkishness axis。

這些可列入 V6.6 或 V7.0。

---

## 20. 一句話總結

Macro Pressure Map V6.5 的核心修改是：

> 不再把總經資料權重寫死。使用者可以自由調整 GPI / IPI 的 market vs macro 權重，以及 FCPI 的 market stress vs official FCI 權重。

這讓指標可以更好地校準不同歷史情境，尤其是 2022 這類「市場通膨動能降溫，但實際通膨壓力仍高」的年份。
