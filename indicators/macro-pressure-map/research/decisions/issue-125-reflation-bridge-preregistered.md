# Issue #125 preregistration — HMRA Reflation to exact V6.6 Reflation bridge

Status: **PREREGISTERED BEFORE BRIDGE RESULTS**

Primary overlap window: complete years 2007–2025.

Frozen sources:
- Issue #91 HMRA-v0.1 annual macro states, rebuilt only if canonical Fed/BLS source hashes match the durable Phase 1 freeze.
- Issue #64 exact V6.6 transition history with SHA-256:
  `80446bbcb91be8b18eb0b95e62466edf892e4c04087696a04532f0fe214698af`.

Primary exact-state sampling:
- one observation per calendar month;
- exact regime at the final calendar day of each month;
- annual inference unit is the calendar year, never the month.

Exact axis semantics:
- Growth high = regimes 1/2/3
- Inflation high = regimes 3/6/9
- exact Reflation = regime 3

For each year compute exact monthly occupancy shares for regimes 1..9, Growth-high, Inflation-high, and Regime 3.

Primary comparison:
- same-year HMRA Reflation years versus all other HMRA years.
- 10,000-resample bootstrap over years within the two groups.
- primary metrics: R3 occupancy lift, Growth-high lift, Inflation-high lift.

Specificity:
- Regime 3 must have the largest positive occupancy lift among all nine exact regimes; ties within 1e-12 pass.

Leave-one-HMRA-Reflation-year-out:
- every R3 occupancy lift must remain positive.

Binary monthly overlap is diagnostic only.

Timing diagnostics:
- HMRA state_t versus exact occupancy in t+1
- HMRA state_t versus exact occupancy in t+2
These cannot replace the primary same-year bridge.

Full support requires all:
1. >=15 complete common years
2. >=3 HMRA Reflation years
3. R3 lift > 0
4. R3 bootstrap CI lower bound > 0
5. Growth-high lift > 0
6. Growth-high bootstrap CI lower bound > 0
7. Inflation-high lift > 0
8. Inflation-high bootstrap CI lower bound > 0
9. R3 is the largest positive regime-specific lift
10. every leave-one-Reflation-year-out R3 lift > 0

Verdicts:
- `bridge_supports_hmra_to_exact_v66_reflation_translation`
- `bridge_semantically_related_but_not_reflation_specific`
- `bridge_weak_or_mismatched`
- `bridge_inconclusive_small_overlap`

Semantic-related fallback requires:
- sufficient sample;
- Growth-high lift >0;
- Inflation-high lift >0;
- at least one of those two bootstrap CIs excludes zero positively.

No production authorization in this issue.

Forbidden after result inspection:
- changing month-end sampling;
- changing exact regime grouping;
- switching primary timing to t+1 or t+2;
- dropping an HMRA Reflation year;
- tuning HMRA/V6.6 thresholds;
- using asset returns to redefine the bridge.

No bridge result had been computed when this file was committed.
