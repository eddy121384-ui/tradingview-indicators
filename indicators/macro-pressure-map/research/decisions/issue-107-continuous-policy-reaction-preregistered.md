# Issue #107 preregistration — continuous policy reaction layer

## Product decision being tested

Keep V6.6 as the macro-state engine.

Do **not** create a new Policy Bias regime.

Instead test whether the continuous information already present in:

- GPI level
- IPI level
- GPI/IPI direction
- GPI/IPI acceleration
- current real policy starting point

contains stable information about the Fed's next six-month move.

Only after that is established may a display-only `Policy Pressure Proxy` be designed.

## Frozen trajectory

No new lookbacks.

For both GPI and IPI:

- fast slope = 20-observation slope;
- mid slope = 63-observation slope;
- acceleration = fast slope minus mid slope.

These are the existing V6.6 fast/mid time scales.

## One external policy input only

`real_policy_rate = FEDFUNDS - Core PCE YoY`

For evaluation at month `m`, the policy-state observation is conservatively taken from `m-2`.

No JOLTS, yield curve, term premium, market pricing, FCPI, QE or balance-sheet variables are allowed in this issue.

## Model ladder

- M0 = GPI + IPI
- M1 = M0 + real policy rate
- M2 = M1 + GPI/IPI 20/63 slopes + acceleration

Primary outcome:

`FEDFUNDS(m+6) - FEDFUNDS(m)`

Primary OOS begins January 2015 after a training window through December 2014.

## Two data gates

### A1 — public-feed screening

Use the existing repo public-data V6.6 approximation.

This can kill the hypothesis, but **cannot authorize production**.

### A2 — TradingView-feed confirmation

Required if A1 is promising.

Only A2 can authorize Phase B.

## Phase B

If and only if A2 earns `continuous_policy_information_stable`, preregister one simple continuous display formula.

Default UI:
- one line;
- zero/reference line;
- raw numeric value;
- optional slope/direction cue;
- no Hawkish/Dovish buckets.

The line is display-only and cannot affect GPI, IPI, FCPI, core regime, risk note, existing alerts, or allocation logic.
