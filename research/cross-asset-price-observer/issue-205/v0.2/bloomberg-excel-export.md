# Bloomberg Excel 手動匯出：最小資料契約 v0.2

供授權持有人操作；Codex 不連 Terminal、不啟動 Desktop、不購買資料、不自動執行 Excel。現階段**先交 metadata 即可**；原始值只有在允許此雲端環境處理時才提供，不放公開 GitHub。本文件／範本沒有任何市場值。

## 1. 標的與日期

請在 Bloomberg 的 security description／field help 核對以下候選，不成功就回報 error 與可用範圍，不自動替換：

| series_id | 候選 security | 最小日頻 field | 必須說明的語義 |
| --- | --- | --- | --- |
| SPX | `SPX Index` | `PX_LAST` | S&P 500 price index，非 total return |
| US2Y | `USGG2YR Index` | `PX_LAST` | yield percent；generic benchmark／maturity 定義 |
| US10Y | `USGG10YR Index` | `PX_LAST` | 同上，不匯成 bond price |
| DXY | `DXY Curncy` | `PX_LAST` | 美元現貨指數來源／close，非 DX1 期貨 |
| GOLD | `XAU Curncy` | `PX_LAST` | USD/troy oz；固定 contributor／fix／composite |
| WTI | `USCRWTIC Index` 優先核對 | `PX_LAST` | Cushing spot／assessment 的來源、日切、發布延遲；不要與 CL1 混接 |
| VIX | `VIX Index` | `PX_LAST` | 定義／回算史，非 VIX future |
| EURUSD（補充） | `EURUSD Curncy` | `PX_LAST` | USD per EUR、來源與 day-cut；pre-1999 若合成須標示 |

請求 **1990-01-01 至 2025-12-31，Daily**；不足時保留實際起點與空值，不補成 1990。若容易取得，可額外提供 1989 暖機資料並獨立標記，不能據此聲稱主要期間完整。不要提供 2026 outcomes，也不用計算報酬、指標、勝率或 forward columns。

若只有 WTI `CL1 Comdty` 可得，先記在 metadata 的替代候選；先不要當成 spot 檔，也不必先匯出全部逐月合約。P0 先決定該 proxy 是否適合 state input；若要採用，需另記 generic rule、adjustment、actual contracts／roll dates，可得性未知時維持 BLOCKED。

## 2. 最簡單操作方式

在已登入並獲授權的 Bloomberg Excel Add-in，選 Spreadsheet Builder → Historical Data Table／Historical End of Day，加入上表 security 與 `PX_LAST`，設定日期、Daily、升冪、不以 previous value／零值填補休市或 error；保留 wizard 產生的設定及 override 說明。

BDH 基本式可參照下例（**只是人工輸入範例，未執行**；實際 override 由使用者的 Add-in help 核對）：

```text
=BDH("SPX Index","PX_LAST","19900101","20251231")
```

不預填未核實的 override mnemonic。請記錄 Daily、calendar/fill、currency conversion、price source／adjustment 的實際設定。索引／yield／spot 不沿用 ETF split/dividend adjustment；`PX_LAST` 不能未經確認就重命名為 settlement／official close。若 metadata field 不支援該資產，填 UNKNOWN，勿編造 ID。

將返回資料 **Copy → Paste Values** 到新 `.xlsx`（無 macro／外部 refresh）或 UTF-8 CSV；持有人可在合法本機保留原公式檔與設定。最小檔不需要 O/H/L/V，不需要交易量、不需要 bid/ask 或 open；新 P1 使用 close/fix-to-close/fix 的統計目標，並非交易成交驗證。若 O/H/L 已容易取得，可選附 `PX_OPEN/PX_HIGH/PX_LOW`；V 缺少是 NA，不能用 0／虛構量填入。

## 3. 接受的格式：一張說明表＋每序列兩欄

**最省事的 workbook：**`instruments` 工作表，加七個主要 series 工作表（可再附 EURUSD）。每個 series tab 只含：

```csv
date,PX_LAST
```

日期 `YYYY-MM-DD` 或無時區的 Excel date；升冪、一個來源 session 一列；儲存原始數值，不先轉百分比或做 log。小數用 `.`、不要以百分比 Excel 顯示誤改值。error／缺值保留並附原因，不能刪到看似連續。

`instruments` 每個 series 一列，最低欄位如下（可手填文字，不強求每項都有 Bloomberg field）：

| 欄位 | 必填內容 |
| --- | --- |
| `series_id`, `sheet_name` | 上表鍵與對應 tab；CSV 則填 filename |
| `requested_security`, `resolved_identifier`, `description` | 實際回傳 security／stable vendor ID；沒有 FIGI 用完整 vendor key，不猜 |
| `provider`, `contributor`, `field` | Bloomberg＋來源／BGN／fix 等；field 為 PX_LAST，來源未知明寫 UNKNOWN |
| `unit`, `currency`, `quote_direction` | percent / index_points / USD_per_troy_oz / USD_per_barrel / USD_per_EUR；yield 必須確認值是 percent 而非 decimal，FX 不倒置 |
| `calendar`, `session_timezone`, `close_or_fix`, `publication_lag` | 哪個交易／報價日、IANA timezone、session close／fix／assessment 與發布時程；unknown 保留，不從日期猜 |
| `price_type`, `adjustment`, `revision_or_roll_rule` | price index／yield／spot／generic future、raw/back/ratio-adjustment、回算／roll 說明；無則 NONE，未知 UNKNOWN |
| `requested_start/end`, `returned_start/end`, `row_count` | 請求與實際涵蓋；可先回 metadata，不必提供原始值 |
| `downloaded_at_utc`, `export_settings`, `rights_scope` | 當次下載時間、wizard／override 設定文字、允許的雲端處理／保存／aggregate 發表範圍或 UNCONFIRMED |

`available_at_utc` **不是最低必填的歷史日欄位**。只有真的存在來源證據時才附；否則空值／UNKNOWN。`downloaded_at_utc` 與後續分析的 `assumed_eligible_at` 不能改名成 available_at。不要求使用者手工偽造幾十年 intraday timestamps。

也接受 long-form：`series_id,date,field,value`，另附同一 instruments 表。不得在一個 price 欄混入不同 yield 單位或來源。每檔 SHA-256 可在後續獲准稽核時計算，不需先寫資料平台。

## 4. 收件後的順序與阻擋項

第一步只驗 calendar、schema、單位、coverage、duplicates、missing/errors、來源與設定，不做任何 forward label／收益統計；保留原始檔及 hash、清洗另存，不覆寫。原生 holidays 不補值；close 平坦與實際缺漏／vendor fill 須分辨，但不以可預測性選資料。

若來源／close 定義、WTI roll、1990–2025 共同史或權限仍欠缺，正式 prereg 保持 pending。可以選定 revised-data retrospective 證據層級，不能宣稱歷史 PIT。前瞻時間戳留待單獨授權階段。

文件依據：Bloomberg 自有網域所列 [2018 Primer 的 Excel／Spreadsheet Builder 章節](https://data.bloomberglp.com/professional/sites/10/LUISS_2018Primer.pdf) 搜尋索引確認 BDH 基本流程；完整 PDF 因大小限制未取回，故不以此宣稱現行 override／entitlement 已驗證。具體 field 語義／設定仍以使用者 Add-in／Terminal 的當前說明為準。原 #119 的 `PX_*` 程式可供工程參考，並非此手動流程已成功的證明。
