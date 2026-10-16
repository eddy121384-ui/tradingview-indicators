# Issue #199｜Claude Code Cloud × TradingView MCP 可行性紀錄

> 2026-10-16（UTC+8）｜Parent #196，規格 Draft PR #197（未修改）
>
> **最新 Codex Cloud 結果：`CLOUD_MCP_VERIFIED` / `INTERACTIVE_PILOT_VERIFIED` / `EXPLORATORY_ONLY`。**
> 三個標的的官方 MCP 真實日線、匿名圖與兩個未檢驗假說，見 [Codex Cloud 接手紀錄](codex-cloud-verification-2026-10-16.md)。沒有提交原始行情或圖形時序，沒有 outcome run 或 Alpha 宣稱。`production_authorized=false`。
>
> 以下 A–D 為先前 Claude session 的歷史紀錄，保留原貌；其中 BLOCKED 與日期參數限制已由上方新紀錄更新。批量研究來源仍僅是候選，授權與費率未確認。

## A｜雲端 connector 驗證：BLOCKED

Claude Code on the web 雲端 session（2026-10-16，對應的 claude.ai 帳戶）實際檢查結果：

| 檢查 | 結果 |
|---|---|
| 帳戶 connector 清單（`ListConnectors`，關鍵字 tradingview / market data / trading） | 空清單，查無 TradingView connector |
| Session 工具搜尋 `tradingview`、`search_symbols get_ohlcv` | 無相符工具；session 內只有 GitHub、Gmail、Drive、Notion、Slack、Canva 等 connector |
| 容器網路 → `mcp.tradingview.com`、`www.tradingview.com` | Proxy 回 `CONNECT 403`；WebFetch 回 DNS `ENOTFOUND` |

結論：這個 session 沒有任何 TradingView tool 可以呼叫，因此 `search_symbols` / `get_ohlcv` **都沒有執行**，日期範圍、筆數、成交量缺值等欄位**沒有觀測值**。依 Issue 規定停在 BLOCKED，沒有改用社群 MCP、爬蟲、桌面 bridge 或私有 API 繞過。

### 第二次檢查（使用者表示已完成授權；同一 session，13:12 UTC+8）

同一個 session 是在 11:56 UTC+8 建立的，之後沒有重新建立。三個層次分開記錄如下：

| 層次 | 檢查 | 結果 |
|---|---|---|
| 1. 帳戶授權 | `ListConnectors`（即時查詢、不帶篩選） | 共列出 8 個 connector：Canva、GitHub、Gmail、Google Calendar、Google Drive、Microsoft 365、Notion、Slack。**沒有 TradingView**，連「未連線」狀態也沒有出現。這代表本 session 所屬的 claude.ai 帳戶/組織中看不到這個 connector |
| 2. 工具載入 | ToolSearch：`tradingview`、`get_ohlcv search_symbols` | 0 個工具。即使帳戶端後來授權成功，connector 也只在 session 啟動時讀取，本 session 不會補載 |
| 3. 容器網路 | `curl` 連 `mcp.tradingview.com`、`www.tradingview.com` | proxy `connect_rejected 403`，為環境網路政策所擋。只影響 WebFetch/curl；remote connector 由 claude.ai host 代理，不經過容器網路 |

主要阻擋點是第 1 層。第 2 層需要開新 session 才能解。第 3 層不擋 MCP。

**疑似原因（尚未驗證）**：TradingView 尚未在**這個 claude.ai 帳戶**以 custom connector 完成 OAuth（ChatGPT 端已連接不算數），或已連接但沒有在雲端 session 啟用。Remote connector 由 claude.ai host 代理，所以容器網路 403 不一定是主因；但若要讓 WebFetch 讀官方文件，仍需放行該網域。

**解除步驟**
1. claude.ai → Settings → Connectors（https://claude.ai/customize/connectors）→ Add custom connector → URL `https://mcp.tradingview.com/mcp` → 以 TradingView Essential 以上帳號完成 OAuth。
   授權後回到 Connectors 頁面，確認 TradingView 出現在**啟動此雲端 session 的同一個帳戶、同一個組織**底下。若帳戶屬於 Team/Enterprise 組織，custom connector 可能需要由管理員先加入。
2. 確認該 connector 在 Claude Code 雲端 session 是啟用狀態。Connectors 是在 session 啟動時讀取的，因此**必須開一個新 session**。
3. （選配）在雲端環境 Network access 的 Allowed domains 加入 `tradingview.com`，讓官方文件可以被讀取。
4. 新 session 先列出 tools；確認看得到 `search_symbols`、`get_ohlcv` 後，再進行 B 段。

## B｜互動式 Price Action 試驗：NOT_RUN

A 段被擋，所以沒有合法取得的 OHLCV，也就沒有畫出 K 線圖、沒有提出假說。這裡**刻意不以合成資料或其他來源代替**。

已備妥的最小工具是 `masked_window.py`，只用標準函式庫、沒有外部依賴。它讀取本機授權 CSV，輸出 150–250 根日 K 的 SVG，並遮蔽 `cut` 之後的所有 K 線；價格以第一根 K 線收盤價重設為 100，同時移除日期與代號。這支程式只在合成隨機漫步資料上做過程式 smoke test：修改 `cut` 之後的 K 線，輸出 hash 保持不變（future-masking invariance）。這項測試只驗證程式行為，不代表任何市場結論。`data/`、`out/`、`*.csv` 都已列入 git-ignore。

**connector 可用後的 B 段流程**（約 3 個標的、互動式、由本人發起）
1. `search_symbols` 選 3 個不同家族的標的，例如一個股指或 ETF、一組 FX 貨幣對、一個商品或債券期貨連續合約；不要用 yield 指數充當可交易價格。
2. 每個標的呼叫一次 `get_ohlcv(interval=1D)`，只記錄 metadata：首末日期、筆數、成交量缺值比例、報價類型。原始序列只留在 session 的暫存目錄。
3. 每個標的只取 1 個視窗，以 `masked_window.py` 輸出圖。Opus 只看圖與遮蔽後的數值，最多提出 3 個假說，每個假說填寫下方欄位。
4. 只回報流程可行性與公式是否 causal，不計算後續報酬、勝率或 Sharpe。這 3 個視窗都視為 `EXPLORATORY`，以後不得充當 #196 的 OOS。

**假說登錄欄位**：`id`｜觸發條件（t 收盤時可計算的公式，只用 ≤t 的資料）｜預期（方向或分布，例如 t+1..t+10 的 ATR 標準化報酬或波動）｜理由｜反證條件｜同族變體數｜看過的圖 hash。

## C｜正式大樣本的合法雲端來源（僅調查，未訂閱、未下載）

TradingView MCP 依官方 beta 條款（見 Issue #199 引述）**不適用**於 #196 的批量蒐集：`get_ohlcv` 上限 5,000 bars，而且沒有任意 `date_from`/`date_to` 參數。

| 來源 | 涵蓋（宣稱） | 存活者偏差 | 雲端/API | 授權與成本（待官方確認） | 適合角色 |
|---|---|---|---|---|---|
| **EODHD** | 全球股票、ETF、指數、FX；美股下市標的 6 萬多檔 | 有下市清單；2018 年前下市者只有 EOD | REST，可在雲端執行 | 個人方案約 $20–100/月；需確認研究用途與禁止再散布條款 | 跨國股票、指數、FX 主力 |
| **Nasdaq Data Link — Sharadar SEP** | 美股 1998 年至今 | 含下市標的 | REST 或 bulk 下載 | 個人方案約 $39/月或 $399/年（完整歷史，二手來源） | 美股乾淨的子母體 |
| **Databento** | CME/CBOT/NYMEX/COMEX、ICE、Eurex 期貨約 15 年以上，提供 OHLCV-1d | 不適用（期貨） | API，按量計費，新帳號附 $125 額度 | 歷史資料沒有月費；需確認衍生資料公開條款 | 期貨（債、商品、股指）2010 年後 |
| **CSI Data（Unfair Advantage）** | 期貨與美、加、英股票，多數市場自上市首日起 | 下市股票需特別訂閱 | 以 Windows 軟體為主，雲端不便 | 個人方案約 $37/月起；個人用途上限 59 個期貨市場 | 期貨長歷史（1970s–） |
| **Pinnacle CLC** | 約 70 個商品期貨連續合約，1969/1970 年起 | 不適用 | 檔案下載（一次性），可上傳到私有儲存 | 約 $243（舊報價），需重新確認 | 期貨長歷史的低成本選項 |
| **Norgate** | 美股自 1950/1990 年起（Diamond/Platinum），另有約 100 個期貨市場 | 高階方案含下市標的 | **只能在本機 Windows 執行**，不適合雲端 | 訂閱制 | 不建議（違反雲端優先原則） |
| **WRDS：CRSP / Compustat Global Daily** | 美股自 1925 年起；全球日資料 | 金標準 | 雲端 SQL/Python | 限學術機構授權，禁止商業使用 | 若有學術身分則最佳 |
| **FRED（Fed H.10/H.15）** | FX 與殖利率，數十年 | 不適用 | REST，雲端可用 | Fed 自有序列通常不受版權限制；第三方序列（如 ICE）另有條款 | 只能作為 yield/FX 背景；**只有收盤價，沒有 OHLC**，不能用來做 K 線 PA |
| 不採用 | Yahoo/yfinance、Stooq、TV UI 或 Desktop 爬取 | — | — | 條款不允許或不明確 | — |

**初步建議組合**：EODHD（股票、指數、FX，含下市標的）＋ Databento 或 Pinnacle（期貨，包括債券與商品）。若有學術身分，美股改用 CRSP。#119 的 Bloomberg 管線需要 Terminal，不符合本 Issue 的雲端前提。上表的價格與覆蓋範圍多數來自二手來源，**訂閱前需逐一確認官方條款**，至少包括：研究用途、雲端運算、衍生統計可否公開、raw 是否禁止再散布。

## D｜下一步（最小可執行方案）

1. 先依 A 段步驟授權 TradingView connector，並在**新的雲端 session** 重跑 A、B 兩段。只做 3 個標的，產出 metadata 與 ≤3 個假說登錄，不推送 raw 資料。
2. 同時由使用者選定 C 段的 1–2 個來源，閱讀官方條款，並在 Issue #196 記錄授權結論。
3. 授權確認後，才依 #197 的 P0 盤點 40–60 檔 pilot 母體。資料只存在私有儲存，repo 只提交 manifest 與 hash。
