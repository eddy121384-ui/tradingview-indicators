#!/usr/bin/env python3
"""Issue #107 A1: public-feed screening for a continuous policy reaction layer.

This evaluator is intentionally NOT a production Policy Pressure formula.
It uses the frozen V6.6 default market-only calculation and tests whether
levels, one policy starting-point variable, and 20/63 trajectory features
contain stable OOS information about future 6M Fed Funds changes.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
import requests

from public_data import SERIES_SPECS, align_to_anchor, download_spec
from v6_6_core import V66Config, compute_v66

HERE = Path(__file__).resolve().parent
PREREG = HERE / "decisions" / "issue-107-continuous-policy-reaction-preregistered.json"

GPI_IPI_CANONICAL = {
    "spy", "iwm", "rsp", "xly", "xlp", "xli", "xlu", "copper", "gold",
    "breakeven_10y", "oil", "gasoline", "commodity_basket",
}

MODELS = {
    "M0": ["GPI", "IPI"],
    "M1": ["GPI", "IPI", "real_policy_rate"],
    "M2": [
        "GPI", "IPI", "real_policy_rate",
        "fast_slope_GPI", "mid_slope_GPI", "acceleration_GPI",
        "fast_slope_IPI", "mid_slope_IPI", "acceleration_IPI",
    ],
}

PERIODS = (
    ("pre_COVID_modern", "2015-01", "2019-12"),
    ("COVID_inflation_transition", "2020-01", "2022-12"),
    ("higher_rate_disinflation", "2023-01", "2025-06"),
)


def load_prereg() -> dict:
    return json.loads(PREREG.read_text(encoding="utf-8"))


def sha256_frame(frame: pd.DataFrame) -> str:
    payload = frame.reset_index().to_csv(index=False, float_format="%.10g").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def retry_call(func, *args, attempts: int = 3):
    last = None
    for attempt in range(attempts):
        try:
            return func(*args)
        except Exception as exc:
            last = exc
            if attempt + 1 >= attempts:
                raise
            time.sleep(2.0 * (attempt + 1))
    raise RuntimeError("retry_call exhausted") from last


def _download_fred_bounded_once(series_id: str, start: str, end: str) -> pd.Series:
    """Fetch one bounded FRED slice; end is exclusive."""
    end_inclusive = (pd.Timestamp(end) - pd.Timedelta(days=1)).date().isoformat()
    query = urlencode({"id": series_id, "cosd": start, "coed": end_inclusive})
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?{query}"
    response = requests.get(
        url,
        headers={"User-Agent": "tradingview-indicators-research/1.0"},
        timeout=(15, 60),
    )
    response.raise_for_status()
    payload = response.content
    frame = pd.read_csv(io.BytesIO(payload))
    date_col = "observation_date" if "observation_date" in frame.columns else "DATE"
    if date_col not in frame.columns or series_id not in frame.columns:
        raise RuntimeError(f"FRED bounded CSV for {series_id} has unexpected columns: {list(frame.columns)}")
    index = pd.to_datetime(frame[date_col], errors="raise", utc=True).dt.tz_convert(None).dt.normalize()
    raw = frame[series_id].replace(".", np.nan)
    values = pd.Series(pd.to_numeric(raw, errors="coerce").to_numpy(float), index=pd.DatetimeIndex(index), name=series_id)
    return values[~values.index.duplicated(keep="last")].sort_index()


def _fred_chunk_ranges(start: str, end: str, years: int = 6) -> list[tuple[str, str]]:
    """Split a long end-exclusive FRED request into deterministic calendar chunks."""
    current = pd.Timestamp(start).normalize()
    stop = pd.Timestamp(end).normalize()
    if stop <= current:
        raise ValueError(f"invalid FRED date range: {start}..{end}")
    chunks: list[tuple[str, str]] = []
    while current < stop:
        next_stop = min(current + pd.DateOffset(years=years), stop)
        chunks.append((current.date().isoformat(), next_stop.date().isoformat()))
        current = next_stop
    return chunks


def download_fred_bounded(series_id: str, start: str, end: str) -> pd.Series:
    """Fetch the same bounded FRED series in smaller slices for CI reliability."""
    parts = [
        retry_call(_download_fred_bounded_once, series_id, chunk_start, chunk_end)
        for chunk_start, chunk_end in _fred_chunk_ranges(start, end)
    ]
    values = pd.concat(parts)
    values.name = series_id
    return values[~values.index.duplicated(keep="last")].sort_index()


def build_public_gpi_ipi_sources(start: str, end: str) -> tuple[pd.DataFrame, dict]:
    specs = [s for s in SERIES_SPECS if s.canonical in GPI_IPI_CANONICAL]
    found = {s.canonical for s in specs}
    if found != GPI_IPI_CANONICAL:
        raise RuntimeError(f"missing required public source specs: {sorted(GPI_IPI_CANONICAL-found)}")
    downloaded: dict[str, pd.Series] = {}
    coverage: list[dict] = []
    for spec in specs:
        series = (download_fred_bounded(spec.public_symbol, start, end)
                  if spec.provider == "fred"
                  else retry_call(download_spec, spec, start, end))
        if series.dropna().empty:
            raise RuntimeError(f"no usable source for {spec.canonical}")
        downloaded[spec.canonical] = series
        finite = series.dropna()
        coverage.append({
            "canonical": spec.canonical,
            "provider": spec.provider,
            "public_symbol": spec.public_symbol,
            "first": finite.index.min().date().isoformat(),
            "last": finite.index.max().date().isoformat(),
            "observations": int(len(finite)),
        })
    aligned = align_to_anchor(downloaded, anchor="spy")
    return aligned, {
        "coverage": coverage,
        "aligned_rows": int(len(aligned)),
        "aligned_first": aligned.index.min().date().isoformat(),
        "aligned_last": aligned.index.max().date().isoformat(),
        "aligned_sha256": sha256_frame(aligned),
    }


def trajectory_features(gpi_ipi: pd.DataFrame, fast: int = 20, mid: int = 63) -> pd.DataFrame:
    out = gpi_ipi[["GPI", "IPI"]].copy()
    for axis in ("GPI", "IPI"):
        out[f"fast_slope_{axis}"] = (out[axis] - out[axis].shift(fast)) / float(fast)
        out[f"mid_slope_{axis}"] = (out[axis] - out[axis].shift(mid)) / float(mid)
        out[f"acceleration_{axis}"] = out[f"fast_slope_{axis}"] - out[f"mid_slope_{axis}"]
    return out


def last_daily_each_month(frame: pd.DataFrame) -> pd.DataFrame:
    tmp = frame.copy()
    tmp["month"] = tmp.index.to_period("M")
    tmp = tmp.groupby("month", sort=True).tail(1)
    tmp.index = tmp.pop("month")
    tmp.index.name = "month"
    return tmp


def _monthly_series(series: pd.Series) -> pd.Series:
    out = series.copy()
    out.index = out.index.to_period("M")
    return out.groupby(level=0).last().sort_index()


def build_policy_monthly(start: str = "2005-01-01", end: str = "2026-01-01") -> pd.DataFrame:
    effr = _monthly_series(download_fred_bounded("FEDFUNDS", start, end))
    pce = _monthly_series(download_fred_bounded("PCEPILFE", start, end))
    p = pd.DataFrame({"FEDFUNDS": effr, "PCEPILFE": pce}).sort_index()
    p["core_pce_yoy"] = 100.0 * (p["PCEPILFE"] / p["PCEPILFE"].shift(12) - 1.0)
    p["real_policy_rate_raw"] = p["FEDFUNDS"] - p["core_pce_yoy"]
    p["real_policy_rate"] = p["real_policy_rate_raw"].shift(2)
    p["outcome_3m"] = p["FEDFUNDS"].shift(-3) - p["FEDFUNDS"]
    p["outcome_6m"] = p["FEDFUNDS"].shift(-6) - p["FEDFUNDS"]
    p["outcome_12m"] = p["FEDFUNDS"].shift(-12) - p["FEDFUNDS"]
    return p


def build_monthly_research_frame() -> tuple[pd.DataFrame, dict]:
    prereg = load_prereg()
    sources, source_manifest = build_public_gpi_ipi_sources("2007-01-01", "2026-01-01")
    axes = compute_v66(sources, V66Config())[["GPI", "IPI"]]
    traj = trajectory_features(axes, prereg["features"]["fast_len"], prereg["features"]["mid_len"])
    monthly_axes = last_daily_each_month(traj)
    policy = build_policy_monthly()
    monthly = monthly_axes.join(policy, how="left").sort_index()
    source_manifest["monthly_feature_sha256"] = sha256_frame(monthly)
    source_manifest["policy_sha256"] = sha256_frame(policy)
    source_manifest["feed_guardrail"] = (
        "A1 uses public-feed V6.6 screening inputs. It cannot authorize production; "
        "TradingView-feed A2 confirmation is required."
    )
    return monthly, source_manifest


def complete_case_mask(frame: pd.DataFrame) -> pd.Series:
    required = MODELS["M2"] + ["outcome_6m"]
    return frame[required].notna().all(axis=1)


def standardize_fit_predict(train: pd.DataFrame, row: pd.Series, features: list[str], target: str) -> tuple[float, dict]:
    mean = train[features].mean()
    std = train[features].std(ddof=0)
    if (std <= 0.0).any() or std.isna().any():
        bad = list(std.index[(std <= 0.0) | std.isna()])
        raise RuntimeError(f"zero/invalid training variance: {bad}")
    x = (train[features] - mean) / std
    xr = (row[features] - mean) / std
    X = np.column_stack([np.ones(len(x)), x.to_numpy(float)])
    y = train[target].to_numpy(float)
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    pred = float(np.r_[1.0, xr.to_numpy(float)] @ beta)
    names = ["intercept", *features]
    return pred, {name: float(value) for name, value in zip(names, beta)}


def expanding_predictions(monthly: pd.DataFrame, rolling_months: int | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    prereg = load_prereg()
    min_train = int(prereg["estimation"]["minimum_complete_training_rows"])
    common = monthly.loc[complete_case_mask(monthly)].copy()
    rows: list[dict] = []
    coef_rows: list[dict] = []

    first = pd.Period(prereg["estimation"]["first_oos_origin"], freq="M")
    last = pd.Period(prereg["monthly_sampling"]["latest_primary_forecast_origin"], freq="M")

    for origin in common.index[(common.index >= first) & (common.index <= last)]:
        row = common.loc[origin]
        cutoff = origin - 7  # H=6 plus one full month; outcome known strictly before origin.
        train = common.loc[common.index <= cutoff].copy()
        if rolling_months is not None:
            lower = cutoff - (rolling_months - 1)
            train = train.loc[train.index >= lower]
        if len(train) < min_train:
            continue
        rec = {
            "origin": str(origin),
            "actual_6m": float(row["outcome_6m"]),
            "actual_3m": float(row["outcome_3m"]) if pd.notna(row["outcome_3m"]) else np.nan,
            "actual_12m": float(row["outcome_12m"]) if pd.notna(row["outcome_12m"]) else np.nan,
        }
        for model, features in MODELS.items():
            pred, coefs = standardize_fit_predict(train, row, features, "outcome_6m")
            rec[f"pred_{model}"] = pred
            coef_rows.append({
                "origin": str(origin),
                "window": "expanding" if rolling_months is None else f"rolling_{rolling_months}",
                "model": model,
                "training_rows": int(len(train)),
                **coefs,
            })
        rows.append(rec)
    return pd.DataFrame(rows), pd.DataFrame(coef_rows)


def metrics(pred: pd.DataFrame, model: str) -> dict:
    y = pred["actual_6m"].to_numpy(float)
    p = pred[f"pred_{model}"].to_numpy(float)
    err = p - y
    corr = None
    if len(y) >= 2 and np.std(y) > 0 and np.std(p) > 0:
        corr = float(np.corrcoef(y, p)[0, 1])
    mask = np.abs(y) > 0.25
    direction = None
    if mask.any():
        direction = float((np.sign(p[mask]) == np.sign(y[mask])).mean())
    return {
        "n": int(len(y)),
        "RMSE": float(np.sqrt(np.mean(err**2))) if len(y) else None,
        "MAE": float(np.mean(np.abs(err))) if len(y) else None,
        "correlation": corr,
        "direction_accuracy_nontrivial": direction,
        "nontrivial_n": int(mask.sum()),
    }


def summarize(pred: pd.DataFrame, window: str) -> pd.DataFrame:
    rows: list[dict] = []
    for model in MODELS:
        rows.append({"window": window, "segment": "full", "model": model, **metrics(pred, model)})
    periods = [(name, pd.Period(start, "M"), pd.Period(end, "M")) for name, start, end in PERIODS]
    origins = pd.PeriodIndex(pred["origin"], freq="M")
    for name, start, end in periods:
        sub = pred.loc[(origins >= start) & (origins <= end)].copy()
        if sub.empty:
            continue
        for model in MODELS:
            rows.append({"window": window, "segment": name, "model": model, **metrics(sub, model)})
    return pd.DataFrame(rows)


def incremental(summary: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for (window, segment), group in summary.groupby(["window", "segment"], sort=False):
        g = group.set_index("model")
        for newer, older, label in (("M1", "M0", "M1_minus_M0"), ("M2", "M1", "M2_minus_M1")):
            a, b = g.loc[newer], g.loc[older]
            rows.append({
                "window": window,
                "segment": segment,
                "comparison": label,
                "delta_RMSE": float(a["RMSE"] - b["RMSE"]),
                "delta_MAE": float(a["MAE"] - b["MAE"]),
                "delta_correlation": float(a["correlation"] - b["correlation"]) if pd.notna(a["correlation"]) and pd.notna(b["correlation"]) else np.nan,
                "delta_direction_accuracy": float(a["direction_accuracy_nontrivial"] - b["direction_accuracy_nontrivial"])
                    if pd.notna(a["direction_accuracy_nontrivial"]) and pd.notna(b["direction_accuracy_nontrivial"]) else np.nan,
            })
    return pd.DataFrame(rows)


def run(output_dir: Path) -> dict:
    prereg = load_prereg()
    monthly, source_manifest = build_monthly_research_frame()

    expanding, coefs_expanding = expanding_predictions(monthly)
    rolling, coefs_rolling = expanding_predictions(monthly, rolling_months=96)
    if expanding.empty:
        raise RuntimeError("no expanding OOS predictions produced")

    summary = pd.concat([
        summarize(expanding, "expanding"),
        summarize(rolling, "rolling_96") if not rolling.empty else pd.DataFrame(),
    ], ignore_index=True)
    inc = incremental(summary)
    coefs = pd.concat([coefs_expanding, coefs_rolling], ignore_index=True)

    output_dir.mkdir(parents=True, exist_ok=True)
    feature_path = output_dir / "issue-107-a1-monthly-features.csv"
    pred_path = output_dir / "issue-107-a1-predictions.csv"
    rolling_path = output_dir / "issue-107-a1-predictions-rolling96.csv"
    summary_path = output_dir / "issue-107-a1-summary.csv"
    inc_path = output_dir / "issue-107-a1-incremental.csv"
    coef_path = output_dir / "issue-107-a1-coefficients.csv"

    monthly.reset_index().to_csv(feature_path, index=False)
    expanding.to_csv(pred_path, index=False)
    rolling.to_csv(rolling_path, index=False)
    summary.to_csv(summary_path, index=False)
    inc.to_csv(inc_path, index=False)
    coefs.to_csv(coef_path, index=False)

    full = summary.loc[(summary["window"] == "expanding") & (summary["segment"] == "full")].set_index("model")
    primary_inc = inc.loc[(inc["window"] == "expanding") & (inc["segment"] == "full")]

    manifest = {
        "schema_version": 1,
        "issue": 107,
        "phase": "A1-public-feed-screening",
        "preregistration_preceded_outcomes": True,
        "data_gate": "A1_public_feed_screening",
        "can_authorize_production": False,
        "tradingview_A2_required": True,
        "display_formula_created": False,
        "asset_outcomes_loaded": False,
        "portfolio_metrics_computed": False,
        "production_v66_modified": False,
        "oos": {
            "first_origin": str(expanding["origin"].iloc[0]),
            "last_origin": str(expanding["origin"].iloc[-1]),
            "rows": int(len(expanding)),
        },
        "source_manifest": source_manifest,
        "models": {m: {k: (None if pd.isna(v) else float(v) if isinstance(v, (np.floating, float)) else int(v) if isinstance(v, (np.integer, int)) else v)
                       for k, v in full.loc[m].to_dict().items()} for m in MODELS},
        "primary_incremental": primary_inc.to_dict(orient="records"),
        "output_sha256": {},
        "interpretation_guardrail": (
            "A1 is public-feed screening only. Even a positive A1 result cannot authorize a Policy Pressure production line. "
            "A2 TradingView-feed confirmation is required."
        ),
    }
    for path in [feature_path, pred_path, rolling_path, summary_path, inc_path, coef_path]:
        manifest["output_sha256"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()

    manifest_path = output_dir / "issue-107-a1-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.output_dir)
    print(json.dumps({
        "oos": result["oos"],
        "models": result["models"],
        "primary_incremental": result["primary_incremental"],
        "can_authorize_production": result["can_authorize_production"],
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
