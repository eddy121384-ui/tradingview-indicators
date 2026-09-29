# Issue #119 — Bloomberg OOS2 Equity Data Pipeline
## Initial implementation and workstation handoff

Parent research issue: #78  
Related Draft PR: #80

## Status

Initial implementation is complete in branch:

\`feat/issue-119-bloomberg-oos2-pipeline\`

This is still an **engineering / runtime-validation stage**.

No R0 / Warning-First economics have been calculated or inspected.

PR #80 must remain Draft / open / unmerged.

---

## 1. Diagnostic universe design

The first-pass survivorship-limited diagnostic uses the current constituents of three Bloomberg index sleeves:

- large: \`SPX Index\`
- mid: \`MID Index\`
- small: \`SML Index\`

The builder requests \`INDX_MEMBERS\` for each sleeve and then Bloomberg reference metadata for:

- \`ID_BB_GLOBAL\`
- \`TICKER\`
- \`GICS_SECTOR_NAME\`
- \`CUR_MKT_CAP\`
- \`MARKET_SECTOR_DES\`
- \`SECURITY_TYP\`
- \`EQY_PRIM_EXCH_SHRT\`

Target sample:

- 100 large
- 100 mid
- 100 small
- total 300

Within each size sleeve, the sample is allocated approximately equally across the sectors present in that sleeve.

Selection within each sleeve / sector is deterministic from:

- FIGI
- sleeve
- sector
- frozen seed \`issue119-bbg-oos2-v1\`

No price, return, classifier state, R0 result, Warning-First result, or MFE result participates in selection.

AAPL / JPM / XOM are excluded before sampling.

---

## 2. Eligibility firewall

The current implementation fails closed unless Bloomberg metadata identify a candidate as:

- market sector = Equity;
- security type = Common Stock or REIT;
- nonempty FIGI;
- nonempty GICS sector;
- positive market cap.

Explicit security-type tokens rejected include:

- ETF / ETN
- Preferred / Preference
- ADR / Depositary
- Warrant
- Right
- Unit
- Closed-End

The source indices already provide a U.S. listed-equity starting universe, but metadata are still recorded for audit.

If the workstation returns different Bloomberg field values or entitlement-dependent labels, fix only the Bloomberg compatibility layer and document the observed values.

Do not relax the research filter after viewing policy outcomes.

---

## 3. Historical data request

For every selected security the downloader requests:

- \`PX_OPEN\`
- \`PX_HIGH\`
- \`PX_LOW\`
- \`PX_LAST\`
- \`PX_VOLUME\`

Default range:

- start: 1998-01-01
- end: 2026-08-31

Bloomberg historical adjustment request:

- \`adjustmentSplit = true\`
- \`adjustmentNormal = false\`
- \`adjustmentAbnormal = false\`
- \`adjustmentFollowDPDF = false\`

Intent:

> split-consistent OHLCV without ordinary / abnormal cash-dividend back-adjustment.

Do not silently change these flags during runtime debugging.

---

## 4. Retry / resume behavior

Default batch size:

- 25 securities

Default attempts:

- 3

Backoff:

- 1 second
- 2 seconds

Each completed security is stored as a separate gzip CSV named by FIGI.

Checkpoint:

\`issue119_bbg_oos2_checkpoint.json\`

On restart, a security is skipped only when:

1. it appears in the completed checkpoint;
2. its raw file exists;
3. its SHA-256 still matches the checkpoint.

If any selected security remains failed after the final retry, the downloader writes the failure to the raw manifest and exits nonzero.

It does **not** choose a replacement stock.

---

## 5. Output artifacts

Universe builder emits:

- \`issue119_bbg_oos2_candidates.csv\`
- \`issue119_bbg_oos2_universe_manifest.csv\`
- \`issue119_bbg_oos2_universe.json\`

Downloader emits:

- \`raw/<FIGI>.csv.gz\`
- \`issue119_bbg_oos2_checkpoint.json\`
- \`issue119_bbg_oos2_raw_manifest.json\`

Each completed raw security file has:

- row count;
- usable OHLC row count;
- min / max date;
- missing counts;
- ticker;
- Bloomberg security identifier;
- FIGI;
- SHA-256.

The raw manifest also records:

- requested dates;
- requested Bloomberg fields;
- adjustment policy;
- frozen universe SHA-256;
- downloader Git HEAD where available.

Licensed Bloomberg raw files are local artifacts and should not be committed to Git.

---

## 6. Workstation runtime commands

From:

\`indicators/wyckoff-regime-radar/research\`

first build the frozen universe:

\`\`\`bash
python build_issue119_bbg_oos2_universe.py \
  --output-dir artifacts/issue119_bbg_oos2
\`\`\`

Then download OHLCV:

\`\`\`bash
python download_issue119_bbg_oos2_ohlcv.py \
  --universe artifacts/issue119_bbg_oos2/issue119_bbg_oos2_universe_manifest.csv \
  --output-dir artifacts/issue119_bbg_oos2
\`\`\`

If a run is interrupted, rerun the same downloader command. The checkpoint and hashes provide resume behavior.

---

## 7. Runtime validation checklist

The Bloomberg workstation pass should answer only engineering questions:

1. Do \`SPX Index\`, \`MID Index\`, \`SML Index\` return \`INDX_MEMBERS\` under the installed entitlement?
2. What exact field labels are present in the bulk-member response?
3. Do all seven metadata fields resolve?
4. What exact \`SECURITY_TYP\` values appear for ordinary common stock and REIT constituents?
5. Does the builder successfully freeze exactly 300 securities?
6. Are AAPL / JPM / XOM absent?
7. Does HistoricalDataRequest accept the four explicit adjustment flags?
8. Do batched requests return all selected securities?
9. Does retry / resume behave correctly after an intentional interruption?
10. Are raw hashes stable across a resumed run that does not rewrite completed files?

Allowed to inspect:

- counts;
- sectors;
- size sleeves;
- missing metadata;
- missing OHLCV;
- date coverage;
- download errors.

Still prohibited:

- R0 expectancy;
- Warning-First expectancy;
- win rate;
- payoff ratio;
- MFE slices;
- security replacement based on outcome.

---

## 8. Offline compatibility option

The universe builder accepts:

\`--candidate-csv\`

This exists for deterministic local / CI testing and Bloomberg compatibility debugging.

It must **not** be used to hand-pick the formal 300-stock diagnostic cohort.

If the live Bloomberg universe path cannot work, make a documented pre-outcome amendment before using an externally generated candidate universe.

---

## 9. Implementation files

- \`issue119_bbg_common.py\`
- \`issue119_bbg_client.py\`
- \`build_issue119_bbg_oos2_universe.py\`
- \`download_issue119_bbg_oos2_ohlcv.py\`
- \`test_issue119_bbg_oos2_pipeline.py\`
- \`.github/workflows/wyckoff-issue119-bloomberg-oos2.yml\`

The modules deliberately do not import the frozen classifier or any policy-economics implementation.

---

## Next gate

> Run the universe builder on the Bloomberg workstation and freeze the returned 300-stock manifest before any OOS2 policy economics are inspected.

Refs #119, #78, #80.
