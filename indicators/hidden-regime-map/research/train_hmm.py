#!/usr/bin/env python3
"""Train and inspect a small three-state Gaussian HMM for market regimes.

The script deliberately separates model training from online inference. It fits
feature scaling and the HMM on the chronological training segment, then computes
causal forward-filtered posteriors across the full sample using only information
available through each row.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from sklearn.preprocessing import StandardScaler

FEATURE_NAMES = ["standardized_return", "atr_pct", "trend_strength"]
STATE_NAMES = ["A", "B", "C"]
EPSILON = 1e-300


@dataclass(frozen=True)
class FeatureConfig:
    return_vol_lookback: int = 20
    atr_lookback: int = 20
    fast_ma: int = 20
    slow_ma: int = 100

    def validate(self) -> None:
        values = asdict(self)
        for name, value in values.items():
            if value < 2:
                raise ValueError(f"{name} must be at least 2")
        if self.fast_ma >= self.slow_ma:
            raise ValueError("fast_ma must be smaller than slow_ma")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a three-state Gaussian HMM and export Pine-ready parameters."
    )
    parser.add_argument("--input", type=Path, required=True, help="OHLC CSV file")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--date-column", default="Date")
    parser.add_argument("--open-column", default="Open")
    parser.add_argument("--high-column", default="High")
    parser.add_argument("--low-column", default="Low")
    parser.add_argument("--close-column", default="Close")
    parser.add_argument("--symbol", default="UNKNOWN")
    parser.add_argument("--timeframe", default="UNKNOWN")
    parser.add_argument("--train-fraction", type=float, default=0.80)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--restarts", type=int, default=5)
    parser.add_argument("--return-vol-lookback", type=int, default=20)
    parser.add_argument("--atr-lookback", type=int, default=20)
    parser.add_argument("--fast-ma", type=int, default=20)
    parser.add_argument("--slow-ma", type=int, default=100)
    return parser.parse_args()


def load_ohlc(args: argparse.Namespace) -> pd.DataFrame:
    if not args.input.exists():
        raise FileNotFoundError(f"input file not found: {args.input}")

    frame = pd.read_csv(args.input)
    column_map = {
        args.date_column: "date",
        args.open_column: "open",
        args.high_column: "high",
        args.low_column: "low",
        args.close_column: "close",
    }
    missing = [name for name in column_map if name not in frame.columns]
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")

    frame = frame[list(column_map)].rename(columns=column_map)
    frame["date"] = pd.to_datetime(frame["date"], errors="raise", utc=True)
    for column in ("open", "high", "low", "close"):
        frame[column] = pd.to_numeric(frame[column], errors="raise")

    frame = frame.sort_values("date").drop_duplicates("date", keep="last")
    if frame.empty:
        raise ValueError("input contains no rows")
    if not np.isfinite(frame[["open", "high", "low", "close"]].to_numpy()).all():
        raise ValueError("OHLC columns contain NaN or infinite values")
    if (frame[["open", "high", "low", "close"]] <= 0).any().any():
        raise ValueError("OHLC prices must be positive")
    if (frame["high"] < frame[["open", "low", "close"]].max(axis=1)).any():
        raise ValueError("high is below another OHLC value")
    if (frame["low"] > frame[["open", "high", "close"]].min(axis=1)).any():
        raise ValueError("low is above another OHLC value")

    return frame.reset_index(drop=True)


def calculate_features(frame: pd.DataFrame, config: FeatureConfig) -> pd.DataFrame:
    config.validate()
    close = frame["close"]
    previous_close = close.shift(1)
    log_return = np.log(close / previous_close)
    return_volatility = log_return.rolling(
        config.return_vol_lookback, min_periods=config.return_vol_lookback
    ).std(ddof=0)

    true_range = pd.concat(
        [
            frame["high"] - frame["low"],
            (frame["high"] - previous_close).abs(),
            (frame["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr = true_range.rolling(
        config.atr_lookback, min_periods=config.atr_lookback
    ).mean()
    fast_average = close.rolling(config.fast_ma, min_periods=config.fast_ma).mean()
    slow_average = close.rolling(config.slow_ma, min_periods=config.slow_ma).mean()

    features = frame.copy()
    features["standardized_return"] = log_return / return_volatility.replace(0.0, np.nan)
    features["atr_pct"] = atr / close
    features["trend_strength"] = (fast_average - slow_average) / atr.replace(0.0, np.nan)
    features = features.dropna(subset=FEATURE_NAMES).reset_index(drop=True)

    if len(features) < 300:
        raise ValueError(
            f"only {len(features)} usable rows remain after feature calculation; at least 300 are required"
        )
    if not np.isfinite(features[FEATURE_NAMES].to_numpy()).all():
        raise ValueError("calculated features contain NaN or infinite values")
    return features


def fit_best_model(
    train_matrix: np.ndarray, seed: int, restarts: int
) -> tuple[GaussianHMM, int, float]:
    if restarts < 1:
        raise ValueError("restarts must be at least 1")

    best_model: GaussianHMM | None = None
    best_seed = seed
    best_score = -math.inf
    failures: list[str] = []

    for offset in range(restarts):
        candidate_seed = seed + offset
        model = GaussianHMM(
            n_components=3,
            covariance_type="diag",
            n_iter=500,
            tol=1e-4,
            random_state=candidate_seed,
            algorithm="viterbi",
            implementation="log",
        )
        try:
            model.fit(train_matrix)
            score = float(model.score(train_matrix))
        except Exception as exc:
            failures.append(f"seed {candidate_seed}: {exc}")
            continue
        if not np.isfinite(score):
            failures.append(f"seed {candidate_seed}: non-finite log likelihood")
            continue
        if score > best_score:
            best_model = model
            best_seed = candidate_seed
            best_score = score

    if best_model is None:
        detail = "; ".join(failures) if failures else "no successful fit"
        raise RuntimeError(f"all HMM restarts failed: {detail}")
    return best_model, best_seed, best_score


def diagonal_gaussian_log_likelihood(
    matrix: np.ndarray, means: np.ndarray, variances: np.ndarray
) -> np.ndarray:
    if (variances <= 0).any() or not np.isfinite(variances).all():
        raise ValueError("emission variances must be finite and positive")
    difference = matrix[:, None, :] - means[None, :, :]
    return -0.5 * (
        np.sum(np.log(2.0 * np.pi * variances), axis=1)[None, :]
        + np.sum((difference * difference) / variances[None, :, :], axis=2)
    )


def logsumexp(values: np.ndarray, axis: int) -> np.ndarray:
    maximum = np.max(values, axis=axis, keepdims=True)
    result = maximum + np.log(np.sum(np.exp(values - maximum), axis=axis, keepdims=True))
    return np.squeeze(result, axis=axis)


def forward_filter(model: GaussianHMM, matrix: np.ndarray) -> np.ndarray:
    start_probability = np.clip(model.startprob_, EPSILON, 1.0)
    transition = np.clip(model.transmat_, EPSILON, 1.0)
    variances = np.asarray(model.covars_)
    if variances.ndim == 3:
        variances = np.diagonal(variances, axis1=1, axis2=2)

    log_emission = diagonal_gaussian_log_likelihood(matrix, model.means_, variances)
    log_transition = np.log(transition)
    posterior = np.empty((len(matrix), model.n_components), dtype=float)

    log_alpha = np.log(start_probability) + log_emission[0]
    log_alpha -= logsumexp(log_alpha, axis=0)
    posterior[0] = np.exp(log_alpha)

    for index in range(1, len(matrix)):
        log_prior = logsumexp(log_alpha[:, None] + log_transition, axis=0)
        log_alpha = log_prior + log_emission[index]
        log_alpha -= logsumexp(log_alpha, axis=0)
        posterior[index] = np.exp(log_alpha)

    return posterior


def run_lengths(states: np.ndarray) -> dict[int, list[int]]:
    result = {state: [] for state in range(3)}
    if len(states) == 0:
        return result
    start = 0
    for index in range(1, len(states) + 1):
        if index == len(states) or states[index] != states[start]:
            result[int(states[start])].append(index - start)
            start = index
    return result


def build_diagnostics(
    features: pd.DataFrame,
    posterior: np.ndarray,
    transition: np.ndarray,
    train_rows: int,
) -> pd.DataFrame:
    dominant = posterior.argmax(axis=1)
    lengths_all = run_lengths(dominant)
    lengths_train = run_lengths(dominant[:train_rows])
    lengths_test = run_lengths(dominant[train_rows:])
    rows: list[dict[str, Any]] = []

    for state in range(3):
        mask = dominant == state
        train_mask = dominant[:train_rows] == state
        test_mask = dominant[train_rows:] == state
        state_features = features.loc[mask, FEATURE_NAMES]
        rows.append(
            {
                "state": STATE_NAMES[state],
                "state_index": state,
                "occupancy_all": float(mask.mean()),
                "occupancy_train": float(train_mask.mean()),
                "occupancy_oos": float(test_mask.mean()) if len(test_mask) else float("nan"),
                "mean_standardized_return": float(state_features["standardized_return"].mean()),
                "mean_atr_pct": float(state_features["atr_pct"].mean()),
                "mean_trend_strength": float(state_features["trend_strength"].mean()),
                "mean_duration_all": float(np.mean(lengths_all[state])) if lengths_all[state] else 0.0,
                "mean_duration_train": float(np.mean(lengths_train[state])) if lengths_train[state] else 0.0,
                "mean_duration_oos": float(np.mean(lengths_test[state])) if lengths_test[state] else 0.0,
                "self_transition_probability": float(transition[state, state]),
            }
        )
    return pd.DataFrame(rows)


def suggest_labels(diagnostics: pd.DataFrame) -> dict[str, Any]:
    score = diagnostics["mean_standardized_return"] + diagnostics["mean_trend_strength"]
    bull_index = int(score.idxmax())
    bear_index = int(score.idxmin())
    range_index = int(({0, 1, 2} - {bull_index, bear_index}).pop())

    bull = diagnostics.loc[bull_index]
    bear = diagnostics.loc[bear_index]
    range_state = diagnostics.loc[range_index]
    checks = {
        "bull_has_positive_return_and_trend": bool(
            bull["mean_standardized_return"] > 0 and bull["mean_trend_strength"] > 0
        ),
        "bear_has_negative_return_and_trend": bool(
            bear["mean_standardized_return"] < 0 and bear["mean_trend_strength"] < 0
        ),
        "range_has_weaker_absolute_trend": bool(
            abs(range_state["mean_trend_strength"])
            < max(abs(bull["mean_trend_strength"]), abs(bear["mean_trend_strength"]))
        ),
    }
    labels = {
        str(bull["state"]): "Bull",
        str(bear["state"]): "Bear",
        str(range_state["state"]): "Range",
    }
    return {
        "suggested_labels": labels,
        "interpretation_supported": all(checks.values()),
        "checks": checks,
    }


def json_ready(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    raise TypeError(f"cannot serialize {type(value).__name__}")


def main() -> int:
    args = parse_args()
    if not 0.50 <= args.train_fraction < 1.0:
        raise ValueError("train_fraction must be in [0.50, 1.0)")

    config = FeatureConfig(
        return_vol_lookback=args.return_vol_lookback,
        atr_lookback=args.atr_lookback,
        fast_ma=args.fast_ma,
        slow_ma=args.slow_ma,
    )
    raw = load_ohlc(args)
    features = calculate_features(raw, config)
    train_rows = int(len(features) * args.train_fraction)
    if train_rows < 200 or len(features) - train_rows < 50:
        raise ValueError("chronological split requires at least 200 training and 50 out-of-sample rows")

    scaler = StandardScaler()
    train_matrix = scaler.fit_transform(features.loc[: train_rows - 1, FEATURE_NAMES])
    full_matrix = scaler.transform(features[FEATURE_NAMES])

    model, selected_seed, train_log_likelihood = fit_best_model(
        train_matrix, args.seed, args.restarts
    )
    posterior = forward_filter(model, full_matrix)
    if not np.allclose(posterior.sum(axis=1), 1.0, atol=1e-10):
        raise RuntimeError("forward-filtered posterior probabilities do not sum to one")

    diagnostics = build_diagnostics(
        features, posterior, np.asarray(model.transmat_), train_rows
    )
    interpretation = suggest_labels(diagnostics)

    dominant = posterior.argmax(axis=1)
    posterior_frame = features[["date", "open", "high", "low", "close", *FEATURE_NAMES]].copy()
    for state in range(3):
        posterior_frame[f"posterior_{STATE_NAMES[state]}"] = posterior[:, state]
    posterior_frame["dominant_state"] = [STATE_NAMES[state] for state in dominant]
    posterior_frame["sample"] = np.where(
        np.arange(len(posterior_frame)) < train_rows, "train", "out_of_sample"
    )

    variances = np.asarray(model.covars_)
    if variances.ndim == 3:
        variances = np.diagonal(variances, axis1=1, axis2=2)

    output = {
        "model_version": "hidden-regime-map-v0.1-research",
        "model_type": "GaussianHMM",
        "n_states": 3,
        "state_names": STATE_NAMES,
        "covariance_type": "diag",
        "feature_names": FEATURE_NAMES,
        "feature_config": asdict(config),
        "scaler": {"mean": scaler.mean_, "scale": scaler.scale_},
        "hmm": {
            "start_probability": model.startprob_,
            "transition_matrix": model.transmat_,
            "emission_means": model.means_,
            "emission_variances": variances,
        },
        "training": {
            "symbol": args.symbol,
            "timeframe": args.timeframe,
            "input_file": str(args.input),
            "usable_rows": len(features),
            "train_rows": train_rows,
            "out_of_sample_rows": len(features) - train_rows,
            "train_fraction": args.train_fraction,
            "feature_start": features["date"].iloc[0],
            "feature_end": features["date"].iloc[-1],
            "train_end": features["date"].iloc[train_rows - 1],
            "base_seed": args.seed,
            "selected_seed": selected_seed,
            "restarts": args.restarts,
            "train_log_likelihood": train_log_likelihood,
            "converged": bool(model.monitor_.converged),
            "iterations": int(model.monitor_.iter),
        },
        "interpretation": interpretation,
        "diagnostics": diagnostics.to_dict(orient="records"),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    parameter_path = args.output_dir / "model-parameters.json"
    diagnostics_path = args.output_dir / "state-diagnostics.csv"
    posterior_path = args.output_dir / "filtered-posteriors.csv"

    parameter_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False, default=json_ready) + "\n",
        encoding="utf-8",
    )
    diagnostics.to_csv(diagnostics_path, index=False)
    posterior_frame.to_csv(posterior_path, index=False)

    print(f"trained rows: {train_rows}")
    print(f"out-of-sample rows: {len(features) - train_rows}")
    print(f"selected seed: {selected_seed}")
    print(f"train log likelihood: {train_log_likelihood:.6f}")
    print(f"interpretation supported: {interpretation['interpretation_supported']}")
    print(f"wrote: {parameter_path}")
    print(f"wrote: {diagnostics_path}")
    print(f"wrote: {posterior_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
