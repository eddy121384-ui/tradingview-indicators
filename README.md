# TradingView Indicators

這個 repository 是 Eddy 的 TradingView 指標研究室，用來集中管理各種 TradingView / Pine Script 指標的規格書、程式碼、使用說明、提示詞與素材。

## 目前指標

- `shiori-map`：市場狀態地圖／趨勢與風險語氣輔助指標。
- `macro-pressure-map`：成長、通膨與政策壓力相關的總經壓力圖。
- `wyckoff-regime-radar`：威科夫結構、吸籌／派發與 regime 判讀輔助指標。

## 標準資料夾結構

每個指標都放在 `indicators/{indicator-name}/` 底下，並維持相同結構：

```text
indicators/{indicator-name}/
  specs/      # 規格書、版本規劃、設計想法
  docs/       # 使用說明、發布文案、教學文件
  prompts/    # 給 ChatGPT / Codex / 繪圖模型的提示詞
  src/        # Pine Script 或正式程式碼
  assets/     # 圖片、截圖、插圖、素材
  archive/    # 舊版、棄用文件、歷史備份
```

## AI 協作原則

1. 先討論規格，再修改程式碼。
2. 規格書放進 `specs/`，不要只留在聊天紀錄。
3. Codex 實作前，應明確讀取對應的規格書與提示詞。
4. 正式修改建議走 branch + Pull Request，不直接打進 `main`。
5. 每次 PR 都要檢查：改了哪些檔案、是否越界、是否符合原本指標定位。

## 命名規則

完整命名規則請見：

- `shared/naming-rules.md`
- `shared/workflow-rules.md`

## 初始建立日期

2026-06-05
