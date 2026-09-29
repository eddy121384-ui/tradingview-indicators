# Issue #119 — Bloomberg OOS2 Raw Snapshot Finding

Parent research issue: #78  
Related Draft PRs: #120 and #80

## Decision

> **PASS — the frozen 300-security Bloomberg diagnostic raw snapshot is complete and internally consistent.**

This closes the raw-data transport / provenance gate only.

No R0 / Warning-First policy economics were calculated or inspected.

---

## Frozen universe

- securities: **300**
- large sleeve: **100**
- mid sleeve: **100**
- small sleeve: **100**
- sectors represented: **11 / 11**
- universe SHA-256:
  `e6f07371c9306f2598115cb886cc1cd5d4970d9fdc5e87dd1882bbac304c5712`

The universe remains unchanged from the pre-outcome freeze.

---

## Raw snapshot audit

Workstation audit result:

- `pass = true`
- universe rows: **300**
- completed securities: **300**
- failures: **0**
- universe SHA-256 match: **true**

Coverage diagnostics:

- minimum rows per security: **320**
- median rows per security: **5,789.5**
- maximum rows per security: **7,210**
- earliest security start: **1998-01-02**
- latest security end: **2026-08-31**
- missing volume observations: **74**

The frozen historical OOS2 end date remains 2026-08-31.

---

## Bloomberg OHLC normalization amendment

The first runtime pass exposed historical daily bars on 35 securities where Bloomberg high/low did not always bound that day's open/close.

Before any policy economics were inspected, normalization contract v2 was frozen:

- high = `max(open, high, close)` only when required;
- low = `min(open, low, close)` only when required;
- open and close unchanged;
- every repaired row retained in manifest diagnostics;
- nonpositive OHLC remains a hard failure;
- negative volume remains a hard failure.

Final audit:

- OHLC range repairs: **326**
- securities with one or more repairs: **35**

The 265 securities that passed the original stricter range check were not rewritten.

---

## Checkpoint / resume validation

Runtime behavior was also validated:

- first pass completed 265 / 300;
- 35 remained incomplete due solely to the OHLC-range validation rule;
- after the pre-outcome normalization amendment, rerunning the same downloader retained the 265 completed securities;
- only the remaining 35 were requested;
- final state reached 300 / 300 with zero failures.

No failed security was replaced.

---

## Research firewall

Still not inspected:

- R0 expectancy;
- Warning-First expectancy;
- win rate;
- payoff ratio;
- MFE policy slices;
- outcome-aware stock replacement or filtering.

The next and final Issue #119 engineering gate is a structural smoke run of the **frozen Issue #78 Python classifier** over all 300 normalized raw security files.

That smoke gate verifies execution compatibility only and explicitly computes no policy economics.

Refs #119, #78, #120, #80.
