# Issue #78 — Equity Proof-Policy OOS3 snapshot freeze

Date: 2026-10-01

## Status

The untouched OOS3 Bloomberg price snapshot passed the frozen Issue #119 engineering audit before any OOS3 classifier output or policy economics were inspected.

Frozen universe SHA-256:

`9d4a14d163ed308238737647b94e722c62fd023b641e1015e6d97679f9ba3b44`

Audit:

- pass: **true**
- universe rows: **300**
- completed raw securities: **300**
- failures: **0**
- universe SHA match: **true**
- row-count minimum: **67**
- row-count median: **6,304**
- row-count maximum: **7,210**
- earliest security start: **1998-01-02**
- latest security end: **2026-08-31**
- missing-volume rows: **60**
- normalized OHLC range repairs: **372**
- securities with OHLC range repairs: **38**

The 67-row minimum belongs to a fixed cohort member with short history. It is retained. The frozen classifier / eligibility pipeline will naturally exclude entries that cannot satisfy its warm-up and entry requirements.

No security may be replaced.

## Engineering note

The first audit attempt showed a universe-SHA mismatch because the downloader reserialized the frozen universe through pandas before writing the snapshot copy. No security selection or price data differed.

Downloader commit `2a1f510f11dbc9b711b2b6c92823666b85b14b56` changed this to a byte-for-byte copy of the already-frozen universe file. Re-running the downloader with the existing 300/300 checkpoint required no history re-download and the audit then passed.

This was an artifact-integrity fix only; it did not alter the cohort, raw Bloomberg history, classifier, or policy definitions.

## Firewall

At this freeze point:

- no OOS3 classifier output has been inspected;
- no R0 policy economics have been computed;
- no proof-policy economics have been computed;
- no WarningFirst OOS3 economics have been computed;
- no threshold, exposure state, filter, or cohort member has been changed.

Refs #78, #135, #132, #131, #80.
