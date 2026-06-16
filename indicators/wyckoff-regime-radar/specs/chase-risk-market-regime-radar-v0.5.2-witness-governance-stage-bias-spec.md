# Chase Risk Market Regime Radar v0.5.2｜Witness Governance / MTF Robustness / Stage Bias Spec

> 本文件是 v0.5.1 之後的下一版 patch spec。  
> 目的：把 Volume / MTF / Divergence 三個 witness layer 的角色統一管理，修正 MTF 經常顯示資料不足的可觀測性問題，並開放一個受控的 Stage Bias Mode，讓 MTF 與 strict divergence 在特定模式下可以小幅影響階段分數與底色。

---

## 0. 一句話定位

v0.5.2 不是重寫威科夫主模型，而是補上三件事：

```text
1. MTF 資料不足時，要知道為什麼不足。
2. Volume / MTF / Divergence 都要放進同一套 witness 權重治理。
3. 允許 MTF 與 strict divergence 在受控模式下進入階段分數，但不能讓 witness 接管主模型。
```

---

## 1. 背景問題

### 1.1 MTF 經常顯示資料不足

在 TVC 利率、指數、總經資料、部分沒有完整 intraday history 的商品上，`request.security_lower_tf()` 可能回傳空陣列或低於最低有效根數。

目前 Dashboard 只顯示：

```text
資料不足 / TF 不適用
```

但使用者不知道是：

- lower timeframe 選太高 / 太低。
- 主商品沒有足夠 intraday 資料。
- 低週期 array 數量不足。
- effort 計算為 `na`。
- 當前圖表週期與 lower TF 不相容。

v0.5.2 必須讓 MTF layer 說人話，而不是只顯示資料不足。

### 1.2 MTF 與 Divergence 的階段權重角色不一致

目前 MTF 已經可在 Auto / Force On 模式下直接進入 effective score multiplier：

```text
accMtfMult
markupMtfMult
reaccMtfMult
distMtfMult
markdownMtfMult
redistMtfMult
```

這代表 MTF 已能實際改變階段機率、主導階段與底色。

Divergence 目前主要只進：

```text
clue observation
candidate conflict
Flat Action no-chase
Pace downgrade
Dashboard / Debug / Alerts
```

v0.5.2 要整理出一套一致規則：哪些 witness 可以改分數、哪些只能改語氣、改多少、何時改。

### 1.3 背離不能變成第二個主模型

背離的價值是提醒「追價品質下降」，不是預測反轉。

因此：

```text
Strict divergence 可以小幅 stage bias。
Soft divergence 只能 clue / no-chase。
Resonance 只能 risk warning / no-chase。
```

不得讓背離在強趨勢中把底色頻繁翻成反向階段。

---

## 2. 設計總原則

### 2.1 主模型仍是 price action engine

六階段主模型仍由價格結構、趨勢、range、突破、支撐壓力、成熟度決定。

```text
Price Action / Structure = 法官
Volume / MTF / Divergence = 證人
```

Witness 可以加強或削弱信心，但不能單獨宣判。

### 2.2 Witness 不得單獨創造 formal regime

若 price-only effective score 不足、top gap 不足、candidate 不成立，witness 不得單獨產生正式階段。

允許：

```text
price model 已有候選方向時，witness 小幅增強 / 降低對應階段權重。
```

不允許：

```text
price model 混沌，但 divergence 單獨把階段改成派發或吸籌。
```

### 2.3 三種模式

v0.5.2 新增一個總控概念：

```text
Witness Stage Bias Mode
```

三種模式：

```text
Conservative｜保守
Balanced｜平衡
Aggressive｜積極
```

語意：

- Conservative：witness 只顯示 / clue / conflict，不直接改階段分數。
- Balanced：MTF 可改階段分數；strict divergence 只改 conflict / no-chase。
- Aggressive：MTF 可改階段分數；strict divergence 可小幅改階段分數；soft / resonance 仍不得直接改階段分數。

預設建議：

```text
Balanced
```

---

## 3. 新增 / 調整 Inputs

### 3.1 新增 Witness Governance Group

```pine
groupWitness = "參數｜Witness Governance v0.5.2"
```

### 3.2 新增總控 inputs

```pine
witnessStageBiasMode = input.string("Balanced", "Witness Stage Bias Mode", options=["Conservative", "Balanced", "Aggressive"], group=groupWitness)
witnessMaxTotalWeight = input.float(25.0, "Witness 總最大權重 %", minval=0.0, maxval=50.0, step=0.5, group=groupWitness)
witnessConflictOnlyWhenNoData = input.bool(true, "資料不足時僅作線索，不改階段", group=groupWitness)
showWitnessDiagnostics = input.bool(true, "Dashboard 顯示 Witness 診斷", group=groupWitness)
```

### 3.3 MTF robustness inputs

新增於 `groupMTF`：

```pine
mtfDiagnostics = input.bool(true, "MTF Diagnostics", group=groupMTF)
mtfUseFallback = input.bool(true, "MTF Auto Fallback", group=groupMTF)
mtfFallbackTf1 = input.timeframe("120", "MTF Fallback TF 1", group=groupMTF)
mtfFallbackTf2 = input.timeframe("60", "MTF Fallback TF 2", group=groupMTF)
mtfFallbackTf3 = input.timeframe("30", "MTF Fallback TF 3", group=groupMTF)
mtfMinIntrabarsSoft = input.int(1, "MTF Soft 最低根數", minval=1, maxval=10, group=groupMTF)
```

### 3.4 Divergence stage-bias inputs

新增於 `groupDivergence`：

```pine
divStrictStageBiasMax = input.float(6.0, "Strict 背離最大階段偏移 %", minval=0.0, maxval=15.0, step=0.5, group=groupDivergence)
divSoftStageBias = input.bool(false, "Soft 背離允許改階段分數", group=groupDivergence)
```

注意：`divSoftStageBias` 預設必須是 `false`。除非後續實測非常穩定，否則 soft divergence 不應直接進階段分數。

---

## 4. MTF Data Robustness

### 4.1 MTF 原本資料成立條件

目前 MTF data ok 條件大致為：

```text
mtfEnabled
AND ltfCount >= mtfMinIntrabars
AND ltfBearEffortRaw not na
AND ltfBullEffortRaw not na
```

此條件應保留作為 strict data ok。

### 4.2 新增 soft data ok

若 `ltfCount` 未達 `mtfMinIntrabars`，但達到 `mtfMinIntrabarsSoft`，可標示為 soft usable。

```text
mtfDataStrictOk = ltfCount >= mtfMinIntrabars and effort not na
mtfDataSoftOk = ltfCount >= mtfMinIntrabarsSoft and effort not na
```

語意：

- strict ok：可正常參與 Auto / Force On。
- soft ok：只可顯示與觀察，或在 Aggressive 模式下極低權重參與。
- not ok：完全不參與。

### 4.3 Fallback TF 選擇

若 `mtfUseFallback = true`，則依序嘗試：

```text
mtfLowerTf
mtfFallbackTf1
mtfFallbackTf2
mtfFallbackTf3
```

選擇第一個 `mtfDataStrictOk` 的 TF 作為 active MTF。

若沒有 strict ok，但有 soft ok，選擇第一個 soft ok 的 TF 作為 observe-only active MTF。

若都沒有資料，MTF layer 顯示資料不足並權重為 0。

### 4.4 Pine 實作注意

Pine 無法在所有情況下動態產生任意數量的 `request.security_lower_tf()`，因此可固定呼叫最多四組：

```text
primary lower TF
fallback TF 1
fallback TF 2
fallback TF 3
```

再用條件選擇有效資料。

### 4.5 MTF diagnostics 必顯示資訊

Dashboard 或 debug row 應顯示：

```text
MTF active TF
ltfCount / mtfMinIntrabars
strict / soft / fail
fallback 是否啟用
failure reason
```

建議文字：

```text
MTF｜240｜count 0/3｜資料不足
MTF｜120｜count 2/3｜Soft觀察
MTF｜60｜count 4/3｜Auto參與
```

### 4.6 Failure reason

至少區分：

```text
MTF關閉
TF不適用
低週期根數不足
effort為na
fallback仍不足
資料可用
```

---

## 5. Witness Governance：統一權重治理

### 5.1 三個 witness layer

v0.5.2 的 witness 包含：

```text
Volume Quality Layer
MTF Effort / Result Layer
Divergence Witness Layer
```

### 5.2 Witness 權重不得無限制疊加

目前 Volume、MTF、Divergence 各自有最大權重。v0.5.2 應新增總上限：

```text
witnessMaxTotalWeight
```

總 witness 權重應做 normalization 或 cap：

```text
rawWitnessWeight = volumeWeight + mtfWeight + divWeight
witnessScale = rawWitnessWeight > witnessMaxTotalWeight ? witnessMaxTotalWeight / rawWitnessWeight : 1
```

套用後：

```text
volumeWeightNorm = volumeWeight * witnessScale
mtfWeightNorm = mtfWeight * witnessScale
divWeightNorm = divWeight * witnessScale
```

避免三個 witness 同時打滿時，把主模型推得太遠。

### 5.3 Witness 分成三種功能

每一個 witness 訊號要標明能做什麼：

```text
Display：只顯示
Conflict：影響 candidate clean / clue observation
Stage Bias：影響 effective score multiplier
```

表格：

| Witness | Display | Conflict / No-Chase | Stage Bias |
|---|---:|---:|---:|
| Volume | Yes | Yes | Auto/Force On 可 |
| MTF strict ok | Yes | Yes | Balanced/Aggressive 可 |
| MTF soft ok | Yes | Yes | Conservative/Balanced 不可；Aggressive 極低權重可 |
| Strict Divergence | Yes | Yes | Aggressive 可，小權重 |
| Soft Divergence | Yes | Yes | 預設不可 |
| Resonance | Yes | Yes | 不可作反向 stage bias |

---

## 6. MTF Stage Bias 規則

MTF 是 effort/result witness，與威科夫階段語意高度相容，因此可以直接進階段分數。

### 6.1 對應關係

```text
MTF吸收 → accEff
MTF拉升確認 → markupEff
MTF派發 → distEff
MTF崩跌確認 → markdownEff
```

次要對應：

```text
MTF吸收強、MTF派發弱 → reaccEff 小幅支援
MTF派發強、MTF吸收弱 → redistEff 小幅支援
```

### 6.2 模式限制

```text
Conservative：MTF 不改階段分數，只顯示 / conflict。
Balanced：MTF strict ok 可改階段分數。
Aggressive：MTF strict ok 正常改分數，soft ok 可極低權重改分數。
```

### 6.3 權重上限

MTF 預設最大權重仍建議 15%。

若使用 soft ok，最多只使用原本 MTF 權重的 25%。

```text
mtfSoftWeight = mtfWeightApplied × 0.25
```

---

## 7. Divergence Stage Bias 規則

### 7.1 Strict divergence 可小幅進 stage bias

只在 `witnessStageBiasMode = Aggressive` 時，strict divergence 可改階段分數。

對應：

```text
Strict 頂背離 → distEff 小幅增加，或 markupEff 小幅降權
Strict 底背離 → accEff 小幅增加，或 markdownEff 小幅降權
```

建議優先使用「小幅增加反向觀察階段」而非大幅砍原趨勢。

```text
strictBearishDiv → distDivMult
strictBullishDiv → accDivMult
```

### 7.2 Soft divergence 不直接改階段分數

Soft 高位供給觀察：

```text
只進 highClueObservation / candidateConflict / no-chase long / Pace downgrade
```

Soft 低位承接觀察：

```text
只進 lowClueObservation / candidateConflict / no-chase short / Pace downgrade
```

不得直接增加派發 / 吸籌分數。

### 7.3 Resonance 不得作反向 stage bias

多頭過熱共振：

```text
趨勢仍強，但追多風險升高。
```

因此不得直接加 `distEff`。

空頭恐慌共振：

```text
下跌仍強，但追空風險升高。
```

因此不得直接加 `accEff`。

Resonance 只用於：

```text
no-chase
protect profit
Pace downgrade
risk warning
```

### 7.4 Divergence 權重上限

Strict divergence 最大 stage bias 建議：

```text
5% ~ 8%
```

預設：

```text
divStrictStageBiasMax = 6%
```

Soft divergence 預設：

```text
divSoftStageBias = false
```

---

## 8. 建議 multiplier 實作

### 8.1 Witness mode gates

```text
mtfCanBias = witnessStageBiasMode != "Conservative"
divCanBias = witnessStageBiasMode == "Aggressive"
```

### 8.2 MTF multipliers

```text
accMtfMult = 1 + mtfBiasWeight × gate(mtfAbsorptionScore)
markupMtfMult = 1 + mtfBiasWeight × gate(mtfMarkupConfirmScore)
distMtfMult = 1 + mtfBiasWeight × gate(mtfDistributionScore)
markdownMtfMult = 1 + mtfBiasWeight × gate(mtfMarkdownConfirmScore)
```

### 8.3 Divergence multipliers

```text
accDivMult = 1 + divBiasWeight × gate(bullishDivergenceScore)
distDivMult = 1 + divBiasWeight × gate(bearishDivergenceScore)
```

可選降權：

```text
markupDivPenalty = 1 - divBiasWeight × gate(bearishDivergenceScore) × 0.50
markdownDivPenalty = 1 - divBiasWeight × gate(bullishDivergenceScore) × 0.50
```

但 v0.5.2 初版建議先不做 penalty，避免讓底色過度翻動。

### 8.4 Final effective score

概念：

```text
accEff = accEffBase × accVolMult × accMtfMult × accDivMult
markupEff = markupEffBase × markupVolMult × markupMtfMult
reaccEff = reaccEffBase × reaccVolMult × reaccMtfMult
distEff = distEffBase × distVolMult × distMtfMult × distDivMult
markdownEff = markdownEffBase × markdownVolMult × markdownMtfMult
redistEff = redistEffBase × redistVolMult × redistMtfMult
```

v0.5.2 不建議讓 soft divergence 進 multiplier。

---

## 9. Dashboard 更新

### 9.1 MTF diagnostics row

新增或改寫 MTF row：

```text
MTF｜active TF｜count x/y｜strict/soft/fail｜W z%
```

範例：

```text
MTF｜240｜count 0/3｜資料不足｜W 0%
MTF｜120｜count 2/3｜Soft觀察｜W 0%
MTF｜60｜count 5/3｜Auto參與｜W 7.5%
```

### 9.2 Witness governance row

新增 row：

```text
Witness｜Balanced｜V 8% / M 6% / D 0%｜Total 14% / Cap 25%
```

或精簡：

```text
證人｜平衡｜V8 M6 D0｜Σ14/25
```

### 9.3 Stage Bias row

新增 row：

```text
Stage Bias｜MTF ON｜Div strict OFF｜Soft OFF
```

Aggressive 模式：

```text
Stage Bias｜MTF ON｜Div strict ON 6%｜Soft OFF
```

---

## 10. Debug 更新

新增 debug single-line options：

```text
MTF Count
MTF Active TF
MTF Data Quality
Witness Total Weight
Witness Scale
MTF Bias Weight
Divergence Bias Weight
```

保留原本 Volume / MTF / Divergence 分數 debug。

---

## 11. Alerts

v0.5.2 不新增交易訊號 alerts。

可新增資訊型 alerts：

```text
MTF data became available
MTF data unavailable
Witness total weight capped
Stage bias mode active
```

Alert 文案不可使用 Buy / Sell / Short / Cover。

---

## 12. 驗收標準

### 12.1 MTF data robustness

以下情境必須能清楚顯示原因：

1. `ltfCount = 0`：Dashboard 顯示 count 0/y，而不是只有資料不足。
2. primary TF 不足但 fallback 成功：Dashboard 顯示 active TF 為 fallback TF。
3. 所有 fallback 都不足：MTF 權重為 0，Dashboard 顯示 fallback 仍不足。
4. soft ok：可顯示 Soft觀察，但 Balanced 不得改階段分數。

### 12.2 Witness governance

1. Conservative 模式：Volume / MTF / Divergence 不得改階段分數。
2. Balanced 模式：MTF strict ok 可改階段分數；strict divergence 不得改階段分數。
3. Aggressive 模式：MTF strict ok 可改階段分數；strict divergence 可小幅改階段分數。
4. Soft divergence 與 resonance 預設不得改階段分數。
5. witness total weight 不得超過 `witnessMaxTotalWeight`。

### 12.3 強趨勢保護

在強趨勢中：

- 多頭過熱共振不得直接加派發分數。
- 空頭恐慌共振不得直接加吸籌分數。
- Soft 高位供給不得直接把拉升底色改成派發。
- Soft 低位承接不得直接把崩跌底色改成吸籌。

### 12.4 Observe-only 保護

若 MTF Mode 或 Divergence Mode 為 Observe Only，該 witness 不得進 stage multiplier。

---

## 13. AI 實作摘要

給 Codex / AI 的施工摘要：

```text
請在 Chase Risk Market Regime Radar v0.5.1 的基礎上實作 v0.5.2。
新增 spec 目標：MTF Data Robustness、Witness Governance、Stage Bias Mode。

重點：
1. MTF 新增 diagnostics：active TF、ltfCount/min、strict/soft/fail、failure reason。
2. MTF 新增 fallback TF：primary、fallback1、fallback2、fallback3，選第一個 strict ok；若無 strict ok 但有 soft ok，僅作觀察。
3. 新增 Witness Stage Bias Mode：Conservative / Balanced / Aggressive。
4. Conservative：witness 不改階段分數。
5. Balanced：MTF strict ok 可改階段分數；divergence 不改階段分數。
6. Aggressive：MTF strict ok 可改階段分數；strict divergence 可小幅改階段分數。
7. Soft divergence 與 resonance 不得直接改階段分數，只能 clue / conflict / no-chase / pace downgrade。
8. 新增 witnessMaxTotalWeight，避免 Volume / MTF / Divergence 權重無限制疊加。
9. 更新 Dashboard：MTF diagnostics、Witness total weight、Stage Bias status。
10. 不要重構主模型；價格結構仍是主引擎，witness 只是低權重輔助。
```

---

## 14. 結論

v0.5.2 的核心不是讓指標更激進，而是讓 witness layer 更可控：

```text
MTF 可以進階段分數，因為它是 effort/result 證據。
Strict divergence 可以在 Aggressive 模式下小幅進階段分數。
Soft divergence 與 resonance 不能直接翻底色，只能提醒不要追價。
```

最後保留這條底線：

```text
Witness 可以讓法官更有信心，但不能自己當法官。
```
