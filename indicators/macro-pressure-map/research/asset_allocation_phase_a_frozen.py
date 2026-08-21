#!/usr/bin/env python3
"""Issue #64 Phase A using the frozen TradingView-derived V6.6 regime history."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from asset_allocation_phase_a import (
    REGIMES,
    _json_safe,
    build_outcome_prices,
    regime_episode_rows,
    summarize_episodes,
    summarize_forward_returns,
    summarize_next_day_risk,
    write_markdown_report,
)

HERE = Path(__file__).resolve().parent
DEFAULT_TRANSITIONS = HERE / "data" / "issue-64-frozen-regime-transitions.csv"
DEFAULT_MANIFEST = HERE / "data" / "issue-64-frozen-regime-transitions-manifest.json"
EXPECTED_TRANSITION_SHA256 = "80446bbcb91be8b18eb0b95e62466edf892e4c04087696a04532f0fe214698af"
SIGNAL_LAST_DATE = pd.Timestamp("2026-08-14")
REGIME_ID_MAP = {index + 1: name for index, name in enumerate(REGIMES)}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _datetime_ns(values) -> pd.DatetimeIndex:
    """Normalize date-only join keys to one explicit nanosecond dtype."""
    return pd.DatetimeIndex(pd.to_datetime(values, errors="raise")).normalize().astype("datetime64[ns]")


def load_frozen_transitions(path: Path = DEFAULT_TRANSITIONS) -> pd.DataFrame:
    actual_sha = sha256_file(path)
    if actual_sha != EXPECTED_TRANSITION_SHA256:
        raise ValueError(
            f"frozen transition SHA mismatch: expected {EXPECTED_TRANSITION_SHA256}, got {actual_sha}"
        )
    frame = pd.read_csv(path)
    if list(frame.columns) != ["start_date", "regime_id"]:
        raise ValueError(f"unexpected transition columns: {list(frame.columns)}")
    frame["start_date"] = _datetime_ns(frame["start_date"])
    frame["regime_id"] = pd.to_numeric(frame["regime_id"], errors="raise").astype(int)
    if frame.empty or frame["start_date"].duplicated().any() or not frame["start_date"].is_monotonic_increasing:
        raise ValueError("frozen transitions must contain unique, increasing dates")
    if not frame["regime_id"].isin(REGIME_ID_MAP).all():
        raise ValueError("frozen transitions contain an unknown regime id")
    if frame["regime_id"].eq(frame["regime_id"].shift(1)).any():
        raise ValueError("frozen transitions contain redundant consecutive regime ids")
    return frame


def map_regimes_to_outcome_calendar(
    prices: pd.DataFrame,
    transitions: pd.DataFrame,
    signal_last_date: pd.Timestamp = SIGNAL_LAST_DATE,
) -> pd.DataFrame:
    """Map known regimes to the outcome calendar without carrying them past signal cutoff."""
    normalized_price_index = _datetime_ns(prices.index)
    lookup = pd.DataFrame({"date": normalized_price_index})
    right = transitions.copy()
    right["start_date"] = _datetime_ns(right["start_date"])
    mapped = pd.merge_asof(
        lookup.sort_values("date"),
        right.sort_values("start_date"),
        left_on="date",
        right_on="start_date",
        direction="backward",
        allow_exact_matches=True,
    )
    mapped.index = pd.DatetimeIndex(mapped["date"])
    history = pd.DataFrame(index=normalized_price_index)
    history["core_regime"] = mapped["regime_id"].map(REGIME_ID_MAP).reindex(normalized_price_index)
    history.loc[history.index > pd.Timestamp(signal_last_date), "core_regime"] = pd.NA
    return history


def run_phase_a_frozen(start: str, end: str | None, output_dir: Path) -> dict:
    transitions = load_frozen_transitions()
    source_manifest = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
    prices, price_manifest = build_outcome_prices(start, end)
    prices.index = _datetime_ns(prices.index)
    history = map_regimes_to_outcome_calendar(prices, transitions)
    finite = history["core_regime"].isin(REGIMES)
    finite_history = history.loc[finite].copy()
    if finite_history.empty:
        raise RuntimeError("no frozen regime dates overlap the outcome price calendar")

    episodes = regime_episode_rows(finite_history["core_regime"])
    episode_summary = summarize_episodes(finite_history["core_regime"])
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
        "schema_version": 2,
        "issue": 64,
        "phase": "A",
        "purpose": "descriptive regime-conditioned SPY/TLT/GLD asset-allocation diagnostics",
        "signal_source": source_manifest,
        "signal_transition_sha256": sha256_file(DEFAULT_TRANSITIONS),
        "signal_first_mapped_date": finite_history.index.min().date().isoformat(),
        "signal_last_mapped_date": finite_history.index.max().date().isoformat(),
        "signal_cutoff": SIGNAL_LAST_DATE.date().isoformat(),
        "signal_after_cutoff_forward_filled": False,
        "outcome_data": price_manifest,
        "outcome_prices_after_signal_cutoff_may_only_complete_prior_forward_windows": True,
        "common_finite_regime_rows": int(finite.sum()),
        "inference_contract": (
            "All-observation means/ranks are descriptive. Bootstrap 95% intervals use deterministic "
            "horizon-embargoed starts within each regime; overlapping forward windows are not treated as independent."
        ),
        "evidence_status": "development_or_reused_exploratory; not newly untouched OOS",
        "allocation_mapping_selected": False,
        "v66_parameters_modified": False,
    }
    (output_dir / "phase-a-manifest.json").write_text(
        json.dumps(_json_safe(manifest), indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    write_markdown_report(
        output_dir / "phase-a-report.md",
        history=finite_history,
        episode_summary=episode_summary,
        points=points,
        inference=inference,
    )
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Issue #64 Phase A from frozen TradingView regimes")
    parser.add_argument("--start", default="2007-01-01")
    parser.add_argument("--end", default=None, help="Exclusive outcome-price end date")
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = run_phase_a_frozen(args.start, args.end, args.output_dir)
    print(json.dumps({
        "phase": manifest["phase"],
        "rows": manifest["common_finite_regime_rows"],
        "first_date": manifest["signal_first_mapped_date"],
        "last_signal_date": manifest["signal_last_mapped_date"],
        "output_dir": str(args.output_dir),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
