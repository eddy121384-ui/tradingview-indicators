# #205 第一階段：P0 資料可行性盤點

日期：2026-10-21（Asia/Taipei）。範圍：研究文件與能力／metadata 稽核。

**結論：`P0_INVENTORY_COMPLETE / DATA_BLOCKED`。** 可以復用下載與驗證工具，但目前沒有已驗證、具時間戳與使用權限的十市場共同日頻樣本。不能開始 P2，也不能把本次 P1 草案稱為已完成可執行的 prereg。

- [P1 prereg 草案](prereg-draft.md)：本 commit 固定設計提案；資料 Gate 通過後另提交正式 freeze SHA，才可考慮下一階段。
- [候選清單](candidate-universe.csv)：十個 core、五個 deferred 候選；空白 coverage 代表 UNKNOWN，不是零筆。
- [實際稽核證據](audit-evidence.json)：能力檢查、來源 SHA、既有 metadata；沒有原始行情或新 outcome。
- `model_training_run=false; strategy_backtest_run=false; new_outcomes_read=false; production_authorized=false`。

## 1. 可復用證據與邊界

已讀下列 issue 本文及所有留言；截至本次讀取，#205/#198/#43 沒有留言。

| 來源 | 可復用 | 不可直接繼承 |
| --- | --- | --- |
| [#205](https://github.com/eddy121384-ui/tradingview-indicators/issues/205) | H0/H1/H2、B0/B1/A/A+Regime 的分層問題；先校準再談經濟意義 | 本次只做 P0 與 P1 草案，未完成整個 issue |
| [#196](https://github.com/eddy121384-ui/tradingview-indicators/issues/196)，計畫 SHA `a83916d905d04a8ed3843eab94cdd4eba93564c2` | provenance、資產群組／時間隔離、污染登錄、重疊標籤與試驗預算原則 | 不帶入 AI 生成的 K 線事件、已觀看 pilot 或其假說；不重跑 discovery |
| [#198](https://github.com/eddy121384-ui/tradingview-indicators/issues/198) | 十標的 smoke 契約、使用權限及不讀未來結果的界線 | issue 仍 open、無完成留言；遠端 heads 無其指定 smoke 分支。不能宣稱已成功跨資產擷取 |
| [#119](https://github.com/eddy121384-ui/tradingview-indicators/issues/119)，SHA `29463cd075281bee35291b08fec5df00033586db` | `issue119_bbg_client.py`、downloader 的 batch/retry/checkpoint/hash、audit 的 dates/nulls/duplicates 概念 | 原 universe 排除 ETF，使用目前美股成分；不沿用該選樣器。原 normalization 會修補 OHLC，原 client 僅日曆 date，沒有當時可見時間；不能直接充當本案 PIT 管線 |
| [#43](https://github.com/eddy121384-ui/tradingview-indicators/issues/43)，main 的 Hidden Regime 工具 | `train_hmm.py` 的 train-only scaling 與 log-space `forward_filter()` 可供後續引用；#39 留下 input hash／feed drift 教訓 | 不沿用 K=8、SPY profile、事後 state labels 或 HMM 有效的假設；#39 明述沒有跨資產／獲利證明 |
| [#188](https://github.com/eddy121384-ui/tradingview-indicators/issues/188)，封存 SHA `5864f6852042c22594529d8d96d02d73d42c6130` | prereg firewall、相同資料可用度／日期對照、失敗保留、對假想延遲與真正 PIT 的區別 | 月頻修訂總經與既有配置結果不適合本案日頻 price-only 輸入；不讀其報酬 CSV、不重算、不更動封存結論 |

#119 的工作站完成證據來自 [結案留言](https://github.com/eddy121384-ui/tradingview-indicators/issues/119#issuecomment-5902102979)，是既有美股工程證據，並非此雲端環境或本案十市場的成功紀錄。#196 留言亦指出 TradingView 官方 MCP 適合使用者發起的小型互動檢查，不能作無人值守大量下載管線。本案不另建資料平台。

## 2. 實際能力稽核

基底為 `origin/main`：`d76cb3b8404a7421b89ba0477bc127008415b1d0`；開始時工作目錄乾淨。只新增 `research/cross-asset-price-observer/issue-205/`，不複製或修改父研究。

| 檢查 | 本次觀察 | 影響／最小補救 |
| --- | --- | --- |
| 執行環境 Python | `blpapi` 不存在；pandas/numpy 存在 | **High、直接觀察**：不能用預設 Python 執行 BBG；先在既有授權工作站完成 metadata/smoke，非安裝大型替代管線 |
| Bloomberg Desktop API | `/proc/net/tcp` 沒有 LISTEN 8194；環境沒有配置 BBG credential 或 outbound identity | **High、直接觀察**：未建立 session。沒有遠端 BBG session 測試；不推論使用者沒有工作站或授權 |
| 私有快照 | `/workspace/shared`、`library-files`、`scratch` 中 CSV/GZ/Parquet/Feather 數均為 0 | **High、範圍限定**：這些位置無可用快照；不宣稱掃描了所有私人儲存 |
| repo FX metadata | #55 manifest 記載四個 FX 各 2,400 列，2012-12-04 至 2022-03-04 | 歷史短、dealer/close provenance 不充分，final OOS 標為 `SEALED_DO_NOT_EVALUATE`。只讀 manifest，沒有打開四份價格 CSV；本案不使用此封存樣本 |
| 共同樣本／nulls／重複／收盤可見時間 | 本案 10 檔均未取得，全部 UNKNOWN | **High、確定缺口**：不能報告共同列數、缺值率或「20 年完整資料」；公開表格的 UNKNOWN 不能填為 0 |
| 雲端使用與公開衍生摘要權限 | 無本案授權證明 | **High、文件缺口**：BBG／第三方之雲端運算、留存與 aggregate 發表權限逐來源確認；不提交行情、憑證或圖表 |

環境網路清單容許 GitHub 及指定供應商文件域名，但 runtime readiness 回報 network-policy state 為 `unknown`；不把允許域名當成 API entitlement。已實際成功讀取 GitHub 與以下文件頁面，未呼叫行情 API、未購買或聯繫供應商。

## 3. 候選市場、資料型態與歷史長度

**P1 提案固定十檔美國掛牌代理：SPY、QQQ、SHY、IEF、UUP、FXE、GLD、USO、HYG、LQD。** 這是十個價格序列，不是十個獨立風險因子；QQQ/SPY、HYG/LQD 有共同風險。四個預測目標固定 SPY、IEF、GLD、USO，分別代表股票、duration、黃金、油基金。其餘只作輸入。以同一市場日曆與美元交易價格減少同步負擔；不稱為全球交易所的普適驗證。

下列年份是**歷史規劃估計**，不是本次供應商實測起始日；最早／最晚可用日、缺值與授權一律待 manifest 驗證，詳見 CSV。按 2026 年估計：

| core 代理 | 語義與約略可望長度 | 主要限制 |
| --- | --- | --- |
| SPY / QQQ | 股指 ETF；約 1993 / 1999 年起，約 33 / 27 年 | 不等於現貨指數點數；split/cash dividend、adjusted-history revisions |
| SHY / IEF | 1–3Y / 7–10Y Treasury ETF；約 2002 年起，約 24 年 | SHY 不是恆定 2Y、IEF 不是 10Y 合約；duration、carry、配息與基金費用混合 |
| UUP / FXE | 美元指數期貨基金 / 歐元信託價格；約 2007 / 2006 年起，約 19 / 20 年 | UUP 含期貨轉倉，非 DXY spot；FXE 不是 EURUSD spot 或含融資的 FX P&L |
| GLD / USO | 黃金信託 / WTI 期貨基金；約 2004 / 2006 年起，約 22 / 20 年 | USO 含 roll、基金曝險規則變更及反分割，不能當 WTI 現貨或固定近月期貨 |
| HYG / LQD | 高收益／投資級信用債 ETF；約 2007 / 2002 年起，約 19 / 24 年 | 市場價格代理，含 duration/default/liquidity，不是純信用利差；不讀 OAS |

共同歷史理論上受 2007 年的 UUP/HYG 限制，不能達到 20–30 年共同樣本。提案請求 2007-01-01 至 2025-12-31，252 個各檔有效交易日暖機；正式 fit origins 自 2009 年起。**實際共同樣本仍 UNKNOWN**，不能用基金問世年當資料取得證明，也不 backfill 問世前價格。

Deferred 候選為 TU/ZN、EURUSD、CL、VIX。TU/ZN 是可交易期貨（點值、DV01 與合約規格另列）；EURUSD 要固定報價方向與日切；CL 有交割、roll 與非正價格風險；VIX 是期權衍生指數，**非可交易資產、非純成交價格**。這五項不進本輪模型，也不能因 core 成績不好而替換。2Y/10Y 殖利率與信用 OAS 同樣排除。

## 4. 可取得來源：能力與證據層次

1. **首選：既有 BBG 工作站。** 原 #119 `HistoricalDataRequest` 可參考 `PX_OPEN/HIGH/LOW/LAST/VOLUME` 與 split-only flags；先查十檔 stable ID、exchange、price source、timezone、history dates、field exceptions、當時公告／更正時間及權利。`PX_LAST` 是字段名稱，不能自行等同 regular-session official close。原 downloader 固定美股 universe 與舊日期、會修補高低價，不能直接執行當成本案結果。後續最小 adapter 應在新目錄引用 helpers，不修改 #119。
2. **EODHD：可評估的替代來源，非已取得。** [官方 EOD 文件](https://eodhd.com/financial-apis/api-for-historical-data-and-volumes) 本次 HTTP 200，描述 OHLC、adjusted close、volume 與股票／ETF／FX 等日資料，並明述 adjusted close 會隨新配息重算歷史，split-only OHLC 要用 Technical API 的 `splitadjusted`，不能混接 raw OHLC 與 fully adjusted close。各 symbol 實際起始日與修訂可見時間未查。 [條款](https://eodhd.com/financial-apis/terms-conditions) 本次 HTTP 200，限制 redistribution；雲端處理及摘要發表權利不能由 API 可達推定。沒有 token、下載、費用或權限承諾。本文不保存文件內任何價格示例。
3. **Databento：後續期貨候選。** [OHLCV 文件](https://databento.com/docs/schemas-and-data-formats/ohlcv) 可讀、轉向 `/docs/schemas/ohlcv`；官方明述 `ohlcv-1d` 依 **UTC 日期**，不是交易所 session bars，且電子交易彙總 **不等於 official settlement**，不能直接 date-join 本案。兩個試探的 continuous 文件路徑（`/docs/standards-and-conventions/continuous-contracts`、`/docs/symbology/continuous`）均 404，roll 語義未確認。#196 既有留言提及約 16+ 年與成本估價能力，此為舊紀錄，沒有本次 dataset coverage 驗證或價格承諾。
4. **TradingView / 既有 Yahoo 工具**：僅小型人工互動核對或工程參考；本輪不抓資料、不用未確認權限／時點的 live adjusted download 補缺，不依賴短期 artifact 保存唯一輸入。

## 5. 同步時間與可見資料契約

**決策時點固定每個 NYSE regular session 的下一個曆日 08:00 UTC**（台北 16:00）。取該 session 截至收盤的價格，沒有盤後價；在下一個 NYSE regular-session open 前產生預測。美東正常收盤 16:00，夏令 UTC 20:00／冬令 21:00；遇早收盤用交易所歷史日曆。不能用固定 UTC 收盤時間處理全部年份。

- 每列至少有 `instrument_id, session_date, exchange_tz, event_time_utc, available_at_utc, retrieved_at_utc, price_type, adjustment_policy, revision_id, source_hash`；target 另需 regular open。`available_at` 是最早實際可用時間，與下載時間不同。歷史 API 只有 date 時，不可編造當時發布時間。
- 僅接受 `available_at <= decision_time` 的已封存版本。當時 timestamp/vintage 不足時，隔一晚或再延一天只是 **lagged revised-data sensitivity**，不能解決未知修訂，也不能冠 PIT。只能另列 `RETROSPECTIVE_REVISED_PRICES` 診斷，不能解除本案 G-time 或替代正式 H1/H2 裁決；真實 PIT 驗證另以前瞻 append-only 快照完成。
- 十 core 不作 forward/back fill 或插值；休市依日曆辨識。某檔應有卻缺／未到達，當日全組 abstain，B0/B1/A 用相同 mask；公開缺漏與資料遲到率。不得僅保留 A 可預測的漂亮日。
- 跨市場 deferred 系列須用各自官方 close／settlement／fix 的 **發布**時間做 as-of join；美國日期與亞洲日期不能只按字串相等 join。FX 17:00 New York、倫敦 fix、CME settlement 是不同定義，沒有 provider 證據前不指定為本案已確認時間。
- 歷史已知消息與 revision 不能回填決策列。close-to-next-open 的隔夜段不混入「決策後可成交」目標；精確 outcome 見 P1。

## 6. 期貨、公司行動與風險單位

Core 不自行拼接期貨；但 USO/UUP 的內含 roll、持倉規則、費用與 tracking error 仍在基金價格中，必須列為代理限制。USO 的反分割與 2020 曝險規則變化須做 metadata 事件登錄，不能靠改樣本抹去。禁止以殖利率差／WTI spot 的報酬替換 ETF 損益。

若未來納入 TU/ZN/CL，須另 prereg：逐月合約 ID、到期／first-notice、乘數／tick／貨幣／DV01、歷史交易日曆；固定「first-notice 或最後交易日較早者前五個交易所 session」換到下一個合格交割月，並逐合約驗證可交易性。這只是待驗證規則，未知交割 metadata 時停止，不能執行。成交量觸發 roll 若另提案，只能用前一完整日資料。

期貨不得用新舊合約價差製造持有報酬；back-adjust 的過去價格會隨未來轉倉改寫，不能直接餵 point-in-time 特徵。須保存當時 unadjusted 合約價與 roll ledger，同合約內計算價格變動，跨 roll 以逐日美元 P&L／固定事前風險單位加總。非正 CL 價格不能套 log return；未預註冊替代表示前排除期貨研究。點數／tick／notional return／DV01 風險不能混算。這些不是本次新增工程工作。

Core 目標固定 split-only、現金配息未調整的價格報酬，包含 ex-dividend 價格落差；不稱 total return。split factor 必須當時已生效、按相鄰日與區間內事件處理，不能用未來公司行動回改整段訓練快照。日後 P4 才處理配息、bid/ask、滑價、開盤可成交性、基金費用／追蹤與融資；本階段不設定臆測交易成本、不計 P&L。風險尺度為目標自身、當時已知 20 日價格波動，非配置權重或期貨 notional。

## 7. 缺口、啟動 Gate 與下一步

| Gate | 狀態 | 所需證據／負責角色 |
| --- | --- | --- |
| G-data | BLOCKED | 資料操作者在既有合法工作站回傳十檔 stable IDs、各年 counts/nulls/duplicates/min/max、共同交易日、target open 品質、來源／欄位與 hash；公開僅允許的 metadata |
| G-time | BLOCKED | source/session/adjustment/revision semantics 與 availability 證據；無歷史 vintage 時明確降級 retrospective，不能假稱真實 PIT |
| G-rights | UNKNOWN | 資料持有人確認既有授權涵蓋此環境處理、保存與公開 aggregate；不透過本 PR 聯繫外部供應商或購買 |
| G-freeze | DRAFT | metadata-only audit 通過，填入不可變 data manifest/hash、模式與污染登錄；不變更本稿的假說／指標，另 commit 正式 prereg SHA |
| G-execute | NOT_AUTHORIZED_THIS_PHASE | 本次到文件與必要稽核為止；後續 P2/P3 需另有執行指示，不因 Draft PR 自動開始 |

最小下一步是**復用 #119，在既有授權工作站做十檔 metadata-only smoke**；先確認雲端可處理範圍，不建立新平台、不擴樣、不選神經網路。若取不到完整十檔／同期價格與 open，停止並回報，任何縮減標的、改用 futures／total return 或改日期皆需在 outcome 前留下新版本，不能默默換標的。

未解決：實際共同樣本是否足夠？歷史 regular open／close 的字段能否固定？split與修訂是否有 PIT 證據？BBG 或替代來源允許何種雲端處理與摘要發表？十檔代理的資訊能否代表真正跨交易所市場？即使日後通過校準，實際開盤成本與總報酬仍須另一階段回答。

本次驗證：JSON／CSV 可解析、10 core／5 deferred／4 targets 一致、未知 coverage 保持空值、九個來源 SHA-256 重算相符、文件相對連結存在。讀取 70 個既有 workflow trigger headers，本次新路徑不符合其 paths filters；沒有 dispatch 訓練或回測 workflow。這些是文件／provenance 檢查，**不是資料品質通過或模型效果證據**。
