#!/usr/bin/env python3
"""Issue #78 A6: trigger-layer discovery on frozen Core-2 context (OOS3).

Discovery only. All Core-2 definitions reused from frozen A4/A2 builders
by import — nothing redefined. Structural levels, trigger families,
timing semantics, and dedup follow the frozen A6 preregistration exactly.

Unit of analysis: EVENT (deduped triggers), one row per trigger.
Primary outcomes use next-bar-actionable timing; same-close timing is
descriptive only. Context attached is the causal Core-2 cell at the
confirmation close bar.
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
from audit_issue119_bbg_oos2_snapshot import audit_snapshot
from smoke_issue119_frozen_classifier import FROZEN_CLASSIFIER_BLOB, load_classifier

EXPECTED_FIGI_SET_SHA = a0.EXPECTED_FIGI_SET_SHA
HORIZONS = a0.HORIZONS
MIN_CELL_BARS = a0.MIN_CELL_BARS
MIN_AGG_STOCKS = a0.MIN_AGG_STOCKS

LEVEL_LOOKBACK = 20
T1_BARS = 3
T2_BARS = 5
T3_BARS = 3

_tail_stats = a1._tail_stats
append_cell = a1.append_cell
aggregate_a1_cells = a1.aggregate_a1_cells
paired_deltas = a1.paired_deltas


def structural_levels(frame: pd.DataFrame) -> pd.DataFrame:
    """Frozen prior-20 levels; current bar strictly excluded."""
    high = pd.to_numeric(frame["high"], errors="coerce")
    low = pd.to_numeric(frame["low"], errors="coerce")
    out = pd.DataFrame(
        {
            "prior_high_20": high.rolling(
                LEVEL_LOOKBACK, min_periods=LEVEL_LOOKBACK
            ).max().shift(1),
            "prior_low_20": low.rolling(
                LEVEL_LOOKBACK, min_periods=LEVEL_LOOKBACK
            ).min().shift(1),
        }
    )
    return out


def causal_context_labels(frame: pd.DataFrame) -> np.ndarray:
    """Causal Core-2 cell label per bar (hard 80/20 + relaxed 70/30)."""
    hard = a4._causal_masks(frame, True)
    rel = a4._causal_masks(frame, False)
    label = np.full(len(frame), "non-core", dtype=object)
    for state in ("bear_high", "bear_low", "bull_high", "bull_low"):
        label[hard[state][0]] = state
    label_rel = np.full(len(frame), "non-core", dtype=object)
    for state in ("bear_high", "bear_low", "bull_high", "bull_low"):
        label_rel[rel[state][0]] = state
    return label, label_rel


def detect_triggers(frame: pd.DataFrame) -> pd.DataFrame:
    """Frozen dedup state machine + T0/T1/T2/T3 derivation (CLOSE only).

    Returns one row per trigger event with confirmation timestamp,
    frozen level, context labels at confirmation, and evaluation bars
    for primary (next-bar actionable) and descriptive (same-close) timing.
    """
    close = pd.to_numeric(frame["close"], errors="coerce").to_numpy(float)
    if "prior_high_20" not in frame.columns:
        lv = structural_levels(frame)
        frame = frame.copy()
        frame["prior_high_20"] = lv["prior_high_20"].to_numpy(float)
        frame["prior_low_20"] = lv["prior_low_20"].to_numpy(float)
    ph = frame["prior_high_20"].to_numpy(float)
    pl = frame["prior_low_20"].to_numpy(float)
    n = len(frame)
    label, _ = causal_context_labels(frame)
    events = []

    def emit(side, family, t0, t_confirm, level, context):
        e_primary = t_confirm + 1
        e_desc = t_confirm
        if e_primary >= n:
            return
        events.append(
            {
                "side": side,
                "family": family,
                "t0": int(t0),
                "t_confirm": int(t_confirm),
                "level": float(level),
                "context": str(context),
                "e_primary": int(e_primary),
                "e_desc": int(e_desc),
            }
        )

    blocked = {"bull": -1, "bear": -1}
    for side in ("bull", "bear"):
        for t0 in range(n):
            if t0 <= blocked[side]:
                continue
            c, lo, hi = close[t0], pl[t0], ph[t0]
            if not (np.isfinite(c) and np.isfinite(lo) and np.isfinite(hi)):
                continue
            if side == "bull":
                fires = c > hi
                prev = (
                    close[t0 - 1] > ph[t0 - 1]
                    if t0 > 0
                    and np.isfinite(close[t0 - 1])
                    and np.isfinite(ph[t0 - 1])
                    else False
                )
            else:
                fires = c < lo
                prev = (
                    close[t0 - 1] < pl[t0 - 1]
                    if t0 > 0
                    and np.isfinite(close[t0 - 1])
                    and np.isfinite(pl[t0 - 1])
                    else False
                )
            if not fires or prev:
                continue
            level = hi if side == "bull" else lo
            ctx0 = label[t0]
            emit(side, "T0", t0, t0, level, ctx0)
            # T1: next 3 completed bars, majority + final-close rule.
            if t0 + T1_BARS < n:
                window = close[t0 + 1 : t0 + 1 + T1_BARS]
                if np.isfinite(window).all():
                    if side == "bull":
                        beyond = window > level
                    else:
                        beyond = window < level
                    if beyond.sum() >= 2 and bool(beyond[-1]):
                        emit(
                            side, "T1", t0, t0 + T1_BARS, level,
                            label[t0 + T1_BARS],
                        )
            # T2: pullback first, reclaim later, within 5 bars.
            end2 = min(t0 + T2_BARS, n - 1)
            pulled = False
            for k in range(t0 + 1, end2 + 1):
                ck = close[k]
                if not np.isfinite(ck):
                    break
                if not pulled:
                    if (ck <= level) if side == "bull" else (ck >= level):
                        pulled = True
                else:
                    if (ck > level) if side == "bull" else (ck < level):
                        emit(side, "T2", t0, k, level, label[k])
                        break
            # T3: failure back inside within 3 bars (reversal semantics).
            end3 = min(t0 + T3_BARS, n - 1)
            for k in range(t0 + 1, end3 + 1):
                ck = close[k]
                if not np.isfinite(ck):
                    break
                if (ck > level) if side == "bear" else (ck < level):
                    # Bear raw event reclaimed above -> bullish failure, etc.
                    # Recorded under the ORIGINAL break side with family T3.
                    fail_side = (
                        "bull" if side == "bear" else "bear"
                    )
                    emit(fail_side, "T3", t0, k, level, label[k])
                    break
            blocked[side] = t0 + T2_BARS
    return pd.DataFrame(events)


def build_trigger_frame(raw: pd.DataFrame, classifier) -> pd.DataFrame:
    """A2 frame + causal ranks + OHLC + levels (all causal inputs)."""
    frame = a4.add_causal_ranks(
        a2.add_within_stock_ranks(a2.build_sd_frame(raw, classifier))
    )
    dates = pd.to_datetime(raw["date"], errors="coerce")
    order = np.argsort(dates.to_numpy(), kind="stable")
    ohlc = pd.DataFrame(
        {
            "high": pd.to_numeric(
                raw["high"], errors="coerce"
            ).to_numpy(float)[order],
            "low": pd.to_numeric(
                raw["low"], errors="coerce"
            ).to_numpy(float)[order],
            "close": pd.to_numeric(
                raw["close"], errors="coerce"
            ).to_numpy(float)[order],
        }
    )
    if not (frame["date"].to_numpy() == np.sort(dates.to_numpy())).all():
        raise AssertionError("date order drift")
    for col in ("high", "low", "close"):
        frame[col] = ohlc[col].to_numpy(float)
    levels = structural_levels(frame)
    frame["prior_high_20"] = levels["prior_high_20"].to_numpy(float)
    frame["prior_low_20"] = levels["prior_low_20"].to_numpy(float)
    return frame


STANDALONE = (
    ("T0", "bull"),
    ("T0", "bear"),
    ("T1", "bull"),
    ("T1", "bear"),
    ("T2", "bull"),
    ("T2", "bear"),
    ("T3", "bull"),
    ("T3", "bear"),
)

COMBOS = (
    ("bull_low", "T0", "bull"),
    ("bull_high", "T0", "bull"),
    ("bull_low", "T1", "bull"),
    ("bull_high", "T1", "bull"),
    ("bull_low", "T2", "bull"),
    ("bull_high", "T2", "bull"),
    ("bear_low", "T0", "bear"),
    ("bear_high", "T0", "bear"),
    ("bear_low", "T1", "bear"),
    ("bear_high", "T1", "bear"),
    ("bear_low", "T2", "bear"),
    ("bear_high", "T2", "bear"),
    ("bull_low", "T3", "bull"),
    ("bull_high", "T3", "bull"),
    ("bear_low", "T3", "bear"),
    ("bear_high", "T3", "bear"),
)


def _block_masks_events(frame: pd.DataFrame, idx: np.ndarray) -> dict:
    dates_block = frame["block"].to_numpy()[idx]
    masks = {"ALL": np.ones(len(idx), dtype=bool)}
    for name, _, _ in a1.BLOCKS:
        masks[name] = dates_block == name
    return masks


def event_cells(
    figi: str,
    frame: pd.DataFrame,
    events: pd.DataFrame,
    meta: dict,
) -> list[dict]:
    """Aggregate deduped events one-stock-one-vote (primary + descriptive)."""
    rows = []
    if events.empty:
        return rows
    for h in HORIZONS:
        fwd = frame[f"fwd_{h}"].to_numpy(float)
        for timing, ecol in (("primary", "e_primary"), ("descriptive", "e_desc")):
            eidx = events[ecol].to_numpy(int)
            valid_e = (eidx >= 0) & (eidx < len(frame))
            for family, side in STANDALONE:
                sign = 1.0 if side == "bull" else -1.0
                sel = (
                    (events["family"] == family)
                    & (events["side"] == side)
                    & valid_e
                )
                if not sel.any():
                    continue
                vals = fwd[eidx[sel.to_numpy()]] * sign
                blocks = _block_masks_events(
                    frame, np.flatnonzero(sel.to_numpy())
                )
                for block, bmask in blocks.items():
                    append_cell(
                        rows,
                        figi=figi,
                        block=block,
                        horizon=h,
                        test=f"{timing}_{family}_{side}",
                        state="trigger",
                        mask=bmask,
                        forward=vals,
                        meta=meta,
                    )
            for context, family, side in COMBOS:
                sign = 1.0 if side == "bull" else -1.0
                if timing != "primary":
                    continue
                sel = (
                    (events["family"] == family)
                    & (events["side"] == side)
                    & (events["context"] == context)
                    & valid_e
                )
                if not sel.any():
                    continue
                vals = fwd[eidx[sel.to_numpy()]] * sign
                blocks = _block_masks_events(
                    frame, np.flatnonzero(sel.to_numpy())
                )
                for block, bmask in blocks.items():
                    append_cell(
                        rows,
                        figi=figi,
                        block=block,
                        horizon=h,
                        test=f"combo_{context}_{family}_{side}",
                        state="trigger",
                        mask=bmask,
                        forward=vals,
                        meta=meta,
                    )
    return rows


def aggregate_events(frame: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    return a1.aggregate_a1_cells(frame, group_cols)


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
    cell_rows = []

    for i, meta_row in enumerate(universe.itertuples(index=False), start=1):
        figi = str(meta_row.figi)
        raw_path = args.raw_dir / f"{figi}.csv.gz"
        if not raw_path.exists():
            raise FileNotFoundError(raw_path)
        raw = pd.read_csv(raw_path)
        frame = build_trigger_frame(raw, classifier)
        events = detect_triggers(frame)
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
                "causal_ready_rows": int(frame["causal_ready"].sum()),
                "trigger_events": int(len(events)),
            }
        )
        for _, ev in events.iterrows():
            event_rows.append({"figi": figi, **ev.to_dict(), **meta})
        cell_rows.extend(event_cells(figi, frame, events, meta))
        print(
            f"[trigger-layer-a6] "
            f"{i}/{len(universe)} {meta_row.ticker} "
            f"events={len(events)}",
            flush=True,
        )

    events_stock = pd.DataFrame(event_rows)
    cells_stock = pd.DataFrame(cell_rows)
    cells_summary = aggregate_events(
        cells_stock, ["test", "state", "block", "horizon"]
    )

    summary = {
        "integrity": {
            "issue": 78,
            "study": "Trigger-Layer Discovery A6",
            "role": (
                "post-outcome architecture discovery; "
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
        },
        "a6_frozen": {
            "level": "prior-20 completed bars, current excluded",
            "timing": "next-bar actionable primary, same-close descriptive",
            "dedup": "no consecutive repeats, one sequence per side window",
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
    write_csv(args.out / "trigger_per_stock.csv", cells_stock)
    write_csv(args.out / "trigger_summary.csv", cells_summary)
    (args.out / "summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
