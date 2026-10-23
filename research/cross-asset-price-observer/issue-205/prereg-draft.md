# #205 P1 prereg 草案 v0.1

`DRAFT_DESIGN_FIXED / DATA_MANIFEST_PENDING / NO_OUTCOME_RUN`

日期：2026-10-21（Asia/Taipei）。控制需求：[Issue #205](https://github.com/eddy121384-ui/tradingview-indicators/issues/205)。[P0 與未解 Gate](p0-feasibility.md) 是本稿前提。

**本 commit 固定以下設計提案，但尚非可執行的正式 prereg。** 未知的來源、時間戳、hash 與可用樣本不能假裝凍結完成。正式 freeze 必須另有不可變 manifest、經證實的 PIT 可見資料契約、污染登錄及完整 SHA；在任何 outcome 計算前提交。只有修訂後歷史時保持 G-time BLOCKED，若要做 `RETROSPECTIVE_REVISED_PRICES` 診斷須另寫 outcome 前 amendment，不能用診斷取代本稿正式裁決。日後執行仍須另獲指示。本階段不訓練、不回測、不算任何候選未來 outcome。

## 1. 問題、假說與解釋範圍

- **H0**：在相同資料可見時間、目標、日期與計算預算下，跨資產輸入對單資產／簡單統計 baseline 沒有穩健、達實質門檻的分布預測增量。
- **H1**：A 相對 B1 及 B0，在未用於設計調整的年代，改善固定四目標的 5 與 20 日報酬分布品質，並符合方向、分位數與尾端校準限制。
- **H2（條件式、獨立報告）**：H1 通過後，A+Regime 相對同一 A 額外改善分布品質。漂亮 state、聚類分離、train likelihood 或 Risk-on 故事均不構成支持。

只比較此提案下的價格資訊；不引入新聞、總經發布／修訂值、手工市場狀態標籤、#196 K 線假說或 #188 總經分組。不聲稱價格預言、因果機制、alpha 或 production。`production_authorized=false`。

## 2. 凍結 cohort、來源與樣本 Gate

十輸入固定 **SPY、QQQ、SHY、IEF、UUP、FXE、GLD、USO、HYG、LQD**；四 target 固定 **SPY、IEF、GLD、USO**。皆以美元掛牌基金價格表示；[候選 CSV](candidate-universe.csv) 記錄代理限制，deferred 標的不參與或替補。不根據 outcome 刪市場。此設計是跨風險家族的美元代理測試，不是未見資產 generalization 測試。

原始請求窗固定 2007-01-01 至 2025-12-31；不載入 2026 價格作設計。至少 252 個該標的有效 session 暖機，fit origin 自 2009 年起；缺資料不向前合成。正式資料只保存在獲准位置；公開僅 schema、metadata、hash、授權允許的 aggregate。

資料 Gate：每 core 各年有效 close 至少佔其應有 NYSE sessions 的 99%；target regular open 同門檻；所有 target 在每個 fold 至少 1,000 個成熟 fit labels、252 個成熟 calibration labels。開發評估至少 756 個共同 origin、最終至少 1,000 個，且各 target 至少覆蓋該期間 90% 應有 origins。先依 metadata／calendar 判定，不讀未來報酬分布。無法達成則 `inconclusive/data_blocked`，不移動切割救結果。

來源正式 manifest 必填：stable ID/venue、字段、price type、currency、split policy、session calendar/tz、availability/revision semantics、擷取時間、每檔／共同 coverage、程式與檔案 hashes、使用權限、known exposure。來源模式不同不可混成同一實驗。

## 3. 每日 Observer 輸入、時間與目標

Decision D(t) = NYSE session t 下一曆日 08:00 UTC，只用 available_at ≤ D(t) 的 session t 及更早 regular close。B0/B1/A/A+Regime 完全同時點。無合法可見快照時停止主研究；另獲授權的 revised-price 診斷不得稱 actionable historical PIT。

令 t+1 是下一 NYSE session，h ∈ {5,20}，固定目標：

`y[a,t,h] = log(C_split[a,t+h] / O_split[a,t+1])`。

它涵蓋從下一開盤到第 h 個 session 收盤的 h 個交易日；不含 t 收盤到 t+1 開盤的隔夜報酬。split-only、現金配息未調整；區間內 split 用當時生效事件保持股份尺度。不是期貨報酬、含息總報酬或淨成本策略 P&L。direction 為 `1[y>0]`，零報酬屬非正。target open 只在 label 形成時讀取，絕不進 t 特徵。

任一 core close 缺漏／未可見即當日全組 abstain；所有模型在完全相同 origins 比較；不能為 B1 另保留 A 無資料日期。label 任一指定端點缺漏即該 cell 缺失，不以其他日代替；報告共同 mask 及拒答率，不插值／填補。成熟 label 必須其終點價格已 available，而非只是日曆時間已過。

## 4. 特徵：固定少量、因果、無搜尋

每個序列只用 split-event-safe 的 close 變動 `r_t=log(C_t/C_(t-1))`；`s20_t` 為最近 20 個 session r 的 sample SD（ddof=1，單位日 log return），零值下限 `1e-6`。每檔四特徵：

1. `r_t / s20_t`。
2. `sum(r[t-4:t]) / (s20_t*sqrt(5))`。
3. `sum(r[t-19:t]) / (s20_t*sqrt(20))`。
4. `log(s20_t / s60_t)`，s60 同定義、同下限。

B1 只用 target 的四項；A 使用十檔共 40 項，再加三項差值：SHY−IEF、HYG−LQD、GLD−USO 各自上述第 3 項（共 43）。這是標準化相對動量，**不是殖利率期限利差或信用 spread**。不額外加入所有 pairwise interaction／PCA／特徵選擇。無 volume、calendar 或當日 open。

每個 fold 的每欄均值／SD 只在 fit 區估計，SD 下限 `1e-6`；transform 後 clip ±8，cal/test 不重估、不用全樣本 winsorization。所有 lookback 必須是有效連續 session；不能跳過缺日把 20 列當成 20 日。

## 5. 對照與小型模型：不跑參數網格

固定分開對各 target×horizon 擬合；不把不同 target 當獨立 iid 行。**首輪唯一 supervised family 是兩個 ridge regression 的 location/scale Student-t Observer**。不選定神經網路、不做 autoML、不另跑樹模型競賽。小樹／分位數迴歸可作未來新 prereg 候選，當前試驗預算為零。

| arm | 固定定義 |
| --- | --- |
| B0-E | 滾動最近 1,260 個已成熟 y 的等權 empirical CDF；至少 252 個。每個 origin 僅加入已 available 的 labels，ties 保留；ECDF quantile 使用 inverse-CDF（第一個累積概率達 q 的值） |
| B0-MV | 簡單動能／波動：mean = `h*sum(last20 r)/20`；SD = `s20_t*sqrt(h)`；Student-t df=5、scale=SD×sqrt(3/5)。不得掃動能窗或自由度 |
| B1 | 以下相同 location/scale family，只用自身四項 |
| A | 同 family／lambda／calibration，使用固定 43 項跨資產特徵 |
| A+Regime | 僅 H1 通過才可進 P3；同 A 加一個 K=2 的 filtered state 機率，沒有手工 state 名稱 |

B1/A 對標準化目標 `z=y/(s20_t*sqrt(h))`：第一個 ridge 最小化 `sum((z-Xβ)^2)+10*sum(β²)`，intercept 不罰；第二個同 lambda ridge 擬合 `log(max((z-mu_fit)^2,1e-4))`。第二階段使用 fit 區 in-sample residuals（已知偏小風險，不能解讀為 OOS error）；預測 `sigma_z=sqrt(exp(clip(logvar,-9.21034,4.60517)))`。不用 test residual 改 scale。

轉回 y：mean=`mu_z*s20_t*sqrt(h)`，SD=`c*sigma_z*s20_t*sqrt(h)`；固定 Student-t df=5 的 scale=SD×sqrt(3/5)。c 在獨立 calibration 區以 `sqrt(mean(((z-mu_z)/sigma_z)^2))` 估計後 clip [0.25,4]，每年只估一次。B0-MV 也用相同 cal scale 公式；B0-E 原樣、不做偏好性校準。若 c hit 邊界，保留並標示，不擴範圍。方向 p、quantiles 與 tail 均來自同一分布，不各自調到好看。

B0 comparator 在每 fold 僅按 calibration 的 mean normalized CRPS 選 B0-E 或 B0-MV，平手選 B0-E；test 永不選。兩種 B0 都完整報告，不能用較弱者聲稱增量。B1/A 的架構相同，A 維度較高的優勢由固定 regularization／OOS 承擔，不聲稱參數數量完全相等。

每 fold supervised 預算：B1/A 各 4 targets×2 horizons×2 ridge = 16 次，兩 arm 共 32 次 closed-form fits；lambda 固定 10、無搜尋／restart。B0 無搜尋、每 arm/horizon/target 最多一次 cal scale。數值失敗直接記錄，不追加 family 或 seed。

## 6. H2 的固定額外規格

只有 P2 的 H1 通過全部 Gate 才可執行，不因描述性 states 有趣而提早啟動。HMM 觀測固定十檔第 3 項（10 維），只用 fit 區 scaling；K=2、diagonal Gaussian、covariance floor=1e-3、EM max_iter=100、tol=1e-3、seeds={0,1,2}，初始 startprob=(0.5,0.5)、transmat 對角 0.95／非對角 0.05，emissions 用該 seed 的 fit-only k-means 初始化。

只在有限且收斂解中選最高 train likelihood、平手取較小 seed；任一 fit state 平均 filtered occupancy <5% 即該解不合格。最多三次，全部失敗則 H2 inconclusive，不改 K、不加 seed。只使用 `P(S_t|x_<=t)` 的 forward filter，禁止 full-history smoothing／Viterbi hindsight；跨 gap 也只 sequential filter 可見觀測。可引用既有 `forward_filter()`，但不執行父研究訓練 entrypoint。

不跨 refit 以 raw state ID 命名或挑「risk-off」；固定加入第二 state 的概率（另一項冗餘），標籤置換不影響可擬合資訊。HMM 重新 fit、生成 fit/cal/test filtered features、A+ 兩 ridge 與 c 的步驟皆限當年合法資料；每 fold 多 3 個 HMM attempts、16 個 ridge fits，零額外搜尋。其餘目標、mask、scoring、calibration 與 P2 完全一致。

## 7. Walk-forward、purge 與隔離

NYSE sessions、年度按 origin 日期切分，固定 expanding fit + 兩年 calibration + 一年 test。對每個評估年 Y：fit origins 為 2009-01-01 至 Y−3 年末；calibration 為 Y−2 與 Y−1；test 為 Y 全年。2016 首 fold 即 fit 2009–2013、cal 2014–2015、test 2016；此後機械前推，每年首個預測前 refit 一次。不得在年中因結果重訓或改規則。

為兩個 horizon 共用保守界線：fit→cal、cal→test 各移除左側最後 20 個 NYSE origins，並逐 label interval 驗證 `label_end < next_partition_start` 與 availability。未成熟 labels 不得進入 fit 或 c。對每次 refit 都重做，不只第一個 fold。test 不回訓同年度；前一年 test 依已凍結的排程、成熟及 purge 規則，日後可以進 calibration/fit，屬 prequential OOS，非六年完全固定模型。

- **開發 walk-forward：2016–2019**，四年只檢查預先寫定 Gate；不調參。若開發未通過 §10，停止，最終期保持封存。
- **最終歷史 lockbox：2020–2025**，六年，單次自動整批執行；運算可機械使用先前年份成熟資料，但人員不得逐年看分數修設計。所有年度預測先封存，再一次揭露整體與細分分數。
- **真正未來樣本**：正式 freeze／另行執行授權後下一個 NYSE session 開始，預先固定 504 個 origins 並等待最後 20 日 label 成熟；不看中途績效更改設計。前瞻開始的精確 timestamp 必須在 freeze 記錄，不能回溯選起點。此前只規劃，不啟動收集或訓練。

污染登錄：#55 sealed FX 不讀不用；#196 pilot 已曝光，不移入；#78/#170/#179/#188 已接觸歷史與一般金融事件知識，2020–2025 不能稱為全新 untouched history。它只能是**對此新固定流程未用於調整的時間 holdout**。沒有未見資產 claim；通過歷史結果仍需前瞻才能提高可信度。正式 freeze 補全 instrument×era 的 known/unknown exposure，未知不得標 clean。

原始窗止於 2025-12-31，最後 20 個 2025 origins 從兩 horizon 的共同評分移除，確保所有 label endpoints 都在窗內；不為取得年末 labels 讀入 2026 價格。歷史 PIT 不成立時，上述歷史設計只是待滿足資料條件的規格，不得由目前 revised download 啟動。

## 8. 輸出契約：分布不等於估計信心

每個 origin×target×horizon 輸出：decision/as-of、資料與模型 hash/version、價格／return basis、arm、p(y>0)、q={.01,.05,.10,.25,.50,.75,.90,.95,.99}、50%/90% interval、5% lower-tail expected shortfall、data-quality/abstain flag。B0-E tail 用 empirical quantile 下的含邊界分數權重取得恰 5% tail mass；Student-t tail 用其固定分布公式。ES 是模型 tail estimate，非保證或策略損失。

區間寬度代表 **aleatoric return uncertainty**。不把 HMM posterior、低 entropy 或窄區間稱為 epistemic confidence。附上截至當日已成熟的過去 252 origins 校準樣本量、90% coverage、Brier 與 normalized CRPS；不足 252 記 `calibration_unknown`。整體／分組估計可信度以 §9 joint-block confidence intervals 呈現，不聲稱已量化單筆 epistemic posterior。原始 p 與 quantile 不因這些診斷而再次調整。

## 9. 評分、相依樣本與多重比較

**Primary：normalized CRPS**，以 forecast y 的 CRPS 除以該 target／origin 當時的 `s20_t*sqrt(h)`；Student-t 用確定性公式，ECDF 用 `E|X-y|−0.5E|X-X'|` 精確計算。不以 Sharpe、勝率或績效替代。四 target 等權，h=5、20 **分開**裁決，不能用單一 horizon 救另一個。

每個 horizon 的 effect=`(mean loss_control−mean loss_candidate)/mean loss_control`。H1 四個 planned contrasts：A vs B1 及 A vs cal-selected B0，各兩 horizon；H2 兩個：A+ vs A，各兩 horizon。全程只這兩假說，給 H1/H2 各單尾 alpha=0.025；H1 四比較 Bonferroni 下界用 99.375% 單尾，H2 兩比較用 98.75% 單尾。僅宣告整體 gate，不對 asset/year 細格挑顯著結果。

使用 paired stationary bootstrap，expected block=60 NYSE origins、5,000 replicates、seed=205；一次抽 joint 日期索引，同時套用全部 arms／四資產／兩 horizon，保留市場共同衝擊與 20 日重疊相依。每 fold 邊界不跨抽 block，按原年樣本量重新組合；不可將 4×日數當 iid n。20/120 block 僅作預先列定敏感度，各 5,000 replicates、seed=206/207，不改 primary 裁決；方向矛盾須報告。

Secondary／calibration 全報：direction Brier/log loss（p clip [1e-6,1−1e-6] 只為 log loss）、10 個固定等寬 p bins 的 reliability/ECE、PIT histogram（ECDF 用 seeded randomized PIT，seed=205）、50%/90% interval coverage 與寬度、q05 breach rate、.05/.50/.95 pinball loss、ES 診斷。bin n<50 不推定該 bin 可靠，但仍納入 ECE、空 bin 記 n=0；充分性要求 pooled 至少 500 forecasts，且至少 90% forecasts 位於 n≥50 的 bins，其餘標 inadequate。不能無聲刪小 bin；PIT/KS 不套 iid p 值。

分層列出四 targets、每年、5/20 日，樣本數、abstentions、所有失敗與 CI；罕見尾端只作不確定性診斷，尾端命中次數不夠不能稱精準 ES。相同 masks 與全部 B0 都要留存。禁止事後換 CRPS 為 log loss／損益救結果。

## 10. 通過、停止與裁決（事前門檻、非已觀察數值）

開發 Gate：資料／因果驗證通過；A vs B1 每 horizon 的 2016–2019 pooled CRPS improvement ≥1%，至少 3/4 年為正；且符合下列 calibration Gate。失敗即停止 P2，不揭露 lockbox、不增加模型。

**歷史 H1 supported 必須同時符合：**

1. 四個 primary contrasts 的 improvement 均 ≥1%，且 §9 校正後 lower bound >0。
2. vs B1 每 horizon 至少 3/4 targets 為正，無 target 惡化 >5%；至少 4/6 年為正，不能只由單一事件成立。
3. Calibration Gate：每 horizon pooled 50%/90% coverage 各距名目 ≤5 個百分點，且每 target 各 ≤10pp；pooled q05 breach ≤8%、各 target ≤10%；pooled ECE≤0.05，並符合 §9 樣本充分性要求。這些是預先選定的實用容忍度，非金融定律。
4. 方向 Brier 不比 B1 差 >0.005、log loss 不比 B1 差 >0.01（每 horizon pooled）；沒有因果／來源完整性失敗。所有區間與方向指標一併公開。

H2 supported 要 A+ vs A 兩 contrasts 各 improvement≥1%、校正 lower bound>0，並通過相同的 target/year/calibration Gate（方向對照改 A）。HMM state 解釋力不得替代這些條件；H1 未通過時 H2=`not_tested/prerequisite_failed`。

在資料充足與完整性通過下，若 vs B1（H2 則 vs A）兩 horizon 的相同校正 **upper bounds** 都 <1%，判該假說 `rejected_for_material_increment_under_this_design`；不代表對所有市場／模型證明 H0。其餘無法全部支持、精度不足或結果相衝突一律 `inconclusive`。開發失敗記 `inconclusive/development_gate_failed`，不冒稱最終檢定 rejected。重大資料洩漏／rights／model failure 則停止並標 invalid/blocked，不挑剩餘成功 folds。

停止後保存失敗，不追加 features/K/NN／新切點、不重開 lockbox、不為勝率改假說。任何更改均新版本、說明資料接觸與獨立新 holdout；工程 bug 若在揭露後發現，保存原輸出與修正差異，舊 holdout 從此不是 untouched。

## 11. 後續實作的驗收與交接（本次不執行）

正式 freeze 後的最小實作需先用 synthetic fixtures 驗證 future-append invariance、train-only preprocessing、split/revision as-of、DST/早收盤、next-open label endpoints、20-session purge／成熟度、相同 mask／缺日 abstain 與分布 quantile 單調。不得用正式 outcomes 修公式。P2/P3 一律從新目錄引用必要 pure helpers，不啟動既有 train/backtest workflows。

產物應有正式 prereg SHA、data/provenance manifest、全 trial/failure ledger、各 arm 每日 OOS distribution、共同 masks、分層 calibration／paired CI、supported/inconclusive/rejected 裁決及限制。沒有 P2 結果前不做 P4；若通過，另固定同一簡單風險／下注規則，再研究費用、滑價、配息、轉倉及同風險成本比較。不訓練 RL Gambler、不下單、不改 Pine、不合併 PR。
