#!/usr/bin/env python3
"""Issue #57 burned-data exit-policy comparison for the existing v0.6 indicator.

Question
--------
For actionable Top-2 episodes that survive long enough to develop a first
2+ deterioration warning, does exiting on that warning improve the actual
position-management outcome versus waiting until the actionable regime has
visibly ended?

This is an exploratory behavior study on already-burned FX fixtures. It does
not optimize the indicator and is not independent OOS validation.

Execution convention
--------------------
Signals are assumed known only after a daily bar closes.
- episode entry: next open after the actionable Top-2 episode first appears;
- warning exit: next open after the first 2+ simultaneous decay warning;
- regime-change exit: the actionable episode ends at bar e, the first changed
  bar e+1 confirms that fact at its close, so exit at open e+2.

The same entry is used for both policies. The key comparison is also reported
from warning-exit open to regime-change-exit open, which isolates only the
incremental decision to hold versus leave.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from diagnose_consensus_formation_and_formal_lag import (
    compute_v06,
    consensus_components,
    load_burned_pairs,
)
from diagnose_transition_formation_and_regime_decay import (
    HEALTH_LOOKBACK,
    extract_action_episodes,
    normalized_entropy,
    opposite_structural_pressure,
)


HERE = Path(__file__).resolve().parent
WARNING_COUNT = 2


def median_or_none(values: list[float]) -> float | None:
    return float(np.median(values)) if values else None


def mean_or_none(values: list[float]) -> float | None:
    return float(np.mean(values)) if values else None


def directional_return(entry: float, exit_price: float, direction: float) -> float | None:
    if not all(np.isfinite(v) and v > 0.0 for v in (entry, exit_price)):
        return None
    if direction > 0.0:
        return float(exit_price / entry - 1.0)
    if direction < 0.0:
        return float(entry / exit_price - 1.0)
    return None


def trade_excursions(
    frame: pd.DataFrame,
    entry_index: int,
    exit_index: int,
    direction: float,
) -> tuple[float | None, float | None]:
    """Return (MAE, MFE) from entry open until just before exit open."""
    if entry_index < 0 or exit_index <= entry_index or exit_index > len(frame):
        return None, None
    open_ = pd.to_numeric(frame["open"], errors="coerce").to_numpy(float)
    high = pd.to_numeric(frame["high"], errors="coerce").to_numpy(float)
    low = pd.to_numeric(frame["low"], errors="coerce").to_numpy(float)
    base = open_[entry_index]
    if not np.isfinite(base) or base <= 0.0:
        return None, None
    highs = high[entry_index:exit_index]
    lows = low[entry_index:exit_index]
    if len(highs) == 0 or not np.any(np.isfinite(highs)) or not np.any(np.isfinite(lows)):
        return None, None
    best_high = float(np.nanmax(highs))
    worst_low = float(np.nanmin(lows))
    if direction > 0.0:
        mae = max(0.0, 1.0 - worst_low / base)
        mfe = max(0.0, best_high / base - 1.0)
    elif direction < 0.0:
        worst_high = best_high
        best_low = worst_low
        mae = max(0.0, 1.0 - base / worst_high) if worst_high > 0.0 else None
        mfe = max(0.0, base / best_low - 1.0) if best_low > 0.0 else None
    else:
        return None, None
    return float(mae), float(mfe)


def first_warning_index(
    start: int,
    end: int,
    strength: np.ndarray,
    entropy: np.ndarray,
    opposite: np.ndarray,
) -> int | None:
    for i in range(start + HEALTH_LOOKBACK, end + 1):
        changes = (
            float(strength[i] - strength[i - HEALTH_LOOKBACK]),
            float(entropy[i] - entropy[i - HEALTH_LOOKBACK]),
            float(opposite[i] - opposite[i - HEALTH_LOOKBACK]),
        )
        if not all(np.isfinite(v) for v in changes):
            continue
        warning_count = int(changes[0] < 0.0) + int(changes[1] > 0.0) + int(changes[2] > 0.0)
        if warning_count >= WARNING_COUNT:
            return i
    return None


def extract_exit_events(frame: pd.DataFrame, model: pd.DataFrame) -> list[dict[str, object]]:
    direction, strength, _, _ = consensus_components(model)
    entropy = normalized_entropy(model)
    opposite = opposite_structural_pressure(model, direction)
    episodes = extract_action_episodes(direction)
    open_ = pd.to_numeric(frame["open"], errors="coerce").to_numpy(float)

    rows: list[dict[str, object]] = []
    for episode in episodes:
        start = int(episode["start"])
        end = int(episode["end"])
        d = float(episode["direction"])
        warning = first_warning_index(start, end, strength, entropy, opposite)
        if warning is None:
            continue

        entry_index = start + 1
        warning_exit_index = warning + 1
        changed_bar_index = end + 1
        regime_exit_index = end + 2
        if regime_exit_index >= len(frame) or warning_exit_index >= len(frame) or entry_index >= len(frame):
            continue
        if warning_exit_index < entry_index:
            continue

        entry_price = float(open_[entry_index])
        warning_exit_price = float(open_[warning_exit_index])
        regime_exit_price = float(open_[regime_exit_index])
        early_return = directional_return(entry_price, warning_exit_price, d)
        late_return = directional_return(entry_price, regime_exit_price, d)
        post_warning_hold_return = directional_return(warning_exit_price, regime_exit_price, d)
        if early_return is None or late_return is None or post_warning_hold_return is None:
            continue

        early_mae, early_mfe = trade_excursions(frame, entry_index, warning_exit_index, d)
        late_mae, late_mfe = trade_excursions(frame, entry_index, regime_exit_index, d)
        if None in (early_mae, early_mfe, late_mae, late_mfe):
            continue

        rows.append(
            {
                "start": start,
                "end": end,
                "direction": d,
                "duration": int(episode["duration"]),
                "warning_index": warning,
                "warning_remaining_episode_bars": end - warning,
                "entry_index": entry_index,
                "warning_exit_index": warning_exit_index,
                "changed_bar_index": changed_bar_index,
                "regime_exit_index": regime_exit_index,
                "bars_exited_earlier": regime_exit_index - warning_exit_index,
                "warning_exit_return": early_return,
                "regime_change_exit_return": late_return,
                "warning_exit_advantage": early_return - late_return,
                "post_warning_hold_return": post_warning_hold_return,
                "warning_exit_better": bool(early_return > late_return),
                "regime_change_exit_better": bool(late_return > early_return),
                "warning_exit_mae": early_mae,
                "regime_change_exit_mae": late_mae,
                "mae_reduction_from_warning_exit": float(late_mae - early_mae),
                "warning_exit_mfe": early_mfe,
                "regime_change_exit_mfe": late_mfe,
                "mfe_sacrificed_by_warning_exit": float(late_mfe - early_mfe),
            }
        )
    return rows


def summarize_events(rows: list[dict[str, object]]) -> dict[str, object]:
    if not rows:
        return {"events": 0}

    def values(field: str) -> list[float]:
        return [float(row[field]) for row in rows if row.get(field) is not None]

    return {
        "events": len(rows),
        "warning_exit_better_rate": float(np.mean([bool(row["warning_exit_better"]) for row in rows])),
        "regime_change_exit_better_rate": float(np.mean([bool(row["regime_change_exit_better"]) for row in rows])),
        "median_bars_exited_earlier": median_or_none(values("bars_exited_earlier")),
        "mean_warning_exit_return": mean_or_none(values("warning_exit_return")),
        "mean_regime_change_exit_return": mean_or_none(values("regime_change_exit_return")),
        "mean_warning_exit_advantage": mean_or_none(values("warning_exit_advantage")),
        "median_warning_exit_advantage": median_or_none(values("warning_exit_advantage")),
        "mean_post_warning_hold_return": mean_or_none(values("post_warning_hold_return")),
        "median_post_warning_hold_return": median_or_none(values("post_warning_hold_return")),
        "mean_warning_exit_mae": mean_or_none(values("warning_exit_mae")),
        "mean_regime_change_exit_mae": mean_or_none(values("regime_change_exit_mae")),
        "mean_mae_reduction_from_warning_exit": mean_or_none(values("mae_reduction_from_warning_exit")),
        "mean_warning_exit_mfe": mean_or_none(values("warning_exit_mfe")),
        "mean_regime_change_exit_mfe": mean_or_none(values("regime_change_exit_mfe")),
        "mean_mfe_sacrificed_by_warning_exit": mean_or_none(values("mfe_sacrificed_by_warning_exit")),
    }


def analyze_pair(pair: str, frame: pd.DataFrame) -> dict[str, object]:
    model = compute_v06(frame.copy())
    events = extract_exit_events(frame, model)
    return {
        "rows": len(frame),
        "start_date": str(frame["date"].iloc[0]),
        "end_date": str(frame["date"].iloc[-1]),
        "summary": summarize_events(events),
    }


def aggregate_pairs(pairs: dict[str, dict[str, object]]) -> dict[str, object]:
    summaries = [result["summary"] for result in pairs.values()]  # type: ignore[index]
    nonempty = [row for row in summaries if int(row["events"]) > 0]
    total_events = int(sum(int(row["events"]) for row in nonempty))

    metric_names = (
        "warning_exit_better_rate",
        "regime_change_exit_better_rate",
        "median_bars_exited_earlier",
        "mean_warning_exit_return",
        "mean_regime_change_exit_return",
        "mean_warning_exit_advantage",
        "median_warning_exit_advantage",
        "mean_post_warning_hold_return",
        "median_post_warning_hold_return",
        "mean_warning_exit_mae",
        "mean_regime_change_exit_mae",
        "mean_mae_reduction_from_warning_exit",
        "mean_warning_exit_mfe",
        "mean_regime_change_exit_mfe",
        "mean_mfe_sacrificed_by_warning_exit",
    )
    out: dict[str, object] = {"total_events": total_events, "pairs_with_events": len(nonempty)}
    for metric in metric_names:
        vals = [float(row[metric]) for row in nonempty if row.get(metric) is not None]
        out[f"median_pair_{metric}"] = median_or_none(vals)

    weighted_early_wins = sum(
        float(row["warning_exit_better_rate"]) * int(row["events"])
        for row in nonempty
        if row.get("warning_exit_better_rate") is not None
    )
    out["pooled_warning_exit_better_rate"] = (
        float(weighted_early_wins / total_events) if total_events else None
    )
    out["pairs_where_warning_exit_wins_majority"] = int(
        sum(float(row["warning_exit_better_rate"]) > 0.5 for row in nonempty)
    )
    return out


def build_report() -> dict[str, object]:
    pairs = {pair: analyze_pair(pair, frame) for pair, frame in load_burned_pairs().items()}
    return {
        "schema_version": 1,
        "issue": 57,
        "status": "BURNED_DATA_EXIT_POLICY_COMPARISON_ONLY",
        "engine": "current Issue #57 v0.6 price-only core",
        "warning_definition": "first established-regime bar with at least 2 of 3 signs: Top2 weakening, entropy rising, opposite structural pressure rising; each measured versus 3 bars earlier",
        "execution": {
            "entry": "next open after actionable Top2 episode onset",
            "warning_exit": "next open after first 2+ warning",
            "regime_change_exit": "next open after the first post-episode bar closes and confirms the actionable regime changed",
        },
        "conditioning": "Only actionable Top2 episodes that survive at least 3 bars and produce a 2+ warning are compared. This is a position-management conditional study, not a test of all regimes.",
        "pairs": pairs,
        "aggregate": aggregate_pairs(pairs),
        "boundary": "The same already-burned seven FX fixtures are intentionally reused for behavior research. No production rule or independent validation claim is made.",
    }


def pct(value: float | None) -> str:
    return "—" if value is None else f"{100.0 * value:.2f}%"


def num(value: float | None, digits: int = 2) -> str:
    return "—" if value is None else f"{value:.{digits}f}"


def render_markdown(report: dict[str, object]) -> str:
    agg = report["aggregate"]  # type: ignore[index]
    lines = [
        "# Issue #57 — Decay warning exit vs regime-change exit",
        "",
        "**Burned-data position-management comparison only. Existing v0.6 is unchanged.**",
        "",
        "## Question",
        "",
        "If an established actionable Top-2 regime develops the first 2+ decay warning, is it better to exit on the next open or wait until the regime visibly changes and then exit on the following open?",
        "",
        "## Execution convention",
        "",
        "- Same entry for both policies: next open after episode onset.",
        "- Warning policy: next open after first 2+ warning.",
        "- Regime-change policy: wait for the first post-episode bar to close, then exit next open.",
        "- This therefore avoids same-close look-ahead execution.",
        "",
        "## Aggregate",
        "",
        f"- Comparable warned episodes: **{agg['total_events']}** across **{agg['pairs_with_events']}** FX pairs.",
        f"- Warning exit beats later regime-change exit (pooled): **{pct(agg['pooled_warning_exit_better_rate'])}**.",
        f"- Median pair warning-exit win rate: **{pct(agg['median_pair_warning_exit_better_rate'])}**.",
        f"- Pairs where warning exit wins a majority of events: **{agg['pairs_where_warning_exit_wins_majority']} / {agg['pairs_with_events']}**.",
        f"- Median pair mean incremental return from continuing to hold after the warning: **{pct(agg['median_pair_mean_post_warning_hold_return'])}**.",
        f"- Median pair mean warning-exit advantage: **{pct(agg['median_pair_mean_warning_exit_advantage'])}**.",
        f"- Median pair mean MAE reduction from leaving at warning: **{pct(agg['median_pair_mean_mae_reduction_from_warning_exit'])}**.",
        f"- Median pair mean MFE sacrificed by leaving at warning: **{pct(agg['median_pair_mean_mfe_sacrificed_by_warning_exit'])}**.",
        f"- Median pair bars exited earlier: **{num(agg['median_pair_median_bars_exited_earlier'], 1)}** bars.",
        "",
        "## Per pair",
        "",
        "| Pair | Events | Warning exit wins | Hold-after-warning return | Early advantage | MAE reduction | MFE sacrificed | Bars earlier |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for pair, result in report["pairs"].items():  # type: ignore[index]
        s = result["summary"]
        if int(s["events"]) == 0:
            continue
        lines.append(
            f"| {pair} | {s['events']} | {pct(s['warning_exit_better_rate'])} | "
            f"{pct(s['mean_post_warning_hold_return'])} | {pct(s['mean_warning_exit_advantage'])} | "
            f"{pct(s['mean_mae_reduction_from_warning_exit'])} | {pct(s['mean_mfe_sacrificed_by_warning_exit'])} | "
            f"{num(s['median_bars_exited_earlier'], 1)} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "This comparison is conditional on an episode surviving long enough to develop a warning, and the warning definition itself came from earlier burned-data behavior mapping. It can tell us how the existing indicator behaved historically; it cannot independently validate a production exit rule.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path, default=HERE / "reports" / "issue-57-decay-exit-policy.json")
    parser.add_argument("--md-output", type=Path, default=HERE / "reports" / "issue-57-decay-exit-policy.md")
    args = parser.parse_args()

    report = build_report()
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.md_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.md_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
