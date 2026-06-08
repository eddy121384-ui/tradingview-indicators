# Macro Pressure Map V6.4 規格書

版本：V6.4 Multilingual Dashboard  
對應程式：`indicators/macro-pressure-map/src/macro-pressure-map-v6.4.pine`  
指標名稱：`Macro Pressure Map V6.4 [GPI/IPI/FCPI]`  
Pine Script 版本：v6  
定位：總經壓力與風險姿態儀表板，不是進出場訊號器。

---

## 1. 指標定位

Macro Pressure Map V6.4 是一個 TradingView 副圖指標，用來觀察市場正在定價的三種宏觀壓力：成長壓力、通膨壓力與金融條件壓力。

本指標的核心目的不是產生買賣訊號，而是作為上層 regime filter，用於輔助資產配置、波段交易姿態判斷、部位大小控制、追價意願控制與市場敘事審計。

核心概念是：

> Growth × Inflation 決定市場方向，Financial Conditions 決定油門與煞車。

因此，本指標不應被解讀為單一商品的 entry signal，也不應被用來取代價格結構、風險報酬比、停損與資金管理。

---

## 2. 三大壓力軸

### 2.1 GPI｜Growth Pressure Index

GPI 代表 market-implied growth pressure，也就是市場價格正在反映的成長壓力或風險偏好。

GPI > 0 代表市場偏向定價成長改善或風險承擔改善。  
GPI < 0 代表市場偏向定價成長惡化或防禦需求上升。

重要限制：GPI 不是 GDP nowcast，也不是實體經濟成長率預測。

### 2.2 IPI｜Inflation Pressure Index

IPI 代表通膨壓力軸。V6.4 的 IPI 主要由 market proxy 組成，包括 breakeven inflation、商品籃子、能源價格，以及 optional industrial metals。

IPI > 0 代表市場正在定價通膨壓力升溫。  
IPI < 0 代表市場正在定價通膨壓力降溫。

重要限制：V6.4 預設狀態下，IPI 更接近 market inflation impulse，而不是 realized inflation pressure。也就是說，它對商品與 breakeven 的轉折較敏感，但不一定等同 CPI 或 Core PCE 的實際水位。

### 2.3 FCPI｜Financial Conditions Pressure Index

FCPI 代表金融條件壓力軸。

FCPI > 0 代表金融條件變緊，信用、利率、美元或波動率壓力上升。  
FCPI < 0 代表金融條件轉鬆，市場風險承擔環境改善。

FCPI 是本指標的風控濾鏡。當 FCPI 升高時，應降低追價意願、槓桿與風險預算；當 FCPI 下降時，代表金融環境較有利於風險承擔。

---

## 3. 資料架構

V6.4 的資料分為四層：

1. Market proxy：每日市場價格資料，預設啟用。
2. Macro confirmation：總經確認資料，預設關閉。
3. Official financial conditions：官方金融條件資料，預設關閉。
4. Optional add-ons：T5YIE、Industrial Metals、KRE/SPY stress add-on 等，預設關閉。

所有 symbol 都使用 `input.string()`，讓使用者可以手動修改 TradingView 商品代碼。這是為了避免 `input.symbol()` 在部分資料源無效時造成指標初始化失敗。

所有 `request.security()` 都在主體層級呼叫，分數計算函數只接收已抓取的 series。這是本版的穩定性原則。

---

## 4. GPI 組件

GPI market proxy 使用以下五個相對價格或比率：

- `IWM / SPY`：小型股相對大型股。
- `RSP / SPY`：等權重 S&P 500 相對市值權重 S&P 500。
- `XLY / XLP`：可選消費相對必需消費。
- `XLI / XLU`：工業股相對公用事業。
- `Copper / Gold`：銅金比。

這些組件預設等權平均成 `gpiMarket`。

若 `Use Economic Data` 開啟，則加入 `gpiMacro`，目前包括：

- PMI / ISM Proxy。
- CFNAI。
- Building Permits。
- Initial Jobless Claims，反向處理。
- Unemployment Rate，反向處理。

V6.4 的合成權重固定為：

```pine
GPI = useMacroData ? f_wavg2(gpiMarket, 0.70, gpiMacro, 0.30) : gpiMarket
```

因此目前總經資料只能開關，不能自由調整 70/30 權重。

---

## 5. IPI 組件

IPI market proxy 由以下組件組成：

- Breakeven Pressure：預設使用 10Y breakeven，可選擇加入 5Y breakeven。
- Commodity Basket：預設使用 DBC。
- Energy Pressure：由 crude oil 與 gasoline 平均。
- Industrial Metals：optional，預設關閉。

預設權重：

- Breakeven Pressure：0.35。
- Commodity Basket：0.40。
- Energy Pressure：0.25。
- Industrial Metals optional：0.10。

如果 `Use Industrial Metals in IPI` 關閉，IPI market 使用前三者加權平均。若開啟，會加入 industrial metals optional。

若 `Use Economic Data` 開啟，則加入 `ipiMacro`，目前包括：

- CPI。
- Core CPI。
- PCE Price Index。
- Core PCE。
- PPI。
- Average Hourly Earnings proxy。

V6.4 的合成權重固定為：

```pine
IPI = useMacroData ? f_wavg2(ipiMarket, 0.70, ipiMacro, 0.30) : ipiMarket
```

重要限制：V6.4 仍未把 IPI 拆成 market inflation impulse 與 realized inflation pressure，因此 2022 這類年份可能出現「市場通膨動能降溫，但實際通膨仍高」的語義落差。此項應列入 V6.5 後續修正。

---

## 6. FCPI 組件

FCPI 先拆成三個 sub-index，再合成總分。

### 6.1 Credit Stress

Credit Stress 包括：

- HY OAS。
- HYG / IEF，反向處理。
- KRE / SPY optional stress add-on，反向處理，預設關閉。

若 KRE optional 關閉，Credit Stress 使用 HY OAS 與 HYG/IEF reversed 平均。

若 KRE optional 開啟，權重為：

- HY OAS：0.45。
- HYG/IEF reversed：0.45。
- KRE/SPY reversed：0.10。

### 6.2 Rates / Dollar Constraint

Rates / Dollar Constraint 包括：

- 10Y real yield。
- DXY。

兩者等權平均。

### 6.3 Volatility Shock

Volatility Shock 包括：

- VIX。
- MOVE。

兩者等權平均。

### 6.4 FCPI market 合成

FCPI market 權重可自由調整：

```pine
wCreditStress = input.float(0.40)
wRatesDollar  = input.float(0.35)
wVolShock     = input.float(0.25)
```

合成公式：

```pine
fcpiMarket = f_wavg3(CreditStress, wCreditStress, RatesDollarConstraint, wRatesDollar, VolatilityShock, wVolShock)
```

若 `Use Official Financial Conditions Data` 開啟，則加入 official FCI：

- NFCI。
- STLFSI4。

V6.4 的 official FCI 合成權重固定為：

```pine
FCPI = useOfficialFCI ? f_wavg2(fcpiMarket, 0.80, fcpiOfficial, 0.20) : fcpiMarket
```

因此目前 official FCI 只能開關，不能自由調整 80/20 權重。

---

## 7. 標準化方法

所有 component 都使用同一套 `f_componentScore()`：

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

由於 Pine Script 不支援 `math.tanh()`，V6.4 使用自訂 `f_tanh()`，以 `math.exp()` 實作並限制極端值。

---

## 8. 視覺化設計

V6.4 必須保留雙層視覺架構：

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

使用者可以選擇是否平滑主線：

```pine
useSmoothing = input.bool(true)
smoothLen = input.int(5)
```

如果平滑開啟，主線使用 EMA 平滑；如果關閉，顯示 raw score。

FCPI 同時用背景色提示金融條件狀態，但背景不可取代 FCPI 線本身。

---

## 9. Dashboard 功能

Dashboard 顯示：

- GPI。
- IPI。
- FCPI。
- Quadrant。
- Risk Posture。
- FC State。
- Credit Stress。
- Rates / Dollar。
- Vol Shock。
- Data Mode。
- Official FCI。
- Diagnostics。
- Sentence。

V6.4 支援四種 dashboard 語言：

- English。
- 中文。
- 日本語。
- 한국어。

V6.4 也支援 dashboard 外觀自訂：

- 文字大小。
- 文字顏色。
- 標題背景。
- 左欄背景。
- 一般儲存格背景。
- 中性背景。
- Risk-on / positive 背景。
- Caution 背景。
- Stress 背景。
- Negative 背景。
- IPI 背景。
- Symbol Health OK / NA 背景。

---

## 10. Diagnostics 模式

V6.4 的 diagnostics group 包括：

- Main。
- GPI。
- IPI。
- FCPI。
- Symbols。

Main 顯示 GPI / IPI / FCPI 三條主線。

GPI 顯示 GPI 底層組件。

IPI 顯示 IPI 底層組件。

FCPI 顯示 FCPI sub-index 與底層組件。

Symbols 顯示 Symbol Health dashboard，用於檢查 TradingView 商品代碼是否可用。

Symbol Health 以 OK / NA 顯示每個資料源是否成功抓到資料。NA 可能代表商品代碼錯誤、資料不可用、資料權限不足，或 TradingView 當前資料源不支援。

---

## 11. Regime 判斷

GPI / IPI 使用 threshold 判斷象限：

```pine
growthThreshold = 10
inflationThreshold = 10
```

基本象限：

- GPI > +10 且 IPI < -10：Goldilocks / Disinflationary Expansion。
- GPI > +10 且 IPI > +10：Reflation / Overheating Risk。
- GPI < -10 且 IPI < -10：Slowdown / Disinflation。
- GPI < -10 且 IPI > +10：Stagflation Pressure。
- 其他：Mixed / Transition。

FCPI 使用 threshold 判斷金融條件：

```pine
fcThreshold = 30
stressThreshold = 60
```

- FCPI > +60：Stress rising / Defensive posture。
- FCPI > +30：Conditions tightening / Risk budget reduced。
- FCPI < -30：Conditions easing / Risk-on allowed。
- 其他：Neutral conditions / Standard risk budget。

---

## 12. V6.4 已知限制

1. `Use Economic Data` 目前只有開關，GPI / IPI 的 market / macro 權重固定為 70/30。
2. `Use Official Financial Conditions Data` 目前只有開關，FCPI market / official 權重固定為 80/20。
3. IPI 尚未拆分為 market inflation impulse 與 realized inflation pressure。
4. CPI、Core CPI、PCE、Core PCE 目前以指數 series 進行 component score，尚未改成 YoY、3M annualized 或 6M annualized。
5. TradingView 的 FRED 與官方資料源可能因資料權限、symbol 名稱、頻率或地區限制出現 NA。
6. V6.4 不是 entry signal，不應作為單獨買賣依據。

---

## 13. V6.5 建議方向

下一版建議優先處理：

1. 新增 GPI market / macro 權重 input。
2. 新增 IPI market / macro 權重 input。
3. 新增 FCPI market / official 權重 input。
4. 將 IPI 拆成 Market Inflation Impulse 與 Realized Inflation Pressure。
5. Realized inflation 使用 YoY、3M annualized 或 6M annualized，而不是直接使用 CPI 指數水位。
6. Dashboard 顯示實際可用總經資料數量，例如 `Macro data: 8/11 available`。
7. Dashboard 顯示目前總經資料是否實際進入計算，而不是只顯示開關狀態。

---

## 14. 使用原則

Macro Pressure Map V6.4 應用於：

- 日線與週線資產配置濾鏡。
- 4H / 1D 波段交易上層 regime filter。
- 部位大小調整。
- 追價意願控制。
- 晨報中的市場姿態定位。

不建議用於：

- 單獨產生買賣訊號。
- 1 分鐘或 5 分鐘短線進出場。
- 無視價格結構直接交易。
- 把 GPI 誤認為 GDP。
- 把 IPI 誤認為完整 realized inflation。
- 把 FCPI 高檔誤認為市場一定立刻崩跌。

---

## 15. 一句話總結

Macro Pressure Map V6.4 的功能不是預測市場，而是提醒使用者：市場目前交易的是什麼宏觀敘事，以及這個敘事所處的金融條件是否允許承擔風險。
