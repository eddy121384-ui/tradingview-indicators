# Issue #136 — R7 Asynchronous Bottoming / Turning-Point Finding

Status: **research-only; no production authorization**

Issue: #136  
Draft PR: #137  
Branch: `research/issue-136-r7-async-turn`

Preregistration history preceding outcome evaluation:

- `a73aff06a065b8daf24608b24d630806aecf6f8b` — initial preregistration;
- `63d807051e27a32f98df43fa005bfc01797bea97` — pre-outcome implementation clarifications;
- `af51af0a9b4d1a8f7212cfd88a65bd44b3cf1062` — pre-outcome leaveout-scope clarification.

The evaluator was committed only afterward at `a5a76eaf52f037ab4576092fcdeae157bdb63715`.

Final validated CI:

- run: `36833561439`
- validated code head: `78d7cfb320331ce811c15af8f6e35e4c0224a869`
- artifact digest: `sha256:f6c0770270f3f590bbe2316bdcc62288aabb206d2533e77045176a510d8f984f`

## Executive finding

The asynchronous-turn formulation materially increases the number of distinct exact-modern Regime-7 recovery events and produces a positive three-month Equity-vs-Duration point estimate.

However, the preregistered episode-cluster bootstrap confidence interval still includes zero.

Formal results:

- modern exact verdict: **`async_turn_suggestive_not_robust`**;
- long-history HMRA verdict: **`inconclusive_long_history_async_turn_sample`**;
- cross-history synthesis: **`async_turn_evidence_inconclusive`**;
- `production_authorized=false`.

Issue #133 remains frozen and is not retuned by this study.

## Layer A — exact modern V6.6

Frozen primary definition:

- current exact V6.6 state = Regime 7;
- an axis turns when its monthly slope changes from `<=0` to `>0`;
- both GPI and IPI have completed such a turn in the current or prior two completed months;
- only the first completion inside each contiguous Regime-7 episode is a primary signal;
- primary payoff = next-3M SPY total return minus TLT total return;
- inference = R7-episode cluster bootstrap.

### Sample

Primary analysis contains:

- 22 Regime-7 episodes;
- 31 eligible signal/control rows;
- 14 independent first-trigger episodes;
- 17 eligible pre-trigger / never-trigger control observations.

Trigger dates:

- 2008-12-31
- 2010-08-31
- 2011-08-31
- 2012-06-29
- 2014-10-31
- 2015-01-30
- 2015-07-31
- 2015-12-31
- 2018-10-31
- 2019-05-31
- 2020-04-30
- 2022-08-31
- 2023-03-31
- 2025-04-30

Turn ordering is descriptive only:

- same-month: 7;
- GPI first: 5;
- IPI first: 2.

### Primary 3M result

First-trigger observations:

- n = 14;
- mean next-3M SPY-TLT = **+2.9798%**;
- median = **+3.0917%**;
- positive-spread hit rate = **50.0%**.

Primary controls:

- n = 17;
- mean next-3M SPY-TLT = **+0.0819%**;
- median = **-1.1398%**;
- positive-spread hit rate = **41.18%**.

Incremental signal minus control:

- **+2.8979 percentage points**;
- episode-cluster bootstrap 95% CI:
  **[-6.0920pp, +10.8778pp]**;
- 10,000 valid bootstrap replications.

The point estimate is positive, but the preregistered CI gate fails because the lower bound does not exceed zero.

### Modern preregistered gates

PASS:

1. trigger episodes >=8 — 14;
2. signal mean >0;
3. incremental mean >0;
5. at least 2 temporal segments evaluable;
6. temporal sign requirement;
7. every leave-one-trigger-episode-out incremental result remains positive;
8. strongest positive trigger contribution <=50% — observed 24.03%;
9. one-month delayed implementation preserves positive incremental sign.

FAIL:

4. episode-cluster bootstrap 95% CI lower bound >0.

Therefore the deterministic verdict is:

`async_turn_suggestive_not_robust`.

### Temporal stability

All three inherited segments have positive incremental means:

- pre-2020: **+0.0916pp** (10 signals / 8 controls);
- 2020–2022: **+8.3294pp** (2 / 5);
- 2023+: **+14.5340pp** (2 / 4).

The sign is therefore temporally consistent under the frozen gate, but magnitude is much larger in the small post-2020 samples. This is a reason for caution, not a basis for changing the signal.

Every leave-one-trigger-episode-out comparison remains positive; the smallest leaveout incremental mean is approximately +0.388pp.

### Delayed implementation

Applying the same frozen three-month payoff one month later gives:

- incremental mean = **+3.9637pp**;
- cluster-bootstrap 95% CI = **[-2.2009pp, +10.3653pp]**.

The sign robustness gate passes, but the delayed CI also includes zero.

### Secondary horizons

These were preregistered as descriptive only and cannot rescue the primary test.

Signal minus control mean spread:

- next 1M: approximately **+2.3034pp**;
- next 3M primary: **+2.8979pp**;
- next 6M: approximately **+0.9203pp**.

The descriptive pattern is consistent with a payoff concentrated nearer the first few months after the turning signal, but no horizon optimization is permitted inside Issue #136.

### Descriptive state exits

The 14 triggers leave Regime 7 after a median of 2 months.

First non-R7 states by exact regime id:

- Regime 4: 5;
- Regime 8: 3;
- Regime 2: 2;
- Regime 1: 1;
- Regime 3: 1;
- Regime 5: 1;
- Regime 9: 1.

This supports treating the signal as a **bottoming / turning diagnostic**, not as an automatic immediate transition into an expansion regime.

Ordering subgroup outcomes remain descriptive only. Their samples are too small to justify selecting GPI-first, IPI-first, or same-month as a new rule.

## Layer B — ultra-long-history HMRA analogue

The frozen Issue #91 / #121 pipeline validates HMRA before joining asset outcomes, preserves strict causal `state_t -> return_(t+2)` timing, and retains the frozen Damodaran source SHA:

`127c772f0fea8763391dbf2c1c7d3ecd3a07ca2b23f81ab47af58b529e2b5647`

The asynchronous annual definition increases the long-history signal from Issue #133's one recovery observation to three:

- HMRA state 1931 -> return 1933;
- HMRA state 1953 -> return 1955;
- HMRA state 2020 -> return 2022.

Turn ordering:

- 1931: same year;
- 1953: Growth first;
- 2020: Inflation first.

All three HMRA R7 episodes exit the state one year later. 1931 and 1953 move to Disinflationary Drift; 2020 moves to Reflation / Inflation Rising.

### Long-history result

Signals:

- n = 3;
- mean Equity-Treasury spread = **+27.2833%**;
- median = **+33.94%**;
- positive fraction = **66.67%**.

Controls:

- n = 11;
- mean = **+6.5836%**;
- positive fraction = **63.64%**.

Incremental mean:

- **+20.6997pp**;
- episode-cluster bootstrap 95% CI:
  **[-9.3032pp, +44.5647pp]**.

The three individual causal signal payoffs are:

- 1931 -> 1933: +48.12pp;
- 1953 -> 1955: +33.94pp;
- 2020 -> 2022: -0.21pp.

Two broad eras are evaluable and have positive incremental means, and leave-one-era-out remains positive. However:

- preregistered n>=8 gate fails (n=3);
- CI excludes-zero gate fails;
- strongest-positive-era concentration gate fails at about **60.29%**.

Formal verdict:

`inconclusive_long_history_async_turn_sample`.

## Cross-history interpretation

The new formulation is materially more promising than Issue #133's simultaneous 3-month-improvement formulation:

- exact-modern first triggers increase from 4 to 14;
- modern primary incremental point estimate is positive;
- 8 of 9 modern preregistered gates pass;
- all modern temporal segments and all modern trigger-episode leaveouts preserve a positive sign.

But the one gate that fails is important: the cluster-bootstrap interval remains wide and crosses zero.

Ultra-long-history evidence points in the same positive direction in point estimate, but contains only three first-trigger observations and remains too concentrated to validate the relationship.

Therefore the correct cross-history conclusion is:

`async_turn_evidence_inconclusive`.

This is stronger than "nothing found", but weaker than a validated Action Layer candidate.

## Research boundary / next implication

Do not alter Issue #136's turn window, slope definition, ordering rule, payoff horizon, or asset pair after this result.

If further validation is desired, the next useful study should add **independent evidence** rather than retune the signal—for example a separately preregistered higher-frequency historical analogue, independent macro dataset, or out-of-sample/cross-market validation.

No V6.6 or V6.7 production behavior is authorized to change from this finding.
