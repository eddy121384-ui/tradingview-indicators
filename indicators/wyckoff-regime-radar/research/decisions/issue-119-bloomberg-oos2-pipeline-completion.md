# Issue #119 — Bloomberg OOS2 Equity Data Pipeline Completion

Parent research issue: #78  
Related Draft PRs: #120 and #80

## Decision

> **COMPLETE — the Bloomberg survivorship-limited 300-stock OOS2 diagnostic data pipeline is runtime-validated and ready to hand back to Issue #78.**

No R0 / Warning-First policy economics were inspected during Issue #119.

---

## Frozen universe

- 300 U.S. equities
- large / mid / small sleeves: 100 / 100 / 100
- 11 sectors represented
- AAPL / JPM / XOM excluded before sampling
- deterministic universe selection
- universe SHA-256:
  `e6f07371c9306f2598115cb886cc1cd5d4970d9fdc5e87dd1882bbac304c5712`

No failed or weak security was replaced.

---

## Bloomberg raw snapshot

Final workstation transport:

- completed: **300 / 300**
- failures: **0**
- raw rows: **1,525,618**
- earliest security start: **1998-01-02**
- latest security end: **2026-08-31**
- row-count min / median / max: **320 / 5,789.5 / 7,210**
- missing volume observations: **74**
- raw-file SHA-256 verification: PASS
- universe SHA-256 verification: PASS

Checkpoint / resume was runtime-validated: the first pass retained 265 completed names, then fetched only the 35 incomplete names after the pre-outcome normalization amendment.

---

## OHLC normalization amendment

Before any policy outcome was inspected, the Bloomberg normalization contract was amended to handle historical daily bars whose high/low did not bound open/close.

Frozen rule:

- high = `max(open, high, close)` only when required;
- low = `min(open, low, close)` only when required;
- open / close unchanged;
- every repaired row retained in diagnostics;
- nonpositive OHLC remains a hard failure;
- negative volume remains a hard failure.

Final count:

- repaired rows: **326**
- securities with one or more repairs: **35**

---

## Frozen classifier structural smoke

Exact frozen Issue #78 classifier blob:

`1eec08e791403453853b589373bb2270c508c3bb`

Workstation smoke result:

- raw files: **300**
- classifier-completed securities: **300**
- failures: **0**
- policy economics computed: **false**

The initial smoke metric incorrectly treated finite six-stage probabilities as equivalent to completed warm-up. That interpretation was corrected before any policy economics were run.

The corrected structural-readiness metric uses finite structural price-path diagnostics only.

---

## Structural coverage resolution

Frozen default structural initialization requires approximately **956 consecutive valid OHLC rows** before all selected structural readiness channels can be finite. The binding path is the 200-bar maturity moving average followed by a 756-bar percentile-rank history.

Sixteen securities have zero structurally-ready rows.

Fifteen are explained directly by total raw history shorter than the structural initialization horizon:

- RAL — 320 rows
- SNDK — 388
- SARO — 479
- CPB — 510
- SW — 540
- LIF — 560
- RDDT — 613
- AHR — 644
- BTSG — 651
- LIN — 705
- VSTS — 734
- CART — 740
- KNF — 819
- KVUE — 834
- GEHC — 929

The remaining security, SBSI, has 2,078 total rows but:

- incomplete OHLC rows: **175**
- longest consecutive complete-OHLC run: **459**

Therefore SBSI also cannot satisfy the approximately 956-row structural initialization requirement.

No security is replaced or removed because of this coverage result. These names remain part of the frozen 300-security universe and contribute zero eligible classifier history where the frozen rules cannot initialize.

---

## Research firewall status

Still not inspected:

- R0 expectancy
- Warning-First expectancy
- win rate
- payoff ratio
- MFE policy slices
- outcome-aware stock filtering or replacement

Issue #119 therefore ends with the diagnostic cohort, raw provenance, normalization contract, and frozen-classifier execution path fixed before economics.

---

## Handoff to #78

The next research step is now allowed:

> run the preregistered survivorship-limited 300-stock OOS2 diagnostic using the frozen classifier, frozen universe, frozen entry eligibility, and only the already-frozen R0 NoDeRisk / R0+WarningFirst policies.

The higher-spec point-in-time / delisted-security confirmation remains a separate later gate.

PR #80 must remain Draft / open / unmerged.

Refs #119, #78, #120, #80.
