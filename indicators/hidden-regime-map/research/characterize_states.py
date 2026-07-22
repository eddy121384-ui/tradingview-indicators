#!/usr/bin/env python3
"""Characterize fitted HMM states without changing the model.

Forward returns and event windows are ex-post diagnostics only. They are never
used as HMM observations, training inputs, or filtering inputs.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

STATE_NAMES = ("A", "B", "C")
POSTERIOR_COLUMNS = {state: f"posterior_{state}" for state in STATE_NAMES}
TREND_THRESHOLD = 0.25
FORWARD_20D_THRESHOLD = 0.005
MIN_OOS_OCCUPANCY = 0.05


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create an auditable post-fit characterization report for HMM states."
    )
    parser.add_argument("--posteriors", type=Path, required=True)
    parser.add_argument("--diagnostics", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--events", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--symbol")
    return parser.parse_args()


def load_inputs(
    args: argparse.Namespace,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], str]:
    for path in (args.posteriors, args.diagnostics, args.model):
        if not path.exists():
            raise FileNotFoundError(f"input file not found: {path}")

    posteriors = pd.read_csv(args.posteriors)
    diagnostics = pd.read_csv(args.diagnostics)
    model = json.loads(args.model.read_text(encoding="utf-8"))

    required_posteriors = {
        "date",
        "close",
        "standardized_return",
        "atr_pct",
        "trend_strength",
        "dominant_state",
        "sample",
        *POSTERIOR_COLUMNS.values(),
    }
    missing_posteriors = sorted(required_posteriors - set(posteriors.columns))
    if missing_posteriors:
        raise ValueError(
            "posteriors missing required columns: " + ", ".join(missing_posteriors)
        )

    required_diagnostics = {
        "state",
        "occupancy_all",
        "occupancy_train",
        "occupancy_oos",
        "mean_duration_all",
        "mean_duration_oos",
        "self_transition_probability",
    }
    missing_diagnostics = sorted(required_diagnostics - set(diagnostics.columns))
    if missing_diagnostics:
        raise ValueError(
            "diagnostics missing required columns: " + ", ".join(missing_diagnostics)
        )

    posteriors["date"] = pd.to_datetime(posteriors["date"], errors="raise", utc=True)
    posteriors = posteriors.sort_values("date").reset_index(drop=True)

    numeric_columns = [
        "close",
        "standardized_return",
        "atr_pct",
        "trend_strength",
        *POSTERIOR_COLUMNS.values(),
    ]
    for column in numeric_columns:
        posteriors[column] = pd.to_numeric(posteriors[column], errors="raise")

    posterior_matrix = posteriors[list(POSTERIOR_COLUMNS.values())].to_numpy()
    if not np.isfinite(posterior_matrix).all():
        raise ValueError("posterior columns contain non-finite values")
    if (posterior_matrix < -1e-12).any():
        raise ValueError("posterior columns contain negative values")
    if not np.allclose(posterior_matrix.sum(axis=1), 1.0, atol=1e-8):
        raise ValueError("posterior probabilities do not sum to one")

    if set(diagnostics["state"]) != set(STATE_NAMES):
        raise ValueError("diagnostics must contain exactly states A, B, and C")
    diagnostics = diagnostics.set_index("state").loc[list(STATE_NAMES)].reset_index()

    symbol = args.symbol or str(model.get("training", {}).get("symbol", "UNKNOWN"))
    return posteriors, diagnostics, model, symbol.upper()


def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    valid = values.notna() & weights.notna() & np.isfinite(values) & np.isfinite(weights)
    if not valid.any():
        return float("nan")
    selected_weights = weights.loc[valid].clip(lower=0.0)
    total = float(selected_weights.sum())
    if total <= 0.0:
        return float("nan")
    return float(np.average(values.loc[valid], weights=selected_weights))


def weighted_rate(condition: pd.Series, weights: pd.Series, valid: pd.Series) -> float:
    mask = valid & weights.notna() & np.isfinite(weights)
    if not mask.any():
        return float("nan")
    selected_weights = weights.loc[mask].clip(lower=0.0)
    total = float(selected_weights.sum())
    if total <= 0.0:
        return float("nan")
    return float(np.average(condition.loc[mask].astype(float), weights=selected_weights))


def add_forward_diagnostics(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["forward_5d_return"] = result["close"].shift(-5) / result["close"] - 1.0
    result["forward_20d_return"] = result["close"].shift(-20) / result["close"] - 1.0
    return result


def direction_from_metrics(trend: float, forward_20d: float) -> tuple[str, list[str]]:
    contradictions: list[str] = []
    trend_direction = (
        "positive"
        if trend > TREND_THRESHOLD
        else "negative"
        if trend < -TREND_THRESHOLD
        else "flat"
    )
    forward_direction = (
        "positive"
        if forward_20d > FORWARD_20D_THRESHOLD
        else "negative"
        if forward_20d < -FORWARD_20D_THRESHOLD
        else "flat"
    )

    if trend_direction in {"positive", "negative"} and forward_direction in {
        "positive",
        "negative",
    }:
        if trend_direction == forward_direction:
            return trend_direction, contradictions
        contradictions.append("trend and 20-day forward return point in opposite directions")
        return "mixed", contradictions

    if trend_direction in {"positive", "negative"}:
        return trend_direction, contradictions
    if forward_direction in {"positive", "negative"}:
        contradictions.append("direction comes from forward-return diagnostics, not trend")
        return forward_direction, contradictions
    return "flat", contradictions


def descriptor(direction: str, volatility_bucket: str) -> str:
    mapping = {
        ("positive", "high"): "upside stress",
        ("positive", "normal"): "advance",
        ("positive", "low"): "calm advance",
        ("negative", "high"): "downside stress",
        ("negative", "normal"): "decline",
        ("negative", "low"): "orderly decline",
        ("flat", "high"): "volatile range",
        ("flat", "normal"): "range",
        ("flat", "low"): "quiet range",
        ("mixed", "high"): "two-sided stress",
        ("mixed", "normal"): "mixed regime",
        ("mixed", "low"): "ambiguous regime",
    }
    return mapping[(direction, volatility_bucket)]


def characterize_states(
    frame: pd.DataFrame, diagnostics: pd.DataFrame
) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    diagnostic_lookup = diagnostics.set_index("state")

    for state in STATE_NAMES:
        weights = frame[POSTERIOR_COLUMNS[state]]
        row: dict[str, Any] = {
            "state": state,
            "occupancy_all": float(diagnostic_lookup.loc[state, "occupancy_all"]),
            "occupancy_train": float(diagnostic_lookup.loc[state, "occupancy_train"]),
            "occupancy_oos": float(diagnostic_lookup.loc[state, "occupancy_oos"]),
            "mean_duration_all": float(
                diagnostic_lookup.loc[state, "mean_duration_all"]
            ),
            "mean_duration_oos": float(
                diagnostic_lookup.loc[state, "mean_duration_oos"]
            ),
            "self_transition_probability": float(
                diagnostic_lookup.loc[state, "self_transition_probability"]
            ),
        }

        for sample_name, mask in {
            "all": pd.Series(True, index=frame.index),
            "train": frame["sample"].eq("train"),
            "oos": frame["sample"].eq("out_of_sample"),
        }.items():
            sample_weights = weights.where(mask, 0.0)
            row[f"trend_{sample_name}"] = weighted_mean(
                frame["trend_strength"], sample_weights
            )
            row[f"atr_pct_{sample_name}"] = weighted_mean(
                frame["atr_pct"], sample_weights
            )
            row[f"standardized_return_{sample_name}"] = weighted_mean(
                frame["standardized_return"], sample_weights
            )
            row[f"forward_5d_{sample_name}"] = weighted_mean(
                frame["forward_5d_return"], sample_weights
            )
            row[f"forward_20d_{sample_name}"] = weighted_mean(
                frame["forward_20d_return"], sample_weights
            )
            valid_20d = frame["forward_20d_return"].notna() & mask
            row[f"forward_20d_positive_rate_{sample_name}"] = weighted_rate(
                frame["forward_20d_return"] > 0.0, sample_weights, valid_20d
            )

        rows.append(row)

    result = pd.DataFrame(rows)
    volatility_order = result["atr_pct_all"].rank(method="first")
    result["volatility_bucket"] = volatility_order.map(
        {1.0: "low", 2.0: "normal", 3.0: "high"}
    )

    descriptions: dict[str, Any] = {}
    for index, row in result.iterrows():
        direction, contradictions = direction_from_metrics(
            float(row["trend_all"]), float(row["forward_20d_all"])
        )
        oos_direction, _ = direction_from_metrics(
            float(row["trend_oos"]), float(row["forward_20d_oos"])
        )
        if oos_direction != direction and oos_direction != "flat":
            contradictions.append(
                f"out-of-sample direction is {oos_direction}, versus {direction} overall"
            )
        if float(row["occupancy_oos"]) < MIN_OOS_OCCUPANCY:
            contradictions.append("state has low out-of-sample occupancy")

        confidence = "high"
        if contradictions:
            confidence = "medium"
        if direction == "mixed" or len(contradictions) >= 2:
            confidence = "low"

        label = descriptor(direction, str(row["volatility_bucket"]))
        result.loc[index, "direction"] = direction
        result.loc[index, "oos_direction"] = oos_direction
        result.loc[index, "descriptive_label"] = label
        result.loc[index, "confidence"] = confidence
        result.loc[index, "contradictions"] = "; ".join(contradictions)

        descriptions[str(row["state"])] = {
            "label": label,
            "direction": direction,
            "volatility": str(row["volatility_bucket"]),
            "confidence": confidence,
            "contradictions": contradictions,
        }

    return result, descriptions


def load_events(path: Path | None, symbol: str) -> list[dict[str, str]]:
    if path is None:
        return []
    if not path.exists():
        raise FileNotFoundError(f"event file not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("event file must contain a JSON list")

    events: list[dict[str, str]] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("each event entry must be an object")
        required = {"symbol", "name", "start", "end", "context"}
        missing = required - set(item)
        if missing:
            raise ValueError(f"event entry missing: {', '.join(sorted(missing))}")
        if str(item["symbol"]).upper() == symbol:
            events.append({key: str(item[key]) for key in required})
    return events


def analyze_events(
    frame: pd.DataFrame, events: list[dict[str, str]]
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for event in events:
        start = pd.Timestamp(event["start"], tz="UTC")
        end = pd.Timestamp(event["end"], tz="UTC")
        window = frame.loc[frame["date"].between(start, end)].copy()
        if window.empty:
            rows.append(
                {
                    "event": event["name"],
                    "start": event["start"],
                    "end": event["end"],
                    "context": event["context"],
                    "bars": 0,
                    "state": "NONE",
                    "average_posterior": float("nan"),
                    "dominant_share": float("nan"),
                    "window_return": float("nan"),
                }
            )
            continue

        window_return = float(window["close"].iloc[-1] / window["close"].iloc[0] - 1.0)
        for state in STATE_NAMES:
            rows.append(
                {
                    "event": event["name"],
                    "start": event["start"],
                    "end": event["end"],
                    "context": event["context"],
                    "bars": len(window),
                    "state": state,
                    "average_posterior": float(
                        window[POSTERIOR_COLUMNS[state]].mean()
                    ),
                    "dominant_share": float(
                        window["dominant_state"].eq(state).mean()
                    ),
                    "window_return": window_return,
                }
            )
    return pd.DataFrame(rows)


def markdown_report(
    symbol: str,
    characterization: pd.DataFrame,
    descriptions: dict[str, Any],
    event_analysis: pd.DataFrame,
) -> str:
    lines = [
        f"# {symbol} Hidden Regime state characterization",
        "",
        "> Forward returns and historical event windows are ex-post diagnostics only. "
        "They are not model inputs and must not be used by live Pine inference.",
        "",
        "## State summary",
        "",
        "| State | Description | Confidence | Volatility | Trend | OOS trend | 20d fwd | OOS 20d fwd | OOS occupancy | Mean duration | Self-transition |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in characterization.to_dict(orient="records"):
        lines.append(
            "| {state} | {descriptive_label} | {confidence} | {volatility_bucket} | "
            "{trend_all:.3f} | {trend_oos:.3f} | {forward_20d_all:.3%} | "
            "{forward_20d_oos:.3%} | {occupancy_oos:.3f} | {mean_duration_all:.1f} | "
            "{self_transition_probability:.3f} |".format(**row)
        )

    lines.extend(["", "## Contradictions and caveats", ""])
    for state in STATE_NAMES:
        caveats = descriptions[state]["contradictions"]
        if caveats:
            lines.append(f"- **State {state}:** " + "; ".join(caveats) + ".")
        else:
            lines.append(f"- **State {state}:** no directional contradiction detected.")

    if not event_analysis.empty:
        lines.extend(
            [
                "",
                "## Historical event windows",
                "",
                "| Event | Context | Bars | Window return | Leading state | Avg posterior | Dominant share |",
                "|---|---|---:|---:|---|---:|---:|",
            ]
        )
        for event_name, group in event_analysis.groupby("event", sort=False):
            valid = group.loc[group["state"] != "NONE"]
            first = group.iloc[0]
            if valid.empty:
                lines.append(
                    f"| {event_name} | {first['context']} | 0 | n/a | n/a | n/a | n/a |"
                )
                continue
            leader = valid.sort_values("average_posterior", ascending=False).iloc[0]
            lines.append(
                "| {event} | {context} | {bars} | {window_return:.2%} | {state} | "
                "{average_posterior:.3f} | {dominant_share:.3f} |".format(
                    event=event_name,
                    context=leader["context"],
                    bars=int(leader["bars"]),
                    window_return=leader["window_return"],
                    state=leader["state"],
                    average_posterior=leader["average_posterior"],
                    dominant_share=leader["dominant_share"],
                )
            )

    lines.extend(
        [
            "",
            "## Decision boundary",
            "",
            "These descriptions are asset- and fit-specific. A state may be named for its "
            "dominant statistical character, but mixed or contradictory evidence must remain visible. "
            "This report does not authorize Pine implementation by itself.",
            "",
        ]
    )
    return "\n".join(lines)


def json_ready(value: Any) -> Any:
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, float) and math.isnan(value):
        return None
    raise TypeError(f"cannot serialize {type(value).__name__}")


def main() -> int:
    args = parse_args()
    posteriors, diagnostics, model, symbol = load_inputs(args)
    enriched = add_forward_diagnostics(posteriors)
    characterization, descriptions = characterize_states(enriched, diagnostics)
    events = load_events(args.events, symbol)
    event_analysis = analyze_events(enriched, events)

    output = {
        "symbol": symbol,
        "model_version": model.get("model_version"),
        "causality_boundary": {
            "forward_returns": "ex-post diagnostic only",
            "event_windows": "ex-post diagnostic only",
            "model_or_filter_inputs_changed": False,
        },
        "thresholds": {
            "trend_strength": TREND_THRESHOLD,
            "forward_20d_return": FORWARD_20D_THRESHOLD,
            "minimum_oos_occupancy": MIN_OOS_OCCUPANCY,
        },
        "state_descriptions": descriptions,
        "states": characterization.to_dict(orient="records"),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    characterization.to_csv(
        args.output_dir / "state-characterization.csv", index=False
    )
    event_analysis.to_csv(args.output_dir / "event-window-analysis.csv", index=False)
    (args.output_dir / "characterization.json").write_text(
        json.dumps(output, indent=2, ensure_ascii=False, default=json_ready) + "\n",
        encoding="utf-8",
    )
    report = markdown_report(symbol, characterization, descriptions, event_analysis)
    (args.output_dir / "characterization.md").write_text(report, encoding="utf-8")

    print(report)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
