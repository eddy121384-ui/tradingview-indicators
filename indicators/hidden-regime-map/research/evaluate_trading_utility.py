#!/usr/bin/env python3
"""Evaluate whether causal HMM regime information adds OOS trading value."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

RESEARCH_DIR = Path(__file__).resolve().parent
if str(RESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(RESEARCH_DIR))

import compare_feature_sets
import compare_state_counts
import train_hmm

TRADING_DAYS = 252
FIT_FRACTION = 0.60
EXPLORATORY_FRACTION = 0.20
FINAL_FRACTION = 0.20
COST_BPS = 5.0
GROUP_SEEDS = (42, 84, 126)
BASELINES = ("buy_and_hold", "trend_100", "momentum_63")
HMM_ROLES = ("favorable_filter", "size_modifier", "defensive_switch")
SIMPLE_FILTER = "sma200_filter"

SHARPE_IMPROVEMENT = 0.15
SIMPLE_SHARPE_EDGE = 0.05
MAX_RETURN_SACRIFICE_TRADING = 0.01
DRAWDOWN_REDUCTION = 0.20
SIMPLE_DRAWDOWN_EDGE = 0.05
CALMAR_IMPROVEMENT = 0.10
MAX_RETURN_SACRIFICE_RISK = 0.02
MIN_ACTIVE_DAYS = 100
MAX_TOP5_POSITIVE_PNL_SHARE = 0.50
MIN_BASELINES = 2


@dataclass(frozen=True)
class CandidateConfig:
    name: str
    k: int
    feature_names: tuple[str, ...]


CANDIDATES = (
    CandidateConfig("k3_baseline", 3, tuple(train_hmm.FEATURE_NAMES)),
    CandidateConfig(
        "k8_baseline_er_downside",
        8,
        tuple(compare_feature_sets.FEATURE_SETS["baseline_er_downside"]),
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate Issue #40 HMM trading utility")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--sha256-file", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--symbol", default="SPY")
    parser.add_argument("--timeframe", default="1D")
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


def load_frozen_input(args: argparse.Namespace) -> tuple[pd.DataFrame, str]:
    if args.symbol.upper() != "SPY" or args.timeframe.upper() != "1D":
        raise ValueError("Issue #40 is restricted to frozen SPY 1D data")
    expected = expected_sha256(args.sha256_file)
    actual = sha256_decompressed(args.input)
    if actual != expected:
        raise ValueError(f"frozen input SHA-256 mismatch: expected {expected}, got {actual}")
    loader_args = SimpleNamespace(
        input=args.input,
        date_column="Date",
        open_column="Open",
        high_column="High",
        low_column="Low",
        close_column="Close",
    )
    return train_hmm.load_ohlc(loader_args), actual


def prepare_features(raw: pd.DataFrame) -> pd.DataFrame:
    baseline = train_hmm.calculate_features(raw, train_hmm.FeatureConfig())
    enriched = compare_feature_sets.add_path_features(baseline, raw)
    columns = list(compare_feature_sets.FEATURE_SETS["baseline_er_downside"])
    if not np.isfinite(enriched[columns].to_numpy()).all():
        raise ValueError("prepared Issue #40 features contain non-finite values")
    return enriched


def split_boundaries(rows: int) -> tuple[int, int]:
    fit_end = int(rows * FIT_FRACTION)
    exploratory_end = fit_end + int(rows * EXPLORATORY_FRACTION)
    if fit_end < 500 or exploratory_end - fit_end < 200 or rows - exploratory_end < 200:
        raise ValueError("Issue #40 requires at least 500 fit rows and 200 rows per OOS period")
    return fit_end, exploratory_end


def aligned_ensemble(
    features: pd.DataFrame,
    config: CandidateConfig,
    fit_end: int,
) -> dict[str, Any]:
    scaler = StandardScaler()
    names = list(config.feature_names)
    train_matrix = scaler.fit_transform(features.loc[: fit_end - 1, names])
    full_matrix = scaler.transform(features[names])

    models = []
    restart_records = []
    for group_seed in GROUP_SEEDS:
        model, attempts, selected_seed = compare_state_counts.fit_seed_group(
            train_matrix, config.k, group_seed
        )
        models.append(model)
        restart_records.append(
            {
                "group_seed": group_seed,
                "selected_attempt_seed": selected_seed,
                "restart_attempts": attempts,
            }
        )

    reference = models[0]
    aligned_posteriors = []
    aligned_means = []
    for model in models:
        permutation = compare_state_counts.state_alignment(reference, model)
        aligned_posteriors.append(
            train_hmm.forward_filter(model, full_matrix)[:, permutation]
        )
        aligned_means.append(
            compare_state_counts.aligned_parameters(model, permutation)["means"]
        )

    posterior = np.mean(np.asarray(aligned_posteriors), axis=0)
    posterior /= posterior.sum(axis=1, keepdims=True)
    means = np.mean(np.asarray(aligned_means), axis=0)
    favorable, defensive, risk_scores = state_buckets(means, config.feature_names)
    return {
        "posterior": posterior,
        "favorable_states": favorable,
        "defensive_states": defensive,
        "risk_scores": risk_scores,
        "restart_records": restart_records,
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist(),
    }


def state_buckets(
    emission_means: np.ndarray, feature_names: tuple[str, ...]
) -> tuple[list[int], list[int], list[float]]:
    if emission_means.ndim != 2 or emission_means.shape[1] != len(feature_names):
        raise ValueError("emission means do not match feature names")
    weights = {
        "standardized_return": -1.0,
        "atr_pct": 1.0,
        "trend_strength": -1.0,
        compare_feature_sets.EFFICIENCY_RATIO: -1.0,
        compare_feature_sets.DOWNSIDE_SHARE: 1.0,
    }
    scores = emission_means @ np.asarray(
        [weights[name] for name in feature_names], dtype=float
    )
    bucket = max(1, int(math.ceil(len(scores) * 0.25)))
    order = np.argsort(scores)
    favorable = sorted(int(value) for value in order[:bucket])
    defensive = sorted(int(value) for value in order[-bucket:])
    if set(favorable) & set(defensive):
        raise RuntimeError("favorable and defensive state buckets overlap")
    return favorable, defensive, scores.astype(float).tolist()


def baseline_targets(features: pd.DataFrame) -> dict[str, pd.Series]:
    close = features["close"].astype(float)
    return {
        "buy_and_hold": pd.Series(1.0, index=features.index),
        "trend_100": (close > close.rolling(100, min_periods=100).mean()).astype(float),
        "momentum_63": (close.pct_change(63) > 0.0).astype(float),
    }


def simple_filter_target(base: pd.Series, features: pd.DataFrame) -> pd.Series:
    close = features["close"].astype(float)
    return base * (close > close.rolling(200, min_periods=200).mean()).astype(float)


def hmm_targets(
    base: pd.Series, posterior: np.ndarray, favorable: list[int], defensive: list[int]
) -> dict[str, pd.Series]:
    favorable_probability = pd.Series(
        posterior[:, favorable].sum(axis=1), index=base.index
    )
    defensive_probability = pd.Series(
        posterior[:, defensive].sum(axis=1), index=base.index
    )
    return {
        "favorable_filter": base * (favorable_probability >= 0.50).astype(float),
        "size_modifier": base
        * (0.25 + 0.75 * favorable_probability).clip(lower=0.25, upper=1.0),
        "defensive_switch": base * (defensive_probability < 0.50).astype(float),
    }


def execute_target(
    close: pd.Series, target: pd.Series, cost_bps: float = COST_BPS
) -> pd.DataFrame:
    if not close.index.equals(target.index):
        raise ValueError("close and target indices must match")
    close_return = close.pct_change().fillna(0.0)
    position = target.shift(1).fillna(0.0).clip(lower=0.0, upper=1.0)
    turnover = position.diff().abs()
    turnover.iloc[0] = abs(float(position.iloc[0]))
    net_return = position * close_return - turnover * (cost_bps / 10000.0)
    return pd.DataFrame(
        {
            "close_return": close_return,
            "position": position,
            "turnover": turnover,
            "net_return": net_return,
        },
        index=close.index,
    )


def safe_ratio(numerator: float, denominator: float) -> float | None:
    if denominator <= 0.0 or not math.isfinite(denominator):
        return None
    value = numerator / denominator
    return float(value) if math.isfinite(value) else None


def trade_episode_metrics(
    frame: pd.DataFrame, previous_position: float = 0.0
) -> dict[str, Any]:
    """Describe boundary-aware contiguous positive-exposure episodes."""
    position = frame["position"].astype(float)
    active = position > 0.0
    prior_active = bool(previous_position > 0.0)
    previous_active = active.shift(1, fill_value=prior_active)
    starts = active & ~previous_active
    exits = active & ~active.shift(-1, fill_value=False)
    episode_id = starts.cumsum()
    left_censored = bool(active.iloc[0] and prior_active)
    right_censored = bool(active.iloc[-1])

    episode_returns: list[float] = []
    episode_days: list[int] = []
    completed_round_trips = 0
    if active.any():
        active_frame = frame.loc[active].copy()
        active_frame["episode_id"] = episode_id.loc[active].to_numpy()
        for _, episode in active_frame.groupby("episode_id", sort=True):
            first_location = int(frame.index.get_indexer([episode.index[0]])[0])
            last_location = int(frame.index.get_indexer([episode.index[-1]])[0])
            episode_growth = float((1.0 + episode["net_return"]).prod())
            if last_location < len(frame) - 1 and float(position.iloc[last_location + 1]) <= 0.0:
                episode_growth *= 1.0 + float(frame["net_return"].iloc[last_location + 1])
            episode_returns.append(episode_growth - 1.0)
            episode_days.append(int(len(episode)))
            started_within_period = first_location > 0 or not prior_active
            exited_within_period = last_location < len(frame) - 1
            if started_within_period and exited_within_period:
                completed_round_trips += 1

    values = pd.Series(episode_returns, dtype=float)
    positive = values[values > 0.0].sort_values(ascending=False)
    positive_total = float(positive.sum())
    top3_share = (
        float(positive.head(3).sum() / positive_total) if positive_total > 0.0 else 1.0
    )
    return {
        "trade_episode_count": int(len(values)),
        "new_entries_within_period": int(starts.sum()),
        "exits_within_period": int(exits.iloc[:-1].sum()) if len(exits) > 1 else 0,
        "completed_round_trips": completed_round_trips,
        "left_censored_trade": left_censored,
        "right_censored_trade": right_censored,
        "trade_win_rate": float((values > 0.0).mean()) if len(values) else None,
        "trade_payoff_p05": float(values.quantile(0.05)) if len(values) else None,
        "trade_payoff_median": float(values.median()) if len(values) else None,
        "trade_payoff_p95": float(values.quantile(0.95)) if len(values) else None,
        "mean_trade_days": float(np.mean(episode_days)) if episode_days else None,
        "median_trade_days": float(np.median(episode_days)) if episode_days else None,
        "top_3_positive_trades_share": top3_share,
    }


def performance_metrics(
    frame: pd.DataFrame, previous_position: float = 0.0
) -> dict[str, Any]:
    returns = frame["net_return"].astype(float)
    position = frame["position"].astype(float)
    turnover = frame["turnover"].astype(float)
    if len(returns) < 2:
        raise ValueError("performance period must contain at least two rows")

    wealth = (1.0 + returns).cumprod()
    annualized_return = (
        -1.0
        if (wealth <= 0.0).any()
        else float(wealth.iloc[-1] ** (TRADING_DAYS / len(returns)) - 1.0)
    )
    volatility = float(returns.std(ddof=0) * math.sqrt(TRADING_DAYS))
    mean_return = float(returns.mean())
    daily_std = float(returns.std(ddof=0))
    downside_std = float(returns.clip(upper=0.0).std(ddof=0))
    sharpe = safe_ratio(mean_return * math.sqrt(TRADING_DAYS), daily_std)
    sortino = safe_ratio(mean_return * math.sqrt(TRADING_DAYS), downside_std)

    opening_seeded_peak = np.maximum.accumulate(
        np.concatenate(([1.0], wealth.to_numpy(dtype=float)))
    )[1:]
    drawdown = wealth.to_numpy(dtype=float) / opening_seeded_peak - 1.0
    maximum_drawdown = float(np.min(drawdown))
    calmar = safe_ratio(annualized_return, abs(maximum_drawdown))

    positive = returns[returns > 0.0].sort_values(ascending=False)
    positive_total = float(positive.sum())
    top5_share = (
        float(positive.head(5).sum() / positive_total) if positive_total > 0.0 else 1.0
    )
    active_returns = returns[position > 0.0]
    metrics = {
        "rows": int(len(frame)),
        "annualized_return": annualized_return,
        "annualized_volatility": volatility,
        "sharpe": sharpe,
        "sortino": sortino,
        "calmar": calmar,
        "maximum_drawdown": maximum_drawdown,
        "active_days": int((position > 0.0).sum()),
        "average_exposure": float(position.mean()),
        "turnover": float(turnover.sum()),
        "daily_win_rate_when_active": (
            float((active_returns > 0.0).mean()) if len(active_returns) else None
        ),
        "daily_payoff_p05": (
            float(active_returns.quantile(0.05)) if len(active_returns) else None
        ),
        "daily_payoff_median": (
            float(active_returns.median()) if len(active_returns) else None
        ),
        "daily_payoff_p95": (
            float(active_returns.quantile(0.95)) if len(active_returns) else None
        ),
        "top_5_positive_days_share": top5_share,
        "total_return": float(wealth.iloc[-1] - 1.0),
    }
    metrics.update(trade_episode_metrics(frame, previous_position))
    return metrics


def period_slices(rows: int, fit_end: int, exploratory_end: int) -> dict[str, slice]:
    return {
        "exploratory": slice(fit_end, exploratory_end),
        "final": slice(exploratory_end, rows),
    }


def metric_value(metrics: dict[str, Any], name: str) -> float:
    value = metrics.get(name)
    return float(value) if value is not None else float("-inf")


def claim_checks(
    variant_exploratory: dict[str, Any],
    variant_final: dict[str, Any],
    baseline_exploratory: dict[str, Any],
    baseline_final: dict[str, Any],
    simple_final: dict[str, Any],
) -> dict[str, Any]:
    final_sharpe_delta = metric_value(variant_final, "sharpe") - metric_value(
        baseline_final, "sharpe"
    )
    exploratory_sharpe_delta = metric_value(
        variant_exploratory, "sharpe"
    ) - metric_value(baseline_exploratory, "sharpe")
    final_return_delta = (
        variant_final["annualized_return"] - baseline_final["annualized_return"]
    )
    base_drawdown = abs(float(baseline_final["maximum_drawdown"]))
    variant_drawdown = abs(float(variant_final["maximum_drawdown"]))
    simple_drawdown = abs(float(simple_final["maximum_drawdown"]))
    exploratory_drawdown_improvement = abs(
        float(baseline_exploratory["maximum_drawdown"])
    ) - abs(float(variant_exploratory["maximum_drawdown"]))
    concentration_ok = (
        variant_final["active_days"] >= MIN_ACTIVE_DAYS
        and variant_final["top_5_positive_days_share"]
        <= MAX_TOP5_POSITIVE_PNL_SHARE
    )
    trading_checks = {
        "exploratory_sharpe_improves": exploratory_sharpe_delta > 0.0,
        "final_sharpe_improves_materially": final_sharpe_delta >= SHARPE_IMPROVEMENT,
        "final_return_sacrifice_bounded": final_return_delta
        >= -MAX_RETURN_SACRIFICE_TRADING,
        "beats_simple_filter_sharpe": metric_value(variant_final, "sharpe")
        >= metric_value(simple_final, "sharpe") + SIMPLE_SHARPE_EDGE,
        "activity_and_concentration": concentration_ok,
    }
    risk_checks = {
        "exploratory_drawdown_improves": exploratory_drawdown_improvement > 0.0,
        "final_drawdown_reduction_material": (
            variant_drawdown <= (1.0 - DRAWDOWN_REDUCTION) * base_drawdown
            if base_drawdown > 0.0
            else False
        ),
        "final_calmar_improves": metric_value(variant_final, "calmar")
        >= metric_value(baseline_final, "calmar") + CALMAR_IMPROVEMENT,
        "final_return_sacrifice_bounded": final_return_delta >= -MAX_RETURN_SACRIFICE_RISK,
        "beats_simple_filter_drawdown": (
            variant_drawdown <= (1.0 - SIMPLE_DRAWDOWN_EDGE) * simple_drawdown
            if simple_drawdown > 0.0
            else False
        ),
        "activity_and_concentration": concentration_ok,
    }
    return {
        "trading_value": {"passed": all(trading_checks.values()), "checks": trading_checks},
        "risk_value": {"passed": all(risk_checks.values()), "checks": risk_checks},
        "deltas": {
            "exploratory_sharpe": exploratory_sharpe_delta,
            "final_sharpe": final_sharpe_delta,
            "final_annualized_return": final_return_delta,
            "exploratory_drawdown_improvement": exploratory_drawdown_improvement,
            "final_drawdown_improvement": base_drawdown - variant_drawdown,
        },
    }


def decide_outcome(claims: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[tuple[str, str], dict[str, list[str]]] = {}
    for claim in claims:
        key = (claim["candidate"], claim["role"])
        bucket = grouped.setdefault(key, {"trading": [], "risk": []})
        if claim["checks"]["trading_value"]["passed"]:
            bucket["trading"].append(claim["baseline"])
        if claim["checks"]["risk_value"]["passed"]:
            bucket["risk"].append(claim["baseline"])
    trading_winners = [
        {"candidate": candidate, "role": role, "baselines": values["trading"]}
        for (candidate, role), values in grouped.items()
        if len(values["trading"]) >= MIN_BASELINES
    ]
    risk_winners = [
        {"candidate": candidate, "role": role, "baselines": values["risk"]}
        for (candidate, role), values in grouped.items()
        if len(values["risk"]) >= MIN_BASELINES
    ]
    if trading_winners:
        outcome = "adds_oos_trading_value"
        reason = (
            "At least one predeclared HMM candidate/role improved exploratory and "
            "final risk-adjusted performance across two or more baselines and beat "
            "the simpler SMA200 filter under the trading-value thresholds."
        )
    elif risk_winners:
        outcome = "adds_oos_risk_value_only"
        reason = (
            "No HMM role cleared the trading-value gate, but at least one candidate/"
            "role reduced drawdown across two or more baselines while preserving "
            "bounded return and beating the simpler SMA200 filter."
        )
    else:
        outcome = "no_incremental_value"
        reason = (
            "All predeclared experiments completed, but no single HMM candidate/role "
            "cleared the trading-value or risk-value gate across two or more baselines."
        )
    return {
        "outcome": outcome,
        "reason": reason,
        "trading_winners": trading_winners,
        "risk_winners": risk_winners,
        "minimum_supporting_baselines": MIN_BASELINES,
    }


def strict_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): strict_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [strict_json(item) for item in value]
    if isinstance(value, np.ndarray):
        return strict_json(value.tolist())
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        numeric = float(value)
        return numeric if math.isfinite(numeric) else None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def markdown_report(result: dict[str, Any]) -> str:
    decision = result["decision"]
    lines = [
        "# Issue #40 — HMM trading-utility decision",
        "",
        f"**Outcome:** `{decision['outcome']}`",
        "",
        decision["reason"],
        "",
        "## Frozen experiment",
        "",
        f"- Input SHA-256: `{result['input']['sha256']}`",
        f"- Fit / exploratory / final rows: {result['split']['fit_rows']} / "
        f"{result['split']['exploratory_rows']} / {result['split']['final_rows']}",
        f"- Cost: {result['experiment']['cost_bps']:.1f} bps per unit turnover",
        "- Execution: confirmed-bar target, applied one bar later",
        "",
        "## Final-period metrics",
        "",
        "| Candidate | Baseline | Role | Ann. return | Sharpe | Calmar | Max drawdown | Active days | Completed round trips | Trade episodes | Top-3 positive-trade share |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in (item for item in result["metrics"] if item["period"] == "final"):
        metric = row["metrics"]
        sharpe = f"{metric['sharpe']:.3f}" if metric["sharpe"] is not None else "—"
        calmar = f"{metric['calmar']:.3f}" if metric["calmar"] is not None else "—"
        lines.append(
            f"| `{row['candidate']}` | `{row['baseline']}` | `{row['role']}` | "
            f"{metric['annualized_return']:.2%} | {sharpe} | {calmar} | "
            f"{metric['maximum_drawdown']:.2%} | {metric['active_days']} | "
            f"{metric['completed_round_trips']} | {metric['trade_episode_count']} | "
            f"{metric['top_3_positive_trades_share']:.2%} |"
        )
    lines += [
        "",
        "Trade episodes are contiguous positive-exposure intervals. Episodes crossing "
        "a reporting boundary are retained and marked as left/right censored in JSON/CSV. "
        "Only episodes with both entry and exit inside the period count as completed round trips. "
        "These descriptive metrics do not change the predeclared decision gates.",
        "",
        "## Claim checks",
        "",
        "| Candidate | Role | Baseline | Trading value | Risk value | Final Sharpe Δ | Final return Δ | Final drawdown improvement |",
        "|---|---|---|---|---|---:|---:|---:|",
    ]
    for claim in result["claims"]:
        delta = claim["checks"]["deltas"]
        lines.append(
            f"| `{claim['candidate']}` | `{claim['role']}` | `{claim['baseline']}` | "
            f"{claim['checks']['trading_value']['passed']} | "
            f"{claim['checks']['risk_value']['passed']} | "
            f"{delta['final_sharpe']:.3f} | "
            f"{delta['final_annualized_return']:.2%} | "
            f"{delta['final_drawdown_improvement']:.2%} |"
        )
    lines += [
        "",
        "The decision is mechanical. Thresholds, roles, baselines, periods, costs, "
        "candidate models, and decision concentration guardrails were fixed before "
        "the final period was evaluated.",
        "",
    ]
    return "\n".join(lines)


def _record_metrics(
    metric_rows: list[dict[str, Any]],
    metric_index: dict[tuple[str, str, str, str], dict[str, Any]],
    candidate: str,
    baseline: str,
    role: str,
    executed: pd.DataFrame,
    periods: dict[str, slice],
) -> None:
    for period_name, period_slice in periods.items():
        previous_position = (
            float(executed["position"].iloc[period_slice.start - 1])
            if period_slice.start and period_slice.start > 0
            else 0.0
        )
        metrics = performance_metrics(
            executed.iloc[period_slice], previous_position=previous_position
        )
        metric_rows.append(
            {
                "candidate": candidate,
                "baseline": baseline,
                "role": role,
                "period": period_name,
                "metrics": metrics,
            }
        )
        metric_index[(candidate, baseline, role, period_name)] = metrics


def run(args: argparse.Namespace) -> dict[str, Any]:
    raw, digest = load_frozen_input(args)
    features = prepare_features(raw)
    fit_end, exploratory_end = split_boundaries(len(features))
    periods = period_slices(len(features), fit_end, exploratory_end)
    baselines = baseline_targets(features)
    close = features["close"].astype(float)

    metric_rows: list[dict[str, Any]] = []
    metric_index: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for baseline_name, base in baselines.items():
        for role, target in {
            "no_hmm": base,
            SIMPLE_FILTER: simple_filter_target(base, features),
        }.items():
            _record_metrics(
                metric_rows,
                metric_index,
                "non_hmm",
                baseline_name,
                role,
                execute_target(close, target),
                periods,
            )

    candidate_details = []
    for candidate in CANDIDATES:
        ensemble = aligned_ensemble(features, candidate, fit_end)
        candidate_details.append(
            {
                "name": candidate.name,
                "k": candidate.k,
                "feature_names": list(candidate.feature_names),
                "favorable_states": ensemble["favorable_states"],
                "defensive_states": ensemble["defensive_states"],
                "risk_scores": ensemble["risk_scores"],
                "restart_records": ensemble["restart_records"],
                "scaler_mean": ensemble["scaler_mean"],
                "scaler_scale": ensemble["scaler_scale"],
            }
        )
        for baseline_name, base in baselines.items():
            for role, target in hmm_targets(
                base,
                ensemble["posterior"],
                ensemble["favorable_states"],
                ensemble["defensive_states"],
            ).items():
                _record_metrics(
                    metric_rows,
                    metric_index,
                    candidate.name,
                    baseline_name,
                    role,
                    execute_target(close, target),
                    periods,
                )

    claims = []
    for candidate in CANDIDATES:
        for role in HMM_ROLES:
            for baseline_name in BASELINES:
                claims.append(
                    {
                        "candidate": candidate.name,
                        "role": role,
                        "baseline": baseline_name,
                        "checks": claim_checks(
                            metric_index[(candidate.name, baseline_name, role, "exploratory")],
                            metric_index[(candidate.name, baseline_name, role, "final")],
                            metric_index[("non_hmm", baseline_name, "no_hmm", "exploratory")],
                            metric_index[("non_hmm", baseline_name, "no_hmm", "final")],
                            metric_index[("non_hmm", baseline_name, SIMPLE_FILTER, "final")],
                        ),
                    }
                )

    result = {
        "schema_version": 2,
        "issue": 40,
        "input": {
            "path": str(args.input),
            "sha256": digest,
            "source_run_number": 58,
            "source_run_id": 30077475634,
            "source_artifact": "hidden-regime-SPY",
            "source_artifact_id": 8590548073,
        },
        "experiment": {
            "symbol": args.symbol,
            "timeframe": args.timeframe,
            "fit_fraction": FIT_FRACTION,
            "exploratory_fraction": EXPLORATORY_FRACTION,
            "final_fraction": FINAL_FRACTION,
            "cost_bps": COST_BPS,
            "execution_lag_bars": 1,
            "group_seeds": list(GROUP_SEEDS),
            "restart_offsets": list(compare_state_counts.RESTART_OFFSETS),
            "baselines": list(BASELINES),
            "simple_non_hmm_filter": SIMPLE_FILTER,
            "hmm_roles": list(HMM_ROLES),
            "descriptive_trade_episode_metrics_added_after_first_run": True,
            "decision_gates_changed_after_first_run": False,
            "thresholds": {
                "sharpe_improvement": SHARPE_IMPROVEMENT,
                "simple_filter_sharpe_edge": SIMPLE_SHARPE_EDGE,
                "maximum_return_sacrifice_trading": MAX_RETURN_SACRIFICE_TRADING,
                "drawdown_reduction": DRAWDOWN_REDUCTION,
                "simple_filter_drawdown_edge": SIMPLE_DRAWDOWN_EDGE,
                "calmar_improvement": CALMAR_IMPROVEMENT,
                "maximum_return_sacrifice_risk": MAX_RETURN_SACRIFICE_RISK,
                "minimum_active_days": MIN_ACTIVE_DAYS,
                "maximum_top5_positive_pnl_share": MAX_TOP5_POSITIVE_PNL_SHARE,
                "minimum_supporting_baselines": MIN_BASELINES,
            },
        },
        "split": {
            "usable_rows": len(features),
            "fit_rows": fit_end,
            "exploratory_rows": exploratory_end - fit_end,
            "final_rows": len(features) - exploratory_end,
            "feature_start": features["date"].iloc[0],
            "fit_end": features["date"].iloc[fit_end - 1],
            "exploratory_start": features["date"].iloc[fit_end],
            "exploratory_end": features["date"].iloc[exploratory_end - 1],
            "final_start": features["date"].iloc[exploratory_end],
            "final_end": features["date"].iloc[-1],
        },
        "candidates": candidate_details,
        "metrics": metric_rows,
        "claims": claims,
        "decision": decide_outcome(claims),
    }
    return strict_json(result)


def main() -> int:
    args = parse_args()
    result = run(args)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "issue-40-trading-utility.json"
    csv_path = args.output_dir / "issue-40-trading-utility-metrics.csv"
    markdown_path = args.output_dir / "issue-40-trading-utility.md"
    json_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    rows = [
        {
            "candidate": row["candidate"],
            "baseline": row["baseline"],
            "role": row["role"],
            "period": row["period"],
            **row["metrics"],
        }
        for row in result["metrics"]
    ]
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    report = markdown_report(result)
    markdown_path.write_text(report, encoding="utf-8")
    print(report)
    print(f"wrote: {json_path}")
    print(f"wrote: {csv_path}")
    print(f"wrote: {markdown_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
