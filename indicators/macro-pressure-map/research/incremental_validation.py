#!/usr/bin/env python3
"""Issue #59 out-of-component incremental-value validation for frozen MPM V6.6."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from compare_tradingview_parity import TV_SOURCES
from v6_6_core import compute_v66

PARITY_MARKER = "MPM_PARITY|"
OOC_MARKER = "MPM_OOC|"
WARMUP_ROWS = 355
HORIZONS = (5, 20, 60)
SIGNAL_LOOKBACK = 20
LOW_Q = 0.20
HIGH_Q = 0.80
BOOTSTRAP_DRAWS = 5000
BOOTSTRAP_SEED = 59066

OOC_COLUMNS = (
    "us10y_tvc", "us02y_tvc", "dgs10_fred", "dgs2_fred",
    "usdjpy", "eurusd", "zn1", "tlt",
)

PRIMARY_OUTCOMES = (
    "us10y_tvc", "us02y_tvc", "usdjpy", "eurusd", "zn1", "tlt",
)

SIGNALS = {
    "GPI": ("axis_gpi_change20", "baseline_copper_gold_mom20"),
    "IPI": ("axis_ipi_change20", "baseline_breakeven10y_change20"),
    "FCPI": ("axis_fcpi_change20", "baseline_hyoas_change20"),
}
SECONDARY_FCPI_BASELINE = "baseline_vix_change20"


def _parse_payload(payload: str) -> dict[str, str]:
    row: dict[str, str] = {}
    for token in payload.split("|"):
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        row[key.strip()] = value.strip()
    return row


def parse_marker_file(path: Path, marker: str) -> pd.DataFrame:
    """Parse Pine Logs from either raw text or TradingView's CSV export."""
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    candidates: list[str] = []
    for raw in text.splitlines():
        pos = raw.find(marker)
        if pos >= 0:
            candidates.append(raw[pos + len(marker):])

    if not candidates:
        try:
            csv = pd.read_csv(path)
        except Exception as exc:  # pragma: no cover - diagnostic branch
            raise ValueError(f"no {marker} lines found in {path}") from exc
        for value in csv.astype(str).to_numpy().ravel():
            pos = value.find(marker)
            if pos >= 0:
                candidates.append(value[pos + len(marker):])

    rows = [_parse_payload(value) for value in candidates]
    rows = [row for row in rows if row]
    if not rows:
        raise ValueError(f"no {marker} rows found in {path}")

    frame = pd.DataFrame(rows)
    if "date" not in frame:
        raise ValueError(f"{marker} rows are missing date")
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    for column in frame.columns:
        if column == "date":
            continue
        frame[column] = pd.to_numeric(
            frame[column].replace({"NaN": np.nan, "na": np.nan, "": np.nan}),
            errors="coerce",
        )
    return frame.sort_values("date").drop_duplicates("date", keep="last").set_index("date")


def forward_return(src: pd.Series, horizon: int) -> pd.Series:
    return 100.0 * (src.shift(-horizon) / src - 1.0)


def forward_bp(src: pd.Series, horizon: int) -> pd.Series:
    return 100.0 * (src.shift(-horizon) - src)


def classify_extremes(signal: pd.Series) -> tuple[pd.Series, pd.Series, float, float]:
    clean = signal.dropna()
    lo = float(clean.quantile(LOW_Q))
    hi = float(clean.quantile(HIGH_Q))
    return signal <= lo, signal >= hi, lo, hi


def entry_events(mask: pd.Series) -> pd.Series:
    prev = mask.shift(1, fill_value=False)
    return mask & ~prev


def bootstrap_spread(
    high_values: np.ndarray,
    low_values: np.ndarray,
    draws: int = BOOTSTRAP_DRAWS,
    seed: int = BOOTSTRAP_SEED,
) -> tuple[float, float]:
    high_values = high_values[np.isfinite(high_values)]
    low_values = low_values[np.isfinite(low_values)]
    if len(high_values) < 5 or len(low_values) < 5:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    sims = np.empty(draws, dtype=float)
    for i in range(draws):
        h = rng.choice(high_values, size=len(high_values), replace=True).mean()
        l = rng.choice(low_values, size=len(low_values), replace=True).mean()
        sims[i] = h - l
    return float(np.quantile(sims, 0.025)), float(np.quantile(sims, 0.975))


def spread_stats(signal: pd.Series, outcome: pd.Series, event_only: bool) -> dict:
    high, low, lo_cut, hi_cut = classify_extremes(signal)
    if event_only:
        high = entry_events(high)
        low = entry_events(low)
    valid_high = high & outcome.notna()
    valid_low = low & outcome.notna()
    hv = outcome[valid_high].to_numpy(float)
    lv = outcome[valid_low].to_numpy(float)
    if len(hv) == 0 or len(lv) == 0:
        return {
            "n_high": int(len(hv)), "n_low": int(len(lv)),
            "mean_high": np.nan, "mean_low": np.nan, "spread": np.nan,
            "ci95_low": np.nan, "ci95_high": np.nan,
            "low_cut": lo_cut, "high_cut": hi_cut,
        }
    spread = float(np.nanmean(hv) - np.nanmean(lv))
    ci_lo, ci_hi = bootstrap_spread(hv, lv)
    return {
        "n_high": int(len(hv)),
        "n_low": int(len(lv)),
        "mean_high": float(np.nanmean(hv)),
        "mean_low": float(np.nanmean(lv)),
        "spread": spread,
        "ci95_low": ci_lo,
        "ci95_high": ci_hi,
        "low_cut": lo_cut,
        "high_cut": hi_cut,
    }


def build_research_frame(parity: pd.DataFrame, ooc: pd.DataFrame) -> pd.DataFrame:
    missing = [name for name in TV_SOURCES.values() if name not in parity]
    if missing:
        raise ValueError(f"parity source log missing columns: {missing}")
    missing_ooc = [name for name in OOC_COLUMNS if name not in ooc]
    if missing_ooc:
        raise ValueError(f"OOC log missing columns: {missing_ooc}")

    source_columns = list(TV_SOURCES.values())
    model = compute_v66(parity[source_columns])
    frame = parity[source_columns].join(
        model[["GPI", "IPI", "FCPI"]], how="left"
    ).join(ooc[list(OOC_COLUMNS)], how="inner")
    if len(frame) <= WARMUP_ROWS:
        raise ValueError("not enough overlapping rows after warmup")
    frame = frame.iloc[WARMUP_ROWS:].copy()

    frame["axis_gpi_change20"] = frame["GPI"].diff(SIGNAL_LOOKBACK)
    frame["axis_ipi_change20"] = frame["IPI"].diff(SIGNAL_LOOKBACK)
    frame["axis_fcpi_change20"] = frame["FCPI"].diff(SIGNAL_LOOKBACK)

    copper_gold = frame["copper"] / frame["gold"]
    frame["baseline_copper_gold_mom20"] = 100.0 * (
        copper_gold / copper_gold.shift(SIGNAL_LOOKBACK) - 1.0
    )
    frame["baseline_breakeven10y_change20"] = frame["breakeven_10y"].diff(SIGNAL_LOOKBACK)
    frame["baseline_hyoas_change20"] = frame["hy_oas"].diff(SIGNAL_LOOKBACK)
    frame["baseline_vix_change20"] = frame["vix"].diff(SIGNAL_LOOKBACK)

    for horizon in HORIZONS:
        for col in ("us10y_tvc", "us02y_tvc", "dgs10_fred", "dgs2_fred"):
            frame[f"fwd_{horizon}_{col}_bp"] = forward_bp(frame[col], horizon)
        for col in ("usdjpy", "eurusd", "zn1", "tlt"):
            frame[f"fwd_{horizon}_{col}_pct"] = forward_return(frame[col], horizon)
    return frame


def outcome_column(name: str, horizon: int) -> str:
    suffix = "bp" if name in {"us10y_tvc", "us02y_tvc", "dgs10_fred", "dgs2_fred"} else "pct"
    return f"fwd_{horizon}_{name}_{suffix}"


def era_masks(index: pd.DatetimeIndex) -> dict[str, pd.Series]:
    years = pd.Series(index.year, index=index)
    return {
        "2008-2012": years.between(2008, 2012),
        "2013-2019": years.between(2013, 2019),
        "2020-2026": years.between(2020, 2026),
    }


def evaluate(frame: pd.DataFrame) -> dict:
    report: dict = {
        "sample": {
            "rows": int(len(frame)),
            "first_date": frame.index.min().date().isoformat(),
            "last_date": frame.index.max().date().isoformat(),
        },
        "axes": {},
    }
    eras = era_masks(frame.index)

    for axis, (axis_signal, baseline_signal) in SIGNALS.items():
        axis_out: dict = {
            "axis_signal": axis_signal,
            "baseline_signal": baseline_signal,
            "outcomes": {},
        }
        baseline_names = [baseline_signal]
        if axis == "FCPI":
            baseline_names.append(SECONDARY_FCPI_BASELINE)

        for outcome in PRIMARY_OUTCOMES:
            outcome_out: dict = {}
            for horizon in HORIZONS:
                col = outcome_column(outcome, horizon)
                cell = {
                    "all_rows": {"axis": spread_stats(frame[axis_signal], frame[col], False)},
                    "entry_events": {"axis": spread_stats(frame[axis_signal], frame[col], True)},
                    "eras_20d": {},
                }
                for baseline in baseline_names:
                    cell["all_rows"][baseline] = spread_stats(frame[baseline], frame[col], False)
                    cell["entry_events"][baseline] = spread_stats(frame[baseline], frame[col], True)

                if horizon == 20:
                    for era_name, era_mask in eras.items():
                        era_frame = frame.loc[era_mask]
                        era_cell = {
                            "axis": spread_stats(era_frame[axis_signal], era_frame[col], True)
                        }
                        for baseline in baseline_names:
                            era_cell[baseline] = spread_stats(era_frame[baseline], era_frame[col], True)
                        cell["eras_20d"][era_name] = era_cell
                outcome_out[str(horizon)] = cell
            axis_out["outcomes"][outcome] = outcome_out
        report["axes"][axis] = axis_out
    return report


def _fmt(x: float, digits: int = 2) -> str:
    return "n/a" if not np.isfinite(x) else f"{x:.{digits}f}"


def render_markdown(report: dict) -> str:
    lines = [
        "# Issue #59 — Out-of-component incremental-value validation",
        "",
        "Status: **OOC STUDY COMPLETE FOR PROVIDED LOGS**",
        "",
        f"Sample: {report['sample']['rows']:,} rows, {report['sample']['first_date']} to {report['sample']['last_date']}.",
        "",
        "Signal definition: trailing 20-trading-day axis change. Baselines are frozen simple proxies; 20/80% cuts are descriptive research buckets, not production thresholds.",
        "",
        "Primary evidence is the **entry-event** spread (first bar entering an extreme bucket) to reduce overlapping-state duplication. Bootstrap CIs are descriptive and do not correct every form of time-series dependence.",
        "",
    ]
    for axis, axis_data in report["axes"].items():
        lines += [f"## {axis}", ""]
        baseline = axis_data["baseline_signal"]
        lines.append(f"Primary baseline: `{baseline}`.")
        if axis == "FCPI":
            lines.append(f"Secondary baseline: `{SECONDARY_FCPI_BASELINE}`.")
        lines += ["", "| 20d outcome | Axis spread | Baseline spread | Axis 95% CI | n high / low |",
                  "|---|---:|---:|---:|---:|"]
        for outcome, outcome_data in axis_data["outcomes"].items():
            cell = outcome_data["20"]["entry_events"]
            a = cell["axis"]
            b = cell[baseline]
            unit = "bp" if outcome in {"us10y_tvc", "us02y_tvc"} else "%"
            lines.append(
                f"| {outcome} | {_fmt(a['spread'])} {unit} | {_fmt(b['spread'])} {unit} | "
                f"[{_fmt(a['ci95_low'])}, {_fmt(a['ci95_high'])}] | {a['n_high']} / {a['n_low']} |"
            )
        lines += ["", "### Era stability (20d entry events)", ""]
        for outcome in ("us10y_tvc", "usdjpy", "eurusd", "tlt"):
            lines.append(f"**{outcome}**")
            for era, cell in axis_data["outcomes"][outcome]["20"]["eras_20d"].items():
                a = cell["axis"]["spread"]
                b = cell[baseline]["spread"]
                lines.append(f"- {era}: axis {_fmt(a)}, baseline {_fmt(b)}")
            lines.append("")
    lines += [
        "## Interpretation boundary",
        "",
        "- These outcomes are not default-path V6.6 inputs, reducing circular self-validation.",
        "- DGS10/DGS2 FRED series are sensitivity checks for TVC yield feeds, not independent extra votes.",
        "- No V6.6 parameter is tuned by this study.",
        "- A composite only earns incremental-value credit where it repeatedly separates outcomes more than its simple baseline and remains directionally coherent across eras.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parity-log", type=Path, required=True)
    parser.add_argument("--ooc-log", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    parity = parse_marker_file(args.parity_log, PARITY_MARKER)
    ooc = parse_marker_file(args.ooc_log, OOC_MARKER)
    frame = build_research_frame(parity, ooc)
    report = evaluate(frame)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(json.dumps(report["sample"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
