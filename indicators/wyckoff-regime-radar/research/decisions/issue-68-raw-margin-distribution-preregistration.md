# Issue #68 — FR10Y vs DE10Y RAW Margin Distribution Audit

Status: preregistered discovery audit only. No production change.

Branch: `research/issue-68-lifecycle-retest-symmetry-repaired`

Draft PR: #73 must remain Draft / Open. Issue #68 must remain Open.

## Motivation

The compact S1-gate audit shows that post-RAW gating does not explain the FR10Y vs DE10Y divergence: `RAW S2 > S1 -> EFF S1` is effectively zero in both markets. Yet FR10Y spends materially less time with S2 leading S1, even though its average S2 RAW is higher and its average S1 RAW is not higher than DE10Y.

This implies that averages may be hiding a time-distribution / persistence difference. The next audit therefore studies the distribution and run structure of the frozen RAW margin `markupRaw - accRaw` without changing any classifier logic.

## Frozen scope

Window: 2022-01-03 through 2023-12-29.
Primary pair: FR10Y vs DE10Y, daily.

No PnL. No parameter tuning. No threshold search. No changes to `breakoutBars`, stage weights, MA lengths, Strong gates, Formal confirmation, gamma, S1/S2 gates, or production classifier logic.

## Audit outputs

For each market, report:

- Share of bars where S2 RAW leads S1 RAW and vice versa.
- Average RAW margin `S2 - S1` overall.
- Average positive margin when S2 leads and average negative margin when S1 leads.
- Distribution shares in fixed descriptive score bins: `<= -20`, `(-20,-10]`, `(-10,0]`, `(0,10)`, `[10,20)`, `>= 20`.
- Maximum and average consecutive S2-leading run length.
- Maximum and average consecutive S1-leading run length.
- Number of RAW leader sign flips.
- Average S2/S1 RAW levels separately on S2-leading bars and S1-leading bars.

The fixed score bins are descriptive only and cannot become classifier thresholds.

## Interpretation rule

1. If FR10Y has a larger small-negative / S1-leading occupancy and materially longer S1-leading runs, while its S2-leading bars have unusually large positive margins, the paradox `higher average S2 RAW but lower S2 win share` is explained by episodic S2 spikes plus persistent S1 dominance.
2. If FR10Y and DE10Y have similar margin distributions and run structure despite the observed winner-share divergence, stop and audit implementation / sampling alignment before any repair hypothesis.
3. This phase only localizes the temporal RAW pathology. It does not authorize a production change.
4. Component-level near-miss attribution may follow only after the distribution result identifies which RAW region is responsible.

No production repair is allowed in this audit.