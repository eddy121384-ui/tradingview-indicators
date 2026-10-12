"""Issue #185 PTM v0.2 engineering-review runner.

Runs the deterministic synthetic fixtures through the independent PTM
prototype and writes the full audit artifact set:

* per-bar indicator trajectory CSVs (one per fixture + one combined file);
* first-recognition / latency statistics;
* a reproduction table against Sophira's published v0.2 readouts;
* comparison charts (wide box vs true trend vs fake breakout vs healthy retest);
* a machine-readable summary JSON and a human-readable Markdown report.

No market data, no strategy returns, no parameter search, no OOS5.

Usage::

    python analyze_issue185_price_territory.py
    python analyze_issue185_price_territory.py --outdir <path>
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ptm_territory import (  # noqa: E402
    NOVELTY_CLASS_SPARSE,
    NOVELTY_CLASS_UNVISITED,
    REFERENCE_BARS,
    PTMConfig,
    evaluate_episode,
    reference_gap_diagnostics,
)
from ptm_territory_charts import (  # noqa: E402
    render_comparison_chart,
    render_scenario_chart,
)
from ptm_territory_fixtures import (  # noqa: E402
    Fixture,
    all_fixtures,
    creeping_stall,
    fake_breakout,
    healthy_retest,
    post_breakout_stall,
    short_mirror_of,
    true_trend,
    wide_box_traversal,
)

RESEARCH_DIR = Path(__file__).resolve().parent
DEFAULT_OUT = RESEARCH_DIR / "artifacts" / "issue185_price_territory"

# Sophira's published v0.2 synthetic readouts (design comment #6117510142).
# These came from an unavailable original fixture; the comparison below is an
# INDEPENDENT reconstruction, never a claim of byte-level reproduction.
PUBLISHED_READOUTS = [
    ("wide_box_close_118", "wide_box_traversal", 118.0, 6, 1.0 / 7.0),
    ("wide_box_close_119", "wide_box_traversal", 119.0, 6, 1.0 / 7.0),
    ("one_tick_above_high_120_01", "wide_box_traversal", 120.01, 6, 1.0 / 7.0),
    ("initial_crossing_121_6", "true_trend", 121.6, 0, 1.0),
    ("fake_breakout_back_at_116", "fake_breakout", 116.0, 12, 1.0 / 13.0),
    ("true_breakout_123_126_129", "true_trend", 129.0, 0, 1.0),
    ("healthy_retest_to_118", "healthy_retest", 118.0, 6, 1.0 / 7.0),
    ("stall_124_6_for_18_bars", "post_breakout_stall", 124.6, 0, 1.0),
]

CHART_FIXTURES = [
    ("wide_box", "wide_box_traversal",
     "WIDE BOX 100-120 -- repeated intrabox traversals are NOT new territory"),
    ("true_trend", "true_trend",
     "TRUE TREND -- first close beyond the frozen envelope is recognised immediately"),
    ("fake_breakout", "fake_breakout",
     "FAKE BREAKOUT -- identical first escape close, then immediate deterioration"),
    ("healthy_retest", "healthy_retest",
     "HEALTHY RETEST -- novelty weakens into the old zone then recovers"),
    ("post_breakout_stall", "post_breakout_stall",
     "POST-BREAKOUT STALL -- novelty stays 1.0 while progress stops (known defect)"),
    ("creeping_stall", "creeping_stall",
     "CREEPING STALL -- +0.01/bar resets naive frontier age; amplitude gauge fires"),
    ("volatility_regime_shift", "volatility_regime_shift",
     "VOLATILITY REGIME SHIFT -- 15 extreme closes inflate w and collapse the band"),
    ("long_wick", "long_wick",
     "LONG WICK -- one 150 wick makes genuinely new price 135 look half-visited"),
    ("degenerate_history", "degenerate_history",
     "DEGENERATE HISTORY -- zero band width: fail closed, no fabricated novelty"),
]


def run_fixture(fixture: Fixture):
    bars = fixture.bars
    episode = evaluate_episode(
        bars, fixture.probe_index, fixture.direction, fixture.config
    )
    return bars, episode


def structural_escape_bar(fixture: Fixture, episode) -> int | None:
    bars = fixture.bars
    for i in range(fixture.probe_index, len(bars)):
        if fixture.direction > 0 and bars[i].high > episode.reference.max_high:
            return i
        if fixture.direction < 0 and bars[i].low < episode.reference.min_low:
            return i
    return None


def first_of(observations, predicate) -> int | None:
    for o in observations:
        if predicate(o):
            return o.bar_index
    return None


def latency_row(fixture: Fixture, bars, episode) -> dict:
    obs = episode.observations
    usable = [o for o in obs if o.novelty is not None]
    escape = structural_escape_bar(fixture, episode)
    first_claim = first_of(obs, lambda o: o.is_new_territory_claim)
    first_unvisited = first_of(obs, lambda o: o.novelty_class == NOVELTY_CLASS_UNVISITED)
    first_sparse = first_of(
        obs, lambda o: o.novelty_class in (NOVELTY_CLASS_UNVISITED, NOVELTY_CLASS_SPARSE)
    )
    first_mature = first_of(
        obs,
        lambda o: o.evidence_bars >= 3
        and o.novelty_class in (NOVELTY_CLASS_UNVISITED, NOVELTY_CLASS_SPARSE),
    )
    latency = (first_claim - escape) if (first_claim is not None and escape is not None) else None
    return {
        "fixture": fixture.name,
        "direction": fixture.direction,
        "probe_bar": fixture.probe_index,
        "bars_evaluated": len(obs),
        "reference_bars": episode.reference.n_bars,
        "reference_coverage": round(episode.reference.coverage, 6),
        "validity": episode.reference.validity,
        "w": episode.reference.w,
        "structural_escape_bar": escape,
        "first_claim_bar": first_claim,
        "first_unvisited_bar": first_unvisited,
        "first_new_or_sparse_bar": first_sparse,
        "first_mature_acceptance_bar": first_mature,
        "recognition_latency_bars": latency,
        "claim_bars_total": sum(1 for o in obs if o.is_new_territory_claim),
        "stall_bars_total": sum(1 for o in obs if o.stall_flag),
        "min_novelty": min((o.novelty for o in usable), default=None),
        "max_novelty": max((o.novelty for o in usable), default=None),
        "final_novelty": obs[-1].novelty,
        "final_episodes": obs[-1].revisit_episodes,
        "final_occupancy": obs[-1].occupancy,
        "final_frontier": obs[-1].frontier_progress,
        "final_days_since_best_frontier": obs[-1].days_since_best_frontier,
        "max_close_gap_w": reference_gap_diagnostics(episode.reference)["max_close_gap_w"],
        "envelope_covered_fraction": reference_gap_diagnostics(episode.reference)[
            "envelope_covered_fraction"
        ],
        "suspect_scale_break_bars": sum(1 for o in obs if o.suspect_scale_break),
    }


def reproduction_rows(by_name, episodes) -> list[dict]:
    rows = []
    for checkpoint, fixture_name, close, pub_r, pub_n in PUBLISHED_READOUTS:
        episode = episodes[fixture_name]
        hits = [o for o in episode.observations if abs(o.close - close) <= 1e-9]
        if not hits:
            rows.append({
                "checkpoint": checkpoint,
                "fixture": fixture_name,
                "close": close,
                "published_episodes": pub_r,
                "published_novelty": pub_n,
                "observed_episodes": None,
                "observed_novelty": None,
                "episodes_match": False,
                "novelty_match": False,
                "source": "independent reconstruction",
                "note": "close never reached in this fixture",
            })
            continue
        o = hits[-1] if checkpoint.startswith("stall") else hits[0]
        rows.append({
            "checkpoint": checkpoint,
            "fixture": fixture_name,
            "close": close,
            "published_episodes": pub_r,
            "published_novelty": pub_n,
            "observed_episodes": o.revisit_episodes,
            "observed_novelty": o.novelty,
            "episodes_match": o.revisit_episodes == pub_r,
            "novelty_match": (o.novelty is not None and abs(o.novelty - pub_n) < 1e-6),
            "source": "independent reconstruction",
            "note": (
                "published numbers came from an unavailable original fixture; "
                "match is a re-derivation, not a reproduction of that file"
            ),
        })
    return rows


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", default=str(DEFAULT_OUT))
    args = parser.parse_args(argv)

    out = Path(args.outdir)
    traces_dir = out / "traces"
    charts_dir = out / "charts"
    os.makedirs(traces_dir, exist_ok=True)
    os.makedirs(charts_dir, exist_ok=True)

    fixtures = all_fixtures()
    by_name = {f.name: f for f in fixtures}
    episodes = {}
    bars_by_name = {}
    frames = []

    for fixture in fixtures:
        bars, episode = run_fixture(fixture)
        episodes[fixture.name] = episode
        bars_by_name[fixture.name] = bars
        frame = pd.DataFrame(
            [o.as_row(fixture.name) for o in episode.observations]
        )
        frame.to_csv(traces_dir / f"{fixture.name}.csv", index=False,
                     float_format="%.6f", lineterminator="\n")
        frames.append(frame)

    combined = pd.concat(frames, ignore_index=True)
    combined.to_csv(out / "issue185_ptm_traces_all.csv", index=False,
                    float_format="%.6f", lineterminator="\n")

    latency = pd.DataFrame([latency_row(f, bars_by_name[f.name], episodes[f.name])
                            for f in fixtures])
    latency.to_csv(out / "issue185_ptm_latency.csv", index=False,
                   lineterminator="\n")

    repro = pd.DataFrame(reproduction_rows(by_name, episodes))
    repro.to_csv(out / "issue185_ptm_reproduction.csv", index=False,
                 lineterminator="\n")

    chart_paths = []
    chart_rel = []
    for slug, fixture_name, title in CHART_FIXTURES:
        episode = episodes[fixture_name]
        chart_paths.append(render_scenario_chart(
            episode.observations,
            bars_by_name[fixture_name],
            episode.reference,
            title,
            str(charts_dir / f"{slug}.png"),
        ))
        chart_rel.append(f"charts/{slug}.png")

    series = [
        ("wide box 100-120", episodes["wide_box_traversal"].observations),
        ("true trend", episodes["true_trend"].observations),
        ("fake breakout", episodes["fake_breakout"].observations),
        ("healthy retest", episodes["healthy_retest"].observations),
        ("post-breakout stall", episodes["post_breakout_stall"].observations),
    ]
    comparison = render_comparison_chart(
        series,
        "COMPARISON -- novelty and acceptance by bars since probe anchor",
        str(charts_dir / "comparison_novelty.png"),
    )
    chart_paths.append(comparison)
    chart_rel.append("charts/comparison_novelty.png")

    summary = {
        "issue": 185,
        "title": "Price Territory Memory v0.2 -- independent engineering review",
        "base_branch": "research/issue-78-market-structure-dimension-audit",
        "base_commit": "e316d19",
        "config_fingerprint": PTMConfig().fingerprint(),
        "reference_bars": REFERENCE_BARS,
        "fixture_count": len(fixtures),
        "reproduction": {
            "published_source": "issue #185 comment 6117510142 (Sophira v0.2)",
            "status": "independent reconstruction",
            "all_episodes_match": bool(repro["episodes_match"].all()),
            "all_novelty_match": bool(repro["novelty_match"].all()),
            "rows": repro.to_dict(orient="records"),
        },
        "latency": latency.to_dict(orient="records"),
        "charts": chart_rel,
        "outcomes": {
            "wide_box_claims": int(latency.set_index("fixture").loc[
                "wide_box_traversal", "claim_bars_total"]),
            "true_trend_recognition_latency_bars": int(latency.set_index("fixture").loc[
                "true_trend", "recognition_latency_bars"]),
            "fake_breakout_recognition_latency_bars": int(latency.set_index("fixture").loc[
                "fake_breakout", "recognition_latency_bars"]),
            "stall_novelty_pinned": float(latency.set_index("fixture").loc[
                "post_breakout_stall", "final_novelty"]),
            "long_trend_final_novelty": float(latency.set_index("fixture").loc[
                "long_trend_unbounded_novelty", "final_novelty"]),
        },
        "boundaries": {
            "market_data_used": False,
            "historical_returns_computed": False,
            "parameter_search_performed": False,
            "oos5_contacted": False,
            "pine_or_production_modified": False,
            "strategy_rules_modified": False,
        },
    }
    (out / "issue185_ptm_summary.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8", newline="\n"
    )

    _write_report(out, latency, repro, summary)
    print(f"artifacts written to {out}")
    print(f"fixtures: {len(fixtures)}  charts: {len(chart_paths)}")
    print(repro.to_string(index=False))
    return 0


def _write_report(out: Path, latency: pd.DataFrame, repro: pd.DataFrame,
                  summary: dict) -> None:
    lines = [
        "# Issue #185 -- PTM v0.2 engineering-review run report",
        "",
        "Generated by `analyze_issue185_price_territory.py`. Deterministic "
        "synthetic fixtures only: no market data, no returns, no parameter "
        "search, no OOS5, no Pine and no production change.",
        "",
        "## Frozen configuration",
        "",
        "```json",
        json.dumps(PTMConfig().fingerprint(), indent=2),
        "```",
        "",
        "## Reproduction of the published v0.2 readouts",
        "",
        "| checkpoint | fixture | published R | published N | observed R | observed N | match |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in repro.to_dict(orient="records"):
        lines.append(
            f"| {row['checkpoint']} | {row['fixture']} | {row['published_episodes']} | "
            f"{row['published_novelty']:.4f} | {row['observed_episodes']} | "
            f"{float(row['observed_novelty']):.4f} | "
            f"{'yes' if row['episodes_match'] and row['novelty_match'] else 'NO'} |"
        )
    lines += [
        "",
        "Source: issue #185 comment 6117510142. The numbers above are an "
        "INDEPENDENT reconstruction from the written v0.2 definition against a "
        "locally built 6-sweep 120-bar box; they are not a byte-level "
        "reproduction of Sophira's original fixture, which was not handed over.",
        "",
        "## First-recognition latency",
        "",
        "| fixture | probe | structural escape | first claim | latency (bars) | claims | stall bars | final N | validity |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in latency.to_dict(orient="records"):
        lines.append(
            f"| {row['fixture']} | {row['probe_bar']} | {row['structural_escape_bar']} | "
            f"{row['first_claim_bar']} | {row['recognition_latency_bars']} | "
            f"{row['claim_bars_total']} | {row['stall_bars_total']} | "
            f"{'' if row['final_novelty'] is None else round(float(row['final_novelty']), 4)} | "
            f"{row['validity']} |"
        )
    lines += [
        "",
        "## Headline outcomes",
        "",
        "```json",
        json.dumps(summary["outcomes"], indent=2),
        "```",
        "",
        "## Boundaries",
        "",
        "```json",
        json.dumps(summary["boundaries"], indent=2),
        "```",
        "",
    ]
    (out / "issue185_ptm_report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    raise SystemExit(main())
