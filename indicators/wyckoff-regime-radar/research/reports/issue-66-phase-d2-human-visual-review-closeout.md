# Issue #66 Phase D-2 — Human Visual Review Closeout

Status: **human visual review completed / no PnL / no threshold tuning / no formula changes**

## Scope

This note records the human visual review of the Issue #66 C-2 price-only classifier after:

1. reciprocal / bull-bear symmetry repair;
2. Phase C classifier closeout;
3. Pine generation;
4. first real TradingView ↔ Python runtime parity PASS;
5. restoration of the frozen v0.5.2.1 visual / dashboard / alert shell around the repaired C-2 calculation core.

The visual-review build is:

`research/generated/wyckoff-issue66-phase-d2-c2-visual-review.pine`

For this review, Volume, MTF, Divergence, and stage-bias witnesses remain forced off. The purpose is to inspect the repaired **price-only classifier** in real charts. This is not a strategy-performance review.

## Instruments reviewed

The following daily charts were visually compared between the repaired C-2 build and the earlier v0.5 visual baseline:

- EURUSD
- Europe 50
- USDJPY
- GBPUSD
- AUDUSD

The review focused on whether stage / regime semantics looked coherent relative to the visible price structure, especially around trend continuation, consolidation, high-level stress, and transition zones.

## Main qualitative finding

Across the reviewed instruments, the repaired classifier is visually more coherent than v0.5.

The most consistent improvement is **not** more aggressive turning-point detection. Instead, the repaired classifier is better at separating:

- low-level base-building / Accumulation-like conditions; from
- already active trend progression / Markup or Markdown.

In v0.5, Accumulation could act as a broad catch-all when trend evidence was imperfect. The repaired C-2 classifier more readily recognizes that a market which has already advanced materially should be treated as active trend progression rather than continuing to retain excessive Accumulation weight.

A second improvement is that ambiguous or shock-heavy regions are less likely to be forced prematurely into a full opposite-direction regime. This is consistent with the Issue #66 goal of removing quotation-direction / bull-bear asymmetry leakage.

## Per-instrument observations

### EURUSD — repaired classifier modestly better

Both versions preserve the broad historical directional structure, which is important: the symmetry repair did not destroy the original market intuition.

The repaired classifier appears less eager to force ambiguous regions into a bearish interpretation and more cleanly separates transition from active recovery / upward progression.

Main reservation: the latest region may be slightly aggressive in confidence semantics. The direction may be reasonable while the dashboard wording such as high confidence can sound stronger than the visible higher-level breakout structure warrants.

This is recorded as a **confidence-label calibration observation**, not as evidence that the C-2 classifier formula should be retuned.

### Europe 50 — repaired classifier clearly better

Europe 50 presents a long structural bull regime with intermittent sharp corrections.

The repaired classifier better preserves the broader uptrend regime through temporary shocks while still allowing high-level stress / transition signals to appear. It also reduces the older tendency to retain too much Accumulation weight after price is already well into an extended advance.

The repaired output therefore looks more like a regime detector and less like a collection of local event reactions.

A secondary observation is that the repaired version may express violent panic / shock episodes somewhat less dramatically than v0.5. This is worth preserving as a future research observation, but it is outside the directional-symmetry objective of Issue #66.

### USDJPY — repaired classifier materially better

USDJPY is a useful stress case because the long-run structure is a major upward regime with repeated violent pullbacks.

A weak regime classifier tends either to remain blindly bullish or to interpret every sharp correction as a confirmed bearish takeover.

The repaired classifier handles this better than v0.5. In the latest high-level region it can acknowledge elevated distribution / supply pressure without prematurely declaring a confirmed Markdown regime.

This is considered one of the strongest visual confirmations that the repaired classifier is separating **high-level risk** from **confirmed directional regime change** more coherently.

### GBPUSD — repaired classifier somewhat better

GBPUSD looks more like a post-2022 recovery followed by higher-level consolidation than a fresh low-base accumulation process.

The repaired classifier correspondingly assigns more weight to Markup and less to Accumulation than v0.5. This is visually more consistent with the price structure.

The improvement is positive but less decisive than on Europe 50, USDJPY, or AUDUSD.

### AUDUSD — repaired classifier clearly better

AUDUSD shows a comparatively clean recovery / upward-progression structure from the 2025 low.

The repaired classifier more readily recognizes active Markup and reduces the older tendency to keep excessive weight in Accumulation after the market has already moved materially higher.

This strongly supports the broader finding that Issue #66 improved the distinction between base-building and active trend progression.

## Cross-market conclusion

The five reviewed instruments point in the same general direction:

- EURUSD: repaired classifier modestly better;
- Europe 50: repaired classifier clearly better;
- USDJPY: repaired classifier materially better;
- GBPUSD: repaired classifier somewhat better;
- AUDUSD: repaired classifier clearly better.

No major human-visible semantic regression was identified.

The repaired classifier appears more stable as a regime model without becoming a permanently bullish / bearish or excessively inert classifier. It retains transition and stress regions, but is less likely to let direction-specific heuristics force an inappropriate full regime change.

The earlier concern that the classifier might simply prefer one USD quotation direction is also less visually plausible after this review: EURUSD, GBPUSD, AUDUSD, and USDJPY do not collapse into one common USD-biased narrative. Their outputs are more consistent with each chart's own price structure.

## Remaining observation — shock / panic sensitivity

One qualitative question remains worth preserving for future work:

> Did the symmetry repair slightly reduce the intensity with which extreme short-term shock / panic is expressed?

Europe 50 provides the clearest visual example. The repaired classifier appears more stable through a violent correction, which is desirable for regime classification, but the old version may have communicated the immediate shock more strongly.

This does **not** justify reopening Issue #66 formula or threshold tuning. Regime stability and shock-intensity signaling are different layers. If future research concludes that explicit shock expression is useful, it should be investigated separately rather than reintroducing direction-specific asymmetry into the repaired classifier.

## Phase D-2 verdict

**PASS — human visual review supports C-2 as the repaired price-only classifier baseline.**

Combined with the earlier TradingView ↔ Python runtime parity PASS, the repaired C-2 build is considered sufficiently validated for the objective of Issue #66.

This review does not establish profitability and must not be interpreted as a strategy backtest.

## Recommended closeout boundary

Issue #66 should stop here from a classifier-formula perspective:

- no more threshold tuning to chase 100% symmetry;
- no formula changes based on the five reviewed charts;
- no PnL / Sharpe / CAGR / drawdown optimization inside Issue #66;
- keep the residual shock-sensitivity observation as a future research note only.

After explicit approval to close Issue #66, the next work should move to a successor issue for reintroducing / validating the human-reviewed lifecycle shell and only then reopening strategy / performance research.
