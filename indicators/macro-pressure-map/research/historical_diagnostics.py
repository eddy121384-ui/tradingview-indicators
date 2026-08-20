#!/usr/bin/env python3
"""First descriptive historical diagnostics for frozen Macro Pressure Map V6.6.

This script consumes the TradingView Pine Logs export produced by
`macro-pressure-map-v6.6-parity-sources.pine`, recomputes the frozen V6.6 axes
from the same TradingView source rows, and summarizes forward market behavior.

This is descriptive validation only. It does not tune V6.6, define a strategy,
or claim causal/predictive value.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from compare_tradingview_parity import TV_SOURCES
from compare_tradingview_parity_logs import parse_log_text
from v6_6_core import compute_v66

WARMUP_ROWS = 355
HORIZONS = (5, 10, 20, 60)
PRICE_COLUMNS = (
    "spy", "gold", "oil", "dxy", "hyg", "ief",
)
CHANGE_COLUMNS = (
    "breakeven_10y", "real_yield", "hy_oas", "vix", "move",
)


def _load_log_text(path: Path) -> str:
    """Accept either raw copied Pine Logs text or TradingView's CSV log export."""
    raw = path.read_text(encoding="utf-8-sig")
    if "MPM_PARITY|" in raw and not path.suffix.lower() == ".csv":
        return raw

    if path.suffix.lower() == ".csv":
        frame = pd.read_csv(path)
        for column in frame.columns:
            values = frame[column].astype(str)
            if values.str.contains("MPM_PARITY|", regex=False).any():
                return "\n".join(values.tolist())
    return raw


def _era(ts: pd.Timestamp) -> str:
    if ts.year <= 2012:
        return "2008-2012"
    if ts.year <= 2019:
        return "2013-2019"
    return "2020-2026"


def _add_forward_outcomes(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for horizon in HORIZONS:
        for column in PRICE_COLUMNS:
            out[f"{column}_ret_{horizon}"] = out[column].shift(-horizon) / out[column] - 1.0
        for column in CHANGE_COLUMNS:
            out[f"{column}_chg_{horizon}"] = out[column].shift(-horizon) - out[column]
        for axis in ("GPI", "IPI", "FCPI"):
            out[f"{axis}_chg_{horizon}"] = out[axis] - out[axis].shift(horizon)
    return out


def _transition_bins(series: pd.Series) -> pd.Series:
    q20, q40, q60, q80 = series.quantile([0.2, 0.4, 0.6, 0.8]).to_numpy(float)

    def classify(value: float) -> str | float:
        if pd.isna(value):
            return np.nan
        if value <= q20:
            return "Sharp Fall"
        if value <= q40:
            return "Fall"
        if value <= q60:
            return "Flat"
        if value <= q80:
            return "Rise"
        return "Sharp Rise"

    return series.map(classify)


def _mean_table(frame: pd.DataFrame, group: str, metrics: list[str]) -> dict:
    grouped = frame.groupby(group, dropna=False)
    result: dict[str, dict] = {}
    for label, part in grouped:
        if pd.isna(label):
            continue
        result[str(label)] = {"days": int(len(part))}
        for metric in metrics:
            result[str(label)][metric] = float(part[metric].mean()) if part[metric].notna().any() else None
    return result


def build_report(log_path: Path) -> dict:
    log_text = _load_log_text(log_path)
    source_frame = parse_log_text(log_text)
    source_columns = list(TV_SOURCES.values())
    mirror = compute_v66(source_frame[source_columns])

    research = source_frame[source_columns].join(
        mirror[["GPI", "IPI", "FCPI", "gpi_state", "ipi_state", "fcpi_state", "core_regime"]]
    )
    research = research.iloc[WARMUP_ROWS:].copy()
    research = _add_forward_outcomes(research)
    research["era"] = [_era(ts) for ts in research.index]

    for axis in ("GPI", "IPI", "FCPI"):
        research[f"{axis}_chg20_bin"] = _transition_bins(research[f"{axis}_chg_20"])

    baseline = {
        f"spy_ret_{horizon}": float(research[f"spy_ret_{horizon}"].mean())
        for horizon in (5, 20, 60)
    }

    state_metrics = {
        "GPI": ["spy_ret_5", "spy_ret_20", "spy_ret_60", "oil_ret_20", "ief_ret_20", "hy_oas_chg_20", "vix_chg_20"],
        "IPI": ["spy_ret_20", "oil_ret_20", "gold_ret_20", "ief_ret_20", "breakeven_10y_chg_20", "real_yield_chg_20"],
        "FCPI": ["spy_ret_5", "spy_ret_20", "spy_ret_60", "hyg_ret_20", "ief_ret_20", "hy_oas_chg_20", "vix_chg_20"],
    }
    states = {
        axis: _mean_table(research, state_col, state_metrics[axis])
        for axis, state_col in (("GPI", "gpi_state"), ("IPI", "ipi_state"), ("FCPI", "fcpi_state"))
    }

    transition_metrics = [
        "spy_ret_5", "spy_ret_20", "spy_ret_60", "oil_ret_20", "gold_ret_20",
        "ief_ret_20", "hy_oas_chg_20", "vix_chg_20", "breakeven_10y_chg_20", "real_yield_chg_20",
    ]
    transitions = {
        axis: _mean_table(research, f"{axis}_chg20_bin", transition_metrics)
        for axis in ("GPI", "IPI", "FCPI")
    }

    regime_metrics = [
        "spy_ret_20", "gold_ret_20", "oil_ret_20", "dxy_ret_20", "ief_ret_20", "hyg_ret_20",
        "vix_chg_20", "hy_oas_chg_20", "real_yield_chg_20", "breakeven_10y_chg_20",
    ]
    regimes = _mean_table(research, "core_regime", regime_metrics)

    regime_entries = research[research["core_regime"].ne(research["core_regime"].shift(1))]
    regime_entry_summary = _mean_table(regime_entries, "core_regime", regime_metrics)

    era_regime_spy20 = (
        research.groupby(["era", "core_regime"])["spy_ret_20"]
        .agg(["count", "mean"])
        .reset_index()
        .to_dict(orient="records")
    )

    transition_era_rows: list[dict] = []
    for era, part in research.groupby("era"):
        for axis, metric in (
            ("GPI", "hy_oas_chg_20"),
            ("GPI", "breakeven_10y_chg_20"),
            ("IPI", "breakeven_10y_chg_20"),
            ("FCPI", "hy_oas_chg_20"),
        ):
            for label in ("Sharp Fall", "Sharp Rise"):
                sample = part[part[f"{axis}_chg20_bin"] == label]
                transition_era_rows.append({
                    "era": era,
                    "axis": axis,
                    "transition": label,
                    "metric": metric,
                    "n": int(len(sample)),
                    "metric_mean": float(sample[metric].mean()),
                    "spy_ret_20_mean": float(sample["spy_ret_20"].mean()),
                })

    return {
        "sample": {
            "source_rows": int(len(source_frame)),
            "warmup_rows_excluded": WARMUP_ROWS,
            "research_rows": int(len(research)),
            "first_research_date": research.index.min().date().isoformat(),
            "last_research_date": research.index.max().date().isoformat(),
        },
        "unconditional_baseline": baseline,
        "axis_states": states,
        "axis_20d_transition_quintiles": transitions,
        "core_regimes_daily": regimes,
        "core_regime_entries": regime_entry_summary,
        "era_regime_spy20": era_regime_spy20,
        "era_transition_robustness": transition_era_rows,
        "method_notes": [
            "All V6.6 parameters remain frozen.",
            "Transition quintiles are descriptive diagnostics, not new production thresholds.",
            "Daily state/regime rows overlap at forward horizons; do not treat naive means as independent observations.",
            "Many source assets are V6.6 components. Same-component outcomes test persistence/internal coherence, not independent predictive value.",
            "A later gate must compare against simple baselines and out-of-component outcomes before any incremental-value claim.",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Macro Pressure Map V6.6 first historical diagnostics")
    parser.add_argument("--input", type=Path, required=True, help="TradingView Pine Logs text or CSV export")
    parser.add_argument("--output", type=Path, required=True, help="JSON report path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["sample"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
