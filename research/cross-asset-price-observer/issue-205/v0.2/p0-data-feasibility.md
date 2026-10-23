# P0 v0.2 — 長歷史市場資料與取得範圍

`PRE_OUTCOME / METADATA_REVIEW_ONLY / COVERAGE_NOT_VERIFIED`。2026-10-23（Asia/Taipei）。[修訂依據](https://github.com/eddy121384-ui/tradingview-indicators/issues/205#issuecomment-6310413480)。

## 1. 候選清單：市場本身，不再限制 ETF

提案為七個主要輸入；EURUSD 是第八個補充候選。1990-01-01 至 2025-12-31 是**請求／盤點窗，不是已取得的共同樣本**。Bloomberg 代碼均待持有人在 DES／FLDS 核對，不把相似名稱當同一 feed。

| 市場／用途 | TradingView 官方 symbol | Bloomberg 手動匯出候選 | 單位與主要風險 |
| --- | --- | --- | --- |
| S&P 500；input／reference-price target | `SP:SPX` | `SPX Index` | 指數點、price index；非含息、不可直接成交 |
| US 2Y yield；input | `TVC:US02Y` | `USGG2YR Index` | 年化百分比，變動轉 bp；generic benchmark 的換券／曲線定義需確認，非價格、非期貨 P&L |
| US 10Y yield；input | `TVC:US10Y` | `USGG10YR Index` | 同上；不能用殖利率 log return 冒充 duration return |
| 美元指數；input／reference-price target | `TVC:DXY` | `DXY Curncy` | 指數點；spot index 不等於美元期貨、roll 或 FX carry |
| 黃金；input／reference-price target | `TVC:GOLD` | `XAU Curncy`（固定來源，例如 BGN，須核實） | USD/troy oz；TV 的 commodity 分類未證明等同 Bloomberg spot/fix |
| WTI；input only | `TVC:USOIL` | 優先核對 `USCRWTIC Index`；`CL1 Comdty` 僅另列期貨替代候選 | USD/barrel；spot assessment、CFD 與 generic future 不等價，可能非正，roll／合約切換須單列 |
| VIX；衍生狀態 input only | `CBOE:VIX` | `VIX Index` | 波動率指數點、非成交價格，不可交易；與歷史 VXO／回算版本不同 |
| EURUSD；補充 input，非 primary universe | `FX:EURUSD` | `EURUSD Curncy` | USD per EUR；1999 前合成／前身貨幣不當原生歐元歷史；TV 本次搜尋回報來源為 FXCM |

USD、gold、WTI 的 clock／fixing 或 publication lag 比名稱更重要。Bloomberg identifiers 是候選 registry key；若指數沒有 FIGI，可用 vendor identifier＋完整 security 名稱／來源／版本固定，不強求不存在的 FIGI。`PX_LAST` 對 yield 是 yield value，並不保證對所有類別都是官方收盤。

## 2. TradingView 官方能力：三種證據分開

**本次工具宣告與操作：**目前 chat 的 active tools 有官方 `search_symbols`、`get_ohlcv`。本次僅用 `search_symbols` 解析上表八個 symbol，均成功找到 exact match；無 OHLCV、報酬、news、macro、帳戶寫入或 Desktop 操作。搜尋證實路由與基本分類，不證實歷史可下載／可訓練。`TVC:GOLD`／`TVC:USOIL` 回報 commodity，也不足以判定 spot／CFD／roll 定義。

**官方文件核對：**[MCP 工具參考](https://www.tradingview.com/mcp/docs#tools) 與本次工具 schema 一致：`get_ohlcv(symbol, interval, count, summary)`，預設 300、最多 5,000 bars；1m/5m/15m/30m/1h/4h/1D/1W/月頻。現行介面**沒有 from/to、end、offset 或 cursor**；`summary=true` 仍回傳統計，並非 metadata-only。UTC bar timestamp 不是歷史發布時間／PIT vintage。5,000 日 bars 約 20 個交易年，不能覆蓋整段 1990–2025，也不能直接要求截止於 2025 的指定窗。這是介面確認，非本次重新下載 5,000 bars 的實測。

**既有 coverage 證據：**[10/21 留言](https://github.com/eddy121384-ui/tradingview-indicators/issues/205#issuecomment-6310413480) 記載八檔 metadata 已實測，多數宣告更早歷史，US02Y 約 4,776 bars／2006 起。這是既有紀錄；本次未重跑 OHLCV、未驗證確切起迄日／row count。伺服器「更早歷史存在」不代表目前 connector 可取出；不得據此填寫 30 年共同 coverage。

連線邊界：官方文件列有各 client 的 OAuth 設定，但 **ChatGPT 已連線 ≠ Codex Cloud Python 自動有 session／API 權利**。本次只確認此 chat 的官方 metadata 工具呼叫成功；未替雲端配置 OAuth、未複用／轉交 token，未測另一個 chat 或 shell 的行情權限。沒有 tools 或呼叫失敗時應標 `CONNECTOR_UNAVAILABLE`，改由使用者在已授權 client 互動核對，不能猜測可用。

[官方 beta 使用範圍](https://www.tradingview.com/support/solutions/43000795699-mcp-server-connect-your-ai-assistant-to-tradingview/) 限個人互動；行情有延遲，禁止無人值守／排程／bulk 蒐集、原始時序再散布及送入自動交易／決策系統。因此此管道只作 metadata／互動 smoke，**不能當本案歷史模型資料供應契約**。不使用非官方 websocket、cookie、私有 endpoint、tvDatafeed、換 timeframe 拼日線或其他翻頁規避法。日後前瞻 append-only 也須使用另有合法權利的來源，不排程蒐集 MCP。

## 3. 長歷史、同步與風險盤點

| 項目 | 本次可下的結論 | 仍欠資料／處理 |
| --- | --- | --- |
| 七市場共同史 | UNKNOWN；零份本案完整市場價格檔被取得或開啟 | 各檔 min/max、年度列數、應有 session／缺漏／重複；1990–2025 不保證成立 |
| US2Y | TV 既有紀錄僅約 2006 起 | Bloomberg 較長歷史與 benchmark 定義；不能補 ETF 或把缺失視為 0 |
| VIX | 需區分現行定義、回算史、歷史方法變更 | 起始日／方法版本／revision 說明；不得偷偷接 VXO |
| EURUSD | 原生 EUR 機制晚於 1990 | 僅補充，1999 前不合成；不因此縮短七市場 primary panel |
| WTI | spot／generic future 尚待選定；只作 state input | `USCRWTIC` 的 source／clock／publication lag；若是 CL1，需 roll 與 actual contract metadata，不能直接比較連續合約跨月價差 |
| 時區／日切 | 交易所 close、FX day-cut、gold fixing、yield quote、oil assessment 不同步 | 每序列原生日期／timezone／close or fix／發布時程；DST 和假日不可只用 date string join |
| 歷史修訂／available_at | 普通 Excel 歷史匯出通常不能證實當時 vintage | 真正 available_at 留 UNKNOWN；assumed eligibility 與 download time 分欄，禁止後見時間戳 |
| 成本與風險單位 | 沒有成本驗證；本輪無策略損益 | yield bp ≠ DV01 P&L；指數點 ≠ futures notional return；carry、roll、spread、fees 屬未來交易映射 |

WTI 若為近月／連續期貨，不把新舊合約價差當報酬；ratio/back-adjusted 歷史、2020 非正價與事後改寫均需披露。任何 roll reconstruction 須另凍結逐合約 ID、到期／first notice、乘數／tick／切換規則；本次不寫 reconstruction 工具，不用截斷、刪除非正價或補一個「合理」價格救資料。

## 4. Bloomberg 手動路徑與證據層級

優先由授權持有人依 [Excel 匯出規格](bloomberg-excel-export.md) 手動提供 metadata；獲准處理原始值後才取得日檔。**不依賴 blpapi、Terminal GUI automation 或 CC**。#119 的 hash／schema／缺漏稽核概念可復用；不執行其排除 ETF 的 universe builder，不改既有工具或研究。

此 [scope amendment](https://github.com/eddy121384-ui/tradingview-indicators/issues/205#issuecomment-6310413480) 明確放寬 v0.1 的 PIT 硬性前提：

- `REVISED_DATA_RETROSPECTIVE_EXPLORATORY`：允許另正式 prereg 的探索研究；版本／lag 假設／已知修訂清楚記錄，不能稱歷史當時可交易或 PIT。單次匯出不含未來 label 的設計保護，並不能消除歷史修訂。
- `PROSPECTIVE_APPEND_ONLY`：另有來源權限、實際 captured/available timestamps、版本封存與單獨執行授權後，才是較強證據。本次不開始收集。

仍 BLOCKED／UNKNOWN：完整 history 與品質、來源語義／日切、雲端處理及公開 aggregate 權限。實際 PIT 不存在不再永久禁止前一模式，但時間假設仍要在 outcome 前明文凍結；不能把 download time 填進歷史 available_at。

下一個最小動作：使用者回傳七主市場＋EURUSD 可取得的 **metadata 清單**，確認授權處理範圍；再依規格提供 values-only Excel。只有 calendar／schema／coverage 稽核通過後，才能決定共同起點、固定正式 v0.2 manifest／SHA；本次不計 labels、不訓練、不回測。
