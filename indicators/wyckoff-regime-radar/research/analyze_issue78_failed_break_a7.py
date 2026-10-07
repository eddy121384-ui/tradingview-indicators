#!/usr/bin/env python3
"""Issue #78 A7: failed-break rejection / reversal mechanism study (OOS3).

Discovery only. F0 mirrors the frozen A6 T3 derivation exactly (independent
code path; equality asserted on real data — mismatch stops the study).
Structural levels, ATR (`sym_atr` via A2 `scale`), and Core-2 ranks are
reused from frozen builders by import; nothing redefined.

Events: F0 failed breaks (+M1–M5 descriptors), CONTROL A raw breaks
(A6 T0, same forward clock), CONTROL B non-reclaimed breaks (mutually
exclusive with F0). Unit = EVENT, one-stock-one-vote; primary timing is
next-bar-actionable (e = knowable bar + 1), aligned bull +1 / bear −1.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

import analyze_issue78_factorized_classifier_discovery as a0
import analyze_issue78_direction_decomposition_a1 as a1
import analyze_issue78_supply_demand_a2 as a2
import analyze_issue78_causal_core2_a4 as a4
import analyze_issue78_trigger_layer_a6 as a6
from audit_issue119_bbg_oos2_snapshot import audit_snapshot
from smoke_issue119_frozen_classifier import FROZEN_CLASSIFIER_BLOB, load_classifier

EXPECTED_FIGI_SET_SHA = a0.EXPECTED_FIGI_SET_SHA
HORIZONS = a0.HORIZONS
MIN_CELL_BARS = a0.MIN_CELL_BARS
MIN_AGG_STOCKS = a0.MIN_AGG_STOCKS

RECLAIM_WINDOW = 3
BLOCK_BARS = 5  # same-side sequence block, mirroring A6

_tail_stats = a1._tail_stats
append_cell = a1.append_cell
aggregate_a1_cells = a1.aggregate_a1_cells
paired_deltas = a1.paired_deltas


def detect_failed_breaks(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Independent F0 + non-reclaim derivation (must equal A6 T3 / complement).

    Returns (f0_events, nonreclaim_events). Each row: side, t0, tc, level,
    speed, depth, reclaim, clv, follow, struct_side, ext_level, e_primary.
    """
    close = pd.to_numeric(frame["close"], errors="coerce").to_numpy(float)
    high = pd.to_numeric(frame["high"], errors="coerce").to_numpy(float)
    low = pd.to_numeric(frame["low"], errors="coerce").to_numpy(float)
    atr = frame["scale"].to_numpy(float)
    ph = frame["prior_high_20"].to_numpy(float)
    pl = frame["prior_low_20"].to_numpy(float)
    rs = frame["rank_c_struct"].to_numpy(float)
    re_ = frame["rank_c_ext"].to_numpy(float)
    n = len(frame)
    f0, non = [], []
    blocked = {"bull": -1, "bear": -1}

    def strata(depth, reclaim, clv):
        if not np.isfinite(depth):
            d = "nan"
        elif depth <= 0.25:
            d = "shallow"
        elif depth <= 0.75:
            d = "medium"
        else:
            d = "deep"
        if not np.isfinite(reclaim):
            r = "nan"
        elif reclaim <= 0.25:
            r = "weak"
        elif reclaim <= 0.75:
            r = "medium"
        else:
            r = "strong"
        if not np.isfinite(clv):
            c = "nan"
        elif clv < 1.0 / 3.0:
            c = "low"
        elif clv <= 2.0 / 3.0:
            c = "mid"
        else:
            c = "high"
        return d, r, c

    for side in ("bull", "bear"):
        for t0 in range(n):
            if t0 <= blocked[side]:
                continue
            c0, lo, hi = close[t0], pl[t0], ph[t0]
            if not (np.isfinite(c0) and np.isfinite(lo) and np.isfinite(hi)):
                continue
            if side == "bull":
                fires = c0 < lo
                prev = (
                    close[t0 - 1] < pl[t0 - 1]
                    if t0 > 0
                    and np.isfinite(close[t0 - 1])
                    and np.isfinite(pl[t0 - 1])
                    else False
                )
                level = lo
            else:
                fires = c0 > hi
                prev = (
                    close[t0 - 1] > ph[t0 - 1]
                    if t0 > 0
                    and np.isfinite(close[t0 - 1])
                    and np.isfinite(ph[t0 - 1])
                    else False
                )
                level = hi
            if not fires or prev:
                continue
            end = min(t0 + RECLAIM_WINDOW, n - 1)
            confirmed = None
            for k in range(t0 + 1, end + 1):
                ck = close[k]
                if not np.isfinite(ck):
                    break
                if (ck > level) if side == "bull" else (ck < level):
                    confirmed = k
                    break
            a0atr = atr[t0]
            depth = (
                ((level - c0) / a0atr)
                if side == "bull"
                else ((c0 - level) / a0atr)
            ) if np.isfinite(a0atr) and a0atr > 0 else math.nan
            struct_side = (
                "structbull"
                if rs[t0] >= 0.5
                else ("structbear" if np.isfinite(rs[t0]) else "nan")
            )
            ext_level = (
                "extlow"
                if re_[t0] < 0.5
                else ("exthigh" if np.isfinite(re_[t0]) else "nan")
            )
            base = {
                "side": side,
                "t0": int(t0),
                "level": float(level),
                "depth": float(depth),
                "struct_side": struct_side,
                "ext_level": ext_level,
            }
            if confirmed is None:
                if t0 + 1 < n:
                    non.append({**base, "e_primary": int(t0 + 1)})
            else:
                tc = confirmed
                if tc + 1 >= n:
                    # Reclaimed on the final bar: no evaluable forward
                    # outcome exists. Mirror A6, which drops such tail
                    # events at detection (e_primary out of range).
                    blocked[side] = t0 + BLOCK_BARS
                    continue
                cc, ch, cl = close[tc], high[tc], low[tc]
                a1atr = atr[tc]
                reclaim = (
                    ((cc - level) / a1atr)
                    if side == "bull"
                    else ((level - cc) / a1atr)
                ) if np.isfinite(a1atr) and a1atr > 0 else math.nan
                clv = (
                    (cc - cl) / (ch - cl)
                    if np.isfinite(ch) and np.isfinite(cl) and ch > cl
                    else math.nan
                )
                cn = close[tc + 1] if tc + 1 < n else math.nan
                follow = (
                    bool(cn > cc)
                    if side == "bull"
                    else bool(cn < cc)
                ) if np.isfinite(cn) and np.isfinite(cc) else False
                d, r, cter = strata(depth, reclaim, clv)
                speed = tc - t0
                f0.append(
                    {
                        **base,
                        "tc": int(tc),
                        "speed": int(speed),
                        "reclaim": float(reclaim),
                        "clv": float(clv),
                        "follow": bool(follow),
                        "depth_stratum": d,
                        "reclaim_stratum": r,
                        "clv_tertile": cter,
                        "e_primary": int(tc + 1),
                    }
                )
            blocked[side] = t0 + BLOCK_BARS
    f0df = pd.DataFrame(f0)
    nondf = pd.DataFrame(non)
    return f0df, nondf


def _block_masks_events(frame: pd.DataFrame, idx: np.ndarray) -> dict:
    dates_block = frame["block"].to_numpy()[idx]
    masks = {"ALL": np.ones(len(idx), dtype=bool)}
    for name, _, _ in a1.BLOCKS:
        masks[name] = dates_block == name
    return masks


def f0_cells(
    figi: str, frame: pd.DataFrame, f0: pd.DataFrame, meta: dict
) -> list[dict]:
    """F0 headline + M-strata + Core-2 explanatory splits (aligned)."""
    rows = []
    if f0.empty:
        return rows
    blocks_all = _block_masks_events(
        frame, np.zeros(len(frame), dtype=bool)
    )
    for h in HORIZONS:
        fwd = frame[f"fwd_{h}"].to_numpy(float)
        blocks_of = frame["block"].to_numpy()
        for side in ("bull", "bear"):
            sign = 1.0 if side == "bull" else -1.0
            sub = f0[f0["side"] == side]
            if sub.empty:
                continue
            eidx = sub["e_primary"].to_numpy(int)
            ok = (eidx >= 0) & (eidx < len(frame))
            if not ok.any():
                continue
            base_vals = fwd[eidx[ok]] * sign
            base_pos = np.flatnonzero(ok)  # positions into sub
            base_blk = blocks_of[eidx[ok]]
            cases = [("F0_" + side, np.ones(len(sub), dtype=bool))]
            cases += [
                (f"F0_{side}_speed{s}", (sub["speed"] == s).to_numpy())
                for s in (1, 2, 3)
            ]
            cases += [
                (
                    f"F0_{side}_depth_{d}",
                    (sub["depth_stratum"] == d).to_numpy(),
                )
                for d in ("shallow", "medium", "deep")
            ]
            cases += [
                (
                    f"F0_{side}_reclaim_{r}",
                    (sub["reclaim_stratum"] == r).to_numpy(),
                )
                for r in ("weak", "medium", "strong")
            ]
            cases += [
                (
                    f"F0_{side}_clv_{c}",
                    (sub["clv_tertile"] == c).to_numpy(),
                )
                for c in ("low", "mid", "high")
            ]
            cases += [
                (f"F0_{side}_follow_yes", (sub["follow"] == True).to_numpy()),  # noqa: E712
                (f"F0_{side}_follow_no", (sub["follow"] == False).to_numpy()),  # noqa: E712
                (
                    f"F0_{side}_structbull",
                    (sub["struct_side"] == "structbull").to_numpy(),
                ),
                (
                    f"F0_{side}_structbear",
                    (sub["struct_side"] == "structbear").to_numpy(),
                ),
                (
                    f"F0_{side}_extlow",
                    (sub["ext_level"] == "extlow").to_numpy(),
                ),
                (
                    f"F0_{side}_exthigh",
                    (sub["ext_level"] == "exthigh").to_numpy(),
                ),
            ]
            for test, m in cases:
                keep = m[ok]
                if not keep.any():
                    continue
                for block in ("ALL",) + a1.BLOCK_LABELS[1:]:
                    if block == "ALL":
                        sel = keep
                    else:
                        sel = keep & (base_blk == block)
                    if sel.sum() < MIN_CELL_BARS:
                        continue
                    stats = _tail_stats(base_vals[sel])
                    row = {
                        "figi": figi,
                        "block": block,
                        "horizon": h,
                        "test": test,
                        "state": "event",
                        **stats,
                    }
                    if meta:
                        row.update(meta)
                    rows.append(row)
    return rows


def _align_index(idx_all, sel, bmask):
    raise AssertionError("unused")


def control_cells(
    figi: str,
    frame: pd.DataFrame,
    f0: pd.DataFrame,
    non: pd.DataFrame,
    a6events: pd.DataFrame,
    meta: dict,
) -> tuple[list[dict], list[dict]]:
    """CONTROL A (A6 raw T0, same clock) and CONTROL B (non-reclaimed)."""
    rows = []
    if a6events.empty and non.empty:
        return rows, []
    for h in HORIZONS:
        fwd = frame[f"fwd_{h}"].to_numpy(float)
        for side in ("bull", "bear"):
            sign = 1.0 if side == "bull" else -1.0
            t0ev = (
                a6events[
                    (a6events["family"] == "T0")
                    & (a6events["side"] == side)
                ]
                if not a6events.empty
                else a6events
            )
            if not t0ev.empty:
                eidx = t0ev["e_primary"].to_numpy(int)
                ok = (eidx >= 0) & (eidx < len(frame))
                if ok.any():
                    blocks = _block_masks_events(
                        frame, np.flatnonzero(ok)
                    )
                    for block, bmask in blocks.items():
                        append_cell(
                            rows,
                            figi=figi,
                            block=block,
                            horizon=h,
                            test=f"CTRL_raw_{side}",
                            state="event",
                            mask=bmask,
                            forward=fwd[eidx[ok]] * sign,
                            meta=meta,
                        )
            nrev = (
                non[non["side"] == side] if not non.empty else non
            )
            if not nrev.empty:
                eidx = nrev["e_primary"].to_numpy(int)
                ok = (eidx >= 0) & (eidx < len(frame))
                if ok.any():
                    blocks = _block_masks_events(
                        frame, np.flatnonzero(ok)
                    )
                    for block, bmask in blocks.items():
                        append_cell(
                            rows,
                            figi=figi,
                            block=block,
                            horizon=h,
                            test=f"CTRL_nonreclaim_{side}",
                            state="event",
                            mask=bmask,
                            forward=fwd[eidx[ok]] * sign,
                            meta=meta,
                        )
    return rows, []


PAIRED_SPECS = {
    "F0bull_vs_raw": ("good", "bad"),
    "F0bull_vs_nonreclaim": ("good", "bad"),
    "F0bear_vs_raw": ("good", "bad"),
    "F0bear_vs_nonreclaim": ("good", "bad"),
}


def write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--raw-dir", type=Path, required=True)
    ap.add_argument(
        "--classifier",
        type=Path,
        default=Path("generated/wyckoff-issue78-rc-python.py"),
    )
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    audit = audit_snapshot(args.universe, args.manifest, args.raw_dir)
    if not audit["pass"]:
        raise SystemExit("snapshot audit failed")

    universe = pd.read_csv(args.universe)
    if len(universe) != 300 or universe["figi"].nunique() != 300:
        raise AssertionError("universe membership drift")
    cohort_sha = a0.figi_set_sha(universe)
    if cohort_sha != EXPECTED_FIGI_SET_SHA:
        raise AssertionError(f"OOS3 FIGI-set drift: {cohort_sha}")

    classifier, blob = load_classifier(args.classifier)
    if blob != FROZEN_CLASSIFIER_BLOB:
        raise AssertionError("frozen classifier blob drift")

    coverage = []
    event_rows = []
    f0_rows = []
    ctrl_rows = []

    for i, meta_row in enumerate(universe.itertuples(index=False), start=1):
        figi = str(meta_row.figi)
        raw_path = args.raw_dir / f"{figi}.csv.gz"
        if not raw_path.exists():
            raise FileNotFoundError(raw_path)
        raw = pd.read_csv(raw_path)
        frame = a6.build_trigger_frame(raw, classifier)
        f0, non = detect_failed_breaks(frame)
        a6events = a6.detect_triggers(frame)
        # Reproduction gate: F0 must equal A6 T3 exactly.
        t3 = a6events[a6events["family"] == "T3"].copy()
        key = ["side", "t0", "t_confirm"]
        left = (
            f0.rename(columns={"tc": "t_confirm"})[key]
            .sort_values(key)
            .reset_index(drop=True)
            if not f0.empty
            else pd.DataFrame(columns=key)
        )
        # A6 T3 side already equals the F0 break side (bull = failed
        # breakdown below the low; bear = failed breakout above the high).
        right = (
            t3[key].sort_values(key).reset_index(drop=True)
            if not t3.empty
            else pd.DataFrame(columns=key)
        )
        if not left.equals(right):
            raise AssertionError(
                f"A6 T3 reproduction failed for {figi}: "
                f"F0={len(left)} A6T3={len(right)}"
            )
        meta = {
            "sector": str(meta_row.sector),
            "sleeve": str(meta_row.sleeve),
        }
        coverage.append(
            {
                "figi": figi,
                "ticker": str(meta_row.ticker),
                **meta,
                "raw_rows": int(len(frame)),
                "eligible_rows": int(frame["eligible"].sum()),
                "f0_events": int(len(f0)),
                "nonreclaim_events": int(len(non)),
            }
        )
        for _, ev in f0.iterrows():
            event_rows.append({"figi": figi, **ev.to_dict(), **meta})
        f0_rows.extend(f0_cells(figi, frame, f0, meta))
        ctrl, _ = control_cells(figi, frame, f0, non, a6events, meta)
        ctrl_rows.extend(ctrl)
        print(
            f"[failed-break-a7] "
            f"{i}/{len(universe)} {meta_row.ticker} "
            f"f0={len(f0)} nonreclaim={len(non)}",
            flush=True,
        )

    events_stock = pd.DataFrame(event_rows)
    f0_stock = pd.DataFrame(f0_rows)
    f0_summary = aggregate_a1_cells(
        f0_stock, ["test", "state", "block", "horizon"]
    )
    ctrl_stock = pd.DataFrame(ctrl_rows)
    ctrl_summary = aggregate_a1_cells(
        ctrl_stock, ["test", "state", "block", "horizon"]
    )
    pair_frames = []
    for (test, f0test, ctrltest) in (
        ("F0bull_vs_raw", "F0_bull", "CTRL_raw_bull"),
        ("F0bull_vs_nonreclaim", "F0_bull", "CTRL_nonreclaim_bull"),
        ("F0bear_vs_raw", "F0_bear", "CTRL_raw_bear"),
        ("F0bear_vs_nonreclaim", "F0_bear", "CTRL_nonreclaim_bear"),
    ):
        tmp = pd.concat(
            [
                f0_stock[f0_stock["test"] == f0test].assign(
                    test=test, state="good"
                ),
                ctrl_stock[ctrl_stock["test"] == ctrltest].assign(
                    test=test, state="bad"
                ),
            ],
            ignore_index=True,
        )
        pair_frames.append(tmp)
    pair_all = (
        pd.concat(pair_frames, ignore_index=True) if pair_frames else pd.DataFrame()
    )
    if pair_all.empty:
        pair_stock, pair_summary = pd.DataFrame(), pd.DataFrame()
    else:
        pair_stock, pair_summary = paired_deltas(pair_all, PAIRED_SPECS)

    summary = {
        "integrity": {
            "issue": 78,
            "study": "Failed-Break Rejection A7",
            "role": (
                "post-outcome mechanism discovery; "
                "not fresh OOS validation"
            ),
            "classifier_blob": blob,
            "figi_set_sha256": cohort_sha,
            "stocks": int(len(universe)),
            "raw_files": int(audit["completed"]),
            "raw_failures": int(audit["failures"]),
            "horizons": list(HORIZONS),
            "blocks": list(a1.BLOCK_LABELS),
            "min_cell_bars": MIN_CELL_BARS,
            "min_aggregate_stocks": MIN_AGG_STOCKS,
            "oos4_touched": False,
            "a6_t3_reproduction": "exact-or-abort per stock",
        },
        "a7_frozen": {
            "level": "prior-20 completed bars, current excluded",
            "reclaim_window": RECLAIM_WINDOW,
            "timing": "next-bar actionable primary",
            "descriptors": "M1 speed, M2 depth, M3 reclaim, M4 CLV, M5 follow",
        },
        "notes": [
            "OOS3 is deliberately reused for discovery "
            "under the 2026-10-05 amendment.",
            "No result from this run is fresh OOS evidence.",
            "Unit of analysis is the deduped EVENT, one-stock-one-vote.",
        ],
    }

    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "coverage.csv", pd.DataFrame(coverage))
    write_csv(args.out / "events.csv", events_stock)
    write_csv(args.out / "f0_per_stock.csv", f0_stock)
    write_csv(args.out / "f0_summary.csv", f0_summary)
    write_csv(args.out / "control_per_stock.csv", ctrl_stock)
    write_csv(args.out / "control_summary.csv", ctrl_summary)
    write_csv(args.out / "paired_delta_per_stock.csv", pair_stock)
    write_csv(args.out / "paired_delta_summary.csv", pair_summary)
    (args.out / "summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
