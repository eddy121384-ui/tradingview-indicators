# Codex Cloud: official TradingView MCP verification and small interactive pilot

2026-10-16, Asia/Taipei. Issue #199; parent #196; follows the existing Draft PR #200 work at `0920240`.

**CLOUD_MCP_VERIFIED / INTERACTIVE_PILOT_VERIFIED / EXPLORATORY_ONLY / NO_OUTCOME_RUN / production_authorized=false.**

## What changed

The user's completed OAuth approval and environment-setting save enabled this same cloud machine to exchange an authorization code successfully. The official MCP Python SDK then initialized `https://mcp.tradingview.com/mcp`, listed tools, and returned successful symbol searches and real daily OHLCV. No desktop application, unofficial market-data endpoint, scraper, alternate account, or trading system was used.

This is **direct official-MCP access through a cloud Python client**, not proof that TradingView was added to the host's native tool catalog or that ChatGPT's existing OAuth credentials transferred. The platform Codex configuration remains read-only. Earlier CONNECT 403 observations were accurate at the time but no longer describe the successful requests. Earlier uncertainty about OAuth is superseded by a successful code exchange and authenticated requests.

Runtime wire names are `mcp-tv-search-symbols` and `mcp-tv-get-ohlcv`, corresponding to the documented `search_symbols` and `get_ohlcv` tools. The live authenticated OHLCV schema now advertises `date_from`, `date_to`, `format`, and paging hints; the earlier memo's blanket statement that date parameters are unavailable is superseded **as a schema observation**. This pilot did not test date selection/paging and makes no arbitrary-history coverage claim. Expanded technical capability does not authorize bulk collection.

## Actual requests and data provenance

Four explicit searches: SPY with `type_filter=etf`; EURUSD with `type_filter=forex`; XAUUSD with `type_filter=forex` (zero results); XAUUSD without that filter (found the commodity). Then exactly **three** `get_ohlcv` requests, each `interval=1D`, `count=220`, `summary=false`. No paging, scheduler, backfill, outcome query, or account write.

| Window | Selected instrument | Class/price type | Returned UTC dates | Bars | Visible UTC dates | Volume missing / zero |
|---|---|---|---|---:|---|---:|
| W01 | `AMEX:SPY` | US equity ETF price | 2025-12-01–2026-10-15 | 220 | 2025-12-01–2026-09-17 | 0 / 0 |
| W02 | `OANDA:EURUSD` | Broker FX price | 2025-12-10–2026-10-15 | 220 | 2025-12-10–2026-09-17 | 0 / 0 |
| W03 | `OANDA:XAUUSD` | Broker gold price | 2025-12-09–2026-10-15 | 220 | 2025-12-09–2026-09-17 | 0 / 0 |

All responses had `success=true`. Each had 220 unique strictly increasing timestamps and finite, positive, internally consistent OHLC. Those checks do not certify exchange-calendar completeness, independently verified prices, or absence of feed revisions. OANDA volume is provider-specific and is not assumed to be consolidated FX/gold trading volume. No hypothesis uses volume. This is a price sample, not a yield series, dividend total-return index, or rolled futures series.

The service notice says bars depend on the user's plan/exchange subscriptions, may be delayed, use regular sessions, are split-adjusted only, and the last bar may still be forming. The final 20 returned bars were hidden from the exploration view, including the potentially forming last bar. Dates here are returned bar timestamps in UTC, not a claim about local session labels.

## Existing renderer reused, numerical and visual inspection

Used the unchanged PR #200 `masked_window.py`, `--cut 200 --bars 200`, once per instrument. Rendered bars `[0,200)` only, rebased their first close to 100, and omitted dates/symbol labels. The existing SVGs were rasterized solely for visual inspection. Both the three charts and 25-bar summaries of **visible** rebased OHLC were examined. The 20 hidden bars were not inspected for outcomes, scored, or used to select hypotheses.

The render matched the existing renderer's direct output, and multiplying OHLC at/after the cut by ten left the visible SVG byte-identical. All three 200-bar charts were visually inspected. Earlier synthetic smoke checks also passed for 150/200/250 candles, rejected 149/251, and verified future masking and date/name omission. No renderer rewrite or protected source change was needed.

Visible observations motivating candidates, not evidence of predictive skill:

- W01 contains an extended directional rise with stretches of relatively little adjacent-candle overlap; W02 repeatedly revisits overlapping price territory. This motivates measuring displacement versus overlap rather than naming a traditional chart pattern.
- W03 contains wide bars with substantial intrabar travel relative to close-to-close progress. Its visible 25-bar mean high-low range varies much more than W02 after rebasing. This motivates distinguishing two-sided range expansion from directed displacement at a comparable shock size.

**Anonymization is not investigator blinding:** the agent selected the symbols and knows the mapping and dates. Chart labels were removed; no identity-blind or untouched-OOS claim is made. These recent windows also overlap the ChatGPT connectivity check already recorded in Issue #199.

## Two exploratory, falsifiable candidates

Both definitions use only information available at the close of `t`. Thresholds below were chosen after visible-window inspection, not optimized or tested. All three viewed windows are discovery-contaminated. There is one written formulation per candidate, no parameter sweep, and **zero outcome runs**. Novelty is not claimed. Future endpoints below are proposed definitions, not computed results.

Let `O,H,L,C` be daily OHLC, `r_i=log(C_i/C_(i-1))`, and `s_t` the population standard deviation of `r_(t-19)..r_t`; discard rows with zero/undefined denominators or insufficient history.

### H1 — displacement with low adjacent-range overlap

For `i=t-4..t`, define `J_i=max(0,min(H_i,H_(i-1))-max(L_i,L_(i-1)))/(max(H_i,H_(i-1))-min(L_i,L_(i-1)))`.

At close `t`:

- `E_t=abs(C_t-C_(t-5))/sum(i=t-4..t, abs(C_i-C_(i-1)))`.
- `Jbar_t=mean(J_(t-4)..J_t)`; `A_t=mean(i=t-10..t-1,H_i-L_i)`.
- Event: `E_t>=0.75`, `Jbar_t<=0.35`, `abs(C_t-C_(t-5))/A_t>=1.5`.
- Direction: `d_t=sign(C_t-C_(t-5))`.
- Proposed primary endpoint: `Y_t=d_t*log(C_(t+5)/C_t)/(s_t*sqrt(5))`.

Prediction: event rows have greater mean `Y` than non-event controls matched on asset, era, direction, trailing 20-day volatility, and trailing 20-day signed displacement. A future matched mean difference at or below zero is evidence against the candidate; an interval spanning zero is inconclusive. Conditioning on displacement is necessary to test whether overlap adds information beyond ordinary directional persistence. A convincing claim would require independent assets/eras and appropriate uncertainty; none are tested here.

### H2 — two-sided shock versus directed shock at comparable range

Define `R_t=(H_t-L_t)/C_(t-1)`, `M_t=median(R_(t-20)..R_(t-1))`, `Q_t=R_t/M_t`, and `P_t=abs(C_t-C_(t-1))/(H_t-L_t)`.

- Event: `Q_t>=2.5` and `P_t<=0.25`.
- Directed-shock control: `Q_t>=2.5` and `P_t>=0.75`, matched on asset, era, `Q_t`, and pre-event 20-day volatility.
- Proposed primary endpoint: `V_t=mean(R_(t+1)..R_(t+5))/M_t`.

Prediction: events have greater mean `V` than matched directed-shock controls: intrabar disagreement may carry incremental short-run volatility persistence. This is a **volatility**, not return-direction hypothesis. A future matched difference at or below zero is evidence against it; inadequate matched observations or an interval spanning zero is inconclusive. Matching on shock size is necessary to avoid presenting mechanical range mean-reversion or generic volatility clustering as a discovery.

No trigger counts, returns, Sharpe, win rates, MFE/MAE, profitability, or hypothesis support estimates were calculated. These formulas have not undergone the separate engineering/parity stage. Before any confirmation, #196/#197 require independent formula verification, frozen definitions/cohorts/endpoints, handling overlapping events and asset dependence, multiplicity control, and a preregistration SHA.

## Reproduction receipts without licensed prices

| Window | Private response SHA256 | Anonymous SVG SHA256 |
|---|---|---|
| W01 | `56d4c296dd387b5f416da0762cc3ccc4ec2cd62550e318143574ad3d7092f31e` | `985b8ef2a86b63137ad86f142847df6d5679998f25b14937df0f8931880522e7` |
| W02 | `38d5ca02164b5aa25dade49af42bb0d397239bde241e8f26d0d45f3d634418a8` | `3c02f0c8d61e8c672ca91294131de277ee2db13ab530e8b4000575f1b814cf57` |
| W03 | `7e7a760c75f0d774775e8586735a763c2f0849871c5624fffa9aa2932532bc3c` | `0a2271de424bfe3b3e867d5eb85e342006eacea791af977109aff81b07890691` |

Renderer SHA256: `ac803be3f082a5a4974cd1d9bb5ab8d20cc5cdeae7ecef6608567d817c4fc716`. The SDK client and its private data are outside the checkout. Neither raw responses, CSVs, chart images, OAuth callbacks, PKCE verifiers, nor tokens are included in this PR. Rebased charts still encode a time series; anonymization is not treated as redistribution permission.

## Decision and limitations

The immediate cloud connectivity and three-instrument visual/numerical workflow are feasible. No data subscription was purchased. The existing licensed-source survey remains a candidate survey with unverified historical prices/terms; it was not redone. **Bulk-research authorization is still not verified.** Do not expand this MCP experiment into unattended or 300–500-instrument collection.

Use the two candidates only as a demonstration of the discovery-to-formula step. The next research decision is whether they add anything beyond known persistence/volatility effects; do the engineering/literature check and obtain explicit cloud/bulk-research data rights before designing independent confirmation under #196. Keep this PR Draft, leave #195/#197 and existing Pine/research untouched, and do not merge.

Current-session OAuth credentials are temporary, not portable authentication for a fresh cloud task. The cloud setup instructions record how to authorize again if state is absent. The user can clear the consumed callback environment value; it must not be copied into code, logs, or research records.

Official references: [MCP setup/tools](https://www.tradingview.com/mcp/docs), [MCP use conditions](https://www.tradingview.com/support/solutions/43000795699-mcp-server-connect-your-ai-assistant-to-tradingview/). The live authenticated schema, rather than a stale docs snippet, was used for these three requests.
