#!/usr/bin/env python3
"""Evaluate preregistered Issue #50 U.S. rates regime utility."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

RESEARCH_DIR = Path(__file__).resolve().parent
if str(RESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(RESEARCH_DIR))

import compare_state_counts
import train_hmm

FEATURE_NAMES = (
    "curve_level",
    "slope_2s10s",
    "slope_5s30s",
    "level_change_bp",
    "level_vol_20_bp",
)
ASSETS = ("SHY", "IEF", "TLT", "CASH")
ETF_ASSETS = ("SHY", "IEF", "TLT")
CANDIDATES = (3, 4)
GROUP_SEEDS = (42, 84, 126)
TRADING_DAYS = 252
FIT_FRACTION = 0.60
EXPLORATORY_FRACTION = 0.20
COST_BPS = 2.0
TARGET_VOL = 0.08
MIN_ACTIVE_DAYS = 100
MAX_TOP5_SHARE = 0.50


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate Issue #50 rates regime utility")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--sha256-file", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def sha256_decompressed(path: Path) -> str:
    opener = gzip.open if path.suffix == ".gz" else open
    digest = hashlib.sha256()
    with opener(path, "rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def expected_sha256(path: Path) -> str:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError("SHA-256 file is empty")
    value = text.split()[0].lower()
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError("SHA-256 file does not start with a valid digest")
    return value


def load_frozen_input(path: Path, sha_path: Path) -> tuple[pd.DataFrame, str]:
    actual = sha256_decompressed(path)
    expected = expected_sha256(sha_path)
    if actual != expected:
        raise ValueError(f"frozen input SHA-256 mismatch: expected {expected}, got {actual}")

    frame = pd.read_csv(path)
    required = ["Date", "DGS3MO", "DGS2", "DGS5", "DGS10", "DGS30", "SHY", "IEF", "TLT"]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"missing frozen rates columns: {missing}")
    frame = frame[required].copy()
    frame["Date"] = pd.to_datetime(frame["Date"], errors="raise", utc=True)
    for column in required[1:]:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    frame = frame.sort_values("Date").drop_duplicates("Date", keep="last").reset_index(drop=True)
    if len(frame) < 3000:
        raise ValueError("frozen rates input must contain at least 3000 rows")
    if not np.isfinite(frame[required[1:]].to_numpy(dtype=float)).all():
        raise ValueError("frozen rates input contains non-finite values")
    if (frame[list(ETF_ASSETS)] <= 0.0).any().any():
        raise ValueError("ETF prices must be positive")
    return frame, actual


def prepare_panel(raw: pd.DataFrame) -> pd.DataFrame:
    panel = raw.copy()
    yield_columns = ["DGS2", "DGS5", "DGS10", "DGS30"]
    panel["curve_level"] = panel[yield_columns].mean(axis=1)
    panel["slope_2s10s"] = panel["DGS10"] - panel["DGS2"]
    panel["slope_5s30s"] = panel["DGS30"] - panel["DGS5"]
    panel["level_change_bp"] = panel["curve_level"].diff() * 100.0
    panel["level_vol_20_bp"] = panel["level_change_bp"].rolling(
        20, min_periods=20
    ).std(ddof=0)

    for asset in ETF_ASSETS:
        panel[f"{asset}_return"] = panel[asset].pct_change()
    panel["CASH_return"] = panel["DGS3MO"].shift(1) / 100.0 / TRADING_DAYS

    required = list(FEATURE_NAMES) + [f"{asset}_return" for asset in ASSETS]
    panel = panel.dropna(subset=required).reset_index(drop=True)
    if len(panel) < 2500:
        raise ValueError("too few rows remain after rates feature warm-up")
    if not np.isfinite(panel[required].to_numpy(dtype=float)).all():
        raise ValueError("prepared rates panel contains non-finite values")
    return panel


def split_boundaries(rows: int) -> tuple[int, int]:
    fit_end = int(rows * FIT_FRACTION)
    exploratory_end = fit_end + int(rows * EXPLORATORY_FRACTION)
    if fit_end < 1200 or exploratory_end - fit_end < 500 or rows - exploratory_end < 500:
        raise ValueError("rates experiment requires at least 1200 fit rows and 500 rows per OOS slice")
    return fit_end, exploratory_end


def aligned_ensemble(panel: pd.DataFrame, n_states: int, fit_end: int) -> dict[str, Any]:
    scaler = StandardScaler()
    train = scaler.fit_transform(panel.loc[: fit_end - 1, list(FEATURE_NAMES)])
    full = scaler.transform(panel[list(FEATURE_NAMES)])

    models = []
    restart_records = []
    for group_seed in GROUP_SEEDS:
        model, attempts, selected_seed = compare_state_counts.fit_seed_group(
            train, n_states, group_seed
        )
        models.append(model)
        restart_records.append(
            {
                "group_seed": group_seed,
                "selected_attempt_seed": selected_seed,
                "attempts": attempts,
            }
        )

    reference = models[0]
    posteriors = []
    means = []
    for model in models:
        permutation = compare_state_counts.state_alignment(reference, model)
        posteriors.append(train_hmm.forward_filter(model, full)[:, permutation])
        means.append(compare_state_counts.aligned_parameters(model, permutation)["means"])

    posterior = np.mean(np.asarray(posteriors), axis=0)
    posterior /= posterior.sum(axis=1, keepdims=True)
    aligned_mean = np.mean(np.asarray(means), axis=0)
    mapping, risk_scores = state_duration_mapping(aligned_mean, n_states)
    return {
        "posterior": posterior,
        "emission_means": aligned_mean.tolist(),
        "mapping": mapping,
        "risk_scores": risk_scores,
        "restart_records": restart_records,
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist(),
    }


def state_duration_mapping(
    emission_means: np.ndarray, n_states: int
) -> tuple[dict[int, str], list[float]]:
    if emission_means.shape != (n_states, len(FEATURE_NAMES)):
        raise ValueError("emission means do not match rates feature contract")
    change_index = FEATURE_NAMES.index("level_change_bp")
    vol_index = FEATURE_NAMES.index("level_vol_20_bp")
    scores = emission_means[:, change_index] + 0.75 * emission_means[:, vol_index]
    order = np.argsort(scores)
    ladder = ("TLT", "IEF", "SHY") if n_states == 3 else ("TLT", "IEF", "SHY", "CASH")
    mapping = {int(state): ladder[rank] for rank, state in enumerate(order)}
    return mapping, scores.astype(float).tolist()


def posterior_duration_weights(
    posterior: np.ndarray, mapping: dict[int, str], index: pd.Index
) -> pd.DataFrame:
    weights = pd.DataFrame(0.0, index=index, columns=ASSETS)
    for state, asset in mapping.items():
        weights[asset] += posterior[:, state]
    if not np.allclose(weights.sum(axis=1).to_numpy(), 1.0, atol=1e-10):
        raise RuntimeError("HMM target weights are not fully invested")
    return weights


def empty_weights(index: pd.Index) -> pd.DataFrame:
    return pd.DataFrame(0.0, index=index, columns=ASSETS)


def baseline_weights(panel: pd.DataFrame) -> dict[str, pd.DataFrame]:
    index = panel.index
    targets: dict[str, pd.DataFrame] = {}

    tlt = empty_weights(index)
    tlt["TLT"] = 1.0
    targets["tlt_buy_hold"] = tlt

    equal = empty_weights(index)
    equal[list(ETF_ASSETS)] = 1.0 / 3.0
    targets["equal_duration"] = equal

    etf_returns = panel[[f"{asset}_return" for asset in ETF_ASSETS]].copy()
    etf_returns.columns = ETF_ASSETS
    vol63 = etf_returns.rolling(63, min_periods=63).std(ddof=0)
    inverse = 1.0 / vol63.replace(0.0, np.nan)
    inverse = inverse.div(inverse.sum(axis=1), axis=0).fillna(1.0 / 3.0)
    inverse_target = empty_weights(index)
    inverse_target[list(ETF_ASSETS)] = inverse
    targets["inverse_vol_63"] = inverse_target

    trend = empty_weights(index)
    above = panel["TLT"] > panel["TLT"].rolling(200, min_periods=200).mean()
    trend.loc[above, "TLT"] = 1.0
    trend.loc[~above, "SHY"] = 1.0
    targets["trend_duration_200"] = trend

    vol20 = panel["TLT_return"].rolling(20, min_periods=20).std(ddof=0) * math.sqrt(TRADING_DAYS)
    exposure = (TARGET_VOL / vol20.replace(0.0, np.nan)).clip(0.0, 1.0).fillna(0.0)
    vol_target = empty_weights(index)
    vol_target["TLT"] = exposure
    vol_target["CASH"] = 1.0 - exposure
    targets["vol_target_tlt_20"] = vol_target

    for name, frame in targets.items():
        if not np.allclose(frame.sum(axis=1).to_numpy(), 1.0, atol=1e-10):
            raise RuntimeError(f"baseline {name} is not fully invested")
    return targets


def execute_weights(
    panel: pd.DataFrame, target: pd.DataFrame, cost_bps: float = COST_BPS
) -> pd.DataFrame:
    if not panel.index.equals(target.index):
        raise ValueError("panel and target indices must match")
    returns = pd.DataFrame(
        {asset: panel[f"{asset}_return"].astype(float) for asset in ASSETS},
        index=panel.index,
    )
    position = target.shift(1)
    position.iloc[0] = [0.0, 0.0, 0.0, 1.0]
    position = position.fillna(0.0)
    prior = position.shift(1)
    prior.iloc[0] = [0.0, 0.0, 0.0, 1.0]
    turnover = 0.5 * (position - prior).abs().sum(axis=1)
    gross_return = (position * returns).sum(axis=1)
    cost = turnover * (cost_bps / 10000.0)
    net_return = gross_return - cost
    result = position.add_prefix("weight_")
    result["turnover"] = turnover
    result["cost"] = cost
    result["gross_return"] = gross_return
    result["net_return"] = net_return
    result["cash_return"] = returns["CASH"]
    return result


def max_drawdown(returns: pd.Series) -> float:
    wealth = (1.0 + returns.astype(float)).cumprod()
    seeded = pd.concat([pd.Series([1.0]), wealth.reset_index(drop=True)], ignore_index=True)
    peak = seeded.cummax()
    return float((seeded / peak - 1.0).min())


def safe_ratio(numerator: float, denominator: float) -> float | None:
    if denominator <= 0.0 or not math.isfinite(denominator):
        return None
    value = numerator / denominator
    return float(value) if math.isfinite(value) else None


def performance_metrics(frame: pd.DataFrame) -> dict[str, Any]:
    returns = frame["net_return"].astype(float)
    cash = frame["cash_return"].astype(float)
    if len(returns) < 2:
        raise ValueError("performance slice must contain at least two rows")
    wealth = float((1.0 + returns).prod())
    annualized_return = wealth ** (TRADING_DAYS / len(returns)) - 1.0
    annualized_volatility = float(returns.std(ddof=0) * math.sqrt(TRADING_DAYS))
    excess = returns - cash
    sharpe = safe_ratio(
        float(excess.mean() * math.sqrt(TRADING_DAYS)),
        float(excess.std(ddof=0)),
    )
    drawdown = max_drawdown(returns)
    calmar = safe_ratio(annualized_return, abs(drawdown))
    positive = returns[returns > 0.0].sort_values(ascending=False)
    positive_total = float(positive.sum())
    top5_share = float(positive.head(5).sum() / positive_total) if positive_total > 0 else 1.0
    duration_exposure = frame[[f"weight_{asset}" for asset in ETF_ASSETS]].sum(axis=1)
    return {
        "rows": int(len(frame)),
        "annualized_return": float(annualized_return),
        "annualized_volatility": annualized_volatility,
        "sharpe_excess_cash": sharpe,
        "maximum_drawdown": drawdown,
        "calmar": calmar,
        "total_turnover": float(frame["turnover"].sum()),
        "annualized_turnover": float(frame["turnover"].mean() * TRADING_DAYS),
        "cost_drag_sum": float(frame["cost"].sum()),
        "active_duration_days": int((duration_exposure > 0.01).sum()),
        "top_5_positive_days_share": top5_share,
        "average_weights": {
            asset: float(frame[f"weight_{asset}"].mean()) for asset in ASSETS
        },
    }


def period_slices(fit_end: int, exploratory_end: int, rows: int) -> dict[str, slice]:
    return {
        "exploratory_oos": slice(fit_end, exploratory_end),
        "final_oos": slice(exploratory_end, rows),
    }


def occupancy(posterior: np.ndarray, period: slice) -> list[float]:
    return np.mean(posterior[period], axis=0).astype(float).tolist()


def gate_comparison(hmm: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    hmm_sharpe = hmm["sharpe_excess_cash"]
    base_sharpe = baseline["sharpe_excess_cash"]
    sharpe_improvement = (
        None if hmm_sharpe is None or base_sharpe is None else hmm_sharpe - base_sharpe
    )
    return_sacrifice = baseline["annualized_return"] - hmm["annualized_return"]
    base_dd = abs(baseline["maximum_drawdown"])
    hmm_dd = abs(hmm["maximum_drawdown"])
    drawdown_reduction = 0.0 if base_dd <= 0 else (base_dd - hmm_dd) / base_dd
    calmar_improvement = (
        None
        if hmm["calmar"] is None or baseline["calmar"] is None
        else hmm["calmar"] - baseline["calmar"]
    )
    common_guardrails = (
        hmm["top_5_positive_days_share"] <= MAX_TOP5_SHARE
        and hmm["active_duration_days"] >= MIN_ACTIVE_DAYS
    )
    trading_pass = (
        sharpe_improvement is not None
        and sharpe_improvement >= 0.10
        and return_sacrifice <= 0.01
        and common_guardrails
    )
    risk_pass = (
        calmar_improvement is not None
        and drawdown_reduction >= 0.20
        and calmar_improvement >= 0.10
        and return_sacrifice <= 0.02
        and common_guardrails
    )
    return {
        "sharpe_improvement": sharpe_improvement,
        "annualized_return_sacrifice": float(return_sacrifice),
        "drawdown_reduction": float(drawdown_reduction),
        "calmar_improvement": calmar_improvement,
        "guardrails_pass": bool(common_guardrails),
        "trading_value_pass": bool(trading_pass),
        "risk_value_pass": bool(risk_pass),
    }


def exploratory_contradiction(hmm: dict[str, Any], baseline: dict[str, Any]) -> bool:
    hmm_sharpe = hmm["sharpe_excess_cash"]
    base_sharpe = baseline["sharpe_excess_cash"]
    if hmm_sharpe is not None and base_sharpe is not None and hmm_sharpe < base_sharpe - 0.10:
        return True
    return baseline["annualized_return"] - hmm["annualized_return"] > 0.02


def make_report(result: dict[str, Any]) -> str:
    lines = [
        "# Issue #50 rates regime-utility result",
        "",
        f"Outcome: `{result['outcome']}`",
        "",
        f"Frozen input SHA-256: `{result['input_sha256']}`",
        "",
        "## Final OOS metrics",
        "",
        "| variant | ann. return | Sharpe | max drawdown | Calmar | ann. turnover |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, metrics in result["period_metrics"]["final_oos"].items():
        sharpe = metrics["sharpe_excess_cash"]
        calmar = metrics["calmar"]
        lines.append(
            f"| {name} | {metrics['annualized_return']:.4f} | "
            f"{'' if sharpe is None else f'{sharpe:.3f}'} | "
            f"{metrics['maximum_drawdown']:.4f} | "
            f"{'' if calmar is None else f'{calmar:.3f}'} | "
            f"{metrics['annualized_turnover']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Mechanical decision",
            "",
            f"Trading winners: {result['trading_winners']}",
            "",
            f"Risk winners: {result['risk_winners']}",
            "",
            "This result is bounded to the preregistered U.S. rates experiment. A passing outcome remains provisional until adjacent-window or walk-forward sensitivity succeeds.",
            "",
        ]
    )
    return "\n".join(lines)


def evaluate(panel: pd.DataFrame, input_sha: str) -> dict[str, Any]:
    fit_end, exploratory_end = split_boundaries(len(panel))
    slices = period_slices(fit_end, exploratory_end, len(panel))

    targets = baseline_weights(panel)
    baselines = list(targets.keys())
    ensembles: dict[str, dict[str, Any]] = {}
    for n_states in CANDIDATES:
        ensemble = aligned_ensemble(panel, n_states, fit_end)
        name = f"hmm_k{n_states}_duration_blend"
        targets[name] = posterior_duration_weights(
            ensemble["posterior"], ensemble["mapping"], panel.index
        )
        ensembles[name] = ensemble

    executed = {name: execute_weights(panel, target) for name, target in targets.items()}
    metrics: dict[str, dict[str, Any]] = {period: {} for period in slices}
    for period_name, period_slice in slices.items():
        for variant, frame in executed.items():
            metrics[period_name][variant] = performance_metrics(frame.iloc[period_slice])

    trading_winners: dict[str, list[str]] = {}
    risk_winners: dict[str, list[str]] = {}
    comparisons: dict[str, dict[str, Any]] = {}
    unstable_candidates = []
    for candidate, ensemble in ensembles.items():
        final_occ = occupancy(ensemble["posterior"], slices["final_oos"])
        fit_occ = occupancy(ensemble["posterior"], slice(0, fit_end))
        if min(final_occ) < 0.01 or min(fit_occ) < 0.01:
            unstable_candidates.append(candidate)
        candidate_comparisons: dict[str, Any] = {}
        trading_passes = []
        risk_passes = []
        for baseline in baselines:
            gate = gate_comparison(
                metrics["final_oos"][candidate], metrics["final_oos"][baseline]
            )
            contradiction = exploratory_contradiction(
                metrics["exploratory_oos"][candidate],
                metrics["exploratory_oos"][baseline],
            )
            gate["exploratory_contradiction"] = contradiction
            gate["qualified_trading_pass"] = bool(
                gate["trading_value_pass"] and not contradiction
            )
            gate["qualified_risk_pass"] = bool(
                gate["risk_value_pass"] and not contradiction
            )
            if gate["qualified_trading_pass"]:
                trading_passes.append(baseline)
            if gate["qualified_risk_pass"]:
                risk_passes.append(baseline)
            candidate_comparisons[baseline] = gate
        comparisons[candidate] = candidate_comparisons
        if len(trading_passes) >= 2:
            trading_winners[candidate] = trading_passes
        if len(risk_passes) >= 2:
            risk_winners[candidate] = risk_passes

    if len(unstable_candidates) == len(ensembles):
        outcome = "inconclusive_instability"
    elif trading_winners:
        outcome = "incremental_value_supported"
    elif risk_winners:
        outcome = "risk_value_only"
    else:
        outcome = "no_incremental_value"

    return {
        "schema_version": 1,
        "issue": 50,
        "contract": "issue-50-rates-v1",
        "outcome": outcome,
        "input_sha256": input_sha,
        "rows": int(len(panel)),
        "split": {
            "fit_end_row": fit_end,
            "exploratory_end_row": exploratory_end,
            "fit_fraction": FIT_FRACTION,
            "exploratory_fraction": EXPLORATORY_FRACTION,
            "final_fraction": 1.0 - FIT_FRACTION - EXPLORATORY_FRACTION,
            "fit_last_date": panel["Date"].iloc[fit_end - 1].isoformat(),
            "exploratory_last_date": panel["Date"].iloc[exploratory_end - 1].isoformat(),
            "final_last_date": panel["Date"].iloc[-1].isoformat(),
        },
        "features": list(FEATURE_NAMES),
        "cost_bps_per_unit_turnover": COST_BPS,
        "period_metrics": metrics,
        "candidate_diagnostics": {
            name: {
                "mapping": ensemble["mapping"],
                "risk_scores": ensemble["risk_scores"],
                "emission_means": ensemble["emission_means"],
                "restart_records": ensemble["restart_records"],
                "fit_occupancy": occupancy(ensemble["posterior"], slice(0, fit_end)),
                "exploratory_occupancy": occupancy(
                    ensemble["posterior"], slices["exploratory_oos"]
                ),
                "final_occupancy": occupancy(
                    ensemble["posterior"], slices["final_oos"]
                ),
            }
            for name, ensemble in ensembles.items()
        },
        "comparisons": comparisons,
        "trading_winners": trading_winners,
        "risk_winners": risk_winners,
        "unstable_candidates": unstable_candidates,
    }


def key_metrics_frame(result: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for period, variants in result["period_metrics"].items():
        for variant, metrics in variants.items():
            rows.append(
                {
                    "period": period,
                    "variant": variant,
                    "annualized_return": metrics["annualized_return"],
                    "annualized_volatility": metrics["annualized_volatility"],
                    "sharpe_excess_cash": metrics["sharpe_excess_cash"],
                    "maximum_drawdown": metrics["maximum_drawdown"],
                    "calmar": metrics["calmar"],
                    "annualized_turnover": metrics["annualized_turnover"],
                    "cost_drag_sum": metrics["cost_drag_sum"],
                    "active_duration_days": metrics["active_duration_days"],
                    "top_5_positive_days_share": metrics["top_5_positive_days_share"],
                }
            )
    return pd.DataFrame(rows).sort_values(["period", "variant"]).reset_index(drop=True)


def main() -> None:
    args = parse_args()
    raw, input_sha = load_frozen_input(args.input, args.sha256_file)
    panel = prepare_panel(raw)
    result = evaluate(panel, input_sha)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "rates-utility-result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    key_metrics_frame(result).to_csv(
        args.output_dir / "rates-utility-key-metrics.csv",
        index=False,
        float_format="%.12g",
        lineterminator="\n",
    )
    (args.output_dir / "rates-utility-report.md").write_text(
        make_report(result), encoding="utf-8"
    )
    print(json.dumps({"outcome": result["outcome"], "rows": result["rows"]}, indent=2))


if __name__ == "__main__":
    main()
