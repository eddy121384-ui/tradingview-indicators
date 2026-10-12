# #189 Phase 1C GPT-6 vs OC post-unblinding reconciliation

**Independent GPT-6 finding was frozen FIRST** at commit `ea494da7957e3642c860cd30b22047685b778a5d` on `research/issue-189-gpt6-phase1c-independent`, based only on #189 Phase 1B `434ee8e`. Only afterward did GPT-6 read OC's concurrently produced Phase 1C `180c3df29653ddc37d0c6926d1628d0ad92cf3c9`. This note is a *post-unblinding comparison*, not a revision to the blind finding or its code.

## Agreement

- The ALFRED category's `2000-08-01 … 2003-12-22 / Jan 1959 … Oct 2003` metadata cannot mean that August 2000's first vintage contained observations from October 2003.
- Frozen #160 requires first valid score index **74** on original monthly data (zero-based), i.e. **75 consecutive raw observations** including scored month. OC says “74 raw months” meaning **74 prior month offsets**; these are the SAME mathematical result, not a substantive disagreement.
- G3/G4 are the binding series because of 12m YoY plus 60 momentum observations needing a 3-month history. 1960-01 index 74 = 1966-03.
- Neither team reviewed asset returns or changed allocation policy. Full 5-factor PIT remains blocked by G5.

## New stronger OC evidence after independent findings frozen

OC discovered **public, keyless** historical CSV endpoints:

`https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=PCEPILFE&vintage_date=2000-08-01`

and analogous `PCEPI` URLs. OC's tracked hash/coverage manifest:

`generated/issue-189/phase1c/alfred-vintage-spans.json`

reports 28 HTTP-200 pulls on 2026-10-12. GPT-6 inspected the machine-readable file AFTER freezing its own finding. Selected records:

| Series | As-of date | Obs first | Obs last | Rows |
|---|---|---|---|---:|
| PCEPI | 2000-08-01 | 1959-01 | 2000-06 | 498 |
| PCEPILFE | 2000-08-01 | 1959-01 | 2000-06 | 498 |
| PCEPI | 2006-06-01 | 1959-01 | 2006-04 | 568 |
| PCEPILFE | 2006-06-01 | 1959-01 | 2006-04 | 568 |

For these four: `rows == inclusive calendar months(first,last)`; no date exceeds the as-of query. Across all 28 manifest records, GPT-6 found **zero obvious post-as-of observation ranges**. This supports that, AT THE SAMPLED DATES, both PCEPI and Core PCE have ample old-history observation coverage for the 2006 ETF start.

**Crucial evidence distinction:** GPT-6 verified OC's already recorded dataset *internal consistency and its reported hashes/metadata*, but this isolated environment could not independently retrieve and hash the raw CSV HTTP bytes. The 28 raw downloads and SHA-256 calculation are OC's evidence, not a second independent network replication. This should be reported transparently.

The prior GPT-6 independent finding's `exact_2006_decision_vintage_coverage = NOT_VERIFIED` was true **at the time of the independent audit**. Post-unblinding, OC has supplied additional sampled-date value/coverage evidence. This does not prove *all* monthly vintage densities or economic definition parity across 2006–2026.

## Residual scientific gaps

1. Confirm all months/as-of vintages rather than 2000-08 / 2006-06 endpoint samples and check missing within the 75-point rolling window; do not confuse contiguous-looking endpoints with complete between-month observations for all roles.
2. Verify corresponding as-of release timestamps and trade eligibility; catalog dates remain date-only.
3. I3/I4/I5 original TradingView definitions unresolved. G5 continuous vintage remains unavailable; spot press evidence is NOT full-state PIT.
4. Note nomenclature precisely in future code: `max_raw_lookback_offsets=74`, `min_raw_observation_count=75` for no-gap G3/G4. Avoid reintroducing the 72-month undercount.

**Overall verdict remains `partially_feasible`.** OC's sampled vintage span audit considerably strengthens the ETF-era **partial 10/11 feasibility**, without authorizing a full nine-state PIT return replay.

No original files changed. `production_authorized=false`.
