# Issue #68 — DownEx Current-Context Major-Bull Control Finding

Status: discovery-only finding. Production C-2 remains frozen. PR #73 remains Draft/Open and Issue #68 remains open.

## Frozen control windows

The control audit reused the already-preregistered major Bull-yield windows for JP10Y, US10Y, and GB10Y. No window was selected from the current-context results.

## TradingView observations

### JP10Y

- Population: 778 bars.
- Bull TOP: 34.19% PROD -> 59.38% PROD+CTX (+25.19 pp).
- S1 TOP: 44.99% -> 10.15%.
- Existing PROD Bull retained: 266 / 266 = 100%; Bull lost = 0.
- New Bull gained: 196 bars.
- S1 gate average: 0.52 -> 0.15.
- DownEx cap bound: 92.03% of bars.
- Longest CTX Bear run: 3 bars.
- Existing hard semantic rule: no hard fail.

### US10Y

- Population: 833 bars.
- Bull TOP: 48.38% -> 56.18% (+7.80 pp).
- S1 TOP: 18.25% -> 6.48%.
- Existing PROD Bull retained: 403 / 403 = 100%; Bull lost = 0.
- New Bull gained: 65 bars.
- S1 gate average: 0.22 -> 0.07.
- DownEx cap bound: 93.04% of bars.
- Longest CTX Bear run: 15 bars.
- Existing hard semantic rule: no hard fail.

### GB10Y

- Population: 501 bars.
- Bull TOP: 58.68% -> 63.87% (+5.19 pp).
- S1 TOP: 7.19% -> 1.40%.
- Existing PROD Bull retained: 294 / 294 = 100%; Bull lost = 0.
- New Bull gained: 26 bars.
- S1 gate average: 0.21 -> 0.06.
- DownEx cap bound: 92.61% of bars.
- Longest CTX Bear run: 10 bars.
- Existing hard semantic rule: no hard fail.

## Interpretation

The current-context cap passes the first safety layer: across all three preregistered major Bull controls it loses zero existing Bull TOP bars, increases Bull occupancy, sharply reduces S1 occupancy, and does not trigger the existing >50% Bear or >63-bar consecutive-Bear hard semantic failure.

However, the cap binds on more than 92% of bars in every control. This is a broad intervention. Major-Bull success therefore cannot authorize a production repair by itself; the next required safety layer is explicit preservation of fresh S1 / accumulation semantics.

## Next step

Run a no-lookahead Fresh-S1 Preserve Audit. Do not hand-pick a favorable historical window. Define the control population mechanically from frozen production semantics plus current-path evidence, before observing the counterfactual result.

No PnL, no tuning, no threshold search, no production edit.