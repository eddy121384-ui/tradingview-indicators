#!/usr/bin/env python3
"""Issue #78 factorized-classifier discovery on the already-inspected OOS3 cohort.

This is explicitly a discovery analyzer, not fresh OOS validation. It reuses the
frozen classifier's primitive diagnostics but does not use its six-stage raw,
effective, probability, candidate, or formal-state outputs as factor inputs.
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
from audit_issue119_bbg_oos2_snapshot import audit_snapshot
from smoke_issue119_frozen_classifier import FROZEN_CLASSIFIER_BLOB, load_classifier

EXPECTED_FIGI_SET_SHA = (
    "017e9360402afa002dc0970088649e7c411c4f02333dec550f2432be3c0dd701"
)
HORIZONS = (1, 5, 10, 20)
MIN_CELL_BARS = 5
MIN_AGG_STOCKS = 30

FACTOR_NAMES = (
    "direction",
    "range_factor",
    "sd",
    "emerging",
    "established",
    "deteriorating",
)


def figi_set_sha(universe: pd.DataFrame) -> str:
    figis = sorted(universe["figi"].astype(str).tolist())
    payload = "\n".join(figis) + "\n"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _numeric(frame: pd.DataFrame, name: str) -> np.ndarray:
    return pd.to_numeric(frame[name], errors="coerce").to_numpy(float)


def _shift(values: np.ndarray) -> np.ndarray:
    out = np.full(len(values), np.nan, dtype=float)
    if len(values) > 1:
        out[1:] = values[:-1]
    return out


def compute_factor_scores(classified: pd.DataFrame) -> pd.DataFrame:
    """Compute baseline A0 factors from frozen primitive diagnostics only."""
    speed_rank = _numeric(classified, "speed_rank")
    direction_short = 2.0 * speed_rank - 100.0

    ma_log = _numeric(classified, "issue66_b1_ma_log")
    maturity_ma_log = _numeric(classified, "issue66_b1_maturity_ma_log")
    ma_spread_atr = _numeric(classified, "issue66_b1_ma_spread_atr")

    prev_ma = _shift(ma_log)
    prev_maturity = _shift(maturity_ma_log)
    prev_spread = _shift(ma_spread_atr)

    ma_bull_spread = (
        np.where(ma_log > maturity_ma_log, 100.0, 0.0) * 0.35
        + np.where(ma_log > prev_ma, 100.0, 0.0) * 0.25
        + np.where(maturity_ma_log >= prev_maturity, 100.0, 0.0) * 0.15
        + np.where(ma_spread_atr > prev_spread, 100.0, 0.0) * 0.25
    )
    ma_bear_spread = (
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
    ma_bull_spread[invalid_structure] = np.nan
    ma_bear_spread[invalid_structure] = np.nan

    direction_structure = ma_bull_spread - ma_bear_spread
    direction = np.clip(
        (direction_short + direction_structure) / 2.0, -100.0, 100.0
    )

    range_factor = _numeric(classified, "range_score")
    expansion_factor = 100.0 - range_factor

    downside_exhaustion = _numeric(classified, "downside_exhaustion")
    support_holding = _numeric(classified, "support_holding")
    upside_exhaustion = _numeric(classified, "upside_exhaustion")
    resistance_holding = _numeric(classified, "resistance_holding")

    demand = (downside_exhaustion + support_holding) / 2.0
    supply = (upside_exhaustion + resistance_holding) / 2.0
    sd = np.clip(demand - supply, -100.0, 100.0)

    breakout_score = _numeric(classified, "breakout_score")
    breakdown_score = _numeric(classified, "explicit_breakdown_score")
    range_cont_up = _numeric(classified, "range_cont_up")
    range_cont_dn = _numeric(classified, "range_cont_dn")

    active_up = direction >= 0.0
    emerging = np.where(active_up, breakout_score, breakdown_score)
    established = np.where(
        active_up,
        (range_cont_up + ma_bull_spread) / 2.0,
        (range_cont_dn + ma_bear_spread) / 2.0,
    )
    deteriorating = np.where(active_up, supply, demand)

    return pd.DataFrame(
        {
            "direction_short": direction_short,
            "direction_structure": direction_structure,
            "direction": direction,
            "range_factor": range_factor,
            "expansion_factor": expansion_factor,
            "demand": demand,
            "supply": supply,
            "sd": sd,
            "emerging": emerging,
            "established": established,
            "deteriorating": deteriorating,
        }
    )


def build_frame(raw: pd.DataFrame, classifier) -> pd.DataFrame:
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

    factors = compute_factor_scores(classified)
    out = pd.DataFrame(
        {
            "date": frame["date"],
            "eligible": eligible,
            "close_coord": close_coord,
            "scale": scale,
        }
    )
    for column in factors.columns:
        out[column] = factors[column].to_numpy(float)

    matrix = out[list(FACTOR_NAMES)].to_numpy(float)
    out["ready"] = eligible & np.isfinite(matrix).all(axis=1)

    for h in HORIZONS:
        future = pd.Series(close_coord).shift(-h).to_numpy(float)
        out[f"fwd_{h}"] = (future - close_coord) / scale
    return out


def add_within_stock_ranks(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    ready = out["ready"].to_numpy(bool)
    for factor in FACTOR_NAMES:
        rank = np.full(len(out), np.nan, dtype=float)
        values = out.loc[ready, factor]
        if len(values):
            rank[ready] = values.rank(
                method="average", pct=True
            ).to_numpy(float)
        out[f"rank_{factor}"] = rank
    return out


def _stats(values: np.ndarray) -> dict:
    vals = np.asarray(values, dtype=float)
    vals = vals[np.isfinite(vals)]
    if len(vals) == 0:
        return {
            "bars": 0,
            "mean": math.nan,
            "median": math.nan,
            "positive_fraction": math.nan,
            "mean_abs": math.nan,
        }
    return {
        "bars": int(len(vals)),
        "mean": float(np.mean(vals)),
        "median": float(np.median(vals)),
        "positive_fraction": float(np.mean(vals > 0.0)),
        "mean_abs": float(np.mean(np.abs(vals))),
    }


def append_cell(
    rows,
    *,
    figi,
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
    stats = _stats(vals)
    if stats["bars"] < MIN_CELL_BARS:
        return
    row = {
        "figi": figi,
        "horizon": horizon,
        "test": test,
        "state": state,
        **stats,
    }
    if meta:
        row.update(meta)
    rows.append(row)


def conditional_cells(
    figi: str, frame: pd.DataFrame, meta: dict
) -> list[dict]:
    rows = []
    ready = frame["ready"].to_numpy(bool)
    up = frame["rank_direction"].to_numpy(float) >= 0.80
    down = frame["rank_direction"].to_numpy(float) <= 0.20
    high_range = frame["rank_range_factor"].to_numpy(float) >= 0.80
    high_sd = frame["rank_sd"].to_numpy(float) >= 0.80
    low_sd = frame["rank_sd"].to_numpy(float) <= 0.20
    high_emerging = frame["rank_emerging"].to_numpy(float) >= 0.80
    high_established = (
        frame["rank_established"].to_numpy(float) >= 0.80
    )
    low_deteriorating = (
        frame["rank_deteriorating"].to_numpy(float) <= 0.20
    )
    high_deteriorating = (
        frame["rank_deteriorating"].to_numpy(float) >= 0.80
    )

    masks = {
        ("direction", "up_extreme"): (ready & up, 1.0),
        ("direction", "down_extreme"): (ready & down, -1.0),
        (
            "lifecycle_up",
            "established_low_deteriorating",
        ): (
            ready & up & high_established & low_deteriorating,
            1.0,
        ),
        (
            "lifecycle_up",
            "high_deteriorating",
        ): (ready & up & high_deteriorating, 1.0),
        (
            "lifecycle_down",
            "established_low_deteriorating",
        ): (
            ready & down & high_established & low_deteriorating,
            -1.0,
        ),
        (
            "lifecycle_down",
            "high_deteriorating",
        ): (ready & down & high_deteriorating, -1.0),
        (
            "range_sd_up",
            "demand",
        ): (ready & up & high_range & high_sd, 1.0),
        (
            "range_sd_up",
            "supply",
        ): (ready & up & high_range & low_sd, 1.0),
        (
            "range_sd_down",
            "supply",
        ): (ready & down & high_range & low_sd, -1.0),
        (
            "range_sd_down",
            "demand",
        ): (ready & down & high_range & high_sd, -1.0),
        (
            "emerging_up",
            "low_deteriorating",
        ): (
            ready & up & high_emerging & low_deteriorating,
            1.0,
        ),
        (
            "emerging_up",
            "high_deteriorating",
        ): (
            ready & up & high_emerging & high_deteriorating,
            1.0,
        ),
        (
            "emerging_down",
            "low_deteriorating",
        ): (
            ready & down & high_emerging & low_deteriorating,
            -1.0,
        ),
        (
            "emerging_down",
            "high_deteriorating",
        ): (
            ready & down & high_emerging & high_deteriorating,
            -1.0,
        ),
    }

    for h in HORIZONS:
        fwd = frame[f"fwd_{h}"].to_numpy(float)
        for (test, state), (mask, sign) in masks.items():
            append_cell(
                rows,
                figi=figi,
                horizon=h,
                test=test,
                state=state,
                mask=mask,
                forward=fwd,
                direction=sign,
                meta=meta,
            )

        high_exp = ready & (
            frame["rank_range_factor"].to_numpy(float) <= 0.20
        )
        append_cell(
            rows,
            figi=figi,
            horizon=h,
            test="range_abs_move",
            state="high_expansion",
            mask=high_exp,
            forward=np.abs(fwd),
            meta=meta,
        )
        append_cell(
            rows,
            figi=figi,
            horizon=h,
            test="range_abs_move",
            state="high_range",
            mask=ready & high_range,
            forward=np.abs(fwd),
            meta=meta,
        )
    return rows


def factor_quintile_cells(
    figi: str, frame: pd.DataFrame, meta: dict
) -> list[dict]:
    rows = []
    ready = frame["ready"].to_numpy(bool)
    for factor in FACTOR_NAMES:
        rank = frame[f"rank_{factor}"].to_numpy(float)
        for q in range(1, 6):
            lo = (q - 1) / 5.0
            hi = q / 5.0
            if q == 1:
                mask = ready & (rank <= hi)
            else:
                mask = ready & (rank > lo) & (rank <= hi)
            for h in HORIZONS:
                fwd = frame[f"fwd_{h}"].to_numpy(float)
                append_cell(
                    rows,
                    figi=figi,
                    horizon=h,
                    test=f"quintile_{factor}",
                    state=f"Q{q}",
                    mask=mask,
                    forward=fwd,
                    meta=meta,
                )
    return rows


def aggregate_stock_cells(
    frame: pd.DataFrame, group_cols: list[str]
) -> pd.DataFrame:
    rows = []
    if frame.empty:
        return pd.DataFrame()
    for keys, group in frame.groupby(
        group_cols, dropna=False, sort=True
    ):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_cols, keys))
        means = pd.to_numeric(group["mean"], errors="coerce")
        medians = pd.to_numeric(group["median"], errors="coerce")
        hits = pd.to_numeric(
            group["positive_fraction"], errors="coerce"
        )
        abs_moves = pd.to_numeric(group["mean_abs"], errors="coerce")
        valid = np.isfinite(means.to_numpy(float))
        stock_count = int(valid.sum())
        row.update(
            {
                "stocks": stock_count,
                "bars": int(
                    pd.to_numeric(
                        group["bars"], errors="coerce"
                    ).fillna(0).sum()
                ),
                "adequate": int(stock_count >= MIN_AGG_STOCKS),
                "equal_stock_mean": (
                    float(means[valid].mean())
                    if stock_count
                    else math.nan
                ),
                "median_stock_median": (
                    float(
                        medians[
                            np.isfinite(medians)
                        ].median()
                    )
                    if np.isfinite(medians).any()
                    else math.nan
                ),
                "equal_stock_positive_fraction": (
                    float(hits[np.isfinite(hits)].mean())
                    if np.isfinite(hits).any()
                    else math.nan
                ),
                "equal_stock_mean_abs": (
                    float(
                        abs_moves[
                            np.isfinite(abs_moves)
                        ].mean()
                    )
                    if np.isfinite(abs_moves).any()
                    else math.nan
                ),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def paired_deltas(
    stock_cells: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    specs = {
        "lifecycle_up": (
            "established_low_deteriorating",
            "high_deteriorating",
        ),
        "lifecycle_down": (
            "established_low_deteriorating",
            "high_deteriorating",
        ),
        "range_sd_up": ("demand", "supply"),
        "range_sd_down": ("supply", "demand"),
        "emerging_up": (
            "low_deteriorating",
            "high_deteriorating",
        ),
        "emerging_down": (
            "low_deteriorating",
            "high_deteriorating",
        ),
        "range_abs_move": ("high_expansion", "high_range"),
    }
    rows = []
    for test, (good, bad) in specs.items():
        subset = stock_cells[stock_cells["test"] == test]
        for (figi, horizon), group in subset.groupby(
            ["figi", "horizon"]
        ):
            by_state = group.set_index("state")
            if good not in by_state.index or bad not in by_state.index:
                continue
            good_mean = float(by_state.loc[good, "mean"])
            bad_mean = float(by_state.loc[bad, "mean"])
            first = group.iloc[0]
            rows.append(
                {
                    "figi": figi,
                    "horizon": int(horizon),
                    "test": test,
                    "good_state": good,
                    "bad_state": bad,
                    "good_mean": good_mean,
                    "bad_mean": bad_mean,
                    "delta": good_mean - bad_mean,
                    "sector": first.get("sector", ""),
                    "sleeve": first.get("sleeve", ""),
                }
            )
    per_stock = pd.DataFrame(rows)
    summary_rows = []
    if not per_stock.empty:
        for (test, horizon), group in per_stock.groupby(
            ["test", "horizon"], sort=True
        ):
            delta = pd.to_numeric(group["delta"], errors="coerce")
            delta = delta[np.isfinite(delta)]
            summary_rows.append(
                {
                    "test": test,
                    "horizon": int(horizon),
                    "stocks": int(len(delta)),
                    "adequate": int(
                        len(delta) >= MIN_AGG_STOCKS
                    ),
                    "equal_stock_mean_delta": (
                        float(delta.mean())
                        if len(delta)
                        else math.nan
                    ),
                    "median_stock_delta": (
                        float(delta.median())
                        if len(delta)
                        else math.nan
                    ),
                    "positive_stock_fraction": (
                        float((delta > 0).mean())
                        if len(delta)
                        else math.nan
                    ),
                }
            )
    return per_stock, pd.DataFrame(summary_rows)


def factor_correlations(
    figi: str, frame: pd.DataFrame, meta: dict
) -> list[dict]:
    ready = frame.loc[frame["ready"], list(FACTOR_NAMES)]
    rows = []
    for a, b in combinations(FACTOR_NAMES, 2):
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


def correlation_summary(
    per_stock: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    if per_stock.empty:
        return pd.DataFrame()
    for (a, b), group in per_stock.groupby(
        ["factor_a", "factor_b"], sort=True
    ):
        vals = pd.to_numeric(
            group["spearman"], errors="coerce"
        )
        vals = vals[np.isfinite(vals)]
        rows.append(
            {
                "factor_a": a,
                "factor_b": b,
                "stocks": int(len(vals)),
                "equal_stock_mean_spearman": (
                    float(vals.mean())
                    if len(vals)
                    else math.nan
                ),
                "median_stock_spearman": (
                    float(vals.median())
                    if len(vals)
                    else math.nan
                ),
                "mean_abs_spearman": (
                    float(np.abs(vals).mean())
                    if len(vals)
                    else math.nan
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

    audit = audit_snapshot(
        args.universe, args.manifest, args.raw_dir
    )
    if not audit["pass"]:
        raise SystemExit("snapshot audit failed")

    universe = pd.read_csv(args.universe)
    if (
        len(universe) != 300
        or universe["figi"].nunique() != 300
    ):
        raise AssertionError("universe membership drift")
    cohort_sha = figi_set_sha(universe)
    if cohort_sha != EXPECTED_FIGI_SET_SHA:
        raise AssertionError(
            f"OOS3 FIGI-set drift: {cohort_sha}"
        )

    classifier, blob = load_classifier(args.classifier)
    if blob != FROZEN_CLASSIFIER_BLOB:
        raise AssertionError("frozen classifier blob drift")

    coverage = []
    conditional_rows = []
    quintile_rows = []
    corr_rows = []

    for i, meta_row in enumerate(
        universe.itertuples(index=False), start=1
    ):
        figi = str(meta_row.figi)
        raw_path = args.raw_dir / f"{figi}.csv.gz"
        if not raw_path.exists():
            raise FileNotFoundError(raw_path)
        raw = pd.read_csv(raw_path)
        frame = add_within_stock_ranks(
            build_frame(raw, classifier)
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
                "eligible_rows": int(
                    frame["eligible"].sum()
                ),
                "factor_ready_rows": int(
                    frame["ready"].sum()
                ),
            }
        )
        conditional_rows.extend(
            conditional_cells(figi, frame, meta)
        )
        quintile_rows.extend(
            factor_quintile_cells(figi, frame, meta)
        )
        corr_rows.extend(
            factor_correlations(figi, frame, meta)
        )

        print(
            f"[factorized-discovery] "
            f"{i}/{len(universe)} {meta_row.ticker} "
            f"eligible={int(frame['eligible'].sum())} "
            f"ready={int(frame['ready'].sum())}",
            flush=True,
        )

    conditional_stock = pd.DataFrame(conditional_rows)
    conditional_summary = aggregate_stock_cells(
        conditional_stock, ["test", "state", "horizon"]
    )
    paired_stock, paired_summary = paired_deltas(
        conditional_stock
    )

    quintile_stock = pd.DataFrame(quintile_rows)
    quintile_summary = aggregate_stock_cells(
        quintile_stock, ["test", "state", "horizon"]
    )

    corr_stock = pd.DataFrame(corr_rows)
    corr_summary = correlation_summary(corr_stock)

    headline_h10 = (
        paired_summary[
            paired_summary["horizon"] == 10
        ].to_dict("records")
        if not paired_summary.empty
        else []
    )
    direction_h10 = (
        conditional_summary[
            (conditional_summary["test"] == "direction")
            & (conditional_summary["horizon"] == 10)
        ].to_dict("records")
        if not conditional_summary.empty
        else []
    )

    summary = {
        "integrity": {
            "issue": 78,
            "study": "Factorized Classifier Discovery A0",
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
            "min_cell_bars": MIN_CELL_BARS,
            "min_aggregate_stocks": MIN_AGG_STOCKS,
        },
        "a0_formulas": {
            "direction": (
                "mean(2*speed_rank-100, "
                "ma_bull_spread-ma_bear_spread)"
            ),
            "range_factor": "range_score",
            "sd": (
                "mean(downside_exhaustion,support_holding)"
                "-mean(upside_exhaustion,resistance_holding)"
            ),
            "emerging": (
                "breakout_score if direction>=0 "
                "else explicit_breakdown_score"
            ),
            "established": (
                "mean(range_cont_direction, "
                "ma_direction_spread)"
            ),
            "deteriorating": (
                "supply if direction>=0 else demand"
            ),
        },
        "direction_10bar": direction_h10,
        "paired_tests_10bar": headline_h10,
        "notes": [
            (
                "OOS3 is deliberately reused for discovery "
                "under the 2026-10-05 amendment."
            ),
            (
                "No result from this run is fresh "
                "OOS evidence."
            ),
            (
                "Old six-stage raw/effective/probability/"
                "formal labels are not factor inputs."
            ),
            (
                "Within-stock quintiles are retrospective "
                "discovery bins, not live thresholds."
            ),
        ],
    }

    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(
        args.out / "coverage.csv",
        pd.DataFrame(coverage),
    )
    write_csv(
        args.out / "conditional_per_stock.csv",
        conditional_stock,
    )
    write_csv(
        args.out / "conditional_summary.csv",
        conditional_summary,
    )
    write_csv(
        args.out / "paired_delta_per_stock.csv",
        paired_stock,
    )
    write_csv(
        args.out / "paired_delta_summary.csv",
        paired_summary,
    )
    write_csv(
        args.out / "factor_quintile_per_stock.csv",
        quintile_stock,
    )
    write_csv(
        args.out / "factor_quintile_summary.csv",
        quintile_summary,
    )
    write_csv(
        args.out / "factor_correlation_per_stock.csv",
        corr_stock,
    )
    write_csv(
        args.out / "factor_correlation_summary.csv",
        corr_summary,
    )
    (
        args.out / "summary.json"
    ).write_text(
        json.dumps(summary, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
