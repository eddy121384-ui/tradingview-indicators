# P1 v0.2 — Market Observer prereg 修訂草案

`PRE_OUTCOME / NOT_FROZEN / NO_EXECUTION_AUTHORIZATION`。2026-10-23（Asia/Taipei）。

控制來源：[10/21 scope amendment](https://github.com/eddy121384-ui/tradingview-indicators/issues/205#issuecomment-6310413480)。本稿**明文取代提案** v0.1 的 universe／label／資料證據門檻，保留 [原檔](../prereg-draft.md) 原樣；兩版都未正式 freeze。資料未知不等於已凍結；必須在任何 labels／outcome 計算前補 manifest、共同起點、證據層級及 commit SHA，並等待單獨執行指示。

## 1. 假說與採用層級

H0：少數跨市場狀態與 latent regime 對自身歷史／簡單統計分布沒有穩健增量。H1：相同信息時點、target、日期下，跨市場 A 改善 B1／B0 的 5／20 日分布品質並通過校準。H2：只有 H1 通過，A+Regime 相對 A 才有額外增量。三者均可被否證；state 故事、attention、Sharpe 不能替代 proper scores。

首輪提案以 `REVISED_DATA_RETROSPECTIVE_EXPLORATORY` 進行：來源版本與 lag 假設可稽核、時間外驗證，但不能聲稱歷史實際可見／可交易 PIT。這是使用者修訂明確允許的模式，取消 v0.1 的「無 PIT 即永久禁止回溯研究」前提。`PROSPECTIVE_APPEND_ONLY` 為更高層級的後續方案，另需合法來源、真實 timestamps、封存與授權；本次不收集。

## 2. Cohort、target 與資料 Gate

主要 inputs 固定七個市場：**SPX、US2Y yield、US10Y yield、DXY、GOLD、WTI、VIX**，各來源定義依 [P0 registry](p0-data-feasibility.md)。EURUSD 為第八個補充候選，只作 metadata／後續探索，不進 primary H1/H2，不以其成績決定增刪。沒有 ETF fallback，沒有因 outcome 而替換市場。

Primary reference-price targets 固定 **SPX price index、DXY spot index、GOLD spot/fix**，每個 5／20 reference sessions。這是三個 reference series 的價格變動分布，**不是可成交策略／期貨／含息報酬**。原 #205 的可交易資產分布與 P4 交接仍欠逐商品映射，不據本輪宣稱整個 issue 完成。US2Y/10Y、VIX 是 inputs；WTI 因非正價與來源／roll 未定，首輪 input only，不輸出虛假 log-return target。

請求窗 1990–2025，先取 [手動 Excel 最小欄位](bloomberg-excel-export.md)。OHLCV／next open 不再是最低條件。每主市場必須確認 field、units、source／clock、revision／roll，日期與年度 counts／缺值／重複；年度應有觀測至少 99%，有效共同 origins 至少佔 reference calendar 90%。缺／未知 calendar 不能先視為 weekend；無填補／插值。WTI 若只能取 generic future，維持 pending，先以 metadata 定義 roll-safe state 表示的新 amendment，不能直接拿跨合約跳價當特徵。

每 fold 至少 1,500 個成熟 fit labels、252 個 cal labels；開發至少五個完整評估年且 pooled 1,000 個共同 origins；最終至少 1,000 個共同 origins。coverage 先由 metadata 判定，不看 outcome；失敗就 data-blocked，不移測試窗救樣本。

## 3. Clock、lag 與 5／20 日 outcome 定義

Reference calendar 固定 SPX／NYSE regular sessions。令 t 為剛結束的 reference session，D(t) 為**下一個 reference session 當日 08:00 UTC**（台北 16:00，早於美股開盤）。價格／yield／fixing 各保留原生 local date、timezone、觀測與發布時程，再映射 reference calendar；不把所有日期字串相同的 bars 視為同時收盤。

主規格採一個完整 reference-session 的 **global extra lag**：所有 arms 只用原生觀測映射至 t−1 或更早、且符合來源可見／假設 eligibility 的列。日切或發布比此更晚者需再延遲並在正式 freeze 寫死。B1/A 用同一 target 自身與跨市場 cutoff；不給 A 較晚的資料。這是借用 DeePM 因果延遲原則的保守控制，**不能修復未知歷史 revisions**。

Retrospective 的 `assumed_eligible_at` 必須與真正 `available_at`（未知可空）、`downloaded_at` 分開；未知發布時程不能由 data date 或下載時間推定。來源 clock 仍不清楚就停止正式 freeze，不假設 extra lag 已萬能。前瞻只用已 captured／available 的版本。

為了最低只要求 PX_LAST，v0.1 的 next-open label 改為**下一個 reference close/fix 到再後 h 個 reference sessions close/fix**：

`y[a,t,h] = log(P[a,t+1+h] / P[a,t+1]), h in {5,20}`。

t+1 的 anchor 本身也在 D(t) 之後，絕不進 inputs／normalizer；例如 h=5 用 t+1 至 t+6 的五個 close-to-close increments。來源 close／fix 必須固定，指定端點缺值不改用附近日期，三 targets 共用合法 label mask。這是延後開始的市場 reference-price forecast，不以 fixing／指數點當可成交價，不將尚未知的 next close 當成已知入場資訊。

SPX、DXY、GOLD 合格價格須正；例外 fail closed，不刪除不利事件。方向為 `1[y>0]`。由於最遠 endpoint 是 t+21，split purge 與最後資料邊界都用 **21 reference sessions**，不能沿用 v0.1 的 20。2025 最後 21 origins 不評分，不讀 2026 端點補 labels。

## 4. 因果特徵與單位

只使用 cutoff 以前的相鄰有效原生 session 變動，再映射 reference calendar；lookback 不跨未知缺日：

- SPX／DXY／GOLD：log price changes；不是 total return。
- US2Y／US10Y：`100*(yield_percent_t−yield_percent_(t−1))`，單位 bp；level 可為零／負，不套 log。
- WTI：已確認 spot/assessment 的 **USD/barrel 差值**，可正可負；不除以接近零的價、不對非正值取 log。未確認 roll 的 generic future 不直接使用。
- VIX：指數點差；是衍生市場狀態，不是持有 VIX 的收益。

每序列四項：最新變動／s20、最近 5／20 變動和分別除以 s20×sqrt(5/20)、log(s20/s60)；s 為對應變動的 trailing sample SD（ddof=1、單位內下限 1e-6），window 端點一律在 cutoff。暖機至少 252 sessions。A 共 28 項，加唯一額外特徵 `100*(US10Y_percent−US2Y_percent)`（bp level spread），共29。不是債券套利或 carry。

B1 只有該 target 自身四項；A 有同樣四項＋跨市場項。scaler 只 fit 區估計、SD 下限1e-6、transform clip ±8；cal／test 不重估、不按全樣本分位數裁切。缺市場／無法確定該日已可用時，全組 abstain；不 forward fill、不為 A 刪日而讓 B1 用另一套較佳日曆。

## 5. B0／B1／A 的最小模型與試驗預算

沿用 v0.1 的小統計 family，**不移植四篇論文的大型 NN／graph／Sharpe loss**：

| arm | 固定規格 |
| --- | --- |
| B0-E | 最近 1,260 個已成熟、同一 target/horizon y 的等權 ECDF，至少252個；label endpoint 也須≤該 origin 的 input cutoff（t−1），不能利用較晚資料更新 baseline |
| B0-MV | mean=`h*trailing20_mean(target_daily_log_changes)`，SD=`s20*sqrt(h)`；Student-t df5、scale=SD×sqrt(3/5)，資料止於 cutoff |
| B1 | target 自身四特徵，ridge location／log-variance Student-t df5 |
| A | 相同 family／lambda／calibration，固定29項；與B1比較跨市場增量 |

目標標準化為 `z=y/(target_s20_at_cutoff*sqrt(h))`。location ridge：`sum((z−Xβ)^2)+10*sum(β²)`，intercept 不罰；log-variance ridge 同 lambda 擬合 `log(max((z−mu_fit)^2,1e-4))`。in-sample residual 用於第二 fit，並非 OOS error；sigma_z=`sqrt(exp(clip(logvar,-9.21034,4.60517)))`。

cal 區只估一次 c=`sqrt(mean(((z−mu_z)/sigma_z)^2))`、clip [.25,4]；轉回 mean=mu_z×target_s20×sqrt(h)、SD=c×sigma_z×target_s20×sqrt(h)，Student-t scale 再乘sqrt(3/5)。B0-MV 用自己的 mean／sigma_z=1 以同方式校準，B0-E 不重校。c hit bound 保留警告、不擴範圍；不用 test 改 c。

每 target×horizon 的 B0 comparator 僅按 cal normalized CRPS 選 E 或 MV，tie 選 E，兩者完整報告。B1/A 每 fold 合計 `2 arms*3 targets*2 horizons*2 ridge=24` 次 closed-form fits；lambda10、df5、windows固定，零 parameter search、零樹模型／NN trials。A 維度較高，不能宣稱參數數完全相等，但不給它額外搜尋預算。

## 6. H2 隔離

H1 全 Gate 通過才執行 A+Regime；本版預先固定 K2 diagonal Gaussian HMM，觀測為七市場第3項，不用 outcome／手工 risk-on labels。fit-only scaling、covariance floor1e-3、EM100、tol1e-3、seeds0/1/2，start=(.5,.5)、初始 transition 對角.95，emissions用fit-only seeded k-means。有限／收斂且每 state fit filtered occupancy≥5% 的解中，選 train likelihood 最大、tie小seed；全失敗就 inconclusive，不增加 K／seed。

A 加第二 state 的 filtered probability；只能 `P(S_t|x_<=t)`，不得全歷史 smoothing／事後 state 命名選擇。每 fold 另三個 HMM attempts、12個ridge fits，其他 clock／target／calibration 完全相同。A+ 對 A 的 score 才是 H2，fit likelihood／state 圖不是支持證據。

## 7. 長歷史 OOS 與污染登錄

正式 freeze 先從 coverage metadata 決定 S：七主市場均有252有效session暖機後的第一個完整 reference-calendar 年，不以 outcome 挑起點。年度 fold Y：fit origins=S…Y−3年末、cal=Y−2及Y−1、test=Y，年初一次 refit。最早 test year=`max(2000,S+10)`，確保至少八個完整 fit 年＋兩 cal 年；開發到2019至少五年，否則停止，不將 TV 約2006的US2Y資料硬湊成長歷史研究。

fit→cal、cal→test 移除左側最後21 origins，逐 interval 驗證 label endpoint 早於右區起點、且已成熟／可用。scaler、variance/calibration 均不得接觸右區。每年重做。前一年 test 在之後固定排程中可作成熟 cal/fit 資料，屬 prequential OOS，不是永不更新的模型。

- 開發：最早合格Y至2019，僅一次預先定義 Gate，失敗不調參。
- 最終歷史：2020–2025，single sealed batch；所有預測先封存再一次揭露，不逐年看分數修設計。
- 前瞻：另經授權後，freeze 記錄精確開始時間，下一 reference session 起504 origins並等待最後21 sessions labels成熟；不在本次啟動。

1990–2025 含已知危機、#78/#170/#179/#188 接觸史及本文閱讀的公開文獻；不是全新 untouched history。#55 sealed FX 檔與#196 discovery bars 不打開、不移入。正式 manifest 記 instrument×era exposure（UNKNOWN不能標clean）。只能宣稱對本流程未用於調整的時間 holdout；回溯模式結論加 `retrospective_only`，不當前瞻證據。

## 8. 輸出、校準與裁決

每 origin×三targets×horizon 輸出同一分布的 p(y>0)、q01/05/10/25/50/75/90/95/99、50%/90% interval、5% lower ES，另附 decision/cutoff、source／model hash、assumed/actual availability、證據層級與拒答原因。ECDF inverse quantiles保留ties，ES取含邊界分數權重的恰5% tail；不把 output當期貨／實盤尾損。

區間寬度是 aleatoric return uncertainty；HMM posterior 不是模型信心。附過去252已成熟 forecasts 的coverage/Brier/normalizedCRPS與樣本數，不足則unknown。估計可信度用paired blocks的aggregate／bin intervals；未量化單筆 epistemic，不把窄區間或 MC-dropout 當校準保證。

Primary 為 CRPS／(target_s20_at_cutoff×sqrt(h))；三target等權，5／20 horizon各自裁決。Student-t用確定公式，ECDF用精確`E|X−y|−.5E|X−X'|`。效應=`(meanLoss_control−meanLoss_candidate)/meanLoss_control`。H1四comparisons（A vs B1／cal-selectedB0，各兩h），H2兩（A+ vs A，各兩h）；各hypothesis單尾alpha .025，Bonferroni 下界分別99.375%／98.75%。不另挑單一市場顯著性。

配對 stationary time-block bootstrap：expected block60 reference origins、5,000 replicates、seed205，joint索引套三資產／horizons／arms；不跨年度fold抽block，同年維持原樣本量。block20/120、seed206/207只是固定敏感度，不改primary裁決；三市場×日數不當iid n。

Secondary全報：Brier、log loss（p僅為logloss clip[1e-6,1−1e-6]）、10等寬bins reliability/ECE、PIT（ECDF randomized seed205）、50/90coverage／width、q05breach、pinball、ES診斷。空bin記0，n<50保留但不聲稱可靠；pooled至少500 forecasts、90%forecast mass須落在n≥50 bins。PIT/KS不套iid p值。逐target／年份／h列全部效果、CI、失敗與拒答，不依危機故事挑子樣本。

**開發 Gate：**A vs B1 每h pooled improvement≥1%、至少ceil(.7*評估年數)年為正、符合以下calibration Gate，否則停止、不開最終期。

**H1 supported_retrospective_only：**四comparisons各improvement≥1%、校正lower bound>0；vsB1每h至少2/3targets正、無target惡化>5%、最終至少4/6年正。Calibration Gate：pooled50/90coverage距名目≤5pp、各target≤10pp；pooled q05breach≤8%、各target≤10%；pooledECE≤.05且樣本充分；Brier不差於B1逾.005、logloss不差逾.01。這是本研究事前實用門檻，不來自論文Sharpe或本案outcome。

H2用同Gate，primary改A+vsA兩comparisons、方向／target對照改A；H1未通過即not_tested。資料充足時，若對B1（H2對A）兩h的相同校正upper bounds都<1%，記rejected_for_material_increment_under_this_design；其餘inconclusive。重大source／rights／time／causal failure記invalid/blocked；不刪失敗fold、不改指標救結果。retrospective結論不升格為PIT／live alpha。

## 9. 正式 freeze 前的最小下一步

1. 使用者確認Excel候選／field／clock／權利，提供metadata與獲准處理的values-only日資料。
2. 僅做schema／calendar／coverage稽核，固定source/version、WTI語義、S、證據層級、lag假設與hash；不計labels。
3. 另commit正式prereg SHA，再等待P2執行指示。日後工程先用synthetic fixtures驗證future-append invariance、as-of、units／非正WTI、21-session purge、共同mask與quantile單調。

本次到文件為止。沒有訓練／回測／新outcome、RL／Gambler、P4成本研究、交易下單、Pine變更、merge、CC Desktop或自動行情蒐集。
