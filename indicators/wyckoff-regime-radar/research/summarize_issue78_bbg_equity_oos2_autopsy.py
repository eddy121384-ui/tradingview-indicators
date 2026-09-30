#!/usr/bin/env python3
"""Descriptive autopsy for the frozen Bloomberg 300-stock OOS2 result.

This script does not change the classifier, eligibility, policy, or primary
interpretation gates. It only summarizes already-generated OOS2 artifacts to
explain where the Diagnostic Weak / Failed result came from.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

R0 = "R0_NoDerisk"
WF = "R0_WarningFirst"


def finite_mean(series: pd.Series) -> float:
    vals = pd.to_numeric(series, errors="coerce")
    vals = vals[np.isfinite(vals)]
    return float(vals.mean()) if len(vals) else math.nan


def finite_median(series: pd.Series) -> float:
    vals = pd.to_numeric(series, errors="coerce")
    vals = vals[np.isfinite(vals)]
    return float(vals.median()) if len(vals) else math.nan


def sign_label(x: float) -> str:
    if not math.isfinite(float(x)):
        return "NA"
    if x > 0:
        return "positive"
    if x < 0:
        return "negative"
    return "flat"


def path_table(episodes: pd.DataFrame) -> pd.DataFrame:
    work = episodes[episodes["policy"] == R0].copy()
    total = int(work["episode_id"].count())
    stock_path = (
        work.groupby(["figi", "path"], as_index=False)
        .agg(
            episodes=("episode_id", "count"),
            mean_harvest=("harvest", "mean"),
            mean_bars=("bars", "mean"),
            mean_mfe=("mfe", "mean"),
        )
    )
    rows = []
    for path, group in stock_path.groupby("path"):
        episode_count = int(group["episodes"].sum())
        rows.append(
            {
                "path": path,
                "stocks": int(group["figi"].nunique()),
                "episodes": episode_count,
                "episode_share": episode_count / total if total else math.nan,
                "equal_stock_mean_harvest": finite_mean(group["mean_harvest"]),
                "median_stock_mean_harvest": finite_median(group["mean_harvest"]),
                "positive_stock_fraction": float(
                    (group["mean_harvest"] > 0).mean()
                ),
                "equal_stock_mean_episode_bars": finite_mean(group["mean_bars"]),
                "equal_stock_mean_mfe": finite_mean(group["mean_mfe"]),
            }
        )
    return pd.DataFrame(rows).sort_values("path").reset_index(drop=True)


def path_direction_table(episodes: pd.DataFrame) -> pd.DataFrame:
    work = episodes[episodes["policy"] == R0].copy()
    stock = (
        work.groupby(["figi", "direction", "path"], as_index=False)
        .agg(
            episodes=("episode_id", "count"),
            mean_harvest=("harvest", "mean"),
        )
    )
    rows = []
    for (direction, path), group in stock.groupby(["direction", "path"]):
        rows.append(
            {
                "direction": direction,
                "path": path,
                "stocks": int(group["figi"].nunique()),
                "episodes": int(group["episodes"].sum()),
                "equal_stock_mean_harvest": finite_mean(
                    group["mean_harvest"]
                ),
                "positive_stock_fraction": float(
                    (group["mean_harvest"] > 0).mean()
                ),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["direction", "path"]
    ).reset_index(drop=True)


def summarize_tables(root: Path) -> tuple[dict, dict[str, pd.DataFrame]]:
    summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    episode = pd.read_csv(root / "episode_policy.csv")
    direction = pd.read_csv(root / "direction_summary.csv")
    temporal = pd.read_csv(root / "temporal_summary.csv")
    sector = pd.read_csv(root / "sector_summary.csv")
    sleeve = pd.read_csv(root / "sleeve_summary.csv")
    mfe = pd.read_csv(root / "mfe_slice_summary.csv")
    wf = pd.read_csv(root / "warning_first_summary.csv")

    r0_dir = direction[direction["policy"] == R0].copy()
    r0_time = temporal[temporal["policy"] == R0].copy()
    r0_sector = sector[sector["policy"] == R0].copy()
    r0_sleeve = sleeve[sleeve["policy"] == R0].copy()
    r0_mfe = mfe[mfe["policy"] == R0].copy()

    paths = path_table(episode)
    path_direction = path_direction_table(episode)

    diagnostic = {
        "frozen_label": summary["r0_classification"]["label"],
        "primary_r0_equal_stock_mean_expectancy": next(
            x["equal_stock_mean_expectancy"]
            for x in summary["primary"]
            if x["policy"] == R0
        ),
        "directions": [
            {
                "direction": str(r.direction),
                "stocks": int(r.stocks),
                "equal_stock_mean_expectancy": float(
                    r.equal_stock_mean_expectancy
                ),
                "sign": sign_label(float(r.equal_stock_mean_expectancy)),
            }
            for r in r0_dir.itertuples(index=False)
        ],
        "temporal_blocks": [
            {
                "block": str(r.block),
                "stocks": int(r.stocks),
                "equal_stock_mean_expectancy": float(
                    r.equal_stock_mean_expectancy
                ),
                "positive_stock_fraction": float(
                    r.positive_stock_fraction
                ),
                "sign": sign_label(float(r.equal_stock_mean_expectancy)),
            }
            for r in r0_time.itertuples(index=False)
        ],
        "sectors": [
            {
                "sector": str(r.sector),
                "stocks": int(r.stocks),
                "equal_stock_mean_expectancy": float(
                    r.equal_stock_mean_expectancy
                ),
                "positive_stock_fraction": float(
                    r.positive_stock_fraction
                ),
                "sign": sign_label(float(r.equal_stock_mean_expectancy)),
            }
            for r in r0_sector.itertuples(index=False)
        ],
        "sleeves": [
            {
                "sleeve": str(r.sleeve),
                "stocks": int(r.stocks),
                "equal_stock_mean_expectancy": float(
                    r.equal_stock_mean_expectancy
                ),
                "positive_stock_fraction": float(
                    r.positive_stock_fraction
                ),
                "sign": sign_label(float(r.equal_stock_mean_expectancy)),
            }
            for r in r0_sleeve.itertuples(index=False)
        ],
        "mfe_slices": [
            {
                "slice": str(r.mfe_slice),
                "stocks": int(r.stocks),
                "equal_stock_mean_harvest": float(
                    r.equal_stock_mean_harvest
                ),
                "sign": sign_label(float(r.equal_stock_mean_harvest)),
            }
            for r in r0_mfe.itertuples(index=False)
        ],
        "warning_first": (
            wf.iloc[0].to_dict() if len(wf) else {}
        ),
    }

    tables = {
        "direction": direction,
        "temporal": temporal,
        "sector": sector,
        "sleeve": sleeve,
        "mfe": mfe,
        "path": paths,
        "path_direction": path_direction,
    }
    return diagnostic, tables


def format_markdown(diagnostic: dict, tables: dict[str, pd.DataFrame]) -> str:
    lines = [
        "# Issue #78 Bloomberg 300-Stock OOS2 — Descriptive Autopsy",
        "",
        "This report is explanatory only. It does not alter any frozen rule.",
        "",
        f"Frozen classification: **{diagnostic['frozen_label']}**",
        "",
        "## Direction",
        "",
        tables["direction"].to_markdown(index=False),
        "",
        "## Temporal blocks",
        "",
        tables["temporal"].to_markdown(index=False),
        "",
        "## Sector",
        "",
        tables["sector"].to_markdown(index=False),
        "",
        "## Size sleeve",
        "",
        tables["sleeve"].to_markdown(index=False),
        "",
        "## MFE slices",
        "",
        tables["mfe"].to_markdown(index=False),
        "",
        "## R0 path decomposition",
        "",
        tables["path"].to_markdown(index=False),
        "",
        "## R0 path x direction",
        "",
        tables["path_direction"].to_markdown(index=False),
        "",
        "## WarningFirst defensive summary",
        "",
        pd.DataFrame([diagnostic["warning_first"]]).to_markdown(index=False),
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--input",
        type=Path,
        default=Path("artifacts/issue78_bbg_equity_oos2"),
    )
    ap.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/issue78_bbg_equity_oos2/autopsy"),
    )
    args = ap.parse_args()

    diagnostic, tables = summarize_tables(args.input)
    args.output.mkdir(parents=True, exist_ok=True)

    (args.output / "autopsy_summary.json").write_text(
        json.dumps(diagnostic, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    for name, frame in tables.items():
        frame.to_csv(args.output / f"{name}.csv", index=False)

    # tabulate is a pandas optional dependency; fail clearly if absent.
    try:
        markdown = format_markdown(diagnostic, tables)
    except ImportError as exc:
        raise SystemExit(
            "Install tabulate to emit markdown: "
            "uv pip install --python .venv119\\Scripts\\python.exe tabulate"
        ) from exc

    (args.output / "autopsy.md").write_text(
        markdown + "\n", encoding="utf-8"
    )

    print(json.dumps(diagnostic, indent=2, default=str))


if __name__ == "__main__":
    main()
