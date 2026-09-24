# Issue #109 A2 pre-outcome transport amendment — self-contained exact V6.6 axes

Status: **ENGINEERING TRANSPORT AMENDMENT — BEFORE ANY A2 PAYOFF RESULT WAS VIEWED**

## Trigger

Two user runtime files from the input-source helper failed the exact-axis gate before any A2 payoff evaluation.

The latest genuine r3 upload:

- SHA-256: `7f161d22ecd75960759ce2b62f7b3a25e88a45b174370cf05821ba3ec95fcddf`;
- 4,681 `MPM_A2` rows;
- payload coverage 2007-01-02 through 2026-09-22;
- `helper_rev=r3` present on all rows;
- `raw_gpi == raw_ipi` on 100% of rows;
- `regime_id == 5` on all rows;
- values lie roughly between 0.041 and 5.445, inconsistent with the frozen V6.6 GPI/IPI axes.

The input.source transport therefore did not reliably bind the intended production plots.

No A2 asset payoff, M0/M1 comparison, portfolio result, or trajectory verdict was computed or viewed.

## Amendment

Replace the manual `input.source()` transport with a **self-contained exact V6.6 market-axis helper**.

The helper directly requests the exact frozen default market sources used by V6.6:

### GPI

- AMEX:SPY
- AMEX:IWM
- AMEX:RSP
- AMEX:XLY
- AMEX:XLP
- AMEX:XLI
- AMEX:XLU
- COMEX:HG1!
- COMEX:GC1!

GPI remains the simple average of the five frozen component scores:

- IWM/SPY
- RSP/SPY
- XLY/XLP
- XLI/XLU
- Copper/Gold

### IPI

- FRED:T10YIE
- AMEX:DBC
- NYMEX:CL1!
- NYMEX:RB1!

IPI remains the frozen weighted average:

- 10Y breakeven score: 0.35
- commodity basket score: 0.40
- energy pressure score: 0.25

Energy pressure remains the simple average of crude-oil and gasoline component scores.

## Frozen configuration

The helper hard-codes the Issue #59/#64 V6.6 default research configuration:

- market timeframe: D
- z-score length: 252
- fast component momentum: 20
- mid component momentum: 63
- use macro data: false
- use 5Y breakeven: false
- use industrial metals in IPI: false
- GPI/IPI regime thresholds: ±10

The production indicator is not modified.

The helper does not compute FCPI because A2 trajectory preregistration requires only GPI/IPI.

## A2 trajectory

Unchanged:

```
fast_slope_X = (X_t - X_t-20) / 20
mid_slope_X  = (X_t - X_t-63) / 63
acceleration_X = fast_slope_X - mid_slope_X
```

No new feature, lookback, threshold, asset, horizon, or model is introduced.

## Calendar gate

The self-contained helper fails closed unless the chart is:

- ticker: SPY
- timeframe: 1D

This preserves the exact Issue #64 anchor-market calendar.

## Acceptance

The resulting Pine Logs remain subject to the same frozen pre-payoff acceptance gate:

- exact #64 axis-audit checkpoint agreement;
- zero regime mismatch against the frozen #64 transition history;
- exact 20/63 feature recomputation;
- SHA-256 freeze before A2 payoff evaluation.

A failed self-contained export will stop the research rather than trigger post-hoc formula changes.

No A2 payoff result had been viewed when this amendment was committed.
