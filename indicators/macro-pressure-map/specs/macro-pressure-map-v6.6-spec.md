# Macro Pressure Map V6.6 規格書

版本：V6.6 Tiered Growth / Inflation States  
對應程式：`indicators/macro-pressure-map/src/macro-pressure-map-v6.6.pine`  
前版規格：`indicators/macro-pressure-map/specs/macro-pressure-map-v6.5-spec.md`  
前版程式：`indicators/macro-pressure-map/src/macro-pressure-map-v6.5.pine`  
指標名稱建議：`Macro Pressure Map V6.6 [Tiered GPI/IPI/FCPI]`  
Pine Script 版本：v6  
定位：總經壓力與風險姿態儀表板，不是進出場訊號器。

---

## 1. V6.6 修正目標

V6.6 的主要目標，是修正 V6.5 以前 regime 分類過於粗糙的問題。

V6.5 以前的 Growth × Inflation 判斷主要是四象限：

```text
GPI > +10 且 IPI < -10：Goldilocks / Disinflationary Expansion
GPI > +10 且 IPI > +10：Reflation / Overheating Risk
GPI < -10 且 IPI < -10：Slowdown / Disinflation
GPI < -10 且 IPI > +10：Stagflation Pressure
其他：Mixed / Transition
```

這個設計有兩個問題：

1. `Mixed / Transition` 過大，會把「成長溫和、通膨穩定」這類重要且正常的市場狀態錯誤歸類成混合期。
2. `GPI > +10 且 IPI > +10` 直接命名為 `Reflation / Overheating Risk` 太重，因為 reflation 不一定等於 overheating。

V6.6 必須把 GPI / IPI 改成類似 FCPI 的兩段式門檻：

- 第一層：方向成立，偏溫和或需注意。
- 第二層：壓力過強，進入過熱、衝擊或嚴重風險。

核心原則：

> 底層分層更細，dashboard 表層仍保持簡潔，不製造 25 格總經占星盤。

---

## 2. 延續 V6.5 的內容

V6.6 必須完整延續 V6.5 的可調權重設計。

以下 input 必須保留：

```pine
wGpiMarket = input.float(0.70, "GPI Weight: Market Proxy", minval=0.0, maxval=1.0, step=0.05, group=groupWeights)
wGpiMacro = input.float(0.30, "GPI Weight: Macro Confirmation", minval=0.0, maxval=1.0, step=0.05, group=groupWeights)
wIpiMarket = input.float(0.70, "IPI Weight: Market Proxy", minval=0.0, maxval=1.0, step=0.05, group=groupWeights)
wIpiMacro = input.float(0.30, "IPI Weight: Macro Confirmation", minval=0.0, maxval=1.0, step=0.05, group=groupWeights)
wFcpiMarket = input.float(0.80, "FCPI Weight: Market Stress", minval=0.0, maxval=1.0, step=0.05, group=groupWeights)
wFcpiOfficial = input.float(0.20, "FCPI Weight: Official FCI", minval=0.0, maxval=1.0, step=0.05, group=groupWeights)
```

合成公式仍為：

```pine
GPI = useMacroData ? f_wavg2(gpiMarket, wGpiMarket, gpiMacro, wGpiMacro) : gpiMarket
IPI = useMacroData ? f_wavg2(ipiMarket, wIpiMarket, ipiMacro, wIpiMacro) : ipiMarket
FCPI = useOfficialFCI ? f_wavg2(fcpiMarket, wFcpiMarket, fcpiOfficial, wFcpiOfficial) : fcpiMarket
```

V6.6 不應回到 V6.4 的固定 70/30 或 80/20。

---

## 3. 新增兩段式門檻

V6.6 必須保留原本的 mild threshold，並新增 GPI / IPI 的 extreme threshold。

### 3.1 既有 mild thresholds

```pine
growthThreshold = input.float(10.0, "Growth Threshold", step=1.0, group=groupCore)
inflationThreshold = input.float(10.0, "Inflation Threshold", step=1.0, group=groupCore)
fcThreshold = input.float(30.0, "Financial Conditions Threshold", step=1.0, group=groupCore)
stressThreshold = input.float(60.0, "Stress Threshold", step=1.0, group=groupCore)
```

語意：

- `growthThreshold`：GPI 第一層方向門檻。
- `inflationThreshold`：IPI 第一層方向門檻。
- `fcThreshold`：FCPI 第一層金融條件警戒門檻。
- `stressThreshold`：FCPI 第二層金融壓力危險門檻。

### 3.2 新增 GPI / IPI extreme thresholds

```pine
growthExtremeThreshold = input.float(60.0, "Growth Extreme Threshold", step=1.0, group=groupCore)
inflationExtremeThreshold = input.float(60.0, "Inflation Extreme Threshold", step=1.0, group=groupCore)
```

語意：

- `growthExtremeThreshold`：GPI 第二層門檻，用於判斷成長敘事或風險偏好是否過度亢奮，或下方是否進入嚴重成長壓力。
- `inflationExtremeThreshold`：IPI 第二層門檻，用於判斷通膨壓力是否進入衝擊區，或下方是否進入通縮 / 需求破壞風險。

預設值先設為 60，與 FCPI 的 `stressThreshold` 保持語意對稱。

---

## 4. GPI 五段狀態

V6.6 的 GPI 不再只有 growth improving / weakening / mixed，而是分成五段。

| 條件 | 英文狀態 | 中文狀態 | 語意 |
|---|---|---|---|
| `GPI >= +growthExtremeThreshold` | Growth Euphoria / Overextension Risk | 成長亢奮 / 風險偏好過熱 | 市場成長敘事或風險偏好過強，可能有過度外推風險 |
| `GPI > +growthThreshold` | Mild Growth / Expansion | 溫和成長 / 擴張 | 成長敘事改善，但尚未達過熱 |
| `-growthThreshold <= GPI <= +growthThreshold` | Growth Neutral | 成長中性 | 成長訊號不明顯，偏中性或雜訊區 |
| `GPI < -growthThreshold` | Mild Slowdown | 溫和放緩 | 成長敘事轉弱，但尚未達嚴重壓力 |
| `GPI <= -growthExtremeThreshold` | Severe Slowdown / Contraction Risk | 嚴重放緩 / 收縮風險 | 成長壓力嚴重，可能接近衰退或需求快速轉弱 |

注意：GPI 是 market-implied growth pressure，不是真實 GDP。因此 `Growth Euphoria` 不代表官方經濟成長率一定過熱，而是代表市場價格反映的成長與風險偏好過度強烈。

---

## 5. IPI 五段狀態

V6.6 的 IPI 不再只有 inflation rising / cooling / mixed，而是分成五段。

| 條件 | 英文狀態 | 中文狀態 | 語意 |
|---|---|---|---|
| `IPI >= +inflationExtremeThreshold` | Inflation Shock / Severe Inflation Pressure | 通膨衝擊 / 嚴重通膨壓力 | 通膨壓力或市場通膨動能非常強 |
| `IPI > +inflationThreshold` | Mild Inflation / Inflation Rising | 溫和通膨 / 通膨升溫 | 通膨壓力升溫，但尚未達嚴重衝擊 |
| `-inflationThreshold <= IPI <= +inflationThreshold` | Stable Inflation | 通膨穩定 | 通膨壓力不明顯，偏穩定或中性 |
| `IPI < -inflationThreshold` | Disinflation / Inflation Cooling | 通膨降溫 | 通膨壓力下降 |
| `IPI <= -inflationExtremeThreshold` | Deflation Pressure / Demand Destruction Risk | 通縮壓力 / 需求破壞風險 | 通膨壓力急降，可能反映需求破壞或通縮風險 |

注意：V6.6 仍沿用 V6.5 的 IPI 架構，尚未強制拆分 Market Inflation Impulse 與 Realized Inflation Pressure。因此 `Inflation Shock` 在本版語意上仍偏向「市場通膨壓力或商品 / breakeven 衝擊」，不必然等同 realized CPI 爆表。

---

## 6. FCPI 五段狀態

V6.6 的 FCPI 可沿用既有兩段式架構，但 dashboard 建議也用五段語意呈現。

| 條件 | 英文狀態 | 中文狀態 | 語意 |
|---|---|---|---|
| `FCPI >= +stressThreshold` | Financial Stress | 金融壓力升高 | 金融壓力進入危險區，防禦姿態 |
| `FCPI > +fcThreshold` | Conditions Tightening | 金融條件轉緊 | 風險預算降低，避免追價或加槓桿 |
| `-fcThreshold <= FCPI <= +fcThreshold` | Neutral Conditions | 金融條件中性 | 正常風險預算 |
| `FCPI < -fcThreshold` | Conditions Easing | 金融條件轉鬆 | risk-on 環境較友善 |
| `FCPI <= -stressThreshold` | Very Loose Conditions | 金融條件極度寬鬆 | 流動性非常友善，但也可能暗示市場樂觀過度 |

V6.6 不一定要把 `FCPI <= -stressThreshold` 作為強警報，但可以在 dashboard 中顯示為 `Very Loose Conditions`。

---

## 7. 不採用完整 25 格 regime 表

V6.6 不應建立完整 5 × 5 的 Growth × Inflation regime 命名表。

理由：

1. 25 種命名會造成假精密感。
2. dashboard 會過度複雜，交易時不易閱讀。
3. 很多邊界狀態沒有穩定的經濟語意，硬命名反而誤導。

V6.6 採用：

1. GPI State：單獨顯示成長軸五段狀態。
2. IPI State：單獨顯示通膨軸五段狀態。
3. FCPI State：單獨顯示金融條件五段狀態。
4. Core Regime：仍用簡潔 3 × 3 regime 命名。
5. Regime Sentence：用一句自然語言整合三軸狀態。

---

## 8. Core Regime 改為 3 × 3

V6.6 的 Core Regime 使用 GPI / IPI 的 mild threshold 形成 3 × 3。

### 8.1 Growth 狀態

```pine
growthPositive = GPI > growthThreshold
growthNeutral = GPI <= growthThreshold and GPI >= -growthThreshold
growthNegative = GPI < -growthThreshold
```

### 8.2 Inflation 狀態

```pine
inflationPositive = IPI > inflationThreshold
inflationNeutral = IPI <= inflationThreshold and IPI >= -inflationThreshold
inflationNegative = IPI < -inflationThreshold
```

### 8.3 3 × 3 regime 命名

| Growth / Inflation | Inflation Cooling | Stable Inflation | Inflation Rising |
|---|---|---|---|
| Growth Improving | Goldilocks / Disinflationary Expansion | Benign Expansion / Stable Inflation | Reflation / Inflation Rising |
| Growth Neutral | Disinflationary Drift | Neutral / Range-bound Macro | Inflation Pressure without Growth Confirmation |
| Growth Weakening | Slowdown / Disinflation | Growth Slowdown / Stable Inflation | Stagflation Pressure |

中文建議：

| 成長 / 通膨 | 通膨降溫 | 通膨穩定 | 通膨升溫 |
|---|---|---|---|
| 成長改善 | 金髮女孩 / 去通膨擴張 | 溫和擴張 / 通膨穩定 | 再通膨 / 通膨升溫 |
| 成長中性 | 去通膨漂移 | 中性 / 區間總經 | 缺乏成長確認的通膨壓力 |
| 成長轉弱 | 成長放緩 / 通膨降溫 | 成長放緩 / 通膨穩定 | 滯脹壓力 |

---

## 9. Extreme Overlay 規則

V6.6 的 extreme threshold 不直接創造 25 格 regime，而是作為 overlay 修飾 core regime。

### 9.1 Overheating Risk

若：

```pine
GPI >= growthExtremeThreshold and IPI >= inflationThreshold
```

或：

```pine
GPI > growthThreshold and IPI >= inflationExtremeThreshold
```

則在 regime sentence 或 risk note 中加入：

```text
Overheating risk rising.
```

中文：

```text
過熱風險升高。
```

### 9.2 Inflation Shock without Growth Support

若：

```pine
IPI >= inflationExtremeThreshold and GPI <= growthThreshold
```

則提示：

```text
Inflation shock without strong growth confirmation.
```

中文：

```text
通膨衝擊缺乏強成長支撐。
```

### 9.3 Severe Slowdown Risk

若：

```pine
GPI <= -growthExtremeThreshold
```

則提示：

```text
Severe growth slowdown risk.
```

中文：

```text
嚴重成長放緩風險。
```

### 9.4 Deflation / Demand Destruction Risk

若：

```pine
IPI <= -inflationExtremeThreshold
```

則提示：

```text
Deflation or demand destruction risk.
```

中文：

```text
通縮或需求破壞風險。
```

### 9.5 Financial Stress Overlay

若：

```pine
FCPI >= stressThreshold
```

則不論 core regime 為何，都必須加入金融壓力提示：

```text
Financial stress overrides risk appetite.
```

中文：

```text
金融壓力壓過風險偏好。
```

---

## 10. Dashboard 必須新增 / 調整的內容

V6.6 dashboard 必須新增或調整以下 rows：

- `GPI State`：顯示 GPI 五段狀態。
- `IPI State`：顯示 IPI 五段狀態。
- `FCPI State`：顯示 FCPI 五段狀態。
- `Core Regime`：顯示 3 × 3 regime。
- `Risk Note`：顯示 extreme overlay 或金融壓力提示。

V6.5 已有的權重 rows 必須保留：

- `GPI Wgt`。
- `IPI Wgt`。
- `FCPI Wgt`。

原本的 `Quadrant` 可以改名為 `Core Regime`，避免四象限語意殘留。

原本的 `Sentence` 可以保留，但內容要改成三軸整合句，而不是只說 growth improving / inflation rising / FC state。

---

## 11. Dashboard 四語系需求

V6.6 必須延續四語系：

- English。
- 中文。
- 日本語。
- 한국어。

新增 label 必須完整翻譯，不可只顯示英文。

建議新增 label：

```pine
lblGpiState = f_lang("GPI State", "GPI 狀態", "GPI 状態", "GPI 상태")
lblIpiState = f_lang("IPI State", "IPI 狀態", "IPI 状態", "IPI 상태")
lblFcpiState = f_lang("FCPI State", "FCPI 狀態", "FCPI 状態", "FCPI 상태")
lblCoreRegime = f_lang("Core Regime", "核心情境", "コア局面", "핵심 국면")
lblRiskNote = f_lang("Risk Note", "風險提示", "リスク注記", "위험 메모")
```

狀態文字也必須四語系化。

---

## 12. 建議新增狀態函數

### 12.1 GPI 狀態函數

```pine
f_gpiState(v) =>
    na(v) ? f_lang("n/a", "n/a", "n/a", "n/a") :
     v >= growthExtremeThreshold ? f_lang("Growth Euphoria", "成長亢奮", "成長過熱", "성장 과열") :
     v > growthThreshold ? f_lang("Mild Growth", "溫和成長", "緩やかな成長", "완만한 성장") :
     v <= -growthExtremeThreshold ? f_lang("Severe Slowdown", "嚴重放緩", "深刻な減速", "심각한 둔화") :
     v < -growthThreshold ? f_lang("Mild Slowdown", "溫和放緩", "緩やかな減速", "완만한 둔화") :
     f_lang("Growth Neutral", "成長中性", "成長中立", "성장 중립")
```

### 12.2 IPI 狀態函數

```pine
f_ipiState(v) =>
    na(v) ? f_lang("n/a", "n/a", "n/a", "n/a") :
     v >= inflationExtremeThreshold ? f_lang("Inflation Shock", "通膨衝擊", "インフレショック", "인플레 충격") :
     v > inflationThreshold ? f_lang("Inflation Rising", "通膨升溫", "インフレ上昇", "인플레 상승") :
     v <= -inflationExtremeThreshold ? f_lang("Deflation Pressure", "通縮壓力", "デフレ圧力", "디플레 압력") :
     v < -inflationThreshold ? f_lang("Inflation Cooling", "通膨降溫", "インフレ低下", "인플레 둔화") :
     f_lang("Stable Inflation", "通膨穩定", "インフレ安定", "인플레 안정")
```

### 12.3 FCPI 狀態函數

```pine
f_fcpiState(v) =>
    na(v) ? f_lang("n/a", "n/a", "n/a", "n/a") :
     v >= stressThreshold ? f_lang("Financial Stress", "金融壓力升高", "金融ストレス", "금융 스트레스") :
     v > fcThreshold ? f_lang("Conditions Tightening", "金融條件轉緊", "金融環境引き締まり", "금융 여건 긴축") :
     v <= -stressThreshold ? f_lang("Very Loose Conditions", "金融條件極度寬鬆", "金融環境極度緩和", "금융 여건 매우 완화") :
     v < -fcThreshold ? f_lang("Conditions Easing", "金融條件轉鬆", "金融環境緩和", "금융 여건 완화") :
     f_lang("Neutral Conditions", "金融條件中性", "金融環境中立", "금융 여건 중립")
```

---

## 13. 建議新增 Core Regime 函數

V6.6 應新增 `coreRegime`，使用 3 × 3 判斷。

```pine
f_coreRegime() =>
    growthPositive and inflationNegative ? f_lang("Goldilocks / Disinflationary Expansion", "金髮女孩 / 去通膨擴張", "ゴルディロックス / ディスインフレ型拡大", "골디락스 / 디스인플레이션 확장") :
    growthPositive and inflationNeutral ? f_lang("Benign Expansion / Stable Inflation", "溫和擴張 / 通膨穩定", "穏やかな拡大 / インフレ安定", "완만한 확장 / 인플레 안정") :
    growthPositive and inflationPositive ? f_lang("Reflation / Inflation Rising", "再通膨 / 通膨升溫", "リフレ / インフレ上昇", "리플레이션 / 인플레 상승") :
    growthNeutral and inflationNegative ? f_lang("Disinflationary Drift", "去通膨漂移", "ディスインフレ傾向", "디스인플레이션 흐름") :
    growthNeutral and inflationNeutral ? f_lang("Neutral / Range-bound Macro", "中性 / 區間總經", "中立 / レンジ型マクロ", "중립 / 박스권 매크로") :
    growthNeutral and inflationPositive ? f_lang("Inflation Pressure without Growth Confirmation", "缺乏成長確認的通膨壓力", "成長確認なきインフレ圧力", "성장 확인 없는 인플레 압력") :
    growthNegative and inflationNegative ? f_lang("Slowdown / Disinflation", "成長放緩 / 通膨降溫", "景気減速 / ディスインフレ", "둔화 / 디스인플레이션") :
    growthNegative and inflationNeutral ? f_lang("Growth Slowdown / Stable Inflation", "成長放緩 / 通膨穩定", "景気減速 / インフレ安定", "성장 둔화 / 인플레 안정") :
    f_lang("Stagflation Pressure", "滯脹壓力", "スタグフレーション圧力", "스태그플레이션 압력")
```

---

## 14. 建議新增 Risk Note 函數

Risk Note 應簡潔，不要堆太多文字。若多個 overlay 同時觸發，優先序如下：

1. Financial Stress。
2. Inflation Shock without Growth Support。
3. Overheating Risk。
4. Severe Slowdown Risk。
5. Deflation / Demand Destruction Risk。
6. No major overlay。

```pine
riskNote = FCPI >= stressThreshold ? f_lang("Financial stress overrides risk appetite", "金融壓力壓過風險偏好", "金融ストレスがリスク選好を上回る", "금융 스트레스가 위험 선호를 압도") :
     IPI >= inflationExtremeThreshold and GPI <= growthThreshold ? f_lang("Inflation shock without strong growth confirmation", "通膨衝擊缺乏強成長支撐", "強い成長確認なきインフレショック", "강한 성장 확인 없는 인플레 충격") :
     (GPI >= growthExtremeThreshold and IPI >= inflationThreshold) or (GPI > growthThreshold and IPI >= inflationExtremeThreshold) ? f_lang("Overheating risk rising", "過熱風險升高", "過熱リスク上昇", "과열 위험 상승") :
     GPI <= -growthExtremeThreshold ? f_lang("Severe growth slowdown risk", "嚴重成長放緩風險", "深刻な景気減速リスク", "심각한 성장 둔화 위험") :
     IPI <= -inflationExtremeThreshold ? f_lang("Deflation or demand destruction risk", "通縮或需求破壞風險", "デフレまたは需要破壊リスク", "디플레 또는 수요 파괴 위험") :
     f_lang("No major overlay", "無重大額外警示", "重大な追加警戒なし", "중대한 추가 경고 없음")
```

---

## 15. Regime Sentence 建議

V6.6 的 sentence 應改成由三軸狀態 + core regime + risk note 組成，但不要太長。

英文範例：

```text
Benign Expansion / Stable Inflation: Mild Growth, Stable Inflation, Neutral Conditions. No major overlay.
```

中文範例：

```text
溫和擴張 / 通膨穩定：溫和成長、通膨穩定、金融條件中性。無重大額外警示。
```

當極端 overlay 觸發時：

```text
Reflation / Inflation Rising: Growth Euphoria, Inflation Rising, Conditions Tightening. Overheating risk rising.
```

中文：

```text
再通膨 / 通膨升溫：成長亢奮、通膨升溫、金融條件轉緊。過熱風險升高。
```

---

## 16. 顏色建議

V6.6 不必新增大量顏色 input，以免設定面板過度膨脹。

建議沿用 V6.5 既有 dashboard 顏色：

- Positive / risk-on background。
- Caution background。
- Stress background。
- Negative background。
- Neutral background。
- IPI background。

但各狀態可依語意套用：

- Growth Euphoria：Caution background。
- Mild Growth：Risk-on / Positive background。
- Growth Neutral：Neutral background。
- Mild Slowdown：Negative background。
- Severe Slowdown：Stress background。
- Inflation Shock：Stress background。
- Inflation Rising：IPI background 或 Caution background。
- Stable Inflation：Neutral background。
- Inflation Cooling：Risk-on / Positive 或 Neutral background。
- Deflation Pressure：Stress background。

---

## 17. V6.6 程式修改清單

相對 V6.5，V6.6 程式至少需要做以下修改。

### 17.1 新增 input

```pine
growthExtremeThreshold = input.float(60.0, "Growth Extreme Threshold", step=1.0, group=groupCore)
inflationExtremeThreshold = input.float(60.0, "Inflation Extreme Threshold", step=1.0, group=groupCore)
```

### 17.2 新增三軸五段狀態

新增：

- `gpiState`
- `ipiState`
- `fcpiState`

### 17.3 修改 core regime

把原本四象限 `quadrant` 改成 3 × 3 `coreRegime`。

原本 `Mixed / Transition` 不應再作為大範圍 fallback。只有資料為 `na` 或真的無法判斷時，才可顯示 `n/a` 或 `Transition`。

### 17.4 新增 risk note

新增 `riskNote`，用 extreme overlay 與 financial stress overlay 產生簡短警示。

### 17.5 Dashboard 修改

新增 rows：

- GPI State。
- IPI State。
- FCPI State。
- Core Regime。
- Risk Note。

保留 rows：

- GPI。
- IPI。
- FCPI。
- Credit Stress。
- Rates / Dollar。
- Vol Shock。
- Data Mode。
- Official FCI。
- GPI Wgt。
- IPI Wgt。
- FCPI Wgt。
- Diagnostics。
- Sentence。

---

## 18. V6.6 驗收標準

完成 V6.6 程式後，至少需檢查以下項目。

1. 當 `GPI > growthThreshold` 且 `IPI` 介於 `-inflationThreshold` 與 `+inflationThreshold` 時，core regime 應顯示 `Benign Expansion / Stable Inflation`，不可顯示 `Mixed / Transition`。
2. 當 `GPI > growthThreshold` 且 `IPI > inflationThreshold` 時，core regime 應顯示 `Reflation / Inflation Rising`，不可直接寫死為 `Overheating Risk`。
3. 只有 extreme overlay 觸發時，才應顯示 `Overheating risk rising`。
4. 當 `GPI >= growthExtremeThreshold` 時，GPI State 應顯示 Growth Euphoria / 成長亢奮。
5. 當 `IPI >= inflationExtremeThreshold` 時，IPI State 應顯示 Inflation Shock / 通膨衝擊。
6. 當 `GPI <= -growthExtremeThreshold` 時，GPI State 應顯示 Severe Slowdown / 嚴重放緩。
7. 當 `IPI <= -inflationExtremeThreshold` 時，IPI State 應顯示 Deflation Pressure / 通縮壓力。
8. 當 `FCPI >= stressThreshold` 時，risk note 必須優先顯示金融壓力相關警示。
9. Dashboard 四語系切換時，新增 rows 不可出現未翻譯的英文殘留。
10. V6.5 的可調權重功能必須完全保留。
11. Symbol Health 模式必須正常保留。
12. 若 GPI / IPI / FCPI 為 `na`，dashboard 不應報錯，應顯示 `n/a` 或中性提示。

---

## 19. V6.6 已知仍未處理事項

V6.6 只處理 GPI / IPI 的兩段式門檻與 regime 語意細化。

以下事項暫不列入 V6.6 強制範圍：

1. IPI 拆分為 Market Inflation Impulse 與 Realized Inflation Pressure。
2. CPI / Core CPI / PCE / Core PCE 改用 YoY 或 3M/6M annualized。
3. 顯示各 macro component 的實際有效資料數量。
4. 顯示因 NA 重新正規化後的 actual effective weights。
5. 新增 policy pressure / Fed hawkishness axis。
6. 將 GPI 的 Growth Euphoria 拆成基本面成長過熱與風險偏好過熱。

這些可列入 V6.7 或 V7.0。

---

## 20. 一句話總結

Macro Pressure Map V6.6 的核心修改是：

> GPI / IPI 不再只有單一方向門檻，而是改成兩段式門檻：第一層辨認溫和方向，第二層辨認過熱、衝擊或嚴重下行情境。

但 V6.6 不把 dashboard 做成 25 格分類表，而是採用：

> 三軸五段狀態 + 3 × 3 core regime + extreme risk overlay。

這樣可以保留交易員需要的語意細節，又避免指標變成複雜但不可讀的總經占星盤。
