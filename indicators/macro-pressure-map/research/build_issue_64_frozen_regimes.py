#!/usr/bin/env python3
"""Derive Issue #64 frozen 3x3 regimes from the Issue #59 Pine log.

The raw TradingView log is operator-local and is not committed. The expected
SHA-256 is frozen here so this script can reproduce the committed transition
artifact and deterministic raw-axis audit checkpoints from exactly the evidence
already used in Issue #59.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pandas as pd

EXPECTED_SOURCE_SHA256 = "c0220d4974b2fd0154c4cf8f33b4b3effb27a58e21ee96a1b0109011ce638e3d"
EMA_ALPHA = 2.0 / (5.0 + 1.0)
AUDIT_STRIDE = 100
REGIME_NAMES = {
    1: "Goldilocks / Disinflationary Expansion",
    2: "Benign Expansion / Stable Inflation",
    3: "Reflation / Inflation Rising",
    4: "Disinflationary Drift",
    5: "Neutral / Range-bound Macro",
    6: "Inflation Pressure without Growth Confirmation",
    7: "Slowdown / Disinflation",
    8: "Growth Slowdown / Stable Inflation",
    9: "Stagflation Pressure",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_message(message: str) -> dict[str, str]:
    parts = str(message).split("|")
    if not parts or parts[0] != "MPM_PARITY":
        raise ValueError("unexpected Pine log message prefix")
    result: dict[str, str] = {}
    for part in parts[1:]:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        result[key] = value
    required = {"date", "tv_plot_gpi", "tv_plot_ipi", "tv_plot_fcpi"}
    missing = required.difference(result)
    if missing:
        raise ValueError(f"Pine log row missing fields: {sorted(missing)}")
    return result


def regime_id(gpi: float, ipi: float) -> int:
    gp, gn = gpi > 10.0, gpi < -10.0
    ip, inn = ipi > 10.0, ipi < -10.0
    if gp and inn:
        return 1
    if gp and not ip and not inn:
        return 2
    if gp and ip:
        return 3
    if not gp and not gn and inn:
        return 4
    if not gp and not gn and not ip and not inn:
        return 5
    if not gp and not gn and ip:
        return 6
    if gn and inn:
        return 7
    if gn and not ip and not inn:
        return 8
    return 9


def derive_daily_regimes(log_path: Path) -> pd.DataFrame:
    actual_sha = sha256_file(log_path)
    if actual_sha != EXPECTED_SOURCE_SHA256:
        raise ValueError(
            f"Pine log SHA-256 mismatch: expected {EXPECTED_SOURCE_SHA256}, got {actual_sha}"
        )

    source = pd.read_csv(log_path)
    if "訊息" not in source.columns:
        raise ValueError("Pine log is missing the 訊息 column")
    parsed = pd.DataFrame([parse_message(message) for message in source["訊息"]])
    parsed["date"] = pd.to_datetime(parsed["date"], errors="raise").dt.normalize()
    for column in ("tv_plot_gpi", "tv_plot_ipi", "tv_plot_fcpi"):
        parsed[column] = pd.to_numeric(parsed[column], errors="raise").astype(float)

    for date, group in parsed.groupby("date"):
        if len(group) <= 1:
            continue
        unique = group[["tv_plot_gpi", "tv_plot_ipi", "tv_plot_fcpi"]].drop_duplicates()
        if len(unique) != 1:
            raise ValueError(f"conflicting duplicate Pine rows for {date.date()}")

    plots = (
        parsed.sort_values("date")
        .drop_duplicates("date", keep="last")
        .set_index("date")[["tv_plot_gpi", "tv_plot_ipi", "tv_plot_fcpi"]]
    )
    daily = pd.DataFrame(index=plots.index)
    for axis, plot_column in (
        ("GPI", "tv_plot_gpi"),
        ("IPI", "tv_plot_ipi"),
        ("FCPI", "tv_plot_fcpi"),
    ):
        daily[axis] = (
            plots[plot_column] - (1.0 - EMA_ALPHA) * plots[plot_column].shift(1)
        ) / EMA_ALPHA

    daily = daily.dropna()
    daily["regime_id"] = [regime_id(g, i) for g, i in zip(daily["GPI"], daily["IPI"])]
    return daily


def derive_transitions(daily: pd.DataFrame) -> pd.DataFrame:
    changed = daily["regime_id"].ne(daily["regime_id"].shift(1))
    transitions = daily.loc[changed, ["regime_id"]].reset_index()
    return transitions.rename(columns={"date": "start_date"})


def derive_axis_audit(daily: pd.DataFrame, stride: int = AUDIT_STRIDE) -> pd.DataFrame:
    """Persist deterministic raw-axis checkpoints without committing the local log."""
    if stride < 1:
        raise ValueError("audit stride must be positive")
    positions = list(range(0, len(daily), stride))
    if positions[-1] != len(daily) - 1:
        positions.append(len(daily) - 1)
    audit = daily.iloc[positions][["GPI", "IPI", "FCPI", "regime_id"]].reset_index()
    return audit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Derive Issue #64 regimes from frozen Pine log")
    parser.add_argument("--pine-log", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="transition CSV output")
    parser.add_argument("--axis-audit-output", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    daily = derive_daily_regimes(args.pine_log)
    transitions = derive_transitions(daily)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    transitions.to_csv(args.output, index=False, date_format="%Y-%m-%d")
    if args.axis_audit_output is not None:
        audit = derive_axis_audit(daily)
        args.axis_audit_output.parent.mkdir(parents=True, exist_ok=True)
        audit.to_csv(
            args.axis_audit_output,
            index=False,
            date_format="%Y-%m-%d",
            float_format="%.8f",
        )
    print(
        f"derived_rows={len(daily)} transitions={len(transitions)} "
        f"first={daily.index.min().date()} last={daily.index.max().date()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
