# Issue #78 — Breakout / Retest / Resume Evidence Checkpoint

## Why this checkpoint exists

Issue #78 has accumulated several preregistered studies around progressive exposure and trend evidence. Before opening another resume-definition challenger, this document consolidates the current evidence chain so that later work does not silently revive rejected ideas or blur diagnostic findings with admitted evidence.

This is a synthesis of already-completed studies. It does not introduce new thresholds, rerun results, or change any prior admission decision.

## Current evidence chain

### 1. Normalizer

Entry ATR remains the working cross-market normalizer.

The Normalizer Challenge did not show a material, robust advantage from pre-entry realized sigma or median absolute move. The conclusion is simplicity / integration, not theoretical optimality.

Operational interpretation:

> directional progress appears informative; entry ATR is a convenient common ruler rather than a universal law of market structure.

### 2. Pre-breakout compression geometry

The historical Shiori Compression Cage was tested as a causal breakout-structure baseline.

Results:

- old 3-of-5 / 80% binary Cage was far too sparse on the daily nine-market sample;
- narrow 5-bar box width relative to ATR did not predict healthier breakouts;
- parameter-free bar overlap showed only a modest extension signal and failed temporal robustness.

Decision:

> **Do not use narrowness, the old Cage, or overlap as a universal add-risk gate.**

The box remains useful as a causal reference boundary, not as a proven quality filter.

### 3. Immediate breakout quality

Breakout-close overshoot beyond the old box is useful, but its semantics are narrow.

Result:

- larger overshoot strongly reduces immediate return into the old box;
- it is much weaker at predicting long continuation by itself.

Decision:

> **Immediate overshoot is evidence against an immediate false breakout, not standalone proof of a durable trend.**

Breakout-bar close location / range were not promoted as universal inputs.

### 4. Three-bar post-breakout acceptance and follow-through

This is the strongest evidence family found in the breakout studies.

After the breakout, over the frozen next-three-bar window:

- worst acceptance margin outside the old box strongly predicts future re-expansion and durability;
- three-bar directional follow-through is stronger still;
- both work across markets and do not collapse in 2015–2019;
- acceptance adds information after controlling breakout overshoot;
- follow-through adds information after controlling acceptance.

Decision:

> **Promote post-breakout acceptance and follow-through as primary continuation evidence families.**

Important structural result:

- immediate overshoot and three-bar follow-through are almost orthogonal;
- “strong on breakout day” and “continues progressing after breakout” are different evidence paths.

### 5. Retest / acceptance path states

Using only information known by t+3, breakout paths were frozen into:

- P0 — No-touch / Immediate Expansion;
- P1 — Wick Retest / Hold;
- P2 — Close Re-entry / Reclaim;
- P3 — Failed Acceptance.

Main findings:

- P1 strongly outperforms P3 on future re-expansion;
- P2 also strongly outperforms P3;
- P2 reclaim remains informative after partially controlling retest depth;
- P1 is roughly comparable to P0 for near-term re-expansion after matching three-bar follow-through;
- P0 tends to have greater formal-regime durability;
- P3 is clear negative evidence.

Decision:

> **A retest is not itself weakness. The key distinction is whether the breakout boundary is held or reclaimed versus whether price remains accepted back inside the old range.**

Healthy paths therefore include at least:

1. Immediate Expansion;
2. Retest / Hold;
3. Reclaim after temporary re-entry.

### 6. Resume Trigger Challenge Stage 1

Only P1/P2 states were eligible.

All anchors were frozen once at t+3 and never reset, preventing recursive waiting.

Tested:

- R1 — new favorable close extreme beyond all closes known through t+3;
- R2 — new favorable intrabar price extreme;
- R3 — close beyond frozen retest-segment high/low;
- R4 — +0.5 ATR progress from t+3.

Main findings:

#### R1 Close Extreme

Best current coverage / timing frontier:

- trigger coverage ~82%;
- no-trigger ~18%;
- median equal-market delay <2 bars;
- strong post-trigger re-expansion;
- moderate confirmation tax;
- stable through 2015–2019;
- usable for both P1 and P2.

Decision:

> **Retain R1 as the clean baseline resume definition.**

#### R2 Price Extreme

Does not materially dominate R1.

Decision:

> Do not promote over R1.

#### R3 Retest-Segment High/Low Break

Failed its intended purpose.

The retest wick itself raises the hurdle, so requiring a later close through the segment high/low is often later than R1.

Decision:

> **Reject this R3 definition as an early local resume trigger.**

This does not reject the broader local-structure idea.

#### R4 +0.5 ATR Progress

Produces cleaner immediate post-trigger failure behavior but at the cost of:

- lower coverage;
- more no-trigger episodes;
- larger confirmation tax.

Decision:

> Retain only as a momentum benchmark.

## Current state-machine interpretation

The research currently supports this evidence architecture:

### Fresh formal trend

Small / initial risk only.

### Breakout event

A causal old-range boundary is left.

### Immediate Expansion path

A strong overshoot can reduce immediate false-breakout risk.

### Post-breakout evidence window

Observe three completed bars.

### Healthy continuation states

- P0 Immediate Expansion;
- P1 Wick Retest / Hold;
- P2 Close Re-entry / Reclaim.

### Negative state

- P3 Failed Acceptance.

### Resume after P1/P2

R1 new favorable close extreme is the current baseline.

No economic sizing rule has yet been promoted.

## Explicitly rejected / not promoted

Do not silently revive these as if they were proven:

- old binary Compression Cage as universal gate;
- narrow box width as positive breakout filter;
- pairwise overlap as universal gate;
- breakout-bar strength as standalone long-trend proof;
- price-extreme R2 as superior to close-extreme R1;
- high/low-based retest-segment R3 as an early local trigger;
- +0.5 ATR R4 as a free improvement.

## Current unresolved question

The only resume-definition challenger justified before an economic policy test is:

> **Can a frozen retest-segment CLOSE boundary confirm resumed directional control earlier / more broadly than R1 without materially increasing false resumes?**

This differs materially from rejected R3:

- rejected R3 uses retest-segment high/low wicks;
- the proposed challenger uses only favorable closes inside the retest segment.

The reason to test it is structural, not post-hoc threshold tuning:

> a local close boundary may capture “the pullback structure has been broken” without forcing price to clear either the old breakout extreme or a wick-defined hurdle.

## Next-step discipline

Before any second-entry sizing / PnL test:

1. preregister the local-close resume challenger;
2. compare it directly against frozen R1 on coverage, delay, confirmation tax, post-trigger re-expansion, old-box failure, remaining runway, temporal robustness, and direction robustness;
3. if it fails to improve the frontier, stop definition research and carry R1 forward;
4. if it improves the frontier, retain both or select only through a later preregistered economic-policy comparison.

PR #80 remains Draft and must not be merged as part of this checkpoint.

Refs #78, #80, #76.
