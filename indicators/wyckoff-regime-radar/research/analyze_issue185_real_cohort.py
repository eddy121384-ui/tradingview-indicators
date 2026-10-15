#!/usr/bin/env python3
"""Issue #185 -- freeze the REAL parent cohort inputs and ranges (feature-only).

WHAT THIS DOES
--------------
1. Reads the operator-side Issue #76 Pine forward-logger export.
2. Reproduces the parent's frozen parity contract as a COUNTS-ONLY rehearsal
   (events / episodes / B3 events / P1+P2) and asserts it.
3. Identifies the parent's B3 decision cohort with the parent's own loop.
4. Computes the EX-ANTE range-regime descriptor for each B3 event using ONLY
   bars strictly before the probe, and freezes feature-only tertile edges.
5. Records a manifest of the raw input files (name, bytes, sha256, rows) so the
   exact inputs can be re-identified later.

WHAT THIS MUST NEVER DO
-----------------------
No forward return, no PnL, no MFE/MAE, no outcome function of the parent
modules.  ``scipy.stats.rankdata`` -- which the parent's outcome helpers use --
is stubbed to raise, so a stray outcome call cannot pass silently.  The probe
walk stops before the parent ever computes a return.

The raw export is PRIVATE market data.  It is never copied into the repository;
only its hashes, sizes and counts are recorded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import types
from pathlib import Path

# ---------------------------------------------------------------------------
# scipy is not a dependency of this repository.  The parent modules import it at
# module level for their OUTCOME helpers; stub it so those helpers raise if they
# are ever reached on this path.
# ---------------------------------------------------------------------------
def _install_scipy_guard() -> None:
    if "scipy" in sys.modules:
        return

    def _guard(*_a, **_k):
        raise AssertionError(
            "scipy.stats.rankdata was called: an OUTCOME function ran on the "
            "feature-only path.  This script must never compute returns."
        )

    scipy = types.ModuleType("scipy")
    stats = types.ModuleType("scipy.stats")
    stats.rankdata = _guard
    scipy.stats = stats
    sys.modules["scipy"] = scipy
    sys.modules["scipy.stats"] = stats


DEFAULT_GLOB = "/mnt/data/pine-logs-#76 Forward Logger*.csv"
LOCAL_HINT = r"C:\Users\EDDY\Downloads\pine-logs-#76 Forward Logger*.csv"

#: Terrace edges are feature-only quantiles of the REAL B3 cohort.  They are
#: written here so the prereg has stable numbers; ``--min-only`` mode reports
#: them without touching anything.
TERTILE_Q = (1.0 / 3.0, 2.0 / 3.0)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def quantile(xs, q: float):
    s = sorted(xs)
    if not s:
        return None
    pos = q * (len(s) - 1)
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(s) - 1)
    frac = pos - lo
    return s[lo] * (1.0 - frac) + s[hi] * frac


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--export-glob", default=DEFAULT_GLOB,
                    help="glob for the Issue #76 forward-logger export")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--atr-window", type=int, default=14)
    ap.add_argument("--reference-bars", type=int, default=120)
    args = ap.parse_args()

    # Both lengths are the frozen, feature-only research contract.  A
    # different value would silently change the cohort and its tertile edges.
    if args.reference_bars != 120 or args.atr_window != 14:
        ap.error("formal cohort requires --reference-bars=120 and --atr-window=14")

    glob = args.export_glob
    paths = sorted(Path(p) for p in __import__("glob").glob(glob))
    if not paths:
        print(f"NO EXPORT FOUND for glob {glob!r}")
        print(f"local hint: {LOCAL_HINT}")
        print("This script is OPTIONAL and is never required by CI.")
        return 2

    _install_scipy_guard()
    sys.path.insert(0, str(Path(__file__).resolve().parent))

    import analyze_issue78_retest_path_stage1 as s1
    import analyze_issue78_second_entry_economic_policy as s2
    from ptm_range_regime import (ATR_WINDOW_BARS, WIDTH_BIN_MID,
                                  WIDTH_BIN_NARROW, WIDTH_BIN_WIDE,
                                  range_regime_pre_bars)

    # The frozen parity contract lives in the parent's own policy module.
    EXPECTED = {
        "events": s2.EXPECTED_EVENTS,
        "episodes": s2.EXPECTED_EPISODES,
        "b3_events": s2.EXPECTED_B3_EVENTS,
        "P12": s2.EXPECTED_P12,
    }
    print("parent contract: PROBE=%.2f FULL=%.2f MARKER=%s LOOKBACK=%d"
          % (s2.PROBE, s2.FULL, s1.MARKER, s1.LOOKBACK))

    manifest = []
    for p in paths:
        with p.open("r", encoding="utf-8", errors="replace") as fh:
            rows = sum(1 for _ in fh)
        manifest.append({
            "name": p.name,
            "bytes": p.stat().st_size,
            "rows": rows,
            "sha256": sha256_file(p),
        })
    manifest.sort(key=lambda r: r["name"])
    print("input files: %d, total bytes %d" % (
        len(manifest), sum(r["bytes"] for r in manifest)))
    for r in manifest:
        print("  %-44s %9d B %8d rows %s" % (r["name"][:44], r["bytes"],
                                             r["rows"], r["sha256"][:16]))

    events = s1.read_events([str(p) for p in paths])
    frames, recon_err = s1.reconstruct(events)
    episodes = s1.build_episodes(frames)
    print("\ncounts-only rehearsal: events=%d episodes=%d recon_err=%.3e"
          % (len(events), len(episodes), recon_err))

    # --- identify the B3 cohort with the parent's own loop ------------------
    b3 = []
    counts = {"events": len(events), "episodes": len(episodes)}
    for ticker, stage, episode_id, start, episode in episodes:
        if len(episode) < 7:
            continue
        frame = frames[ticker]
        direction = 1 if stage == 2 else -1
        for local_t in range(6, len(episode)):
            idx = start + local_t
            pre = frame.iloc[idx - s1.LOOKBACK:idx]
            cur = frame.iloc[idx]
            if (len(pre) != s1.LOOKBACK
                    or pre[["high_coord", "low_coord"]].isna().any().any()
                    or math.isnan(float(cur["high_coord"]))
                    or math.isnan(float(cur["low_coord"]))):
                continue
            box_high = float(pre["high_coord"].max())
            box_low = float(pre["low_coord"].min())
            if not box_high > box_low:
                continue
            close = float(cur["close_coord"])
            if not (close > box_high if direction == 1 else close < box_low):
                continue
            if not float(s1.raw_scale(frame.iloc[idx - 1])) > 0:
                continue
            remaining = len(episode) - 1 - local_t
            if remaining < 3:
                counts["b3_ineligible"] = counts.get("b3_ineligible", 0) + 1
                break
            early = frame.iloc[idx + 1:idx + 4]
            if (len(early) != 3
                    or early[["close_coord", "high_coord", "low_coord"]]
                    .isna().any().any()):
                counts["b3_missing"] = counts.get("b3_missing", 0) + 1
                break
            closes = early["close_coord"].to_numpy(float)
            highs = early["high_coord"].to_numpy(float)
            lows = early["low_coord"].to_numpy(float)
            if direction == 1:
                touch = bool((lows <= box_high).any())
                reentry = bool((closes <= box_high).any())
                final_outside = bool(closes[-1] > box_high)
            else:
                touch = bool((highs >= box_low).any())
                reentry = bool((closes >= box_low).any())
                final_outside = bool(closes[-1] < box_low)
            if not touch:
                path = "P0_NoTouch"
            elif not reentry:
                path = "P1_WickHold"
            elif final_outside:
                path = "P2_Reclaim"
            else:
                path = "P3_FailedAcceptance"
            b3.append({"ticker": ticker, "stage": stage, "probe_start": start,
                       "b3_idx": idx, "path": path,
                       "break_bar": int(cur["event_bar"])})
            break

    counts["b3_events"] = len(b3)
    counts["P12"] = sum(1 for r in b3 if r["path"] in ("P1_WickHold",
                                                       "P2_Reclaim"))
    for name in ("events", "episodes", "b3_events", "P12"):
        expected = EXPECTED[name]
        got = counts[name]
        flag = "MATCH" if got == expected else "MISMATCH"
        print("  parity %-10s expected %6d got %6d  %s"
              % (name, expected, got, flag))
        if got != expected:
            raise SystemExit(f"parity contract broken for {name}")

    path_breakdown = {}
    for r in b3:
        path_breakdown[r["path"]] = path_breakdown.get(r["path"], 0) + 1
    print("  path composition:", json.dumps(path_breakdown, sort_keys=True))

    # --- ex-ante feature, computed from PRE-PROBE bars only -----------------
    feats = []
    unavail = {}
    for r in b3:
        frame = frames[r["ticker"]]
        recs = frame.to_dict("records")
        start = r["probe_start"]
        lo = max(0, start - args.reference_bars)
        window = recs[lo:start]
        bars = [(float(x["high_coord"]), float(x["low_coord"]),
                 float(x["close_coord"])) for x in window]
        f = range_regime_pre_bars(
            bars, atr_window=args.atr_window,
            require_full_reference=True)
        if f.status != "OK":
            unavail[f.reason] = unavail.get(f.reason, 0) + 1
            continue
        feats.append({"ticker": r["ticker"], "path": r["path"],
                      "break_bar": r["break_bar"], "width_atr": f.width_atr,
                      "atr_pre": f.atr_pre, "ref_span": f.ref_span})

    print("\nex-ante feature: usable %d of %d B3 events" % (len(feats), len(b3)))
    print("  unavailable:", json.dumps(unavail, sort_keys=True))

    edges = None
    bins = {WIDTH_BIN_NARROW: 0, WIDTH_BIN_MID: 0, WIDTH_BIN_WIDE: 0}
    if feats:
        w = [f["width_atr"] for f in feats]
        edges = tuple(round(quantile(w, q), 4) for q in TERTILE_Q)
        print("  width_atr: n=%d min=%.4f q33=%.4f q50=%.4f q67=%.4f max=%.4f"
              % (len(w), min(w), edges[0], quantile(w, 0.5), edges[1], max(w)))
        print("  distinct values: %d  (a tautological criterion would be 1)"
              % len(set(round(x, 9) for x in w)))
        print("  FROZEN TERTILE EDGES (feature-only): %r" % (edges,))
        for x in w:
            bins[WIDTH_BIN_NARROW if x < edges[0]
                 else (WIDTH_BIN_WIDE if x >= edges[1] else WIDTH_BIN_MID)] += 1
        print("  bin counts:", json.dumps(bins, sort_keys=True))

    # Feature-only guard: the committed v2 manifest must be regenerated from
    # the same input hashes, not amended by manually chosen cohort figures.
    short_unavailable = sum(v for k, v in unavail.items()
                            if k.startswith("full pre-probe reference required"))
    coordinate_unavailable = sum(v for k, v in unavail.items()
                                 if "coordinate reset(s)" in k)
    summary = {
        "b3_events": len(b3),
        "usable_width_atr": len(feats),
        "unavailable": sum(unavail.values()),
        "short_reference_unavailable": short_unavailable,
        "coordinate_reset_unavailable": coordinate_unavailable,
        "short_reference_accepted": 0,  # Strict gate rejects all short inputs.
        "distinct_width_atr_values":
            len({f["width_atr"] for f in feats}),
        "width_atr_bins": bins,
        "width_atr_tertile_edges": list(edges) if edges else None,
    }
    if summary["usable_width_atr"] + summary["unavailable"] != len(b3):
        raise AssertionError("real-cohort feature accounting does not reconcile")

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "issue185-real-cohort-v2-strict120",
        "feature_only": True,
        "strict_full_reference": True,
        "outcomes_computed": False,
        "export_glob": glob,
        "raw_data_committed": False,
        "atr_window_bars": args.atr_window,
        "reference_bars": args.reference_bars,
        "manifest": manifest,
        "parity": {"expected": EXPECTED,
                   "observed": counts,
                   "reconstruction_error": recon_err,
                   "path_composition": path_breakdown},
        "parent_contract": {"marker": s1.MARKER, "lookback": s1.LOOKBACK,
                            "probe": s2.PROBE, "full": s2.FULL,
                            "stage1_module": "analyze_issue78_retest_path_stage1.py",
                            "policy_module":
                                "analyze_issue78_second_entry_economic_policy.py"},
        "feature_unavailable": unavail,
        "feature_summary": summary,
        "width_atr_tertile_edges": list(edges) if edges else None,
    }
    # newline="\n" is required: the artifacts directory is marked `-text` in
    # .gitattributes, so the bytes on disk are the bytes CI compares.  Writing
    # with the platform newline would commit CRLF from Windows.
    (out / "issue185_real_cohort_manifest.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8",
        newline="\n")
    print("\nwrote", out / "issue185_real_cohort_manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
