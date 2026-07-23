#!/usr/bin/env python3
"""Compare a TradingView Hidden Regime export with frozen Python checkpoints."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import pandas as pd

FIELD_SUFFIXES = {
    "close": "HRM Adjusted Close",
    "standardized_return": "HRM Standardized Return",
    "atr_pct": "HRM ATR Percent",
    "trend_strength": "HRM Trend Strength",
    "posterior_A": "HRM Posterior A",
    "posterior_B": "HRM Posterior B",
    "posterior_C": "HRM Posterior C",
    "probability_sum": "HRM Probability Sum",
}
FEATURE_FIELDS = ("close", "standardized_return", "atr_pct", "trend_strength")
POSTERIOR_FIELDS = ("posterior_A", "posterior_B", "posterior_C")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare TradingView-exported Pine values with SPY parity checkpoints."
    )
    parser.add_argument("--export", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--date-column")
    parser.add_argument("--feature-tolerance", type=float)
    parser.add_argument("--posterior-tolerance", type=float)
    return parser.parse_args()


def resolve_date_column(frame: pd.DataFrame, requested: str | None) -> str:
    if requested:
        if requested not in frame.columns:
            raise ValueError(f"date column not found: {requested}")
        return requested
    candidates = [column for column in frame.columns if column.casefold() in {"time", "date"}]
    if len(candidates) != 1:
        raise ValueError(
            "could not uniquely resolve date column; pass --date-column. "
            f"Candidates: {candidates or 'none'}"
        )
    return candidates[0]


def resolve_value_column(frame: pd.DataFrame, suffix: str) -> str:
    if suffix in frame.columns:
        return suffix
    matches = [
        column
        for column in frame.columns
        if str(column).casefold().endswith(suffix.casefold())
    ]
    if len(matches) != 1:
        raise ValueError(
            f"could not uniquely resolve export column ending with {suffix!r}: "
            f"{matches or 'none'}"
        )
    return matches[0]


def finite_float(value: Any, label: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} is not finite")
    return number


def dominant_state(row: dict[str, float]) -> str:
    return max("ABC", key=lambda state: row[f"posterior_{state}"])


def compare(
    export_path: Path,
    fixture_path: Path,
    date_column: str | None = None,
) -> dict[str, Any]:
    if not export_path.exists():
        raise FileNotFoundError(f"export not found: {export_path}")
    if not fixture_path.exists():
        raise FileNotFoundError(f"fixture not found: {fixture_path}")

    frame = pd.read_csv(export_path)
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    checkpoints = fixture.get("checkpoints")
    if not isinstance(checkpoints, list) or not checkpoints:
        raise ValueError("fixture must contain a non-empty checkpoints list")

    resolved_date = resolve_date_column(frame, date_column)
    resolved_columns = {
        field: resolve_value_column(frame, suffix)
        for field, suffix in FIELD_SUFFIXES.items()
    }
    frame["_date"] = pd.to_datetime(frame[resolved_date], errors="raise", utc=True).dt.date
    if frame["_date"].duplicated().any():
        duplicates = frame.loc[frame["_date"].duplicated(), "_date"].astype(str).tolist()
        raise ValueError(f"export contains duplicate checkpoint dates: {duplicates[:5]}")
    indexed = frame.set_index("_date")

    rows: list[dict[str, Any]] = []
    missing_dates: list[str] = []
    for checkpoint in checkpoints:
        date_text = str(checkpoint["date"])
        date_value = pd.Timestamp(date_text).date()
        if date_value not in indexed.index:
            missing_dates.append(date_text)
            continue
        export_row = indexed.loc[date_value]
        actual = {
            field: finite_float(export_row[column], f"{date_text} {field}")
            for field, column in resolved_columns.items()
        }
        expected = {
            field: finite_float(checkpoint[field], f"fixture {date_text} {field}")
            for field in (*FEATURE_FIELDS, *POSTERIOR_FIELDS)
        }
        feature_errors = {
            field: abs(actual[field] - expected[field]) for field in FEATURE_FIELDS
        }
        posterior_errors = {
            field: abs(actual[field] - expected[field]) for field in POSTERIOR_FIELDS
        }
        actual_dominant = dominant_state(actual)
        rows.append(
            {
                "date": date_text,
                "expected_dominant_state": checkpoint["dominant_state"],
                "actual_dominant_state": actual_dominant,
                "dominant_state_match": actual_dominant == checkpoint["dominant_state"],
                "feature_errors": feature_errors,
                "posterior_errors": posterior_errors,
                "probability_sum": actual["probability_sum"],
                "probability_sum_error": abs(actual["probability_sum"] - 1.0),
                "expected": expected,
                "actual": actual,
            }
        )

    if missing_dates:
        raise ValueError("export is missing checkpoint dates: " + ", ".join(missing_dates))

    max_feature_errors = {
        field: max(row["feature_errors"][field] for row in rows)
        for field in FEATURE_FIELDS
    }
    max_posterior_errors = {
        field: max(row["posterior_errors"][field] for row in rows)
        for field in POSTERIOR_FIELDS
    }
    return {
        "fixture_id": fixture.get("fixture_id"),
        "profile_id": fixture.get("profile_id"),
        "export_file": str(export_path),
        "resolved_date_column": resolved_date,
        "resolved_value_columns": resolved_columns,
        "checkpoint_count": len(rows),
        "dominant_state_matches": sum(row["dominant_state_match"] for row in rows),
        "max_feature_errors": max_feature_errors,
        "max_posterior_errors": max_posterior_errors,
        "max_probability_sum_error": max(row["probability_sum_error"] for row in rows),
        "rows": rows,
    }


def markdown_report(result: dict[str, Any]) -> str:
    lines = [
        f"# Pine parity report — {result['profile_id']}",
        "",
        f"- Checkpoints: {result['checkpoint_count']}",
        f"- Dominant-state matches: {result['dominant_state_matches']}/{result['checkpoint_count']}",
        f"- Maximum probability-sum error: {result['max_probability_sum_error']:.12g}",
        "",
        "## Maximum feature errors",
        "",
    ]
    lines.extend(
        f"- {field}: {error:.12g}"
        for field, error in result["max_feature_errors"].items()
    )
    lines.extend(["", "## Maximum posterior errors", ""])
    lines.extend(
        f"- {field}: {error:.12g}"
        for field, error in result["max_posterior_errors"].items()
    )
    lines.extend(
        [
            "",
            "## Checkpoints",
            "",
            "| Date | Expected | Actual | Match | Max feature error | Max posterior error | Sum error |",
            "|---|---|---|---|---:|---:|---:|",
        ]
    )
    for row in result["rows"]:
        lines.append(
            "| {date} | {expected} | {actual} | {match} | {feature:.6g} | "
            "{posterior:.6g} | {sum_error:.6g} |".format(
                date=row["date"],
                expected=row["expected_dominant_state"],
                actual=row["actual_dominant_state"],
                match="yes" if row["dominant_state_match"] else "no",
                feature=max(row["feature_errors"].values()),
                posterior=max(row["posterior_errors"].values()),
                sum_error=row["probability_sum_error"],
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    if args.feature_tolerance is not None and args.feature_tolerance < 0.0:
        raise ValueError("feature tolerance must be non-negative")
    if args.posterior_tolerance is not None and args.posterior_tolerance < 0.0:
        raise ValueError("posterior tolerance must be non-negative")

    result = compare(args.export, args.fixture, args.date_column)
    result["requested_tolerances"] = {
        "feature": args.feature_tolerance,
        "posterior": args.posterior_tolerance,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "pine-parity-report.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "pine-parity-report.md").write_text(
        markdown_report(result), encoding="utf-8"
    )

    feature_failed = args.feature_tolerance is not None and any(
        error > args.feature_tolerance
        for error in result["max_feature_errors"].values()
    )
    posterior_failed = args.posterior_tolerance is not None and any(
        error > args.posterior_tolerance
        for error in result["max_posterior_errors"].values()
    )
    print(markdown_report(result), end="")
    return 1 if feature_failed or posterior_failed else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError, KeyError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
