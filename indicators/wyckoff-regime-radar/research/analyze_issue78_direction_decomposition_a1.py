#!/usr/bin/env python3
"""Issue #78 A1: decompose A0 Direction into velocity vs MA structure.

Discovery analyzer, not fresh OOS validation. Reuses the frozen
classifier's primitive diagnostics only; no six-stage raw/effective/
probability/candidate/formal-state outputs are factor inputs.

Decomposition (all causal at bar t, from frozen primitives):
  dir_velocity  = 2 * speed_rank - 100            (signed, short-term velocity)
  ma_bull       = frozen bullish MA-structure score (0..100, A0 formula)
  ma_bear       = frozen bearish MA-structure score (0..100, A0 formula)
  dir_structure = ma_bull - ma_bear               (signed, slow structure)
  extension     = |dir_velocity|                  (unsigned extension magnitude)

A0 controls (comparison only, definitions unchanged):
  direction, sd, deteriorating  (via the A0 factor module)

No new composite A1 score is proposed here; decomposition evidence first.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

import analyze_issue78_bbg_equity_oos2 as base
import analyze_issue78_factorized_classifier_discovery as a0
from audit_issue119_bbg_oos2_snapshot import audit_snapshot
from smoke_issue119_frozen_classifier import FROZEN_CLASSIFIER_BLOB, load_classifier

EXPECTED_FIGI_SET_SHA = a0.EXPECTED_FIGI_SET_SHA
HORIZONS = a0.HORIZONS
MIN_CELL_BARS = a0.MIN_CELL_BARS
MIN_AGG_STOCKS = a0.MIN_AGG_STOCKS

# Fixed calendar blocks (Issue #78 convention). Frozen before inspection.
BLOCKS = (
    ("2000-2004", 2000, 2004),
    ("2005-2009", 2005, 2009),
    ("2010-2014", 2010, 2014),
    ("2015-2019", 2015, 2019),
    ("2020-2026", 2020, 2026),
)
BLOCK_LABELS = ("ALL",) + tuple(name for name, _, _ in BLOCKS)

A1_SCORES = (
    "dir_velocity",
    "dir_structure",
    "ma_bull",
    "ma_bear",
    "extension",
)

# Redundancy set: A1 components + A0 direction + A0 controls.
REDUNDANCY_VARS = (
    "dir_velocity",
    "dir_structure",
    "ma_bull",
    "ma_bear",
    "direction",
    "sd",
    "deteriorating",
)


def figi_set_sha(universe: pd.DataFrame) -> str:
    return a0.figi_set_sha(universe)


def _numeric(frame: pd.DataFrame, name: str) -> np.ndarray:
    return pd.to_numeric(frame[name], errors="coerce").to_numpy(float)


def _shift(values: np.ndarray) -> np.ndarray:
    return a0._shift(values)


def compute_ma_legs(classified: pd.DataFrame) -> pd.DataFrame:
    """Frozen MA-structure legs (same formulas as the A0 factor module).

    Duplicated (not imported) because the A0 module only exposes the signed
    difference; test_a1_recombines_to_a0_direction guards exact equality.
    """
    ma_log = _numeric(classified, "issue66_b1_ma_log")
    maturity_ma_log = _numeric(classified, "issue66_b1_maturity_ma_log")
    ma_spread_atr = _numeric(classified, "issue66_b1_ma_spread_atr")

    prev_ma = _shift(ma_log)
    prev_maturity = _shift(maturity_ma_log)
    prev_spread = _shift(ma_spread_atr)

    ma_bull = (
        np.where(ma_log > maturity_ma_log, 100.0, 0.0) * 0.35
        + np.where(ma_log > prev_ma, 100.0, 0.0) * 0.25
        + np.where(maturity_ma_log >= prev_maturity, 100.0, 0.0) * 0.15
        + np.where(ma_spread_atr > prev_spread, 100.0, 0.0) * 0.25
    )
    ma_bear = (
        np.where(ma_log < maturity_ma_log, 100.0, 0.0) * 0.35
        + np.where(ma_log < prev_ma, 100.0, 0.0) * 0.25
        + np.where(maturity_ma_log <= prev_maturity, 100.0, 0.0) * 0.15
        + np.where(ma_spread_atr < prev_spread, 100.0, 0.0) * 0.25
    )
    invalid_structure = (
        ~np.isfinite(ma_log)
        | ~np.isfinite(maturity_ma_log)
        | ~np.isfinite(ma_spread_atr)
        | ~np.isfinite(prev_ma)
        | ~np.isfinite(prev_maturity)
        | ~np.isfinite(prev_spread)
    )
    ma_bull[invalid_structure] = np.nan
    ma_bear[invalid_structure] = np.nan
    return pd.DataFrame({"ma_bull": ma_bull, "ma_bear": ma_bear})


def build_decomposition_frame(raw: pd.DataFrame, classifier) -> pd.DataFrame:
    """Per-bar frame mirroring the A0 builder (same eligibility, same fwd)."""
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

    speed_rank = _numeric(classified, "speed_rank")
    dir_velocity = 2.0 * speed_rank - 100.0
    legs = compute_ma_legs(classified)
    ma_bull = legs["ma_bull"].to_numpy(float)
    ma_bear = legs["ma_bear"].to_numpy(float)
    dir_structure = ma_bull - ma_bear
    extension = np.abs(dir_velocity)

    controls = a0.compute_factor_scores(classified)
    direction = controls["direction"].to_numpy(float)
    sd = controls["sd"].to_numpy(float)
    deteriorating = controls["deteriorating"].to_numpy(float)

    out = pd.DataFrame(
        {
            "date": frame["date"],
            "eligible": eligible,
            "close_coord": close_coord,
            "scale": scale,
            "dir_velocity": dir_velocity,
            "ma_bull": ma_bull,
            "ma_bear": ma_bear,
            "dir_structure": dir_structure,
            "extension": extension,
            "direction": direction,
            "sd": sd,
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
    for score in A1_SCORES + ("direction", "sd", "deteriorating"):
        rank = np.full(len(out), np.nan, dtype=float)
        values = out.loc[ready, score]
        if len(values):
            rank[ready] = values.rank(
                method="average", pct=True
            ).to_numpy(float)
        out[f"rank_{score}"] = rank
    return out


def _tail_stats(vals: np.ndarray) -> dict:
    vals = np.asarray(vals, dtype=float)
    vals = vals[np.isfinite(vals)]
    if len(vals) == 0:
        return {
            "bars": 0,
            "mean": math.nan,
            "median": math.nan,
            "positive_fraction": math.nan,
            "mean_abs": math.nan,
            "p5": math.nan,
            "p10": math.nan,
            "es5": math.nan,
            "neg_share": math.nan,
            "pos_share": math.nan,
        }
    p5 = float(np.percentile(vals, 5))
    p10 = float(np.percentile(vals, 10))
    left = vals[vals <= p5]
    denom = float(np.sum(np.abs(vals)))
    neg = float(np.sum(vals[vals < 0.0]))
    pos = float(np.sum(vals[vals > 0.0]))
    return {
        "bars": int(len(vals)),
        "mean": float(np.mean(vals)),
        "median": float(np.median(vals)),
        "positive_fraction": float(np.mean(vals > 0.0)),
        "mean_abs": float(np.mean(np.abs(vals))),
        "p5": p5,
        "p10": p10,
        "es5": float(np.mean(left)) if len(left) else math.nan,
        "neg_share": float(-neg / denom) if denom else math.nan,
        "pos_share": float(pos / denom) if denom else math.nan,
    }


def append_cell(
    rows,
    *,
    figi,
    block,
    horizon,
    test,
    state,
    mask,
    forward,
    direction=1.0,
    meta=None,
):
    vals = (
        np.asarray(forward, dtype=float)[np.asarray(mask, dtype=bool)]
        * float(direction)
    )
    stats = _tail_stats(vals)
    if stats["bars"] < MIN_CELL_BARS:
        return
    row = {
        "figi": figi,
        "block": block,
        "horizon": horizon,
        "test": test,
        "state": state,
        **stats,
    }
    if meta:
        row.update(meta)
    rows.append(row)


def _block_masks(frame: pd.DataFrame) -> dict:
    ready = frame["ready"].to_numpy(bool)
    dates_block = frame["block"].to_numpy()
    masks = {"ALL": ready}
    for name, _, _ in BLOCKS:
        masks[name] = ready & (dates_block == name)
    return masks


def quintile_cells(
    figi: str, frame: pd.DataFrame, meta: dict
) -> list[dict]:
    rows = []
    blocks = _block_masks(frame)
    for score in A1_SCORES + ("direction",):
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


def conditional_cells(
    figi: str, frame: pd.DataFrame, meta: dict
) -> list[dict]:
    """Velocity extremes, structure extremes, and structure x extension."""
    rows = []
    blocks = _block_masks(frame)
    rv = frame["rank_dir_velocity"].to_numpy(float)
    rs = frame["rank_dir_structure"].to_numpy(float)
    re_ = frame["rank_extension"].to_numpy(float)

    vel_up = rv >= 0.80
    vel_dn = rv <= 0.20
    bull = rs >= 0.80
    bear = rs <= 0.20
    bull50 = rs >= 0.50
    bear50 = rs < 0.50
    low_ext = re_ <= 0.20
    high_ext = re_ >= 0.80
    low_ext50 = re_ < 0.50
    high_ext50 = re_ >= 0.50

    masks = {
        ("velocity", "up_extreme"): (vel_up, 1.0),
        ("velocity", "down_extreme"): (vel_dn, -1.0),
        ("structure", "up_extreme"): (bull, 1.0),
        ("structure", "down_extreme"): (bear, -1.0),
        ("velocity_in_bull", "vel_high"): (bull & (rv >= 0.80), 1.0),
        ("velocity_in_bull", "vel_low"): (bull & (rv <= 0.20), 1.0),
        ("velocity_in_bear", "vel_high"): (bear & (rv >= 0.80), -1.0),
        ("velocity_in_bear", "vel_low"): (bear & (rv <= 0.20), -1.0),
        # Prespecified hard structure x extension cells.
        ("struct_ext_bull", "low_extension"): (bull & low_ext, 1.0),
        ("struct_ext_bull", "high_extension"): (bull & high_ext, 1.0),
        ("struct_ext_bear", "low_extension"): (bear & low_ext, -1.0),
        ("struct_ext_bear", "high_extension"): (bear & high_ext, -1.0),
        # Relaxed median-split versions.
        ("struct_ext_bull_rel", "low_extension"): (
            bull50 & low_ext50,
            1.0,
        ),
        ("struct_ext_bull_rel", "high_extension"): (
            bull50 & high_ext50,
            1.0,
        ),
        ("struct_ext_bear_rel", "low_extension"): (
            bear50 & low_ext50,
            -1.0,
        ),
        ("struct_ext_bear_rel", "high_extension"): (
            bear50 & high_ext50,
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


def continuous_interaction_rows(
    figi: str, frame: pd.DataFrame, meta: dict
) -> list[dict]:
    """Per-stock Spearman(extension, aligned fwd) within structure sides."""
    rows = []
    ready = frame["ready"].to_numpy(bool)
    rs = frame["rank_dir_structure"].to_numpy(float)
    re_ = frame["rank_extension"].to_numpy(float)
    for side, sidemask in (
        ("bull", ready & (rs >= 0.80)),
        ("bear", ready & (rs <= 0.20)),
    ):
        ext = re_[sidemask]
        for h in HORIZONS:
            fwd = frame[f"fwd_{h}"].to_numpy(float)[sidemask]
            sign = 1.0 if side == "bull" else -1.0
            aligned = fwd * sign
            pair = pd.DataFrame({"ext": ext, "fwd": aligned}).dropna()
            if len(pair) < MIN_CELL_BARS:
                continue
            rho = pair["ext"].corr(pair["fwd"], method="spearman")
            rows.append(
                {
                    "figi": figi,
                    "horizon": h,
                    "side": side,
                    "bars": int(len(pair)),
                    "spearman_ext_vs_aligned_fwd": float(rho),
                    **meta,
                }
            )
    return rows


def redundancy_rows(
    figi: str, frame: pd.DataFrame, meta: dict
) -> list[dict]:
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


def aggregate_a1_cells(frame: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    rows = []
    if frame.empty:
        return pd.DataFrame()
    for keys, group in frame.groupby(group_cols, dropna=False, sort=True):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_cols, keys))
        means = pd.to_numeric(group["mean"], errors="coerce")
        medians = pd.to_numeric(group["median"], errors="coerce")
        hits = pd.to_numeric(group["positive_fraction"], errors="coerce")
        abs_moves = pd.to_numeric(group["mean_abs"], errors="coerce")
        valid = np.isfinite(means.to_numpy(float))
        stock_count = int(valid.sum())
        row.update(
            {
                "stocks": stock_count,
                "bars": int(
                    pd.to_numeric(group["bars"], errors="coerce")
                    .fillna(0)
                    .sum()
                ),
                "adequate": int(stock_count >= MIN_AGG_STOCKS),
                "equal_stock_mean": (
                    float(means[valid].mean()) if stock_count else math.nan
                ),
                "median_stock_median": (
                    float(medians[np.isfinite(medians)].median())
                    if np.isfinite(medians).any()
                    else math.nan
                ),
                "equal_stock_positive_fraction": (
                    float(hits[np.isfinite(hits)].mean())
                    if np.isfinite(hits).any()
                    else math.nan
                ),
                "equal_stock_mean_abs": (
                    float(abs_moves[np.isfinite(abs_moves)].mean())
                    if np.isfinite(abs_moves).any()
                    else math.nan
                ),
            }
        )
        for col in ("p5", "p10", "es5", "neg_share", "pos_share"):
            vals = pd.to_numeric(
                group[col], errors="coerce"
            ).to_numpy(float)
            vals = vals[np.isfinite(vals)]
            row[f"median_stock_{col}"] = (
                float(np.median(vals)) if len(vals) else math.nan
            )
        rows.append(row)
    return pd.DataFrame(rows)


def paired_deltas(
    stock_cells: pd.DataFrame,
    specs: dict,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for test, (good, bad) in specs.items():
        subset = stock_cells[stock_cells["test"] == test]
        for (figi, block, horizon), group in subset.groupby(
            ["figi", "block", "horizon"]
        ):
            by_state = group.set_index("state")
            if good not in by_state.index or bad not in by_state.index:
                continue
            first = group.iloc[0]
            rows.append(
                {
                    "figi": figi,
                    "block": block,
                    "horizon": int(horizon),
                    "test": test,
                    "good_state": good,
                    "bad_state": bad,
                    "good_mean": float(by_state.loc[good, "mean"]),
                    "bad_mean": float(by_state.loc[bad, "mean"]),
                    "delta": float(by_state.loc[good, "mean"])
                    - float(by_state.loc[bad, "mean"]),
                    "sector": first.get("sector", ""),
                    "sleeve": first.get("sleeve", ""),
                }
            )
    per_stock = pd.DataFrame(rows)
    summary_rows = []
    if not per_stock.empty:
        for (test, block, horizon), group in per_stock.groupby(
            ["test", "block", "horizon"], sort=True
        ):
            delta = pd.to_numeric(group["delta"], errors="coerce")
            delta = delta[np.isfinite(delta)]
            summary_rows.append(
                {
                    "test": test,
                    "block": block,
                    "horizon": int(horizon),
                    "stocks": int(len(delta)),
                    "adequate": int(len(delta) >= MIN_AGG_STOCKS),
                    "equal_stock_mean_delta": (
                        float(delta.mean()) if len(delta) else math.nan
                    ),
                    "median_stock_delta": (
                        float(delta.median()) if len(delta) else math.nan
                    ),
                    "positive_stock_fraction": (
                        float((delta > 0).mean()) if len(delta) else math.nan
                    ),
                }
            )
    return per_stock, pd.DataFrame(summary_rows)


PAIRED_SPECS = {
    "struct_ext_bull": ("low_extension", "high_extension"),
    "struct_ext_bear": ("low_extension", "high_extension"),
    "struct_ext_bull_rel": ("low_extension", "high_extension"),
    "struct_ext_bear_rel": ("low_extension", "high_extension"),
    "velocity_in_bull": ("vel_low", "vel_high"),
    "velocity_in_bear": ("vel_low", "vel_high"),
}


def correlation_summary(per_stock: pd.DataFrame) -> pd.DataFrame:
    return a0.correlation_summary(per_stock)


def continuous_summary(per_stock: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if per_stock.empty:
        return pd.DataFrame()
    for (side, horizon), group in per_stock.groupby(
        ["side", "horizon"], sort=True
    ):
        vals = pd.to_numeric(
            group["spearman_ext_vs_aligned_fwd"], errors="coerce"
        )
        vals = vals[np.isfinite(vals)]
        rows.append(
            {
                "side": side,
                "horizon": int(horizon),
                "stocks": int(len(vals)),
                "adequate": int(len(vals) >= MIN_AGG_STOCKS),
                "equal_stock_mean_spearman": (
                    float(vals.mean()) if len(vals) else math.nan
                ),
                "median_stock_spearman": (
                    float(vals.median()) if len(vals) else math.nan
                ),
                "negative_stock_fraction": (
                    float((vals < 0).mean()) if len(vals) else math.nan
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
    cohort_sha = figi_set_sha(universe)
    if cohort_sha != EXPECTED_FIGI_SET_SHA:
        raise AssertionError(f"OOS3 FIGI-set drift: {cohort_sha}")

    classifier, blob = load_classifier(args.classifier)
    if blob != FROZEN_CLASSIFIER_BLOB:
        raise AssertionError("frozen classifier blob drift")

    coverage = []
    quintile_rows = []
    conditional_rows = []
    continuous_rows = []
    corr_rows = []

    for i, meta_row in enumerate(universe.itertuples(index=False), start=1):
        figi = str(meta_row.figi)
        raw_path = args.raw_dir / f"{figi}.csv.gz"
        if not raw_path.exists():
            raise FileNotFoundError(raw_path)
        raw = pd.read_csv(raw_path)
        frame = add_within_stock_ranks(build_decomposition_frame(raw, classifier))
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
        quintile_rows.extend(quintile_cells(figi, frame, meta))
        conditional_rows.extend(conditional_cells(figi, frame, meta))
        continuous_rows.extend(
            continuous_interaction_rows(figi, frame, meta)
        )
        corr_rows.extend(redundancy_rows(figi, frame, meta))
        print(
            f"[direction-decomposition-a1] "
            f"{i}/{len(universe)} {meta_row.ticker} "
            f"eligible={int(frame['eligible'].sum())} "
            f"ready={int(frame['ready'].sum())}",
            flush=True,
        )

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
    continuous_stock = pd.DataFrame(continuous_rows)
    continuous_sum = continuous_summary(continuous_stock)
    corr_stock = pd.DataFrame(corr_rows)
    corr_summary = correlation_summary(corr_stock)

    summary = {
        "integrity": {
            "issue": 78,
            "study": "Direction Decomposition A1",
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
        "a1_formulas": {
            "dir_velocity": "2*speed_rank-100",
            "ma_bull": "frozen A0 bullish MA-structure score (0..100)",
            "ma_bear": "frozen A0 bearish MA-structure score (0..100)",
            "dir_structure": "ma_bull-ma_bear",
            "extension": "abs(dir_velocity)",
            "controls": "A0 direction/sd/deteriorating unchanged",
        },
        "notes": [
            "OOS3 is deliberately reused for discovery "
            "under the 2026-10-05 amendment.",
            "No result from this run is fresh OOS evidence.",
            "No new composite A1 score is proposed here.",
            "Within-stock quintiles are retrospective "
            "discovery bins, not live thresholds.",
            "Blocks are fixed calendar bins; ALL is the full sample.",
        ],
    }

    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "coverage.csv", pd.DataFrame(coverage))
    write_csv(args.out / "quintile_per_stock.csv", quintile_stock)
    write_csv(args.out / "quintile_summary.csv", quintile_summary)
    write_csv(args.out / "conditional_per_stock.csv", conditional_stock)
    write_csv(args.out / "conditional_summary.csv", conditional_summary)
    write_csv(
        args.out / "paired_delta_per_stock.csv", paired_stock
    )
    write_csv(args.out / "paired_delta_summary.csv", paired_summary)
    write_csv(
        args.out / "continuous_interaction_per_stock.csv",
        continuous_stock,
    )
    write_csv(
        args.out / "continuous_interaction_summary.csv", continuous_sum
    )
    write_csv(
        args.out / "redundancy_per_stock.csv", corr_stock
    )
    write_csv(args.out / "redundancy_summary.csv", corr_summary)
    (args.out / "summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
