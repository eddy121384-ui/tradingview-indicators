# Issue #109 Phase A1 finding — state-only pairwise Action Layer

Status: **A1 COMPLETE — STATE-ONLY EVIDENCE**

Workflow:
- run: `35948653281`
- head: `7334a4c2aa8f5b5677e8606135256d70fb8cc1db`
- artifact: `issue-109-a1-state-only`
- artifact id: `10787049104`
- artifact digest: `sha256:316e1b12b7a8dc3dde4766047fc294212771667c097aee29557a3f36e276e963`

No trajectory feature, FCPI directional input, portfolio optimizer, or production tilt size was used.

## Provisional A1 leg summaries

- Equity vs Duration: **`stable_directional_relationship`**
- Duration vs Cash: **`no_material_pairwise_information`**
- Gold vs Cash: **`stable_directional_relationship`**
- Broad Commodities vs Cash: **`no_material_pairwise_information`**

These are A1 research summaries only. They do not authorize production.

## Stable state-level candidates

### Equity vs Duration

Only one of nine states passes the preregistered stability gate.

**Growth Slowdown / Stable Inflation — SPY minus TLT**

- primary 3M non-overlap n = **13**
- mean spread = **+4.82%**
- bootstrap 95% CI = **[+1.93%, +7.88%]**
- positive fraction = 76.9%
- pre-2020: +5.04% (n=8)
- 2020-2022: +6.21% (n=1; insufficient for temporal gate)
- post-2023: +4.02% (n=4)
- strongest-supporting-episode share = **24.2%**
- after removing that episode: mean remains **+3.75%**, n=12

Classification:

`stable_directional_candidate`

Interpretation boundary:

This is evidence for a relative **Equity > Duration** preference in this specific state under the frozen monthly 3M protocol. It does not mean “Growth Slowdown is bullish equities” in absolute-return terms.

### Gold vs Cash

Three defensive states pass.

**Slowdown / Disinflation — GLD minus SHV**

- n = **24**
- mean = **+4.80%**
- 95% CI = **[+1.43%, +8.32%]**
- pre-2020: +3.81% (n=16)
- 2020-2022: +3.91% (n=3)
- post-2023: +8.49% (n=5)
- strongest-supporting-episode share = **20.9%**
- leaveout mean remains **+4.32%**, n=22

**Growth Slowdown / Stable Inflation — GLD minus SHV**

- n = **13**
- mean = **+4.41%**
- 95% CI = **[+1.69%, +7.24%]**
- pre-2020: +1.71% (n=8)
- 2020-2022: +8.90% (n=1; insufficient for temporal gate)
- post-2023: +8.67% (n=4)
- strongest-supporting-episode share = **36.8%**
- leaveout mean remains **+3.91%**, n=12

**Stagflation Pressure — GLD minus SHV**

- n = **12**
- mean = **+4.60%**
- 95% CI = **[+0.64%, +8.38%]**
- pre-2020: +6.09% (n=7)
- 2020-2022: +0.87% (n=2; insufficient for temporal gate)
- post-2023: +3.61% (n=3)
- strongest-supporting-episode share = **46.2%**
- leaveout mean remains **+3.84%**, n=11

All three classify:

`stable_directional_candidate`

This is materially different from Issue #64's Stagflation GLD-vs-SPY result, which was episode-concentrated. A1 asks **Gold vs Cash**, not Gold vs Equity.

## Reflation Equity vs Duration does not pass the stricter A1 gate

Issue #64 previously identified Reflation SPY-over-TLT as the strongest exploratory modern relationship.

Under Issue #109's different and stricter protocol:

- monthly decision origins;
- one eligible trading-row lag;
- 3M primary horizon;
- state-level non-overlap inference;

Reflation SPY minus TLT is still positive:

- n = **21**
- mean = **+2.99%**
- positive fraction = 76.2%
- 95% CI = **[-0.57%, +6.36%]**

Because the CI includes zero, it classifies:

`no_clear_state_edge`

This does not erase #64. It means the relationship does not meet the stricter Action Layer production-candidate gate under the new monthly protocol.

## Duration vs Cash

All nine states classify `no_clear_state_edge` under the primary 3M state-only test.

Leg summary:

`no_material_pairwise_information`

The inherited 4% CPI diagnostic still shows qualitative inflation-dependent sign differences in several cells, broadly consistent with #91, but high-inflation modern subsamples are sparse.

Examples:

- Stagflation, CPI <4%: TLT-SHV +4.49% (n=9; CI [+0.85%, +8.29%])
- Stagflation, CPI >=4%: -1.37% (n=3; CI crosses zero)
- Inflation Pressure without Growth Confirmation, CPI >=4%: -2.44% (n=3)

Because the >=4% samples are sparse and the 4% split is diagnostic only, A1 does **not** authorize a Duration/Cash action rule.

## Broad Commodities vs Cash

All nine states classify `no_clear_state_edge`.

Leg summary:

`no_material_pairwise_information`

The preregistered GSG broad-commodity sleeve therefore earns no state-only Action Layer role in A1.

## Product implication after A1

The evidence does **not** support a four-asset tilt vector that is active in every state.

The defensible state-only candidate set is much narrower:

1. **Growth Slowdown / Stable Inflation**
   - candidate Equity > Duration tilt;
   - candidate Gold > Cash tilt.

2. **Slowdown / Disinflation**
   - candidate Gold > Cash tilt only.

3. **Stagflation Pressure**
   - candidate Gold > Cash tilt only.

Every other state/leg remains zero / no-view under A1.

This is exactly why the Action Layer must permit `0`.

## Next gate

A2 asks whether frozen 20/63 GPI/IPI trajectory adds stable incremental information beyond state.

A2 is **not yet authorized on exact V6.6 trajectory data**, because the repository does not contain a full exact daily GPI/IPI axis series.

Do not infer continuous trajectory from the regime-transition file.

The next research step, if continued, should be either:

1. obtain a durable full exact-V6.6 GPI/IPI history; or
2. preregister a **public-feed trajectory screening gate** that is explicitly non-exact and cannot authorize production by itself.

No production V6.7 Pine is authorized by A1.
