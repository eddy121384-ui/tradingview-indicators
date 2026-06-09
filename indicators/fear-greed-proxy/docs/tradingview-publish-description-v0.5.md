# Shiori Fear & Greed Proxy v0.5 — TradingView Publish Description

This file contains four TradingView-ready descriptions:

- English
- 繁體中文
- 日本語
- 한국어

---

## English

Shiori Fear & Greed Proxy is a CNN-like market sentiment proxy indicator for TradingView.

It combines several risk-sentiment components into a 0–100 score, helping users observe whether the market is leaning toward fear, neutrality, greed, or sentiment extremes.

This is not the official CNN Fear & Greed Index. It is a transparent proxy model built with TradingView-available symbols and ETF-based market sentiment approximations.

Core components:

Market Momentum — equity strength relative to a long-term moving average.
Stock Price Strength — equity position within its 52-week range, normalized by historical percentile.
Stock Price Breadth — equal-weight equity performance versus market-cap-weighted equity performance.
Put/Call Options — optional slot, disabled by default until the user provides a valid TradingView symbol.
Market Volatility — VIX relative stress, inverted so higher volatility means more fear.
Safe Haven Demand — recent equity return versus bond return.
Junk Bond Demand — recent high-yield bond return versus bond proxy return.

Score zones:

0–25: Extreme Fear
25–45: Fear
45–55: Neutral
55–75: Greed
75–100: Extreme Greed

Features:

0–100 sentiment score line.
Dashboard with total score, regime, data quality, factor count, component scores, and weights.
Four dashboard languages: English, Traditional Chinese, Japanese, Korean.
Customizable dashboard colors and regime colors.
Optional component lines for debugging and deeper analysis.
Auto-reweighting when some data sources are unavailable.

Put/Call note:

Put/Call is disabled by default because symbol availability may differ across TradingView accounts. Users may manually replace the Put/Call symbol with a valid symbol such as a SPY or SPX Put/Call Ratio if available, then increase the Put/Call weight above 0.

Suggested use:

This indicator is best used as a market sentiment thermometer. It may help users observe sentiment extremes, compare market mood with price action, and avoid overreacting during fear or greed phases.

It is not a standalone trade entry or exit signal.

---

## 繁體中文

Shiori Fear & Greed Proxy 是一個 TradingView 版的 CNN-like 市場情緒代理指標。

它會將多個風險情緒因子整合成一條 0–100 分的情緒分數線，協助觀察市場目前偏向恐懼、中性、貪婪，或是否進入情緒極端。

本指標不是 CNN 官方 Fear & Greed Index，而是使用 TradingView 可取得商品與 ETF proxy 建立的透明代理模型。

核心因子：

Market Momentum：股票相對長期均線的強弱。
Stock Price Strength：股票位於自身 52 週區間的位置，並以歷史百分位標準化。
Stock Price Breadth：等權重股票表現相對市值加權股票表現。
Put/Call Options：可選用因子，預設關閉，需使用者自行填入可用的 TradingView Put/Call 商品代碼。
Market Volatility：VIX 相對壓力，並反向處理，波動越高代表越恐懼。
Safe Haven Demand：近期股票報酬相對債券報酬。
Junk Bond Demand：近期高收益債報酬相對債券代理報酬。

分數區間：

0–25：極端恐懼
25–45：恐懼
45–55：中性
55–75：貪婪
75–100：極端貪婪

功能特色：

0–100 市場情緒分數線。
Dashboard 顯示總分、狀態、資料品質、有效因子數、各因子分數與權重。
Dashboard 支援英語、繁體中文、日語、韓語。
Dashboard 顏色與情緒區間顏色可自由調整。
可選擇顯示各因子分數線，方便觀察細節。
部分資料源不可用時，可透過 Auto Reweight 自動重新配權。

Put/Call 說明：

Put/Call 因子預設關閉，因為不同 TradingView 帳號可用的 Put/Call 商品代碼可能不同。使用者可自行改成可用的 SPY 或 SPX Put/Call Ratio 等代碼，並將 Put/Call 權重調高至 0 以上。

建議用途：

本指標適合作為市場情緒溫度計，用來觀察情緒極端、比較情緒與價格走勢，並提醒自己不要在恐懼或貪婪階段過度反應。

本指標不應單獨作為進出場訊號。

---

## 日本語

Shiori Fear & Greed Proxy は、TradingView 用の CNN-like 市場センチメント代理指標です。

複数のリスクセンチメント要素を 0〜100 のスコアに統合し、市場が恐怖、中立、強欲、または極端なセンチメント状態に傾いているかを観察するために設計されています。

これは公式の CNN Fear & Greed Index ではありません。TradingView で利用可能なシンボルと ETF ベースの proxy を使った透明な代理モデルです。

主な構成要素：

Market Momentum：株価が長期移動平均に対してどれだけ強いか。
Stock Price Strength：株価が自身の 52 週レンジ内でどの位置にあるかを、過去のパーセンタイルで正規化。
Stock Price Breadth：均等加重株式のパフォーマンスと時価総額加重株式のパフォーマンスを比較。
Put/Call Options：任意の要素。初期設定ではオフで、利用可能な TradingView の Put/Call シンボルを指定する必要があります。
Market Volatility：VIX の相対ストレス。ボラティリティが高いほど恐怖が強いとみなし、反転処理します。
Safe Haven Demand：短期的な株式リターンと債券リターンを比較。
Junk Bond Demand：短期的なハイイールド債リターンと債券 proxy リターンを比較。

スコア区間：

0–25：極端な恐怖
25–45：恐怖
45–55：中立
55–75：強欲
75–100：極端な強欲

機能：

0〜100 のセンチメントスコアライン。
Dashboard にスコア、状態、データ品質、有効ファクター数、各要素のスコアと重みを表示。
Dashboard は英語、繁体字中国語、日本語、韓国語に対応。
Dashboard とレジーム色をカスタマイズ可能。
各コンポーネント線を任意で表示可能。
データが一部利用できない場合は Auto Reweight で再加重。

Put/Call について：

Put/Call 要素は初期設定でオフです。TradingView アカウントによって利用可能な Put/Call シンボルが異なるためです。利用可能な SPY または SPX Put/Call Ratio などに置き換え、Put/Call の重みを 0 より大きく設定すると有効化できます。

使い方：

このインジケーターは市場センチメント温度計として使うことを想定しています。センチメントの極端な状態を確認し、価格行動と比較し、恐怖や強欲の局面で過度に反応しないための補助として利用できます。

単独のエントリーまたはエグジットシグナルではありません。

---

## 한국어

Shiori Fear & Greed Proxy는 TradingView용 CNN-like 시장 심리 프록시 지표입니다.

여러 위험 심리 요소를 하나의 0–100 점수로 통합하여 시장이 공포, 중립, 탐욕 또는 극단적 심리 상태에 가까운지 관찰할 수 있도록 설계되었습니다.

이 지표는 공식 CNN Fear & Greed Index가 아닙니다. TradingView에서 사용 가능한 심볼과 ETF 기반 proxy를 활용한 투명한 대체 모델입니다.

핵심 구성 요소:

Market Momentum: 주가가 장기 이동평균 대비 얼마나 강한지 측정합니다.
Stock Price Strength: 주가가 자신의 52주 범위 안에서 어디에 있는지를 과거 백분위로 정규화합니다.
Stock Price Breadth: 동일가중 주식 성과와 시가총액가중 주식 성과를 비교합니다.
Put/Call Options: 선택 요소입니다. 기본적으로 꺼져 있으며 사용 가능한 TradingView Put/Call 심볼을 직접 입력해야 합니다.
Market Volatility: VIX의 상대 스트레스를 측정합니다. 변동성이 높을수록 공포가 강하다고 보고 반대로 처리합니다.
Safe Haven Demand: 최근 주식 수익률과 채권 수익률을 비교합니다.
Junk Bond Demand: 최근 하이일드 채권 수익률과 채권 proxy 수익률을 비교합니다.

점수 구간:

0–25: 극단적 공포
25–45: 공포
45–55: 중립
55–75: 탐욕
75–100: 극단적 탐욕

기능:

0–100 시장 심리 점수선.
Dashboard에 총점, 상태, 데이터 품질, 유효 팩터 수, 각 구성 요소 점수와 가중치를 표시합니다.
Dashboard는 영어, 번체 중국어, 일본어, 한국어를 지원합니다.
Dashboard 색상과 구간 색상을 자유롭게 조정할 수 있습니다.
구성 요소별 점수선을 선택적으로 표시할 수 있습니다.
일부 데이터가 없을 경우 Auto Reweight로 자동 재가중합니다.

Put/Call 안내:

Put/Call 구성 요소는 기본적으로 꺼져 있습니다. TradingView 계정마다 사용할 수 있는 Put/Call 심볼이 다를 수 있기 때문입니다. 사용 가능한 SPY 또는 SPX Put/Call Ratio 등으로 바꾸고 Put/Call 가중치를 0보다 크게 설정하면 활성화할 수 있습니다.

사용 방법:

이 지표는 시장 심리 온도계로 사용하는 것을 목표로 합니다. 심리의 극단 구간을 확인하고, 가격 흐름과 비교하며, 공포나 탐욕 구간에서 과도하게 반응하지 않도록 돕는 보조 도구로 사용할 수 있습니다.

단독 진입 또는 청산 신호가 아닙니다.
