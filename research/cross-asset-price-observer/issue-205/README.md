# Issue #205 — Cross-Asset Price Observer

目前提案：**v0.2 / PRE-OUTCOME / NOT FROZEN / DATA PENDING**，2026-10-23（Asia/Taipei）。仍在 [Draft PR #207](https://github.com/eddy121384-ui/tradingview-indicators/pull/207)，#205 保持 Open。

本版依 [2026-10-21 scope amendment](https://github.com/eddy121384-ui/tradingview-indicators/issues/205#issuecomment-6310413480) 與 [PR 修訂要求](https://github.com/eddy121384-ui/tradingview-indicators/pull/207#issuecomment-6310418696)，取消 ETF-only 主要 universe。沒有候選 outcome、訓練或回測；沒有啟動 Claude Code Desktop。

| v0.2 文件 | 用途 |
| --- | --- |
| [P0 資料與 TradingView 能力](v0.2/p0-data-feasibility.md) | 七個主要市場及 EURUSD 補充候選；區分已確認工具能力、metadata 與未知 coverage |
| [四篇文獻／程式審查](v0.2/literature-review.md) | 比較資料、輸入輸出、loss、OOS、成本與可復用範圍 |
| [Bloomberg Excel 最小匯出規格](v0.2/bloomberg-excel-export.md) | 授權持有人手動 BDH／Spreadsheet Builder；只需日資料與一張來源說明表 |
| [P1 prereg 修訂草案](v0.2/prereg-draft.md) | 同步時鐘、變數單位、分布目標、簡單對照、OOS／校準／停止規則 |

主要修訂：ETF 價格 → 市場 reference series；1990–2025 改為**待稽核目標窗**；不再要求先取得 Bloomberg API；允許先註冊 **revised-data retrospective/exploratory** 證據層級，與真實 PIT／前瞻 append-only 分開。v0.2 仍需資料與權限證據、正式 freeze SHA 及單獨執行指示。

## v0.1 歷史紀錄（保留原樣，並非有效凍結）

原始 commit：`ca6e8e33713bff6289c18ffe1285556b40f858cb`。

- [原 P0](p0-feasibility.md)
- [原 P1 v0.1](prereg-draft.md)
- [原 ETF 候選表](candidate-universe.csv)
- [原 2026-10-21 稽核](audit-evidence.json)

這四份檔案內容不變。其十 ETF、四 ETF targets、next-open label、20-session purge 與歷史 PIT 硬性阻擋規則，只屬當時提案；v0.2 的明文變更以新文件為準。原稽核是當時環境快照，不是現在 TradingView connector 狀態。

## 本次驗證

v0.1 四檔與原 commit 逐位元相同；五個新檔都是 Markdown，12 個本機文件連結存在，code fences／UTF-8／diff whitespace 檢查通過。純 session-index 算式核對確認 h=5/20 的 endpoint 與21-session purge，不含任何市場值或 outcome。

解析既有139個push/PR event filters，新路徑不觸發現有訓練／回測 workflows；未 dispatch 或執行模型測試。這些是文件與設計一致性檢查，不能代表資料品質或預測增量已通過。
