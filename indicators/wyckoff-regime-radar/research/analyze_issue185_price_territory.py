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
from dataclasses import replace
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ptm_territory import (  # noqa: E402
    MAX_UNOBSERVED_GAP_FRACTION,
    MAX_W_OVER_SCALE,
    MIN_ENVELOPE_COVERED_FRACTION,
    MIN_REFERENCE_CYCLES,
    NOVELTY_CLASS_SPARSE,
    NOVELTY_CLASS_UNVISITED,
    REFERENCE_BARS,
    PTMConfig,
    evaluate_episode,
    reference_gap_diagnostics,
)
from ptm_promotion_clock import build_promotion_clock  # noqa: E402
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
    ref = episode.reference
    diag = reference_gap_diagnostics(ref)
    return {
        "fixture": fixture.name,
        "direction": fixture.direction,
        "probe_bar": fixture.probe_index,
        "bars_evaluated": len(obs),
        "reference_bars": ref.n_bars,
        "reference_coverage": round(ref.coverage, 6),
        "validity": ref.validity,
        "w": ref.w,
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
        "max_close_gap_w": diag["max_close_gap_w"],
        "envelope_covered_fraction": diag["envelope_covered_fraction"],
        "suspect_scale_break_bars": sum(1 for o in obs if o.suspect_scale_break),
        # --- A1 reference adequacy ---
        "swing_legs": ref.swing_legs,
        "reference_cycle_count": ref.reference_cycle_count,
        "reference_adequacy_ok": ref.reference_adequacy_ok,
        "max_unobserved_gap_fraction": ref.max_unobserved_gap_fraction,
        # --- A2 comparability ---
        "comparability_status": obs[0].comparability_status,
        "first_claim_episodes_per_cycle": (
            next((o.episodes_per_cycle for o in obs if o.bar_index == first_claim), None)
            if first_claim is not None else None
        ),
        # --- A3 scale stability ---
        "scale_state": ref.scale_state,
        "w_over_scale": ref.w_over_scale,
        "scale_reference": ref.scale_reference,
        "validity_reasons": " | ".join(ref.validity_reasons),
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


# Classification of the fixtures whose v0.2 signal the phase-2 guards suppress.
#
# This uses each fixture's KNOWN CONSTRUCTION.  These are constructed paths, not
# market observations, and a price-only test genuinely CANNOT separate a long box
# from a real trend -- that inability is precisely why A1 reports "insufficient
# evidence" instead of guessing.  The table therefore reports the parameter-free
# structural measurement (`sustained_escape_refused`) alongside this label
# instead of pretending the two cases can be told apart from prices alone.
SUPPRESSION_CLASS = {
    "gappy_reference": "correct: data-quality guard, sparse download",
    "long_period_box": "correct: the blocking wide-box false release (A1)",
    "one_way_reference_genuine_trend":
        "COST: a genuine sustained escape refused certification",
    # INSTRUMENTATION, not scenarios.  These two fixtures exist so that each A1
    # envelope sub-guard is individually pinned: each is constructed to trip
    # exactly one of them.  They are deliberately blocked, so counting them in
    # the suppression headline would overstate the guard's real-world cost.
    "envelope_gap_only":
        "instrumentation: A1 gap-guard isolation, not a scenario",
    "envelope_coverage_only":
        "instrumentation: A1 coverage-guard isolation, not a scenario",
}

# Fixtures built purely to instrument a guard.  Excluded from every headline
# cost/suppression count, and reported separately instead.
INSTRUMENTATION_FIXTURES = frozenset(
    name for name, cls in SUPPRESSION_CLASS.items()
    if cls.startswith("instrumentation")
)


def _sustained_escape(fixture: Fixture, episode) -> bool:
    """Parameter-free: did the path leave the envelope and never come back?

    No threshold is involved.  It is reported as a measurement, not used as a
    gate or as a substitute for knowing the fixture's construction.
    """
    bars = fixture.bars
    ref = episode.reference
    if ref.max_high is None or ref.min_low is None:
        return False
    beyond = []
    for i in range(fixture.probe_index, len(bars)):
        if fixture.direction > 0:
            beyond.append(bars[i].close > ref.max_high)
        else:
            beyond.append(bars[i].close < ref.min_low)
    first = next((k for k, b in enumerate(beyond) if b), None)
    return first is not None and all(beyond[first:])


def phase2_comparison_rows(fixtures, episodes, legacy_episodes) -> list[dict]:
    """Per-fixture old-signal vs fixed-signal comparison (issue item 6).

    ``legacy_episodes`` are produced with ``apply_phase2_guards=False``, which
    reconstructs the pre-patch claim gate while keeping every diagnostic
    identical.  The model promotion bar is a CONSTRUCTED analogue: the
    synthetic paths contain no markup/markdown/B3 event, so the structural
    escape bar stands in for the breakout and the frozen three-bar
    confirmation is applied to it.  These are illustrations of the corrected
    timing contract, not claims about the parent model's behaviour.
    """
    rows = []
    for fx in fixtures:
        fixed = episodes[fx.name]
        legacy = legacy_episodes[fx.name]
        ref = fixed.reference
        escape = structural_escape_bar(fx, fixed)
        first_fixed = first_of(fixed.observations, lambda o: o.is_new_territory_claim)
        first_legacy = first_of(legacy.observations, lambda o: o.is_new_territory_claim)
        # Corrected clock: promotion eligibility is breakout + 3, never probe + 3.
        promotion_bar = None if escape is None else escape + 3
        naive_bar = fx.probe_index + 3
        if first_fixed is None or promotion_bar is None:
            extra_vs_model = None
        else:
            extra_vs_model = max(first_fixed - promotion_bar, 0)
        if first_fixed is None:
            extra_vs_naive = None
        else:
            extra_vs_naive = max(first_fixed - naive_bar, 0)
        rows.append({
            "fixture": fx.name,
            "direction": fx.direction,
            "probe_bar": fx.probe_index,
            "v02_signal_claim_bar": first_legacy,
            "v02_claim_bars_total": sum(
                1 for o in legacy.observations if o.is_new_territory_claim),
            "phase2_signal_claim_bar": first_fixed,
            "phase2_claim_bars_total": sum(
                1 for o in fixed.observations if o.is_new_territory_claim),
            "signal_suppressed_by_phase2": bool(
                first_legacy is not None and first_fixed is None),
            "first_recognition_bar": first_fixed,
            "added_delay_bars_vs_v02": (
                None if first_fixed is None or first_legacy is None
                else first_fixed - first_legacy),
            # Corrected timing contract.
            "breakout_stand_in_bar": escape,
            "model_confirmation_bar": promotion_bar,
            "naive_probe_plus_three_bar": naive_bar,
            "naive_baseline_error_bars": (
                None if promotion_bar is None else promotion_bar - naive_bar),
            "ptm_extra_delay_vs_model_bars": extra_vs_model,
            "ptm_extra_delay_vs_naive_bars": extra_vs_naive,
            # Guard outcomes.
            "reference_cycle_count": ref.reference_cycle_count,
            "reference_adequacy_ok": ref.reference_adequacy_ok,
            "scale_state": ref.scale_state,
            "validity": ref.validity,
            # Machine-readable so CI can assert that a fixture trips EXACTLY one
            # A1 sub-guard (the isolation property that makes the two envelope
            # guards individually pinned rather than jointly pinned).
            "validity_reasons": " | ".join(ref.validity_reasons),
            "validity_reason_count": len(ref.validity_reasons),
            "suppression_class": (
                SUPPRESSION_CLASS.get(fx.name) if first_fixed is None
                and first_legacy is not None else None),
            "sustained_escape_refused": bool(
                _sustained_escape(fx, fixed)
                and first_fixed is None and first_legacy is not None),
            "final_frontier_progress_w": fixed.observations[-1].frontier_progress,
        })
    return rows


PROMOTION_SCENARIOS = [
    ("coincident_breakout_at_probe",
     dict(probe_t0=120, b3_break_t=120, ptm_observation_t=120)),
    ("breakout_10_bars_after_probe",
     dict(probe_t0=120, b3_break_t=130, ptm_observation_t=130)),
    ("no_qualifying_breakout",
     dict(probe_t0=120, b3_break_t=None, ptm_observation_t=140)),
    ("confirmation_failed",
     dict(probe_t0=120, b3_break_t=130, ptm_observation_t=133,
          confirmation_passed=False)),
    ("ptm_earlier_than_eligibility",
     dict(probe_t0=120, b3_break_t=130, ptm_observation_t=128)),
    ("ptm_on_eligibility_bar",
     dict(probe_t0=120, b3_break_t=130, ptm_observation_t=133)),
    ("ptm_later_than_eligibility",
     dict(probe_t0=120, b3_break_t=130, ptm_observation_t=135)),
]


def promotion_clock_rows() -> list[dict]:
    """The six independent timestamps required by the corrected contract."""
    rows = []
    for label, kwargs in PROMOTION_SCENARIOS:
        c = build_promotion_clock(**kwargs)
        rows.append({
            "scenario": label,
            "probe_t0": c.probe_t0,
            "b3_break_t": c.b3_break_t,
            "b3_confirmation_t": c.b3_confirmation_t,
            "eligible_promotion_t": c.eligible_promotion_t,
            "ptm_observation_t": c.ptm_observation_t,
            "promotion_next_executable_t": c.promotion_next_executable_t,
            "ptm_next_executable_t": c.ptm_next_executable_t,
            "next_executable_t": c.next_executable_t,
            "probe_to_breakout_bars": c.probe_to_breakout_bars,
            "naive_probe_plus_three_t": c.probe_plus_three_naive_t,
            "naive_baseline_error_bars": c.naive_probe_clock_error_bars,
            "ptm_vs_eligibility": c.ptm_vs_eligibility,
            "ptm_extra_delay_bars": c.ptm_extra_delay_bars,
            "promotion_status": c.promotion_status,
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

    # Old-signal vs fixed-signal comparison.  ``apply_phase2_guards=False``
    # reconstructs the pre-patch v0.2 claim gate and leaves every diagnostic
    # (R, O, N, acceptance, A1/A2/A3 values) byte-identical.
    legacy_episodes = {}
    for fixture in fixtures:
        legacy_cfg = replace(fixture.config, apply_phase2_guards=False)
        legacy_episodes[fixture.name] = evaluate_episode(
            bars_by_name[fixture.name], fixture.probe_index,
            fixture.direction, legacy_cfg,
        )
    phase2 = pd.DataFrame(phase2_comparison_rows(fixtures, episodes, legacy_episodes))
    phase2.to_csv(out / "issue185_ptm_phase2_comparison.csv", index=False,
                  lineterminator="\n")

    clock = pd.DataFrame(promotion_clock_rows())
    clock.to_csv(out / "issue185_ptm_promotion_clock.csv", index=False,
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
        "phase2_guard_thresholds": {
            "a1_cycle_swing_fraction": PTMConfig().cycle_swing_fraction,
            "a1_min_reference_cycles": MIN_REFERENCE_CYCLES,
            "a1_min_envelope_covered_fraction": MIN_ENVELOPE_COVERED_FRACTION,
            "a1_max_unobserved_gap_fraction": MAX_UNOBSERVED_GAP_FRACTION,
            "a3_max_w_over_scale": MAX_W_OVER_SCALE,
            "selection_basis": (
                "pre-outcome fixed synthetic-geometry thresholds; NOT selected "
                "on returns and NOT tuned on any market outcome"
            ),
        },
        "phase2_comparison": phase2.to_dict(orient="records"),
        "promotion_clock": clock.to_dict(orient="records"),
        "phase2_outcomes": {
            "fixtures_with_v02_signal_suppressed": int(
                phase2.loc[
                    ~phase2["fixture"].isin(INSTRUMENTATION_FIXTURES),
                    "signal_suppressed_by_phase2",
                ].sum()),
            "instrumentation_fixtures_deliberately_blocked": int(
                phase2.loc[
                    phase2["fixture"].isin(INSTRUMENTATION_FIXTURES),
                    "signal_suppressed_by_phase2",
                ].sum()),
            "fixtures_v02_claimed_and_phase2_does_not": [
                r["fixture"] for r in phase2.to_dict(orient="records")
                if r["signal_suppressed_by_phase2"]
                and r["fixture"] not in INSTRUMENTATION_FIXTURES
            ],
            "instrumentation_fixtures_excluded_from_headline": sorted(
                INSTRUMENTATION_FIXTURES),
            "instrumentation_note": (
                "The fixtures above are guard-instrumentation constructs, not "
                "scenarios. They are deliberately blocked and are NOT counted in "
                "any suppression or false-suppression figure."
            ),
            "long_period_box_v02_claim_bars": int(phase2.set_index("fixture").loc[
                "long_period_box", "v02_claim_bars_total"]),
            "long_period_box_phase2_claim_bars": int(phase2.set_index("fixture").loc[
                "long_period_box", "phase2_claim_bars_total"]),
            "max_added_delay_vs_v02_bars": int(phase2["added_delay_bars_vs_v02"]
                                               .dropna().abs().max())
            if phase2["added_delay_bars_vs_v02"].notna().any() else 0,
            # Scope qualifier: the number above is the max over fixtures that
            # STILL CLAIM under both configurations.  For a suppressed fixture
            # there is no fixed-signal first claim at all, so its added delay is
            # unbounded (NaN in the CSV), not zero.
            "max_added_delay_vs_v02_bars_scope": (
                "max over fixtures that still claim under BOTH configurations; "
                "for a suppressed fixture the added delay is unbounded (NaN in "
                "the CSV), not zero"
            ),
            "genuine_trends_refused_certification": [
                name for name, cls in SUPPRESSION_CLASS.items()
                if cls.startswith("COST")
            ],
            "suppression_classes": {
                str(r["fixture"]): str(r["suppression_class"])
                for r in phase2.to_dict(orient="records")
                if isinstance(r["suppression_class"], str)
            },
            "max_ptm_extra_delay_vs_corrected_model_baseline_bars": (
                int(phase2["ptm_extra_delay_vs_model_bars"].dropna().max())
                if phase2["ptm_extra_delay_vs_model_bars"].notna().any() else 0
            ),
        },
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

    _write_report(out, latency, repro, summary, phase2, clock)
    print(f"artifacts written to {out}")
    print(f"fixtures: {len(fixtures)}  charts: {len(chart_paths)}")
    print(repro.to_string(index=False))
    return 0


def _write_report(out: Path, latency: pd.DataFrame, repro: pd.DataFrame,
                  summary: dict, phase2: pd.DataFrame,
                  clock: pd.DataFrame) -> None:
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
        "## Phase-2 guard outcomes",
        "",
        "```json",
        json.dumps(summary["phase2_outcomes"], indent=2),
        "```",
        "",
        "## Phase-2 guards: fixed pre-outcome safety thresholds",
        "",
        "```json",
        json.dumps(summary["phase2_guard_thresholds"], indent=2),
        "```",
        "",
        "## Old signal (v0.2) vs fixed signal (A1/A2/A3)",
        "",
        "`v02_*` columns come from `apply_phase2_guards=False`, which reproduces "
        "the pre-patch claim gate. It does NOT leave every diagnostic identical: "
        "the gate itself, the derived `validity` label, `guards_enforced` and the "
        "observation-level validity fields all change. What is identical is every "
        "MEASURED quantity -- R, O, N, the acceptance trace and all A1/A2/A3 "
        "numerics -- which is what makes the old-vs-fixed comparison meaningful.",
        "",
        "`added delay` is the delay relative to the v0.2 first claim and is "
        "reported only for fixtures that claim under BOTH configurations; `nan` "
        "means there is no fixed-signal first claim at all, so the delay is "
        "unbounded rather than zero. The `max_added_delay_vs_v02_bars = 0` "
        "headline carries exactly that scope.",
        "",
        "| fixture | v0.2 first claim | fixed first claim | v0.2 claims | fixed claims | suppressed | added delay | cycles | adequacy | scale | validity |",
        "|---|---:|---:|---:|---:|---|---:|---:|---|---|---|",
    ]
    for row in phase2.to_dict(orient="records"):
        lines.append(
            f"| {row['fixture']} | {row['v02_signal_claim_bar']} | "
            f"{row['phase2_signal_claim_bar']} | {row['v02_claim_bars_total']} | "
            f"{row['phase2_claim_bars_total']} | "
            f"{'YES' if row['signal_suppressed_by_phase2'] else 'no'} | "
            f"{row['added_delay_bars_vs_v02']} | {row['reference_cycle_count']} | "
            f"{row['reference_adequacy_ok']} | {row['scale_state']} | "
            f"{row['validity']} |"
        )
    lines += [
        "",
        "`suppression_class` in `issue185_ptm_phase2_comparison.csv` classifies "
        "each suppressed fixture using its KNOWN CONSTRUCTION; "
        "`sustained_escape_refused` is the parameter-free structural measurement "
        "(the path left the envelope and never returned). A price-only test "
        "cannot separate a long box from a real trend, and this table does not "
        "pretend otherwise -- that is exactly why A1 reports insufficient "
        "evidence rather than guessing.",
        "",
        "## Corrected promotion clock (the frozen #78 B3 contract)",
        "",
        "Promotion eligibility is `B3_break + 3`, NOT `probe + 3`. The naive "
        "baseline is included so its error is measurable.",
        "",
        "| scenario | probe | B3 break | B3 confirm | eligible promotion | PTM obs | next executable | naive probe+3 | naive error | PTM vs eligibility | PTM extra delay | status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---|",
    ]
    for row in clock.to_dict(orient="records"):
        lines.append(
            f"| {row['scenario']} | {row['probe_t0']} | {row['b3_break_t']} | "
            f"{row['b3_confirmation_t']} | {row['eligible_promotion_t']} | "
            f"{row['ptm_observation_t']} | {row['next_executable_t']} | "
            f"{row['naive_probe_plus_three_t']} | {row['naive_baseline_error_bars']} | "
            f"{row['ptm_vs_eligibility']} | {row['ptm_extra_delay_bars']} | "
            f"{row['promotion_status']} |"
        )
    lines += [
        "",
        "The synthetic fixtures contain no markup/markdown/B3 event, so "
        "`breakout_stand_in_bar` in the comparison CSV uses the structural "
        "escape bar as a CONSTRUCTED stand-in for the breakout.",
        "",
        "Two different delay baselines exist and must not be confused. This table "
        "compares against the CORRECTED baseline, `eligible_promotion_t = "
        "B3_break_t + 3`, so `PTM extra delay` is measured against the promotion "
        "the frozen #78 mechanics actually allow. The comparison CSV additionally "
        "carries `ptm_extra_delay_vs_naive_bars`, measured against the NAIVE "
        "`probe_t0 + 3` baseline; that column is large and non-zero (up to 80 "
        "bars) precisely because the naive baseline is wrong. Only the corrected "
        "figure answers 'does PTM delay a legitimate add-on'.",
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
