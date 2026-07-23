# Hidden Regime Map v0.3 Usable Indicator Specification

## Decision

Create a separate Pine v6 user-facing indicator for the frozen `SPY 1D` profile.

The v0.2 parity spike remains the audit/reference implementation. The v0.3 script removes checkpoint machinery from the default chart experience but must preserve the same feature calculations, frozen parameters, initialization, transition orientation, and causal forward-filter mathematics.

This is a productization pass, not a model upgrade.

## Supported profile and limitations

The only supported use is:

- profile: `spy-1d-v0.1`;
- symbol: SPY;
- timeframe: 1D;
- prices: TradingView standard daily OHLC with dividend adjustment;
- inference: confirmed-bar causal forward filtering;
- state count: three.

The user-facing script must not display plausible-looking regimes outside SPY 1D. Unsupported use must suppress regime plots and show an obvious warning.

The formal research result remains **feed mismatch** because the frozen Python fixture used Yahoo Finance adjusted OHLC while Pine uses TradingView dividend-adjusted OHLC. Posterior, probability-sum, and dominant-state agreement observed across the two feeds are diagnostics only and are not proof of identical-input parity.

## Frozen model contract

The v0.3 script must reproduce the merged parity reference without changing:

- the three feature formulas;
- feature lookbacks;
- scaler means and scales;
- start probabilities;
- transition matrix orientation;
- emission means and diagonal variances;
- feature-start anchor date;
- confirmed-bar update behavior;
- log-space normalization;
- dominant-state tie-breaking.

The authoritative model artifact remains `models/spy-1d-v0.1.json`.

No smoothing, persistence override, hysteresis, minimum-duration rule, discretionary relabeling, or visual state substitution is allowed.

## State labels and colors

Use the approved SPY-specific labels while retaining the A/B/C state identifiers:

| State | Label | Primary color | Interpretation boundary |
|---|---|---|---|
| A | two-sided stress | red | high-volatility stress; not automatically bearish |
| B | advance | orange | ordinary advancing regime |
| C | calm advance | teal | lower-volatility advancing regime |

Colors are semantic display choices only. They do not change inference.

The script header and dashboard must make clear that these labels are asset-specific descriptions of the frozen SPY model, not universal market-state definitions.

## Default visual hierarchy

The default chart view should communicate information in this order:

1. dominant regime through subtle background shading;
2. current A/B/C posterior probabilities through three lines;
3. compact dashboard showing current state and confidence;
4. optional state-transition markers;
5. optional research diagnostics.

### Posterior lines

- Plot A, B, and C as percentages from 0 to 100.
- Use the same red, orange, and teal state colors.
- Use equal line widths so the UI does not imply one state is structurally more important.
- Include a 50% horizontal guide.
- Do not smooth the posterior lines.

### Background shading

- Enabled by default.
- Shade using the current dominant-state color.
- Keep opacity high enough that candles and other chart content remain readable.
- Apply only when the symbol/timeframe is supported and the filter is initialized.

### Dashboard

Place a compact dashboard at the top right containing:

- status;
- profile ID;
- current dominant state and asset-specific label;
- A probability;
- B probability;
- C probability;
- confidence level;
- maximum posterior;
- margin between the largest and second-largest posterior;
- limitation note: `SPY 1D frozen model`.

The default dashboard must not include checkpoint counts, fixture errors, parity maxima, raw transition matrices, or the 12-row evidence table.

## Confidence definition

Confidence describes **posterior concentration only**. It is not forecast accuracy, win probability, expected return, signal quality, or trading conviction.

Calculate:

- `max_posterior`: the largest of A/B/C;
- `second_posterior`: the second-largest of A/B/C;
- `posterior_margin = max_posterior - second_posterior`.

Display confidence using both measures:

- **High**: `max_posterior >= 0.75` and `posterior_margin >= 0.25`;
- **Medium**: `max_posterior >= 0.60` and `posterior_margin >= 0.10`;
- **Low**: all other initialized cases.

Rationale:

- maximum posterior measures absolute concentration;
- the margin prevents a near tie from being labelled high confidence;
- the thresholds are UI interpretation gates, not trained parameters;
- the thresholds do not affect the dominant state, history, filtering, or state changes.

The dashboard should show both the level and underlying values so the heuristic remains auditable.

## Transition markers

Transition markers are optional and disabled by default to avoid chart clutter.

When enabled:

- place one compact marker on the first confirmed bar where the dominant state differs from the prior confirmed bar;
- show the new state identifier, such as `A`, `B`, or `C`;
- color the marker with the new state's color;
- do not mark initialization as a transition;
- do not create intrabar markers;
- do not add minimum-duration confirmation or retrospective relocation;
- historical markers must remain fixed after the bar is confirmed.

## Inputs

Keep the user-facing input set small:

### Display

- show posterior lines: default on;
- shade dominant state: default on;
- show dashboard: default on;
- show transition markers: default off;
- show research diagnostics: default off.

Do not expose model parameters, feature lengths, scaler values, thresholds for state selection, or initialization date as user-editable inputs.

Confidence thresholds are fixed in v0.3 and documented in this spec. They are not user inputs in the first usable version.

## Research diagnostics

When `show research diagnostics` is enabled, the dashboard may additionally show:

- standardized return;
- ATR percentage;
- trend strength divided by ATR;
- posterior sum;
- whether the current bar is confirmed;
- frozen profile ID.

The user-facing script must not duplicate the 12-checkpoint evidence table. Full parity auditing remains in `pine/hidden-regime-map-spy-parity.pine` and the committed parity report.

## Unsupported and initialization states

The script must distinguish at least:

- unsupported symbol;
- unsupported timeframe;
- insufficient history or missing exact feature-start anchor;
- initialized and active.

For unsupported or uninitialized cases:

- suppress A/B/C regime plots and background shading;
- suppress transition markers;
- show a clear red or amber dashboard warning;
- do not fall back to a shortened-history initialization;
- do not silently start from the first visible chart bar.

Recommended wording:

- symbol warning: `Unsupported symbol — use SPY`;
- timeframe warning: `Unsupported timeframe — use 1D`;
- history warning: `Need history from 2010-05-26`;
- active status: `Frozen SPY 1D model active`.

## Repainting and timing contract

- Update the HMM only on confirmed daily bars.
- No future values or lookahead are permitted.
- The current unconfirmed daily bar must not advance the filter or create a transition marker.
- Historical state backgrounds and markers are non-repainting after bar confirmation, subject to TradingView vendor-data revisions.

## Documentation wording

The script header and README must state all of the following:

- SPY 1D only;
- fixed model trained outside Pine;
- no automatic retraining;
- state labels are SPY-specific;
- confidence is posterior concentration, not predictive accuracy;
- formal Python-versus-Pine result is feed mismatch due to adjusted-price vendor differences;
- the indicator is descriptive research tooling, not a strategy or financial advice.

## Acceptance

The v0.3 implementation is acceptable when:

- a separate user-facing Pine v6 script compiles on SPY 1D;
- current A/B/C posteriors and dominant state match the merged parity script on the same SPY 1D chart;
- no model or feature parameter differs from the frozen profile;
- unsupported symbols and timeframes display a warning and no plausible regime output;
- the default view contains no checkpoint evidence table;
- confidence follows this documented formula and thresholds;
- transition markers appear only after confirmed dominant-state changes;
- research diagnostics are off by default;
- README and script comments preserve the feed-mismatch limitation;
- no future leak or intrabar state advancement is introduced.

## Manual chart checks

Before merge, verify on TradingView:

1. SPY 1D with sufficient history initializes and displays the same current probabilities and dominant state as the parity reference.
2. The default dashboard is readable without opening settings.
3. Transition markers are absent by default and appear correctly when enabled.
4. Another symbol produces an unsupported-symbol warning and no regime output.
5. SPY on a non-1D timeframe produces an unsupported-timeframe warning and no regime output.
6. Hiding posterior lines, background, dashboard, and diagnostics works independently.
7. Research diagnostics do not expose or recreate the checkpoint table.

## Non-goals

- model retraining or TradingView-based refit;
- any asset other than SPY;
- any timeframe other than 1D;
- alerts;
- MTF;
- strategy entries, exits, PnL, optimization, or backtest;
- smoothing or persistence overrides;
- QQQ, TLT, GLD, futures, or Taiwan equities;
- Wyckoff integration;
- public TradingView release copy.

Refs #24, #22, and PR #23.
