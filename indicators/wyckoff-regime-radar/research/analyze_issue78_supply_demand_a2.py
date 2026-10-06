#!/usr/bin/env python3
"""Issue #78 A2: rebuild supply-demand orthogonal to velocity.

Discovery analyzer, not fresh OOS validation. Uses frozen classifier
primitives only; no six-stage outputs are inputs.

Phase A — decompose the four frozen S/D primitives separately:
  downside_exhaustion, support_holding, upside_exhaustion, resistance_holding
Phase B — predeclared simple candidates (no tuned weights, no ML):
  holding_balance    = support_holding - resistance_holding
  exhaustion_balance = downside_exhaustion - upside_exhaustion
  a0_sd              = A0 control only (definitions unchanged)
Phase C — orthogonality gates vs velocity / extension / structure.
Phase D — conditional tests on the frozen A1 axes (structure = side,
  velocity/extension = magnitude). A1 velocity/structure formulas are reused
  by import, never redefined here.
Phase E — fixed calendar blocks (same bins as A1).

No new composite beyond H/E is proposed; no sign-flip rescue.
"""
from __future__ import annotations

import argparse
import json
import math
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

import analyze_issue78_bbg_equity_oos2 as base
import analyze_issue78_factorized_classifier_discovery as a0
import analyze_issue78_direction_decomposition_a1 as a1
from audit_issue119_bbg_oos2_snapshot import audit_snapshot
from smoke_issue119_frozen_classifier import FROZEN_CLASSIFIER_BLOB, load_classifier

EXPECTED_FIGI_SET_SHA = a0.EXPECTED_FIGI_SET_SHA
HORIZONS = a0.HORIZONS
MIN_CELL_BARS = a0.MIN_CELL_BARS
MIN_AGG_STOCKS = a0.MIN_AGG_STOCKS
BLOCKS = a1.BLOCKS
BLOCK_LABELS = a1.BLOCK_LABELS

PRIMITIVES = (
    "down_exh",
    "sup_hold",
    "up_exh",
    "res_hold",
)

CANDIDATES = (
    "holding_balance",
    "exhaustion_balance",
    "a0_sd",
)

# Redundancy set: primitives + candidates + A1 axes + A0 controls.
REDUNDANCY_VARS = (
    "down_exh",
    "sup_hold",
    "up_exh",
    "res_hold",
    "holding_balance",
    "exhaustion_balance",
    "a0_sd",
    "dir_velocity",
    "extension",
    "dir_structure",
    "direction",
    "deteriorating",
)

RANKED = PRIMITIVES + CANDIDATES


def figi_set_sha(universe: pd.DataFrame) -> str:
    return a0.figi_set_sha(universe)


def _numeric(frame: pd.DataFrame, name: str) -> np.ndarray:
    return pd.to_numeric(frame[name], errors="coerce").to_numpy(float)


def build_sd_frame(raw: pd.DataFrame, classifier) -> pd.DataFrame:
    """Per-bar frame mirroring the A1 builder (same eligibility, same fwd)."""
    frame = raw.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    if frame["date"].isna().any():
        raise ValueError("invalid date")
    if frame["date"].duplicated().any():
        raise ValueError("duplicate dates")
    frame = frame.sort_values("date").reset_index(drop=True)

    classified = classifier.compute_price_only(frame)
    if len(classified) != len(frame):
        raise AssertionError("classifier row drift")

    ohlc = frame[["open", "high", "low", "close"]].apply(
        pd.to_numeric, errors="coerce"
    )
    arr = ohlc.to_numpy(float)
    valid_ohlc = np.isfinite(arr).all(axis=1) & (arr > 0).all(axis=1)

    close = pd.to_numeric(frame["close"], errors="coerce").to_numpy(float)
    volume = pd.to_numeric(frame["volume"], errors="coerce").to_numpy(float)
    close_coord = np.where(valid_ohlc, np.log(close), np.nan)
    scale = _numeric(classified, "sym_atr")

    valid_count_before = np.concatenate(
        [[0], np.cumsum(valid_ohlc.astype(int))[:-1]]
    )
    dollar_volume = close * volume
    finite_dv = np.isfinite(dollar_volume) & (dollar_volume >= 0)
    dv = pd.Series(np.where(finite_dv, dollar_volume, np.nan), dtype=float)
    liq_count = (
        dv.rolling(
            base.LIQUIDITY_WINDOW,
            min_periods=base.LIQUIDITY_WINDOW,
        )
        .count()
        .to_numpy()
    )
    liq_median = (
        dv.rolling(
            base.LIQUIDITY_WINDOW,
            min_periods=base.LIQUIDITY_WINDOW,
        )
        .median()
        .to_numpy()
    )

    eligible = (
        valid_ohlc
        & frame["date"].between(base.EVENT_START, base.EVENT_END).to_numpy()
        & (valid_count_before >= base.MIN_PRIOR_VALID)
        & np.isfinite(close)
        & (close >= base.MIN_PRICE)
        & (liq_count >= base.LIQUIDITY_WINDOW)
        & np.isfinite(liq_median)
        & (liq_median >= base.MIN_MEDIAN_DOLLAR_VOLUME)
        & np.isfinite(scale)
        & (scale > 0)
    )

    down_exh = _numeric(classified, "downside_exhaustion")
    sup_hold = _numeric(classified, "support_holding")
    up_exh = _numeric(classified, "upside_exhaustion")
    res_hold = _numeric(classified, "resistance_holding")

    holding_balance = sup_hold - res_hold
    exhaustion_balance = down_exh - up_exh

    # Frozen A1 axes reused by import (never redefined here).
    speed_rank = _numeric(classified, "speed_rank")
    dir_velocity = 2.0 * speed_rank - 100.0
    extension = np.abs(dir_velocity)
    legs = a1.compute_ma_legs(classified)
    dir_structure = (
        legs["ma_bull"].to_numpy(float) - legs["ma_bear"].to_numpy(float)
    )

    controls = a0.compute_factor_scores(classified)
    a0_sd = controls["sd"].to_numpy(float)
    direction = controls["direction"].to_numpy(float)
    deteriorating = controls["deteriorating"].to_numpy(float)

    out = pd.DataFrame(
        {
            "date": frame["date"],
            "eligible": eligible,
            "close_coord": close_coord,
            "scale": scale,
            "down_exh": down_exh,
            "sup_hold": sup_hold,
            "up_exh": up_exh,
            "res_hold": res_hold,
            "holding_balance": holding_balance,
            "exhaustion_balance": exhaustion_balance,
            "a0_sd": a0_sd,
            "dir_velocity": dir_velocity,
            "extension": extension,
            "dir_structure": dir_structure,
            "direction": direction,
            "deteriorating": deteriorating,
        }
    )
    matrix = out[list(REDUNDANCY_VARS)].to_numpy(float)
    out["ready"] = eligible & np.isfinite(matrix).all(axis=1)

    for h in HORIZONS:
        future = pd.Series(close_coord).shift(-h).to_numpy(float)
        out[f"fwd_{h}"] = (future - close_coord) / scale

    year = frame["date"].dt.year.to_numpy(int)
    block = np.full(len(frame), "", dtype=object)
    for name, lo, hi in BLOCKS:
        block[(year >= lo) & (year <= hi)] = name
    out["block"] = block
    return out


def add_within_stock_ranks(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    ready = out["ready"].to_numpy(bool)
    for score in RANKED + (
        "dir_velocity",
        "extension",
        "dir_structure",
    ):
        rank = np.full(len(out), np.nan, dtype=float)
        values = out.loc[ready, score]
        if len(values):
            rank[ready] = values.rank(
                method="average", pct=True
            ).to_numpy(float)
        out[f"rank_{score}"] = rank
    return out


_tail_stats = a1._tail_stats
append_cell = a1.append_cell
_block_masks = a1._block_masks
aggregate_a1_cells = a1.aggregate_a1_cells
paired_deltas = a1.paired_deltas


def distribution_rows(figi: str, frame: pd.DataFrame, meta: dict) -> list[dict]:
    """Per-stock distribution diagnostics for primitives and candidates."""
    rows = []
    ready = frame["ready"].to_numpy(bool)
    for score in PRIMITIVES + CANDIDATES:
        vals = frame.loc[ready, score].to_numpy(float)
        vals = vals[np.isfinite(vals)]
        if len(vals) == 0:
            continue
        uniq, counts = np.unique(vals, return_counts=True)
        rows.append(
            {
                "figi": figi,
                "score": score,
                "bars": int(len(vals)),
                "distinct": int(len(uniq)),
                "modal_share": float(counts.max() / len(vals)),
                "nan_share_ready": 0.0,
                **meta,
            }
        )
    return rows


def distribution_summary(per_stock: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if per_stock.empty:
        return pd.DataFrame()
    for score, group in per_stock.groupby("score", sort=True):
        for col in ("modal_share", "distinct"):
            vals = pd.to_numeric(group[col], errors="coerce").to_numpy(float)
            vals = vals[np.isfinite(vals)]
            rows.append(
                {
                    "score": score,
                    "metric": col,
                    "stocks": int(len(vals)),
                    "mean": float(vals.mean()) if len(vals) else math.nan,
                    "median": float(np.median(vals))
                    if len(vals)
                    else math.nan,
                }
            )
    return pd.DataFrame(rows)


def quintile_cells(figi: str, frame: pd.DataFrame, meta: dict) -> list[dict]:
    rows = []
    blocks = _block_masks(frame)
    for score in RANKED:
        rank = frame[f"rank_{score}"].to_numpy(float)
        for q in range(1, 6):
            lo = (q - 1) / 5.0
            hi = q / 5.0
            if q == 1:
                qmask = rank <= hi
            else:
                qmask = (rank > lo) & (rank <= hi)
            for h in HORIZONS:
                fwd = frame[f"fwd_{h}"].to_numpy(float)
                for block, bmask in blocks.items():
                    append_cell(
                        rows,
                        figi=figi,
                        block=block,
                        horizon=h,
                        test=f"quintile_{score}",
                        state=f"Q{q}",
                        mask=bmask & qmask,
                        forward=fwd,
                        meta=meta,
                    )
    return rows


def _side_masks(frame: pd.DataFrame, hard: bool):
    """Structure side x extension bins. Hard 80/20, relaxed 70/30."""
    rs = frame["rank_dir_structure"].to_numpy(float)
    re_ = frame["rank_extension"].to_numpy(float)
    if hard:
        return {
            "bull": rs >= 0.80,
            "bear": rs <= 0.20,
            "low_ext": re_ <= 0.20,
            "high_ext": re_ >= 0.80,
        }
    return {
        "bull": rs >= 0.70,
        "bear": rs <= 0.30,
        "low_ext": re_ <= 0.30,
        "high_ext": re_ >= 0.70,
    }


def conditional_cells(figi: str, frame: pd.DataFrame, meta: dict) -> list[dict]:
    """Candidate demand-vs-supply inside structure x extension cells.

    High Demand = top quintile of the candidate; high Supply = bottom
    quintile. Bull cells aligned +1 (demand-good), bear cells aligned -1
    (supply-good). Hard 80/20 reported first, then predeclared 70/30.
    """
    rows = []
    blocks = _block_masks(frame)
    for suffix, hard in (("", True), ("_rel", False)):
        sides = _side_masks(frame, hard)
        for candidate in CANDIDATES:
            rc = frame[f"rank_{candidate}"].to_numpy(float)
            demand = rc >= (0.80 if hard else 0.70)
            supply = rc <= (0.20 if hard else 0.30)
            masks = {
                (f"bull_low{suffix}_{candidate}", "demand"): (
                    sides["bull"] & sides["low_ext"] & demand,
                    1.0,
                ),
                (f"bull_low{suffix}_{candidate}", "supply"): (
                    sides["bull"] & sides["low_ext"] & supply,
                    1.0,
                ),
                (f"bull_high{suffix}_{candidate}", "demand"): (
                    sides["bull"] & sides["high_ext"] & demand,
                    1.0,
                ),
                (f"bull_high{suffix}_{candidate}", "supply"): (
                    sides["bull"] & sides["high_ext"] & supply,
                    1.0,
                ),
                (f"bear_low{suffix}_{candidate}", "supply"): (
                    sides["bear"] & sides["low_ext"] & supply,
                    -1.0,
                ),
                (f"bear_low{suffix}_{candidate}", "demand"): (
                    sides["bear"] & sides["low_ext"] & demand,
                    -1.0,
                ),
                (f"bear_high{suffix}_{candidate}", "supply"): (
                    sides["bear"] & sides["high_ext"] & supply,
                    -1.0,
                ),
                (f"bear_high{suffix}_{candidate}", "demand"): (
                    sides["bear"] & sides["high_ext"] & demand,
                    -1.0,
                ),
            }
            for h in HORIZONS:
                fwd = frame[f"fwd_{h}"].to_numpy(float)
                for (test, state), (mask, sign) in masks.items():
                    for block, bmask in blocks.items():
                        append_cell(
                            rows,
                            figi=figi,
                            block=block,
                            horizon=h,
                            test=test,
                            state=state,
                            mask=bmask & mask,
                            forward=fwd,
                            direction=sign,
                            meta=meta,
                        )
    return rows


PAIRED_SPECS = {}
for _cand in CANDIDATES:
    for _suffix in ("", "_rel"):
        PAIRED_SPECS[f"bull_low{_suffix}_{_cand}"] = ("demand", "supply")
        PAIRED_SPECS[f"bull_high{_suffix}_{_cand}"] = ("demand", "supply")
        PAIRED_SPECS[f"bear_low{_suffix}_{_cand}"] = ("supply", "demand")
        PAIRED_SPECS[f"bear_high{_suffix}_{_cand}"] = ("supply", "demand")


def redundancy_rows(figi: str, frame: pd.DataFrame, meta: dict) -> list[dict]:
    ready = frame.loc[frame["ready"], list(REDUNDANCY_VARS)]
    rows = []
    for a, b in combinations(REDUNDANCY_VARS, 2):
        pair = ready[[a, b]].dropna()
        if len(pair) < MIN_CELL_BARS:
            continue
        rho = pair[a].corr(pair[b], method="spearman")
        rows.append(
            {
                "figi": figi,
                "factor_a": a,
                "factor_b": b,
                "bars": int(len(pair)),
                "spearman": float(rho),
                **meta,
            }
        )
    return rows


def correlation_summary(per_stock: pd.DataFrame) -> pd.DataFrame:
    return a0.correlation_summary(per_stock)


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
    cohort_sha = figi_set_sha(universe)
    if cohort_sha != EXPECTED_FIGI_SET_SHA:
        raise AssertionError(f"OOS3 FIGI-set drift: {cohort_sha}")

    classifier, blob = load_classifier(args.classifier)
    if blob != FROZEN_CLASSIFIER_BLOB:
        raise AssertionError("frozen classifier blob drift")

    coverage = []
    dist_rows = []
    quintile_rows = []
    conditional_rows = []
    corr_rows = []

    for i, meta_row in enumerate(universe.itertuples(index=False), start=1):
        figi = str(meta_row.figi)
        raw_path = args.raw_dir / f"{figi}.csv.gz"
        if not raw_path.exists():
            raise FileNotFoundError(raw_path)
        raw = pd.read_csv(raw_path)
        frame = add_within_stock_ranks(build_sd_frame(raw, classifier))
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
        dist_rows.extend(distribution_rows(figi, frame, meta))
        quintile_rows.extend(quintile_cells(figi, frame, meta))
        conditional_rows.extend(conditional_cells(figi, frame, meta))
        corr_rows.extend(redundancy_rows(figi, frame, meta))
        print(
            f"[supply-demand-a2] "
            f"{i}/{len(universe)} {meta_row.ticker} "
            f"eligible={int(frame['eligible'].sum())} "
            f"ready={int(frame['ready'].sum())}",
            flush=True,
        )

    dist_stock = pd.DataFrame(dist_rows)
    dist_summary = distribution_summary(dist_stock)
    quintile_stock = pd.DataFrame(quintile_rows)
    quintile_summary = aggregate_a1_cells(
        quintile_stock, ["test", "state", "block", "horizon"]
    )
    conditional_stock = pd.DataFrame(conditional_rows)
    conditional_summary = aggregate_a1_cells(
        conditional_stock, ["test", "state", "block", "horizon"]
    )
    paired_stock, paired_summary = paired_deltas(
        conditional_stock, PAIRED_SPECS
    )
    corr_stock = pd.DataFrame(corr_rows)
    corr_summary = correlation_summary(corr_stock)

    summary = {
        "integrity": {
            "issue": 78,
            "study": "Supply-Demand Rebuild A2",
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
        "a2_formulas": {
            "holding_balance": "support_holding-resistance_holding",
            "exhaustion_balance": "downside_exhaustion-upside_exhaustion",
            "a0_sd": "A0 control, unchanged",
            "axes": "A1 dir_velocity/extension/dir_structure reused",
        },
        "notes": [
            "OOS3 is deliberately reused for discovery "
            "under the 2026-10-05 amendment.",
            "No result from this run is fresh OOS evidence.",
            "No tuned weights, regression, or ML anywhere.",
            "Within-stock quintiles are retrospective "
            "discovery bins, not live thresholds.",
            "Hard 80/20 cells reported first; 70/30 relaxed "
            "robustness predeclared.",
        ],
    }

    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "coverage.csv", pd.DataFrame(coverage))
    write_csv(args.out / "distribution_per_stock.csv", dist_stock)
    write_csv(args.out / "distribution_summary.csv", dist_summary)
    write_csv(args.out / "quintile_per_stock.csv", quintile_stock)
    write_csv(args.out / "quintile_summary.csv", quintile_summary)
    write_csv(args.out / "conditional_per_stock.csv", conditional_stock)
    write_csv(args.out / "conditional_summary.csv", conditional_summary)
    write_csv(args.out / "paired_delta_per_stock.csv", paired_stock)
    write_csv(args.out / "paired_delta_summary.csv", paired_summary)
    write_csv(args.out / "redundancy_per_stock.csv", corr_stock)
    write_csv(args.out / "redundancy_summary.csv", corr_summary)
    (args.out / "summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
