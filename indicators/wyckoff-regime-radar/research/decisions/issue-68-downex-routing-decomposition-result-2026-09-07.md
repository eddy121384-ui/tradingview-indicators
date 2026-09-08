# Issue #68 — DownEx Routing Decomposition Result (2026-09-07)

Status: discovery-only result. Production C-2 remains frozen.

Window: 2022-01-03 through 2023-12-29, daily.

## TradingView observations

### FR10Y

- PROD S1 EFF avg: 57.97
- RAW-only S1 EFF avg: 60.27 (`+2.30`)
- GATE-only S1 EFF avg: 62.34 (`+4.37`)
- BOTH S1 EFF avg: 64.90 (`+6.94`)
- interaction: `+0.26`
- PROD `S2 EFF > S1`: 21.48%
- GATE-only `S2 EFF > S1`: 6.05%
- PROD Bull TOP: 21.48%
- GATE-only Bull TOP: 6.05%
- PROD S1 gate avg: 0.76
- support-invariant shadow S1 gate avg: 0.81

### DE10Y

- PROD S1 EFF avg: 48.31
- RAW-only S1 EFF avg: 50.80 (`+2.49`)
- GATE-only S1 EFF avg: 58.98 (`+10.67`)
- BOTH S1 EFF avg: 62.21 (`+13.90`)
- interaction: `+0.75`
- PROD `S2 EFF > S1`: 36.13%
- GATE-only `S2 EFF > S1`: 5.47%
- PROD Bull TOP: 36.13%
- GATE-only Bull TOP: 5.47%
- PROD S1 gate avg: 0.63
- support-invariant shadow S1 gate avg: 0.76

## Finding

The support-invariant slope shadow changes S1 much more through the Accumulation **gate route** than through the S1 RAW evidence route, especially in DE10Y. The RAW+Gate interaction is small relative to the gate contribution, so a generic `DownEx is double-counted in RAW and Gate` explanation is downgraded.

The FR/DE Bull-TOP divergence also nearly disappears in the GATE-only shadow (FR 6.05% vs DE 5.47%). Therefore the production FR/DE semantic split is being amplified primarily by the S1 Acc gate, not by S1 RAW.

The S1 gate contains two DownEx-dependent channels:

1. direct: `downsideExhaustion -> downsideExhaustionGate -> accGate`;
2. indirect: `downsideExhaustion -> markdownContinuationScore -> nonMarkdownContinuationGate -> accGate`.

The next audit must decompose these two channels with S1 RAW and all non-DownEx inputs frozen to production.

No tuning, no PnL, and no production change is authorized by this result.