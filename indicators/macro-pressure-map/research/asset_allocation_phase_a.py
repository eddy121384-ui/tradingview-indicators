#!/usr/bin/env python3
"""Issue #64 Phase A: regime-conditioned cross-asset diagnostics.

This module evaluates the frozen Macro Pressure Map V6.6 Growth × Inflation
3x3 state map as an asset-allocation context. It does not optimize portfolio
weights and does not modify the production indicator.

Point estimates may use every eligible daily observation. Confidence intervals
use horizon-embargoed observations within each regime so overlapping forward
windows are not treated as independent evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from build_public_history import build_history
from public_data import build_public_sources
from v6_6_core import V66Config

ASSETS = ("SPY", "TLT", "GLD")
HORIZONS = {"1M": 21, "3M": 63, "6M": 126}
REGIMES = (
    "Goldilocks / Disinflationary Expansion",
    "Benign Expansion / Stable Inflation",
    "Reflation / Inflation Rising",
    "Disinflationary Drift",
    "Neutral / Range-bound Macro",
    "Inflation Pressure without Growth Confirmation",
    "Slowdown / Disinflation",
    "Growth Slowdown / Stable Inflation",
    "Stagflation Pressure",
)


def _normalize_index(index: pd.Index) -> pd.DatetimeIndex:
    result = pd.to_datetime(index, errors="raise", utc=True)
    return result.tz_convert(None).normalize()


def download_adjusted_close(symbol: str, start: str, end: str | None) -> pd.Series:
    """Download a dividend/split-adjusted investable price proxy from Yahoo."""
    try:
        import yfinance as yf
    except ImportError as exc:  # pragma: no cover - environment contract
        raise RuntimeError("yfinance is required for Issue #64 public-data downloads") from exc

    frame = yf.download(
        symbol,
        start=start,
        end=end,
        interval="1d",
        auto_adjust=True,
        actions=False,
        repair=True,
        keepna=True,
        progress=False,
        threads=False,
        timeout=30,
        multi_level_index=False,
    )
    if frame is None or frame.empty or "Close" not in frame.columns:
        raise RuntimeError(f"Yahoo returned no adjusted Close series for {symbol}")
    values = pd.to_numeric(frame["Close"], errors="coerce")
    values.index = _normalize_index(values.index)
    if values.index.duplicated().any():
        raise RuntimeError(f"duplicate Yahoo dates for outcome asset {symbol}")
    values = values.sort_index().dropna().astype(float)
    if values.empty:
        raise RuntimeError(f"Yahoo returned no finite adjusted Close values for {symbol}")
    values.name = symbol
    return values


def build_outcome_prices(start: str, end: str | None) -> tuple[pd.DataFrame, dict]:
    """Build a strict common-date adjusted-price panel for SPY/TLT/GLD."""
    series = {asset: download_adjusted_close(asset, start, end) for asset in ASSETS}
    frame = pd.concat(series.values(), axis=1, join="inner").dropna(how="any")
    frame.columns = list(ASSETS)
    frame = frame.sort_index()
    if frame.empty:
        raise RuntimeError("SPY/TLT/GLD have no common adjusted-price history")
    if frame.index.duplicated().any():
        raise RuntimeError("outcome price panel contains duplicate dates")
    if not np.isfinite(frame.to_numpy(float)).all():
        raise RuntimeError("outcome price panel contains non-finite values")
    manifest = {
        "provider": "Yahoo Finance via yfinance",
        "price_semantics": "auto_adjust=True adjusted Close; dividend/split-adjusted investable price proxy",
        "calendar_semantics": "strict intersection of finite SPY, TLT and GLD observation dates; no outcome forward-fill",
        "symbols": list(ASSETS),
        "rows": int(len(frame)),
        "first_date": frame.index.min().date().isoformat(),
        "last_date": frame.index.max().date().isoformat(),
        "individual_coverage": {
            asset: {
                "observations": int(len(values)),
                "first_date": values.index.min().date().isoformat(),
                "last_date": values.index.max().date().isoformat(),
            }
            for asset, values in series.items()
        },
    }
    return frame, manifest


def align_signal_and_prices(history: pd.DataFrame, prices: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Use only exact dates shared by the signal history and all outcome assets."""
    common = history.index.intersection(prices.index).sort_values()
    if common.empty:
        raise RuntimeError("signal history and outcome prices have no common dates")
    h = history.loc[common].copy()
    p = prices.loc[common].copy()
    valid = h["core_regime"].isin(REGIMES) & h[["GPI", "IPI", "FCPI"]].notna().all(axis=1)
    h = h.loc[valid]
    p = p.loc[h.index]
    if h.empty:
        raise RuntimeError("no finite V6.6 regimes remain after common-date alignment")
    return h, p


def forward_returns(prices: pd.DataFrame, horizon: int) -> pd.DataFrame:
    if horizon <= 0:
        raise ValueError("horizon must be positive")
    return prices.shift(-horizon) / prices - 1.0


def regime_episode_rows(regimes: pd.Series) -> pd.DataFrame:
    """Return one row per contiguous daily regime episode."""
    if regimes.empty:
        return pd.DataFrame(columns=["regime", "start", "end", "observations"])
    values = regimes.astype(str)
    episode_id = values.ne(values.shift(1)).cumsum()
    rows: list[dict] = []
    for _, group in values.groupby(episode_id):
        rows.append({
            "regime": str(group.iloc[0]),
            "start": group.index[0],
            "end": group.index[-1],
            "observations": int(len(group)),
        })
    return pd.DataFrame(rows)


def summarize_episodes(regimes: pd.Series) -> pd.DataFrame:
    episodes = regime_episode_rows(regimes)
    rows: list[dict] = []
    total = int(len(regimes))
    for regime in REGIMES:
        mask = regimes.eq(regime)
        durations = episodes.loc[episodes["regime"].eq(regime), "observations"].astype(float)
        rows.append({
            "regime": regime,
            "observations": int(mask.sum()),
            "occupancy_pct": float(100.0 * mask.sum() / total) if total else np.nan,
            "episodes": int(len(durations)),
            "duration_mean_days": float(durations.mean()) if len(durations) else np.nan,
            "duration_median_days": float(durations.median()) if len(durations) else np.nan,
            "duration_p25_days": float(durations.quantile(0.25)) if len(durations) else np.nan,
            "duration_p75_days": float(durations.quantile(0.75)) if len(durations) else np.nan,
            "duration_max_days": float(durations.max()) if len(durations) else np.nan,
        })
    return pd.DataFrame(rows)


def embargo_positions(candidate_positions: Iterable[int], horizon: int) -> list[int]:
    """Greedily keep starts whose forward windows do not overlap within a regime."""
    if horizon <= 0:
        raise ValueError("horizon must be positive")
    selected: list[int] = []
    last = -10**12
    for pos in sorted(int(x) for x in candidate_positions):
        if pos >= last + horizon:
            selected.append(pos)
            last = pos
    return selected


def forward_max_drawdown(values: np.ndarray, start: int, horizon: int) -> float:
    """Maximum drawdown over [start, start+horizon], seeded at opening wealth 1."""
    if start < 0 or horizon <= 0 or start + horizon >= len(values):
        return np.nan
    path = values[start : start + horizon + 1] / values[start]
    if not np.isfinite(path).all() or path[0] <= 0:
        return np.nan
    peaks = np.maximum.accumulate(path)
    drawdowns = path / peaks - 1.0
    return float(np.min(drawdowns))


def _stable_seed(*parts: object) -> int:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def bootstrap_mean_ci(values: Iterable[float], *, seed: int, draws: int = 4000) -> tuple[float, float]:
    clean = np.asarray([float(x) for x in values if np.isfinite(float(x))], dtype=float)
    if clean.size < 5:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    means = np.empty(draws, dtype=float)
    for i in range(draws):
        means[i] = float(rng.choice(clean, size=clean.size, replace=True).mean())
    low, high = np.quantile(means, [0.025, 0.975])
    return float(low), float(high)


def summarize_forward_returns(history: pd.DataFrame, prices: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return all-observation point estimates plus embargoed inference summaries."""
    point_rows: list[dict] = []
    inference_rows: list[dict] = []
    regime_values = history["core_regime"]
    price_arrays = {asset: prices[asset].to_numpy(float) for asset in ASSETS}

    for horizon_name, horizon in HORIZONS.items():
        fwd = forward_returns(prices, horizon)
        for regime in REGIMES:
            regime_mask = regime_values.eq(regime).to_numpy()
            for asset in ASSETS:
                values = fwd[asset].to_numpy(float)
                eligible = regime_mask & np.isfinite(values)
                sample = values[eligible]
                point_rows.append({
                    "regime": regime,
                    "horizon": horizon_name,
                    "horizon_rows": horizon,
                    "asset": asset,
                    "observations_all": int(sample.size),
                    "mean_forward_return": float(np.mean(sample)) if sample.size else np.nan,
                    "median_forward_return": float(np.median(sample)) if sample.size else np.nan,
                    "positive_rate": float(np.mean(sample > 0.0)) if sample.size else np.nan,
                    "p25_forward_return": float(np.quantile(sample, 0.25)) if sample.size else np.nan,
                    "p75_forward_return": float(np.quantile(sample, 0.75)) if sample.size else np.nan,
                })

                positions = np.flatnonzero(eligible)
                selected = embargo_positions(positions, horizon)
                selected_values = np.asarray([values[pos] for pos in selected], dtype=float)
                ci_low, ci_high = bootstrap_mean_ci(
                    selected_values,
                    seed=_stable_seed("issue64", regime, horizon_name, asset),
                )
                drawdowns = np.asarray([
                    forward_max_drawdown(price_arrays[asset], pos, horizon) for pos in selected
                ], dtype=float)
                drawdowns = drawdowns[np.isfinite(drawdowns)]
                inference_rows.append({
                    "regime": regime,
                    "horizon": horizon_name,
                    "horizon_rows": horizon,
                    "asset": asset,
                    "embargoed_observations": int(selected_values.size),
                    "embargoed_mean_forward_return": (
                        float(np.mean(selected_values)) if selected_values.size else np.nan
                    ),
                    "mean_return_ci95_low": ci_low,
                    "mean_return_ci95_high": ci_high,
                    "mean_forward_max_drawdown": float(np.mean(drawdowns)) if drawdowns.size else np.nan,
                    "median_forward_max_drawdown": float(np.median(drawdowns)) if drawdowns.size else np.nan,
                })

    points = pd.DataFrame(point_rows)
    if not points.empty:
        points["mean_return_rank"] = points.groupby(["regime", "horizon"])[
            "mean_forward_return"
        ].rank(method="min", ascending=False)
    return points, pd.DataFrame(inference_rows)


def summarize_next_day_risk(history: pd.DataFrame, prices: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Conditional next-day realized vol and correlation by today's regime."""
    next_returns = prices.shift(-1) / prices - 1.0
    risk_rows: list[dict] = []
    corr_rows: list[dict] = []
    for regime in REGIMES:
        mask = history["core_regime"].eq(regime)
        block = next_returns.loc[mask].dropna(how="any")
        for asset in ASSETS:
            sample = block[asset].to_numpy(float)
            risk_rows.append({
                "regime": regime,
                "asset": asset,
                "next_day_observations": int(sample.size),
                "mean_next_day_return": float(np.mean(sample)) if sample.size else np.nan,
                "annualized_next_day_vol": (
                    float(np.std(sample, ddof=1) * math.sqrt(252.0)) if sample.size >= 2 else np.nan
                ),
                "next_day_downside_rate": float(np.mean(sample < 0.0)) if sample.size else np.nan,
            })
        if len(block) >= 2:
            corr = block[list(ASSETS)].corr()
            for a, b in (("SPY", "TLT"), ("SPY", "GLD"), ("TLT", "GLD")):
                corr_rows.append({
                    "regime": regime,
                    "asset_a": a,
                    "asset_b": b,
                    "observations": int(len(block)),
                    "correlation": float(corr.loc[a, b]),
                })
        else:
            for a, b in (("SPY", "TLT"), ("SPY", "GLD"), ("TLT", "GLD")):
                corr_rows.append({
                    "regime": regime,
                    "asset_a": a,
                    "asset_b": b,
                    "observations": int(len(block)),
                    "correlation": np.nan,
                })
    return pd.DataFrame(risk_rows), pd.DataFrame(corr_rows)


def _json_safe(value):
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        numeric = float(value)
        return numeric if math.isfinite(numeric) else None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def write_markdown_report(
    path: Path,
    *,
    history: pd.DataFrame,
    episode_summary: pd.DataFrame,
    points: pd.DataFrame,
    inference: pd.DataFrame,
) -> None:
    lines = [
        "# Issue #64 Phase A — Regime-conditioned SPY / TLT / GLD diagnostics",
        "",
        "This is descriptive development / exploratory evidence. It is not a portfolio backtest and not new untouched OOS evidence.",
        "",
        f"Common finite regime period: **{history.index.min().date()} → {history.index.max().date()}** ({len(history):,} rows).",
        "",
        "## Regime occupancy",
        "",
        "| Regime | Obs | Occupancy | Episodes | Median duration |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in episode_summary.itertuples(index=False):
        occupancy = "n/a" if pd.isna(row.occupancy_pct) else f"{row.occupancy_pct:.1f}%"
        duration = "n/a" if pd.isna(row.duration_median_days) else f"{row.duration_median_days:.1f}d"
        lines.append(f"| {row.regime} | {row.observations} | {occupancy} | {row.episodes} | {duration} |")

    lines.extend(["", "## Relative asset leaders by horizon", ""])
    for horizon_name in HORIZONS:
        lines.append(f"### {horizon_name}")
        lines.append("")
        lines.append("| Regime | Best mean-return asset | Mean | Embargoed CI sample | 95% CI |")
        lines.append("|---|---|---:|---:|---:|")
        horizon_points = points.loc[points["horizon"].eq(horizon_name)]
        for regime in REGIMES:
            block = horizon_points.loc[horizon_points["regime"].eq(regime)].dropna(subset=["mean_forward_return"])
            if block.empty:
                lines.append(f"| {regime} | n/a | n/a | 0 | n/a |")
                continue
            best = block.sort_values("mean_forward_return", ascending=False).iloc[0]
            inf = inference.loc[
                inference["regime"].eq(regime)
                & inference["horizon"].eq(horizon_name)
                & inference["asset"].eq(best["asset"])
            ].iloc[0]
            if pd.notna(inf["mean_return_ci95_low"]):
                ci = f"[{inf['mean_return_ci95_low']:.2%}, {inf['mean_return_ci95_high']:.2%}]"
            else:
                ci = "n/a"
            lines.append(
                f"| {regime} | {best['asset']} | {best['mean_forward_return']:.2%} | "
                f"{int(inf['embargoed_observations'])} | {ci} |"
            )
        lines.append("")

    lines.extend([
        "## Inference boundary",
        "",
        "- Daily forward-return means/ranks use all eligible observations and are descriptive only.",
        "- 95% mean-return intervals use horizon-embargoed observations within each regime, so overlapping forward windows are not counted as independent evidence.",
        "- FCPI is retained for context only in Phase A; it does not create a third categorical axis.",
        "- No allocation mapping or portfolio weights are selected in this report.",
        "- History already inspected in Issue #59 remains reused evidence.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def run_phase_a(start: str, end: str | None, output_dir: Path) -> dict:
    sources, signal_manifest = build_public_sources(start=start, end=end)
    history = build_history(sources, V66Config())
    prices, price_manifest = build_outcome_prices(start, end)
    history, prices = align_signal_and_prices(history, prices)

    episodes = regime_episode_rows(history["core_regime"])
    episode_summary = summarize_episodes(history["core_regime"])
    points, inference = summarize_forward_returns(history, prices)
    risk, correlations = summarize_next_day_risk(history, prices)

    output_dir.mkdir(parents=True, exist_ok=True)
    episode_summary.to_csv(output_dir / "phase-a-regime-occupancy.csv", index=False)
    episodes.to_csv(output_dir / "phase-a-regime-episodes.csv", index=False, date_format="%Y-%m-%d")
    points.to_csv(output_dir / "phase-a-forward-returns.csv", index=False)
    inference.to_csv(output_dir / "phase-a-forward-inference.csv", index=False)
    risk.to_csv(output_dir / "phase-a-next-day-risk.csv", index=False)
    correlations.to_csv(output_dir / "phase-a-correlations.csv", index=False)

    manifest = {
        "schema_version": 1,
        "issue": 64,
        "phase": "A",
        "purpose": "descriptive regime-conditioned SPY/TLT/GLD asset-allocation diagnostics",
        "v66_parameters_modified": False,
        "primary_state": "frozen V6.6 raw GPI × raw IPI 3x3 core_regime",
        "fcpi_role": "diagnostic context only",
        "horizons_trading_rows": HORIZONS,
        "signal_data": signal_manifest,
        "outcome_data": price_manifest,
        "common_finite_regime_rows": int(len(history)),
        "common_first_date": history.index.min().date().isoformat(),
        "common_last_date": history.index.max().date().isoformat(),
        "inference_contract": (
            "All-observation means/ranks are descriptive. Bootstrap 95% intervals use deterministic "
            "horizon-embargoed starts within each regime; overlapping forward windows are not treated as independent."
        ),
        "evidence_status": "development_or_reused_exploratory; not newly untouched OOS",
        "allocation_mapping_selected": False,
    }
    (output_dir / "phase-a-manifest.json").write_text(
        json.dumps(_json_safe(manifest), indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    write_markdown_report(
        output_dir / "phase-a-report.md",
        history=history,
        episode_summary=episode_summary,
        points=points,
        inference=inference,
    )
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Issue #64 Phase A Macro Pressure Map asset-allocation diagnostics")
    parser.add_argument("--start", default="2007-01-01")
    parser.add_argument("--end", default=None, help="Exclusive end date, YYYY-MM-DD")
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = run_phase_a(args.start, args.end, args.output_dir)
    print(json.dumps({
        "phase": manifest["phase"],
        "rows": manifest["common_finite_regime_rows"],
        "first_date": manifest["common_first_date"],
        "last_date": manifest["common_last_date"],
        "output_dir": str(args.output_dir),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
