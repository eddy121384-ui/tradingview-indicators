# Issue #78 — Weekly conflict transition diagnostic finding

Status: discovery diagnostic stopped on sample-size grounds.

Preregistration: `issue-78-weekly-conflict-transition-preregistration.md`.

## Result

The hypothesis that a **newly completed weekly flip into opposition** may be more informative than a stale opposing weekly state cannot be evaluated robustly on the accepted sample because the event is extremely rare.

Using the preregistered first-daily-bar-after-weekly-close event definition:

- active daily Markup + fresh opposing weekly flip: **3 events**
- active daily Markdown + fresh opposing weekly flip: **5 events**

At fresh daily trend entry:

- Markup entry with fresh opposing weekly flip: **2 episodes**
- Markdown entry with fresh opposing weekly flip: **3 episodes**

By contrast, persistent opposing weekly context is common:

- active Markup weekly-event observations under persistent conflict: 1,067
- active Markdown weekly-event observations under persistent conflict: 658
- fresh Markup entries under persistent conflict: 236
- fresh Markdown entries under persistent conflict: 164

## Interpretation

The scarcity itself is informative. A weekly classifier rarely flips into the opposite direction while the pre-existing daily directional regime is still active. Most observed daily/weekly disagreement comes from the opposite sequence:

> the weekly trend is already established, then a new local daily counter-trend appears inside it.

Therefore a `weekly just flipped against me` brake is not a practical general-purpose state variable for this architecture.

No outcome comparison is promoted from the 3/5-event samples. The transition hypothesis is **not rejected economically**; it is simply unsupported because there is insufficient evidence.

## Decision

Do not build a production rule around fresh weekly opposition.

The remaining useful research question is not "did weekly just flip?" but rather:

> when a fresh daily trend begins *against an already-established weekly trend*, can the age / maturity of that weekly opposition distinguish a harmless local counter-trend from a daily trend that is genuinely taking over?

That question requires a separate preregistration before inspecting conflict-age outcomes.
