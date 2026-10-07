#!/usr/bin/env python3
"""Issue #78 A3: ablate Supply-Demand, test the two-axis core.

Discovery analyzer, not fresh OOS validation. Ablation study only: it asks
whether Core-2 (structure side x extension) loses anything when the
Supply-Demand axis is dropped entirely. No new S/D factor is invented here.

All scores come from the frozen A1/A2 frame builders by import:
  dir_structure / dir_velocity / extension  (A1, reused unchanged)
  holding_balance / a0_sd                   (A2, controls only)
No weights, no ML/regression, no sign-flips, no six-stage labels.
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
from audit_issue119_bbg_oos2_snapshot import audit_snapshot
from smoke_issue119_frozen_classifier import FROZEN_CLASSIFIER_BLOB, load_classifier

EXPECTED_FIGI_SET_SHA = a0.EXPECTED_FIGI_SET_SHA
HORIZONS = a0.HORIZONS
MIN_CELL_BARS = a0.MIN_CELL_BARS
MIN_AGG_STOCKS = a0.MIN_AGG_STOCKS
BLOCKS = a1.BLOCKS
BLOCK_LABELS = a1.BLOCK_LABELS

CONTROLS = ("a0_sd", "holding_balance")
CORES = ("bull_low", "bull_high", "bear_low", "bear_high")

_tail_stats = a1._tail_stats
append_cell = a1.append_cell
_block_masks = a1._block_masks
aggregate_a1_cells = a1.aggregate_a1_cells
paired_deltas = a1.paired_deltas


def _core_masks(frame: pd.DataFrame, hard: bool) -> dict:
    """Structure side x extension bins. Hard 80/20, relaxed 70/30."""
    rs = frame["rank_dir_structure"].to_numpy(float)
    re_ = frame["rank_extension"].to_numpy(float)
    hi_s, lo_s = (0.80, 0.20) if hard else (0.70, 0.30)
    hi_e, lo_e = (0.80, 0.20) if hard else (0.70, 0.30)
    bull = rs >= hi_s
    bear = rs <= lo_s
    low_ext = re_ <= lo_e
    high_ext = re_ >= hi_e
    return {
        "bull_low": (bull & low_ext, 1.0),
        "bull_high": (bull & high_ext, 1.0),
        "bear_low": (bear & low_ext, -1.0),
        "bear_high": (bear & high_ext, -1.0),
    }


def core_cells(figi: str, frame: pd.DataFrame, meta: dict) -> list[dict]:
    """Phase A: Core-2 cells, hard 80/20 first, then predeclared 70/30."""
    rows = []
    blocks = _block_masks(frame)
    for suffix, hard in (("", True), ("_rel", False)):
        for core, (mask, sign) in _core_masks(frame, hard).items():
            for h in HORIZONS:
                fwd = frame[f"fwd_{h}"].to_numpy(float)
                for block, bmask in blocks.items():
                    append_cell(
                        rows,
                        figi=figi,
                        block=block,
                        horizon=h,
                        test=f"core{suffix}",
                        state=core,
                        mask=bmask & mask,
                        forward=fwd,
                        direction=sign,
                        meta=meta,
                    )
    return rows


def within_cell_control_cells(
    figi: str, frame: pd.DataFrame, meta: dict
) -> list[dict]:
    """Phase B/C: control quintiles and demand/supply splits inside cores."""
    rows = []
    blocks = _block_masks(frame)
    for suffix, hard in (("", True), ("_rel", False)):
        cores = _core_masks(frame, hard)
        qhi, qlo = (0.80, 0.20) if hard else (0.70, 0.30)
        for control in CONTROLS:
            rc = frame[f"rank_{control}"].to_numpy(float)
            demand = rc >= qhi
            supply = rc <= qlo
            for core, (cmask, sign) in cores.items():
                good, bad = (
                    ("demand", "supply")
                    if sign > 0
                    else ("supply", "demand")
                )
                for h in HORIZONS:
                    fwd = frame[f"fwd_{h}"].to_numpy(float)
                    for block, bmask in blocks.items():
                        base = bmask & cmask
                        append_cell(
                            rows,
                            figi=figi,
                            block=block,
                            horizon=h,
                            test=f"core{suffix}_{core}_{control}",
                            state=good,
                            mask=base
                            & (demand if sign > 0 else supply),
                            forward=fwd,
                            direction=sign,
                            meta=meta,
                        )
                        append_cell(
                            rows,
                            figi=figi,
                            block=block,
                            horizon=h,
                            test=f"core{suffix}_{core}_{control}",
                            state=bad,
                            mask=base
                            & (supply if sign > 0 else demand),
                            forward=fwd,
                            direction=sign,
                            meta=meta,
                        )
                        # Within-cell control quintiles (monotonicity view).
                        for q in range(1, 6):
                            lo = (q - 1) / 5.0
                            hi = q / 5.0
                            qmask = (
                                rc <= hi
                                if q == 1
                                else (rc > lo) & (rc <= hi)
                            )
                            append_cell(
                                rows,
                                figi=figi,
                                block=block,
                                horizon=h,
                                test=f"cellq{suffix}_{core}_{control}",
                                state=f"Q{q}",
                                mask=base & qmask,
                                forward=fwd,
                                direction=sign,
                                meta=meta,
                            )
    return rows


def within_cell_rank_info(
    figi: str, frame: pd.DataFrame, meta: dict
) -> list[dict]:
    """Per-stock Spearman(control rank, aligned fwd) inside each core cell."""
    rows = []
    for suffix, hard in (("", True), ("_rel", False)):
        for core, (cmask, sign) in _core_masks(frame, hard).items():
            for control in CONTROLS:
                rc = frame[f"rank_{control}"].to_numpy(float)[cmask]
                for h in HORIZONS:
                    fwd = (
                        frame[f"fwd_{h}"].to_numpy(float)[cmask] * sign
                    )
                    pair = pd.DataFrame(
                        {"rank": rc, "fwd": fwd}
                    ).dropna()
                    if len(pair) < MIN_CELL_BARS:
                        continue
                    rho = pair["rank"].corr(pair["fwd"], method="spearman")
                    rows.append(
                        {
                            "figi": figi,
                            "variant": "hard" if hard else "relaxed",
                            "core": core,
                            "control": control,
                            "horizon": h,
                            "bars": int(len(pair)),
                            "spearman": float(rho),
                            **meta,
                        }
                    )
    return rows


PAIRED_SPECS = {}
for _suffix in ("", "_rel"):
    for _core in CORES:
        _sign = 1.0 if _core.startswith("bull") else -1.0
        for _control in CONTROLS:
            _test = f"core{_suffix}_{_core}_{_control}"
            PAIRED_SPECS[_test] = (
                ("demand", "supply")
                if _sign > 0
                else ("supply", "demand")
            )


def rank_info_summary(per_stock: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if per_stock.empty:
        return pd.DataFrame()
    for (variant, core, control, horizon), group in per_stock.groupby(
        ["variant", "core", "control", "horizon"], sort=True
    ):
        vals = pd.to_numeric(group["spearman"], errors="coerce")
        vals = vals[np.isfinite(vals)]
        rows.append(
            {
                "variant": variant,
                "core": core,
                "control": control,
                "horizon": int(horizon),
                "stocks": int(len(vals)),
                "adequate": int(len(vals) >= MIN_AGG_STOCKS),
                "equal_stock_mean_spearman": (
                    float(vals.mean()) if len(vals) else math.nan
                ),
                "median_stock_spearman": (
                    float(vals.median()) if len(vals) else math.nan
                ),
                "positive_stock_fraction": (
                    float((vals > 0).mean()) if len(vals) else math.nan
                ),
            }
        )
    return pd.DataFrame(rows)


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
    core_rows = []
    control_rows = []
    rankinfo_rows = []

    for i, meta_row in enumerate(universe.itertuples(index=False), start=1):
        figi = str(meta_row.figi)
        raw_path = args.raw_dir / f"{figi}.csv.gz"
        if not raw_path.exists():
            raise FileNotFoundError(raw_path)
        raw = pd.read_csv(raw_path)
        frame = a2.add_within_stock_ranks(
            a2.build_sd_frame(raw, classifier)
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
                "factor_ready_rows": int(frame["ready"].sum()),
            }
        )
        core_rows.extend(core_cells(figi, frame, meta))
        control_rows.extend(
            within_cell_control_cells(figi, frame, meta)
        )
        rankinfo_rows.extend(
            within_cell_rank_info(figi, frame, meta)
        )
        print(
            f"[ablation-a3] "
            f"{i}/{len(universe)} {meta_row.ticker} "
            f"eligible={int(frame['eligible'].sum())} "
            f"ready={int(frame['ready'].sum())}",
            flush=True,
        )

    core_stock = pd.DataFrame(core_rows)
    core_summary = aggregate_a1_cells(
        core_stock, ["test", "state", "block", "horizon"]
    )
    control_stock = pd.DataFrame(control_rows)
    control_summary = aggregate_a1_cells(
        control_stock, ["test", "state", "block", "horizon"]
    )
    paired_stock, paired_summary = paired_deltas(
        control_stock, PAIRED_SPECS
    )
    rankinfo_stock = pd.DataFrame(rankinfo_rows)
    rankinfo_summary = rank_info_summary(rankinfo_stock)

    summary = {
        "integrity": {
            "issue": 78,
            "study": "Supply-Demand Ablation A3",
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
            "blocks": list(BLOCK_LABELS),
            "min_cell_bars": MIN_CELL_BARS,
            "min_aggregate_stocks": MIN_AGG_STOCKS,
        },
        "a3_design": {
            "core": "dir_structure side x extension magnitude (A1, reused)",
            "controls": "a0_sd and holding_balance (overlays only)",
            "no_new_factors": True,
        },
        "notes": [
            "OOS3 is deliberately reused for discovery "
            "under the 2026-10-05 amendment.",
            "No result from this run is fresh OOS evidence.",
            "Hard 80/20 cells reported first; 70/30 relaxed "
            "robustness predeclared.",
            "Within-stock quintiles are retrospective "
            "discovery bins, not live thresholds.",
        ],
    }

    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "coverage.csv", pd.DataFrame(coverage))
    write_csv(args.out / "core_per_stock.csv", core_stock)
    write_csv(args.out / "core_summary.csv", core_summary)
    write_csv(args.out / "control_per_stock.csv", control_stock)
    write_csv(args.out / "control_summary.csv", control_summary)
    write_csv(args.out / "paired_delta_per_stock.csv", paired_stock)
    write_csv(args.out / "paired_delta_summary.csv", paired_summary)
    write_csv(args.out / "rank_info_per_stock.csv", rankinfo_stock)
    write_csv(args.out / "rank_info_summary.csv", rankinfo_summary)
    (args.out / "summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
