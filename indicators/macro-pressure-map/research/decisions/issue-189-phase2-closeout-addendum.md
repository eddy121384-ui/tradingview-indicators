# Issue #189 Phase 2 closeout addendum — common-month correction (short)

- Branch: `research/issue-189-deep-history-pit`; Phase 2 scope (no Phase 3).
- Corrects one sentence in `decisions/issue-189-phase2-finding-v2.md` §Q5
  ("共同可用月恆為決策月前 2 個月"): that sentence over-generalized.
- Verified from committed `generated/issue-189/phase2/staleness.json`
  (no re-download; recomputation command in §2 of the companion review file):
  **239/243** decision months have common_obs = D−2;
  **2019-02 → 2018-11 (D−3)**, **2025-11 → 2025-08 (D−3)**,
  **2026-01 → 2025-10 (D−3)**, **2025-12 → 2025-08 (D−4)**.
- Cause in all four cases: genuine shutdown-driven vintage gaps at the
  frontier (2018-12 BEA from the 2018–19 shutdown; 2025-09/10 multi-agency
  from the 2025 shutdown), which pull the conservative common month back.
  The mechanism (BEA legs bind the common panel) is unchanged; only the
  "恆為" quantifier was wrong.
- No other finding figure changes. Prereg, code, thresholds, verdicts
  untouched. `production_authorized=false`.
