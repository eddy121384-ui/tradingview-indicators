#!/usr/bin/env python3
"""Build the Issue #76 universal cross-asset regime summary.

Input is the per-market table emitted by
analyze_issue76_regime_conditioned_exposure_map.py.

The primary aggregation intentionally does NOT branch on asset class. Each market
is one vote after event-time ATR normalization and same-market baseline
subtraction. Asset-class labels are retained only as diagnostics so heterogeneity
can be detected; they must not be used to create asset-specific exposure rules.

This is descriptive decision-support research, not a strategy backtest.
"""
from __future__ import annotations

import argparse
import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path

KEYS = ("variant", "stage", "stage_name", "layer", "age_bucket", "horizon")
METRICS = ("mean", "median", "positive_rate", "q10", "q90", "mfe", "mae", "future_rv")


def f(row: dict[str, str], key: str) -> float:
    value = float(row[key])
    if not math.isfinite(value):
        raise ValueError(f"non-finite {key}: {row[key]!r}")
    return value


def load(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise ValueError("empty per-market input")
    required = set(KEYS) | {"ticker", "asset_class", "n"}
    for metric in METRICS:
        required |= {metric, f"lift_{metric}"}
    missing = sorted(required - set(rows[0]))
    if missing:
        raise ValueError(f"missing columns: {missing}")
    return rows


def build(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = tuple(row[k] for k in KEYS)
        grouped[key].append(row)

    out: list[dict[str, object]] = []
    for key, group in sorted(grouped.items()):
        rec: dict[str, object] = dict(zip(KEYS, key))
        rec["markets"] = len(group)
        rec["n_total"] = sum(int(r["n"]) for r in group)
        # Diagnostic only: never use these counts to select a different policy.
        rec["fx_markets"] = sum(r["asset_class"] == "FX" for r in group)
        rec["rates_markets"] = sum(r["asset_class"] == "RATES" for r in group)

        for metric in METRICS:
            vals = [f(r, metric) for r in group]
            lifts = [f(r, f"lift_{metric}") for r in group]
            rec[f"equal_market_{metric}"] = statistics.fmean(vals)
            rec[f"equal_market_lift_{metric}"] = statistics.fmean(lifts)

        market_medians = [f(r, "median") for r in group]
        lift_medians = [f(r, "lift_median") for r in group]
        lift_means = [f(r, "lift_mean") for r in group]

        rec["cross_market_median_of_market_medians"] = statistics.median(market_medians)
        rec["cross_market_median_lift_median"] = statistics.median(lift_medians)
        rec["markets_conditional_median_positive"] = sum(x > 0 for x in market_medians)
        rec["markets_conditional_median_negative"] = sum(x < 0 for x in market_medians)
        rec["markets_lift_median_positive"] = sum(x > 0 for x in lift_medians)
        rec["markets_lift_median_negative"] = sum(x < 0 for x in lift_medians)
        rec["markets_lift_mean_positive"] = sum(x > 0 for x in lift_means)
        rec["markets_lift_mean_negative"] = sum(x < 0 for x in lift_means)

        loo = []
        if len(lift_medians) > 1:
            for i in range(len(lift_medians)):
                loo.append(statistics.fmean(lift_medians[:i] + lift_medians[i + 1 :]))
        rec["loo_equal_market_lift_median_positive"] = sum(x > 0 for x in loo)
        rec["loo_equal_market_lift_median_negative"] = sum(x < 0 for x in loo)
        out.append(rec)
    return out


def write(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("per_market_csv", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    rows = load(args.per_market_csv)
    result = build(rows)
    write(args.output, result)
    print(f"universal_rows={len(result)}")
    print("Issue #76 universal cross-asset summary PASS")


if __name__ == "__main__":
    main()
