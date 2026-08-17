#!/usr/bin/env python3
"""Independent OOS validation of the frozen Issue #57 Transition Health candidate."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from diagnose_transition_health_price_outcomes import (
    GROUPS,
    HORIZONS,
    aggregate_pairs,
    build_price_rows,
    pct,
    summarize_group,
)

HERE = Path(__file__).resolve().parent
MANIFEST_PATH = HERE / "data" / "issue-57-transition-health-independent-oos-manifest.json"
EXPECTED_PAIRS = {"NZDUSD", "EURGBP", "GBPJPY", "AUDJPY", "CADJPY"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_frozen_pairs() -> tuple[dict[str, object], dict[str, pd.DataFrame]]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("status") != "FROZEN_BEFORE_OUTCOME_EVALUATION":
        raise RuntimeError("independent OOS manifest status is not frozen")
    if set(manifest.get("pairs", {})) != EXPECTED_PAIRS:
        raise RuntimeError(f"independent OOS pair set drifted: {sorted(manifest.get('pairs', {}))}")

    pairs: dict[str, pd.DataFrame] = {}
    for pair, meta in manifest["pairs"].items():
        path = MANIFEST_PATH.parent / str(meta["frozen_file"])
        raw = path.read_bytes()
        actual = sha256_bytes(raw)
        expected = str(meta["sha256"])
        if actual != expected:
            raise RuntimeError(f"{pair}: frozen SHA mismatch: {actual} != {expected}")
        frame = pd.read_csv(path)
        frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.date
        pairs[pair] = frame.reset_index(drop=True)
    return manifest, pairs


def analyze_pair(frame: pd.DataFrame, score_start: str, score_end: str) -> dict[str, object]:
    start = pd.Timestamp(score_start).date()
    end = pd.Timestamp(score_end).date()
    all_rows = build_price_rows(frame)
    rows: list[dict[str, object]] = []
    for row in all_rows:
        observation = int(row["observation"])
        observation_date = frame["date"].iloc[observation]
        if start <= observation_date <= end:
            copied = dict(row)
            copied["observation_date"] = str(observation_date)
            rows.append(copied)

    groups = {g: summarize_group([r for r in rows if r["group"] == g]) for g in GROUPS}
    return {
        "rows": len(frame),
        "start_date": str(frame["date"].iloc[0]),
        "end_date": str(frame["date"].iloc[-1]),
        "score_start": score_start,
        "score_end": score_end,
        "eligible_events": len(rows),
        "groups": groups,
    }


def build_report() -> dict[str, object]:
    manifest, frames = load_frozen_pairs()
    score_start = str(manifest["score_start"])
    score_end = str(manifest["score_end"])
    pairs = {pair: analyze_pair(frame, score_start, score_end) for pair, frame in frames.items()}
    return {
        "schema_version": 1,
        "issue": 57,
        "status": "INDEPENDENT_OOS_TRANSITION_HEALTH_EVALUATED",
        "checkpoint": 3,
        "horizons": list(HORIZONS),
        "score_start": score_start,
        "score_end": score_end,
        "source_manifest": str(MANIFEST_PATH.relative_to(HERE)),
        "pairs": pairs,
        "aggregate": aggregate_pairs(pairs),
        "boundary": "Independent OOS evaluation of the rule frozen before this sample was read. No threshold or checkpoint tuning is permitted on this sample.",
    }


def render_markdown(report: dict[str, object]) -> str:
    agg = report["aggregate"]  # type: ignore[index]
    lines = [
        "# Issue #57 — Transition Health independent OOS validation",
        "",
        "**Frozen rule, frozen new FX sample, no post-outcome tuning. Existing v0.6 is unchanged.**",
        "",
        f"- Score era: **{report['score_start']} through {report['score_end']}**.",
        "- Pairs: **NZDUSD, EURGBP, GBPJPY, AUDJPY, CADJPY**.",
        "- Observable rule: carried stage takes the handoff lead and keeps a strict lead through **+3 bars**.",
        f"- Eligible +3 events: **{agg['eligible_events']}**.",
        f"- Healthy / damaged events: **{agg['group_events']['healthy_hold']} / {agg['group_events']['damaged_retake']}**.",
        "- Price outcomes start from the +3 close.",
        "",
        "## Cross-pair OOS price outcomes",
        "",
        "| Horizon | Group | Aligned return | Hit rate | MFE | MAE | MFE-MAE |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for horizon in HORIZONS:
        h = agg["horizons"][str(horizon)]
        for group in GROUPS:
            g = h["groups"][group]
            lines.append(
                f"| +{horizon} | {group} | {pct(g['median_pair_mean_aligned_return'])} | "
                f"{pct(g['median_pair_hit_rate'])} | {pct(g['median_pair_mean_mfe'])} | "
                f"{pct(g['median_pair_mean_mae'])} | {pct(g['median_pair_mean_mfe_minus_mae'])} |"
            )

    lines += [
        "",
        "## Pair consistency",
        "",
        "| Horizon | Comparable FX | Healthy wins return | Healthy wins hit rate | Healthy wins MFE-MAE |",
        "|---|---:|---:|---:|---:|",
    ]
    for horizon in HORIZONS:
        c = agg["horizons"][str(horizon)]["pair_comparison"]
        lines.append(
            f"| +{horizon} | {c['comparable_pairs']} | {c['healthy_return_wins']} | "
            f"{c['healthy_hit_rate_wins']} | {c['healthy_mfe_minus_mae_wins']} |"
        )

    lines += [
        "",
        "## Per pair — 10-bar OOS aligned return / hit rate",
        "",
        "| Pair | Healthy n | Healthy return | Healthy hit | Damaged n | Damaged return | Damaged hit |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for pair, result in report["pairs"].items():  # type: ignore[index]
        healthy = result["groups"]["healthy_hold"]
        damaged = result["groups"]["damaged_retake"]
        h10 = healthy["horizons"]["10"]
        d10 = damaged["horizons"]["10"]
        lines.append(
            f"| {pair} | {healthy['events']} | {pct(h10['mean_aligned_return'])} | {pct(h10['hit_rate'])} | "
            f"{damaged['events']} | {pct(d10['mean_aligned_return'])} | {pct(d10['hit_rate'])} |"
        )

    lines += ["", "## Boundary", "", str(report["boundary"]), ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--md-output", type=Path, required=True)
    args = parser.parse_args()
    report = build_report()
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.md_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.md_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2))


if __name__ == "__main__":
    main()
