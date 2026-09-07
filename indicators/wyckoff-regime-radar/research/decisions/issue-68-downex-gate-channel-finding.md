# Issue #68 — DownEx S1 Gate-Channel Finding

Status: discovery-only finding. Production C-2 remains frozen.

Window: 2022-01-03 through 2023-12-29, daily.

## Observed TradingView results

### FR10Y

- Production S1 effective avg: 57.97.
- DIRECT-only shadow S1 effective avg: 62.20 (+4.24).
- INDIRECT-only shadow S1 effective avg: 58.10 (+0.13).
- BOTH shadow S1 effective avg: 62.34 (+4.37).
- Interaction: +0.01.
- Bull TOP: production 21.48%; DIRECT 6.05%; INDIRECT 21.48%; BOTH 6.05%.
- Production DownEx gate avg: 0.85; support-invariant direct shadow: 0.91.

### DE10Y

- Production S1 effective avg: 48.31.
- DIRECT-only shadow S1 effective avg: 58.58 (+10.27).
- INDIRECT-only shadow S1 effective avg: 48.60 (+0.29).
- BOTH shadow S1 effective avg: 58.98 (+10.67).
- Interaction: +0.11.
- Bull TOP: production 36.13%; DIRECT 6.45%; INDIRECT 36.13%; BOTH 5.47%.
- Production DownEx gate avg: 0.75; support-invariant direct shadow: 0.91.

## Interpretation

The S1 amplification caused by the support-invariant slope shadow is overwhelmingly transmitted through the direct `downsideExhaustionGate` route. The indirect `downsideExhaustion -> markdownContinuationScore -> nonMarkdownContinuationGate` route is negligible in both FR10Y and DE10Y, and the two-route interaction is also negligible.

Therefore the primary architecture question is no longer whether DownEx is double-routed. It is whether the direct DownEx gate is semantically allowed to remain strong after the bearish/down-leg context that gave exhaustion its meaning has ceased to be current.

The production S1 gate already contains `bearBackgroundForAccGate = gate(max(bearBg, bearMaturityTrace), 35, 75)`. Because this takes the maximum of current bear background and a maturity trace, historical bearish context can keep the Accumulation gate eligible after current `bearBg` has weakened. The next audit therefore tests a current-context bound on the direct DownEx gate without changing any thresholds or weights.

## Boundary

This finding authorizes no production change. No PnL, threshold search, weight change, or stage retuning is allowed.