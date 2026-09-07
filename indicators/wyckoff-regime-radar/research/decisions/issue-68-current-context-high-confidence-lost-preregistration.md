# Issue #68 — High-Confidence Lost Fresh Semantic Audit Preregistration

Date: 2026-09-07
Branch: `research/issue-68-lifecycle-retest-symmetry-repaired`
PR: #73 (must remain Draft / Open)

## Why this audit exists

The symmetric current-context repair candidate preserves most Fresh S1/S4 anchors and removes stale-looking states selectively, but the lost-fresh anatomy review shows a non-trivial subset of removed Fresh cases with strong production winner margin (`>10`).

This audit asks one narrow question before any production proposal:

**Are high-confidence Fresh losses (`production margin > 10`) genuinely stale-memory cases that production is confidently overrating, or is the current-context cap deleting semantically strong current S1/S4 anchors?**

The `>10` band is not a new tuned threshold. It reuses the descriptive margin band already preregistered and displayed in the preceding lost-fresh anatomy audit.

## Frozen population

Full available 1D history on the same panel used by the symmetric audit:

- US10Y
- DE10Y
- FR10Y
- GB10Y
- AU10Y
- JP10Y

Warmup and model calculations remain identical to frozen C-2 / prior Issue #68 audits.

### S1 high-confidence anchor

`Fresh-S1` remains mechanically frozen as:

- production TOP = S1;
- current `bearBg >= 35`;
- current `downsideExhaustion >= 35`;
- `close - close[20] <= 0`;
- no lookahead.

High-confidence subset adds only the already-existing descriptive condition:

`production S1 winner margin > 10`.

Split into:

- `S1 HC KEEP`: Fresh-S1, margin >10, symmetric CTX result remains S1;
- `S1 HC LOST`: Fresh-S1, margin >10, symmetric CTX result leaves S1.

### S4 exact mirror

`Fresh-S4` remains the exact mirror:

- production TOP = S4;
- current `bullBg >= 35`;
- current `upsideExhaustion >= 35`;
- `close - close[20] >= 0`;
- no lookahead.

High-confidence subset adds:

`production S4 winner margin > 10`.

Split into `S4 HC KEEP` and `S4 HC LOST` identically.

## Frozen intervention

No repair formula changes are introduced.

S1:

`ctxDownExGate = min(downsideExhaustionGate, gate(bearBg, 35, 75))`

S4 exact mirror:

`ctxUpExGate = min(upsideExhaustionGate, gate(bullBg, 35, 75))`

All other stages and multipliers remain production C-2.

## Metrics to report

For S1 HC KEEP / S1 HC LOST / S4 HC KEEP / S4 HC LOST:

1. population N;
2. production winner margin average and maximum;
3. current-context gate average;
4. production historical-background gate average (`max(current background, maturity trace)` path);
5. current background score average (`bearBg` / `bullBg`);
6. maturity-trace score average (`bearMaturityTrace` / `bullMaturityTrace`);
7. trace advantage average = maturity trace - current background;
8. share of bars where maturity trace > current background;
9. exhaustion gate average;
10. cap pressure average = exhaustion gate - current-context gate;
11. production raw S1/S4 average;
12. production effective S1/S4 average;
13. CTX effective S1/S4 average;
14. Fresh age average;
15. absolute 20D yield move average in bp;
16. destination family counts for HC LOST (Bull / Neutral / Bear).

No new plots are required; keep the audit table-only to avoid TradingView plot-budget creep.

## Interpretation locked before output

### Supports the repair candidate

If HC LOST cases, relative to HC KEEP, show materially weaker current context together with larger historical-trace advantage / larger cap pressure, then strong production margin is interpreted as **confident stale-memory support**, not proof that the current-context cap is wrong.

### Challenges the repair candidate

If HC LOST cases have current context, background, and historical/current balance broadly comparable to HC KEEP, yet are removed mainly because the hard `min()` cap is mechanically binding, then the current intervention is too blunt and must not enter production as-is.

### Safety note

Destination family is diagnostic only. A large opposite-family destination share is a red flag for semantic discontinuity, but there is no PnL or forward-return judgment.

## Hard boundaries

- no PnL / returns / Sharpe / drawdown / hit-rate;
- no threshold search;
- no change to 35/75;
- no change to stage weights, gamma, MA, Break, Structure, Strong, Formal, Volume, MTF, Divergence, HMM;
- no one-sided S1/S4 exception;
- no fresh-preserve guard in this step;
- no production edit;
- no merge;
- do not close Issue #68.

This is a casualty-semantics audit only.