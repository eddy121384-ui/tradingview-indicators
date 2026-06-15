# Chase Risk Market Regime Radar v0.5｜MTF Effort / Result Layer 規格書

## 0. 版本定位

v0.5 延續 v0.4 的核心精神：價格行為仍是主引擎，成交量與次級週期都只是「證人」，不是方向投票器，也不是買賣訊號產生器。

本版新增 `MTF Effort / Result Layer`，用次一級 time frame 的價格行為衡量多空 effort，並與主 time frame 的價格 result 對照。其目的不是讓 4H 直接判定 1D 的威科夫階段，而是判斷「次級週期已經付出多少努力，主週期是否真的產生結果」。

本指標仍不是買賣訊號，也不是高低點預測器。六階段權重是相對權重，不是統計機率；主導狀態只是市場階段傾向；Pace Guide 與 Flat Action 仍只是節奏與風控提示。

## 1. 必須完整保留的 v0.4 功能

v0.5 不應刪改 v0.4 的既有主架構，除非是為了讓 MTF 層接入必要的低權重證據。

必須保留：

- 即時熱度、趨勢成熟度、末段風險。
- 區間偵測、突破 / 下破與低波動豁免。
- 吸收 / 出貨辨識。
- Volume Quality Layer。
- 六階段威科夫權重：吸籌、拉升、再吸籌、派發、崩跌、再出貨。
- Regime Inertia：正式主導、候選主導、確認根數。
- Pace Guide。
- Flat Action Level。
- Pace Context Downgrade。
- Dual Layer Background。
- Dashboard、Debug 單線與 plot-count safe alerts。

## 2. MTF Layer 的核心語意

MTF Layer 不做「次級週期階段投票」。

錯誤用法是：4H 判斷為崩跌，所以 1D 也加權崩跌。

正確用法是：4H 空方 effort 很強，但 1D 沒有跌出 result，這代表主週期可能有吸收 / 承接證據。反過來，4H 多方 effort 很強，但 1D 沒有漲出 result，代表主週期可能有派發 / 供給證據。

因此 v0.5 的 MTF Layer 只產生四個核心判讀：

- `mtfAbsorptionScore`：次級空方努力強，但主週期下跌結果弱。
- `mtfDistributionScore`：次級多方努力強，但主週期上漲結果弱。
- `mtfMarkupConfirmScore`：次級多方努力強，且主週期上漲結果也強。
- `mtfMarkdownConfirmScore`：次級空方努力強，且主週期下跌結果也強。

## 3. MTF Mode

新增 `MTF Mode`，選項如下：

- `Off`：完全關閉 MTF Layer。
- `Observe Only`：預設模式。只顯示與警示，不改寫主模型、正式主導、候選、Evidence 或 Flat Action。
- `Auto`：當 MTF 分數足夠明確時，才以低權重參與主模型。
- `Force On`：只要資料可用，就以 `mtfMaxWeight` 固定參與主模型。

`Observe Only` 是 v0.5 預設值，目的是先驗證 MTF 分數是否有穩定語意，而不是一上來就讓 4H 影響 1D 主判斷。

## 4. 新增參數

```pine
mtfMode = input.string("Observe Only", "MTF Mode", options=["Off", "Observe Only", "Auto", "Force On"])
mtfLowerTf = input.timeframe("240", "次一級 Time Frame")
mtfMinIntrabars = input.int(3, "最低有效次級 K 根數", minval=1, maxval=50)
mtfEffortThreshold = input.float(60.0, "MTF Effort / Result 有效門檻", minval=0.0, maxval=100.0, step=0.5)
mtfMaxWeight = input.float(15.0, "MTF 最大參與權重 %", minval=0.0, maxval=30.0, step=0.5)
mtfResultAtrFull = input.float(1.5, "主週期 Result 滿分 ATR 倍數", minval=0.25, maxval=5.0, step=0.25)
showMTFInCompact = input.bool(true, "Dashboard 精簡模式顯示 MTF 層")
```

## 5. 次級週期 effort 計算

v0.5 第一版不複製完整六階段模型到次級週期，只計算單根次級 K 的多空努力。

空方 effort 由以下因素組成：

- 紅 K 實體占 range 的比例。
- 收盤位置偏低。
- 收盤低於前一根。

多方 effort 由以下因素組成：

- 綠 K 實體占 range 的比例。
- 收盤位置偏高。
- 收盤高於前一根。

使用 `request.security_lower_tf()` 抓取主週期 K 棒內部的次級 K 陣列，並以平均值作為該主週期 bar 的 `ltfBearEffort` 與 `ltfBullEffort`。

## 6. 主週期 result 計算

主週期 result 不看次級週期，而是衡量主圖 bar 是否真的產生方向結果。

上漲 result：

- 主週期 close-to-close 上漲幅度相對 ATR。
- 主週期收盤位置偏高。

下跌 result：

- 主週期 close-to-close 下跌幅度相對 ATR。
- 主週期收盤位置偏低。

## 7. 四個 MTF 判讀分數

`mtfAbsorptionScore`：

- 次級空方 effort 高。
- 主週期 downside result 低。
- 主週期收盤位置偏高。

`mtfDistributionScore`：

- 次級多方 effort 高。
- 主週期 upside result 低。
- 主週期收盤位置偏低。

`mtfMarkupConfirmScore`：

- 次級多方 effort 高。
- 主週期 upside result 高。
- 主週期收盤位置偏高。

`mtfMarkdownConfirmScore`：

- 次級空方 effort 高。
- 主週期 downside result 高。
- 主週期收盤位置偏低。

## 8. 權重接入方式

MTF 層不得接管主模型。它只能在 `Auto` 或 `Force On` 模式下以低權重放大原本六階段有效分數。

建議預設最大權重為 15%。

接入邏輯：

- `mtfAbsorptionScore` 加強吸籌。
- `mtfDistributionScore` 加強派發。
- `mtfMarkupConfirmScore` 加強拉升。
- `mtfMarkdownConfirmScore` 加強崩跌。
- 再吸籌可低權重參考 absorption 與 non-distribution。
- 再出貨可低權重參考 distribution 與 non-absorption。

在 `Observe Only` 下，`mtfWeightApplied = 0`，因此不影響背景、候選、正式主導、Evidence 或 Flat Action。

## 9. 與 Evidence / 線索觀察整合

當 `mtfActive` 為 true 時，MTF 可成為 witness support 的一部分。

- topId = 吸籌：MTF support = `mtfAbsorptionScore`。
- topId = 拉升：MTF support = `mtfMarkupConfirmScore`。
- topId = 再吸籌：MTF support = absorption 與 non-distribution 的混合。
- topId = 派發：MTF support = `mtfDistributionScore`。
- topId = 崩跌：MTF support = `mtfMarkdownConfirmScore`。
- topId = 再出貨：MTF support = distribution 與 non-absorption 的混合。

MTF 線索也可納入：

- `highClueObservation`
- `lowClueObservation`
- `trendClueDispute`
- `candidateConflict`
- `flatSupplyConflict`
- `flatDemandConflict`
- `Pace Context Downgrade`

但必須注意：MTF 線索是輔助證據，不是正式反轉訊號。

## 10. Dashboard / Debug / Alerts

新增 Dashboard 顯示：

- 極簡模式：顯示 `MTF`。
- 精簡模式：顯示 `MTF驗證`。
- 完整模式：顯示 `MTF驗證` 四分數。
- 除錯模式：顯示 `MTF Effort` 與 `MTF Result`。

新增 Debug 單線選項：

- `MTF空方努力`
- `MTF多方努力`
- `MTF吸收`
- `MTF派發`
- `MTF拉升確認`
- `MTF崩跌確認`
- `MTF權重`

新增 alertcondition：

- `MTF Effort / Result 重要事件`

新增 dynamic alerts：

- MTF 吸收線索。
- MTF 派發線索。
- MTF 拉升確認。
- MTF 崩跌確認。

## 11. 驗收標準

v0.5 是否有效，不應只看背景是否變化，而應先用 Debug 與 Dashboard 檢查 MTF 分數是否有語意。

應測試以下場景：

- 真 V 轉：`mtfAbsorptionScore` 是否比正式主導更早亮。
- 假 V 轉 / 二次探底：`mtfAbsorptionScore` 是否不會一路錯誤維持高檔。
- 強趨勢下跌：`mtfMarkdownConfirmScore` 應高於 `mtfAbsorptionScore`。
- 高位上攻無效：`mtfDistributionScore` 應升高。
- 健康突破：`mtfMarkupConfirmScore` 應升高，而非派發亂亮。

## 12. 注意事項

MTF Layer 會增加敏感度，也會增加雜訊。它的第一用途不是預測反轉，而是判斷原方向是否仍然乾淨。

若使用者想讓 MTF 影響背景與主導狀態，應先從 `Auto` 測試，不建議一開始就使用 `Force On`。

`Force On` 不是比較強的 Auto，而是更武斷的 Auto。它適合研究情境，不適合作為預設實戰模式。
