# Issue #103 — BCI-10 v1.5 semantic/source audit

This phase freezes what the original indicator **actually computes** before any attempt to validate it against the Fed or Treasury returns.

## Core finding 1 — P and R do not share the same sign meaning

The original P axis is naturally read as:

> positive P = more restrictive / more hawkish.

Higher real policy rate, higher inflation pressure and tighter labor all raise P.

The original R axis behaves in the opposite directional sense:

- weaker leading growth raises R;
- rising unemployment raises R;
- a more inverted yield curve raises R;
- higher/rising inflation lowers R;
- tighter labor lowers R;
- inflation panic lowers R.

That means:

> positive R behaves like **easing / dovish pressure**, while negative R behaves like tightening / hawkish pressure.

But the original PS formula adds them:

`PS = 0.4 P + 0.4 R + 0.2(P×R)`

and then labels positive PS as hawkish.

So the literal PS has an internal sign-semantics conflict. This must be resolved before PS can be treated as a coherent policy-direction signal.

## Core finding 2 — several source comments do not match the actual symbols

### Services PMI

The code says:

`pmi_svs = ECONOMICS:USNMPR`

but `USNMPR` is ISM Non-Manufacturing **Prices**, not the Services PMI composite.

### Manufacturing PMI

The code uses `USISMMP` and calls it manufacturing PMI. Historical symbol/event references associate `USISMMP` with **ISM Manufacturing Prices**. Current TradingView identifies the manufacturing PMI as `USBCOI` and manufacturing prices as `USMPR`.

The legacy symbol must be checked in TradingView itself; no substitution is allowed in the literal variant.

### PCE

The code calls `USPCEPIAC` "core PCE", but it is headline **PCE Price Index Annual Change**. Core PCE annual change is `USCPCEPIAC`.

The code then calculates another 12-month percent change from `USPCEPIAC`, which risks transforming an already-year-over-year series a second time.

### JOLTS

`JTSJOL` is a **level in thousands**, while `JTSQUR` is a **rate**. The original comment says both JOLTS inputs are rate-form.

## What we do next

We keep two concepts separate:

1. **Literal BCI-10** — exact original code. No fixes.
2. **Intended-semantics BCI-10** — a later, separately preregistered repair.

The literal variant is not allowed into Fed validation until:
- the legacy `USISMMP` symbol is runtime-checked in TradingView;
- the P/R sign conflict is acknowledged as literal behavior.

No Fed outcome or Treasury return is used in this audit.


## Core finding 3 — the original Z-score helper zero-fills insufficient history

The original helper is:

`std > 0 ? (src - mean) / std : 0`

In Pine v5, an `na` conditional expression is treated as false. Therefore, before a 120-month standard deviation exists, the helper returns **0** rather than `na`.

Literal BCI-10 can therefore look populated before its 120-month normalization window is actually available.

For the separately preregistered Intended-semantics version, insufficient history must remain `na`; zero is allowed only when a fully populated window has a true zero standard deviation.
