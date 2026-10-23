# P0b v0.2 — 四篇研究與開源可用性

查核日：2026-10-23（Asia/Taipei）。只讀論文、README、license、設定與程式文字／目錄；未安裝、import 或執行外部研究，未取得其原始市場檔／本案 labels。下列「增量」是作者的公開論述，非本案 outcome、獨立重現或跨論文 Sharpe 排名。

## 1. 資料、模型與目標

| 研究／閱讀版本 | 資料與 input | 模型、output／loss |
| --- | --- | --- |
| [DeePM](https://arxiv.org/html/2601.05975v1) v1，§3–6、App.A | Pinnacle 50 futures／FX、1990–2025 daily close，連續合約；報酬／波動／價格特徵。跨市場不同步以 global one-day lag 為主、cascading 為消融 | VSN–LSTM–attention＋跨資產 attention＋macro graph；輸出部位，淨 pooled Sharpe＋worst-window SoftMin，不是報酬 CDF／校準 loss |
| [Deep Inception Networks](https://arxiv.org/html/2307.05522) v1，§II–IV | Pinnacle 50 futures、2000–2022；另測股票、crypto、19 FX。日標準化 returns 同時擷取 TS／CS | Inception 類 feature extractor＋LSTM/TFT position sizer；portfolio Sharpe 加 turnover／long-only correlation regularization；未來 returns 是訓練 target，不是推論 input |
| [Momentum Transformer](https://arxiv.org/html/2112.08534v3) v3（2022 修訂），§IV–V | Pinnacle 50 continuous futures、1990–2020；vol-normalized 多尺度 returns、MACD，選配 online CPD | decoder-only TFT 的 VSN/LSTM/causal attention；輸出每資產 long/short size、Sharpe loss；不是顯式跨資產分布 Observer |
| [Eurodollar uncertainty sizing](https://arxiv.org/html/2007.15982) v1，§2–3 | Reuters 2018 Level-1 quotes，EDc7–15，100 個 event-time curve observations；非日線／長年代資料 | CNN-LSTM-Inception vs MLP，Gaussian mean/covariance 的 NLL；MC-dropout 近似 epistemic，加 aleatoric 後另做 sizing，與前三篇直接 policy loss 不同 |

## 2. OOS、成本、公開實作與限制

| 研究 | OOS／增量證據範圍 | 成本假設 | 原始資料／code |
| --- | --- | --- | --- |
| DeePM | 5 年 expanding、90/10 train/validation，2010–2025 OOS；50 seeds、validation 選 25 ensemble。作者以 lag／graph／loss／cost 消融主張增量；不證明機率校準 | tick／notional、liquidity scalar 等資產別模型，另測 cost-loss scaler；不是本案可直接套用的實際費率 | [MIT repo](https://github.com/kieranjwood/deepm/tree/94aa148295d9147f6533f877256b663b918ed2e6) 已確認；README 明示原始 Parquet 因授權不公開。不能僅靠 clone 重現 |
| DIN | 5 年 expanding、90/10，crypto 改 1 年，5 seeds；作者報告 CS 的效益依家族而異。Hyperband／BO／early stopping 並非小預算單一模型驗證 | 比例 turnover 成本、風險對齊；training regularizers 與 validation 設定須分清；非實際市場深度驗證 | 論文指定 Pinnacle／Compustat 等來源，不等於原檔可公開。本文及作者／title 搜尋未確認作者官方完整 repo；**NOT VERIFIED**，不宣稱不存在 |
| Momentum Transformer | 5 年 expanding、1995–2020 OOS，另列近期／2020；作者主張 temporal attention／CPD 有增量，但家族成本脆弱性不同 | 比例 turnover 0–3 bps 敏感度；需區分原 Sharpe training 與事後成本檢查，不宣稱原模型用了 DeePM cost-aware loss | [MIT sample code](https://github.com/kieranjwood/trading-momentum-transformer/tree/e0352cb0bdbf8045accb1bf1a5705ae0cb9ea624) 已確認；README 改用 CHRIS／100 檔例子，非論文 Pinnacle／50 檔，舊「free」描述不當現行供應承諾 |
| Eurodollar | 月份 1…M−1 fit、M validation、M+1 test（M=7…11），僅 2018 的五個 OOS 月；作者主張 uncertainty sizing 的有限增量，非跨 regime／日線證據 | 0.005 bp／volume 為基準並乘倍數；作者承認遠低於約 0.5 bp quoted spread。非可直接交易成本驗證 | Reuters L1 原檔未提供；本文未連作者 code，title／arXiv 搜尋未確認官方 repo；**NOT VERIFIED** |

## 3. 本案借用與不照搬的部分

| 技術 | v0.2 的決定 |
| --- | --- |
| DeePM 的 directed delay／共同信息集、existence mask、消融 | **立即借用原則**：在資料契約固定 clock／lag／missingness；先比較 B1/A。同日 date 不代表同時可得。graph、GNN、50 seeds、worst-window training 暫不引入 |
| DIN 的 TS／CS 分離與模組對照 | **借用實驗問題**：同一小模型比較自身歷史與跨市場 inputs；feature extractor／position sizer 是後續 benchmark，不把端到端反對兩階段的經濟論點當作本案架構已被否證 |
| Momentum Transformer 的 causal temporal mask、多尺度特徵、時序切分 | **借用因果紀律**；attention／CPD 只是後續需獨立 prereg 的 benchmark，不把 attention map 或 state 故事當 H2 證據 |
| Eurodollar 的 aleatoric／epistemic 分解、分布先於 sizing | **借用輸出語義**：區間寬度與估計可信度分開；先用 proper scores／coverage 驗證。MC-dropout 只是一種近似，不當可靠信心保證；不搬高頻模型、μ/σ² sizing 或原交易成本 |

所有 end-to-end policy 都需先有可交易 returns／cost／risk unit。本案的 SPX、yield、VIX 等 state series 尚無這些條件；不直接移植其 loss、不訓練 Gambler。借用資料同步與公平對照，不能把任何一篇作者績效當本案效果量或門檻依據。

## 4. 可重現性收據

- DeePM pin：`94aa148295d9147f6533f877256b663b918ed2e6`。讀取 `README.md`、`configs/train_settings/deepm-gat.yaml`、`deepm/models/deepm_layers.py` 開頭與 recursive tree；未讀 market Parquet、未啟動 reproduce／smoke 腳本。§6.4／§7.1 的 SoftMin 參數敘述有差異；[固定 config](https://github.com/kieranjwood/deepm/blob/94aa148295d9147f6533f877256b663b918ed2e6/configs/train_settings/deepm-gat.yaml) 是 lambda=0.1、beta=5，若日後重現需先核對，不能從文稿片段猜設定。
- Momentum Transformer pin：`e0352cb0bdbf8045accb1bf1a5705ae0cb9ea624`。讀取 `README.md`、`LICENSE` 與 tree；未執行下載／features／training 程式。原始資料授權與 sample pipeline 可取得性各自待核實。
- DIN 與 Eurodollar：讀取上述 arXiv 全文的方法／評估段落並檢查 code links；搜尋無法確認官方 repo，保留缺口，未將第三方同名 implementation 當作者程式。
- 公開 code license 不授予 Pinnacle／Reuters／Bloomberg 行情權利；本次沒有供應商採購／外聯，也沒有新增軟體依賴。
