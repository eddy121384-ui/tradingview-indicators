#!/usr/bin/env python3
"""Issue #68 B3.17 global false-release / churn audit. Diagnostic only."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import diagnose_issue66_reciprocal_symmetry as phasea
import diagnose_issue68_phase_b314_break_evidence_memory as b314
import diagnose_issue68_phase_b316_counterfactual_stale_range_release as b316

HERE = Path(__file__).resolve().parent
GATE = 0.99
TOL = 1e-9
SIGN_TOL = 1e-12


def contiguous_runs(mask: np.ndarray, start: int = 0) -> list[tuple[int, int]]:
    """Return half-open [start,end) runs where mask is true."""
    out: list[tuple[int, int]] = []
    i = max(int(start), 0)
    n = len(mask)
    while i < n:
        if not bool(mask[i]):
            i += 1
            continue
        j = i + 1
        while j < n and bool(mask[j]):
            j += 1
        out.append((i, j))
        i = j
    return out


def positive_transition_count(values: np.ndarray, warmup: int) -> int:
    v = np.asarray(values, float)
    n = len(v)
    count = 0
    for i in range(max(warmup + 1, 1), n):
        if not (np.isfinite(v[i - 1]) and np.isfinite(v[i])):
            continue
        if bool(v[i - 1] > SIGN_TOL) != bool(v[i] > SIGN_TOL):
            count += 1
    return int(count)


def audit_direction(model: pd.DataFrame, direction: int, warmup: int) -> dict[str, Any]:
    x = b316.arrays(model, direction, warmup)
    n = len(x["obs_d"])
    valid = np.arange(n) >= warmup
    eligible = valid & np.asarray(x["overlap"], bool)
    obs = np.asarray(x["obs_d"], float)
    sh = np.asarray(x["sh_d"], float)
    finite = np.isfinite(obs) & np.isfinite(sh)
    advance = eligible & finite & (obs <= SIGN_TOL) & (sh > SIGN_TOL)
    new_range = np.asarray(x["new_range"], bool)
    ma_target = valid & np.asarray(x["ma_target"], bool)

    episodes: list[dict[str, Any]] = []
    ma_runs: list[dict[str, Any]] = []
    advance_bars = int(np.sum(advance))
    advance_new_range_bars = int(np.sum(advance & new_range))

    for run_id, (rs, re) in enumerate(contiguous_runs(ma_target, warmup)):
        local = advance[rs:re]
        eps = contiguous_runs(local, 0)
        episode_ids: list[int] = []
        for ls, le in eps:
            es, ee = rs + ls, rs + le
            future_obs = next(
                (i for i in range(es, re) if np.isfinite(obs[i]) and obs[i] > SIGN_TOL),
                None,
            )
            outcome = "followed_handoff" if future_obs is not None else "false_release"
            duration = int(ee - es)
            row = {
                "episode_id": len(episodes),
                "ma_run_id": int(run_id),
                "ma_run_start": int(rs),
                "ma_run_end": int(re),
                "start": int(es),
                "end": int(ee),
                "duration": duration,
                "outcome": outcome,
                "observed_handoff_index": None if future_obs is None else int(future_obs),
                "lead_to_observed_handoff": None if future_obs is None else int(future_obs - es),
                "new_range_bars": int(np.sum(new_range[es:ee])),
                "new_range_share": float(np.mean(new_range[es:ee])) if duration else 0.0,
                "one_bar": bool(duration == 1),
            }
            episode_ids.append(len(episodes))
            episodes.append(row)

        ma_runs.append(
            {
                "run_id": int(run_id),
                "start": int(rs),
                "end": int(re),
                "advance_episode_count": int(len(eps)),
                "flipflop_class": "0" if len(eps) == 0 else "1" if len(eps) == 1 else ">1",
                "episode_ids": episode_ids,
            }
        )

    outcomes = Counter(e["outcome"] for e in episodes)
    false_eps = [e for e in episodes if e["outcome"] == "false_release"]
    followed_eps = [e for e in episodes if e["outcome"] == "followed_handoff"]
    durations = [int(e["duration"]) for e in episodes]
    leads = [int(e["lead_to_observed_handoff"]) for e in followed_eps if e["lead_to_observed_handoff"] is not None]
    flip = Counter(r["flipflop_class"] for r in ma_runs)

    return {
        "direction": "bull" if direction == 1 else "bear",
        "eligible_stale_overlap_bars": int(np.sum(eligible)),
        "raw_advance_bars": advance_bars,
        "raw_advance_episodes": int(len(episodes)),
        "followed_handoff_episodes": int(outcomes.get("followed_handoff", 0)),
        "false_release_episodes": int(outcomes.get("false_release", 0)),
        "unexplained_episode_accounting": int(len(episodes) - outcomes.get("followed_handoff", 0) - outcomes.get("false_release", 0)),
        "false_release_share": float(len(false_eps) / len(episodes)) if episodes else 0.0,
        "one_bar_false_release_episodes": int(sum(e["one_bar"] for e in false_eps)),
        "one_bar_false_release_share": float(sum(e["one_bar"] for e in false_eps) / len(false_eps)) if false_eps else 0.0,
        "episode_duration_median": float(np.median(durations)) if durations else None,
        "episode_duration_p75": float(np.percentile(durations, 75)) if durations else None,
        "episode_duration_max": int(np.max(durations)) if durations else None,
        "followed_handoff_lead_median": float(np.median(leads)) if leads else None,
        "followed_handoff_lead_p75": float(np.percentile(leads, 75)) if leads else None,
        "followed_handoff_lead_max": int(np.max(leads)) if leads else None,
        "observed_raw_transition_count": positive_transition_count(obs, warmup),
        "shadow_raw_transition_count": positive_transition_count(sh, warmup),
        "transition_count_ratio": float(positive_transition_count(sh, warmup) / positive_transition_count(obs, warmup)) if positive_transition_count(obs, warmup) else None,
        "ma_runs": int(len(ma_runs)),
        "ma_runs_0_advance_episodes": int(flip.get("0", 0)),
        "ma_runs_1_advance_episode": int(flip.get("1", 0)),
        "ma_runs_gt1_advance_episodes": int(flip.get(">1", 0)),
        "raw_advance_bars_with_new_range": advance_new_range_bars,
        "raw_advance_new_range_share": float(advance_new_range_bars / advance_bars) if advance_bars else 0.0,
        "break_reconstruction_error": float(x["break_err"]),
        "observed_reconstruction_error": float(x["obs_err"]),
        "shadow_reconstruction_error": float(x["shadow_err"]),
        "episodes": episodes,
        "ma_run_details": ma_runs,
        "_eligible": eligible,
        "_advance": advance,
    }


def mirror_compare(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    ea = np.asarray(a["_eligible"], bool)
    eb = np.asarray(b["_eligible"], bool)
    aa = np.asarray(a["_advance"], bool)
    ab = np.asarray(b["_advance"], bool)
    if len(ea) != len(eb):
        return {"eligibility_agreement": 0.0, "advance_agreement": 0.0, "episode_outcome_agreement": 0.0, "transition_count_agreement": 0.0}

    elig_agree = float(np.mean(ea == eb)) if len(ea) else 1.0
    adv_agree = float(np.mean(aa == ab)) if len(aa) else 1.0

    amap = {(e["start"], e["end"]): e["outcome"] for e in a["episodes"]}
    bmap = {(e["start"], e["end"]): e["outcome"] for e in b["episodes"]}
    keys = sorted(set(amap) | set(bmap))
    ep_match = sum(amap.get(k) == bmap.get(k) for k in keys)
    ep_agree = float(ep_match / len(keys)) if keys else 1.0

    ta = (a["observed_raw_transition_count"], a["shadow_raw_transition_count"])
    tb = (b["observed_raw_transition_count"], b["shadow_raw_transition_count"])
    trans_agree = 1.0 if ta == tb else 0.0
    return {
        "eligibility_agreement": elig_agree,
        "advance_agreement": adv_agree,
        "episode_outcome_agreement": ep_agree,
        "episode_union": int(len(keys)),
        "episode_matches": int(ep_match),
        "transition_count_agreement": trans_agree,
        "transition_counts_a": list(ta),
        "transition_counts_b": list(tb),
    }


def analyze_pair(frame: pd.DataFrame) -> dict[str, Any]:
    inv = phasea.reciprocal_ohlc(frame)
    model, cfg = b314.compute(frame)
    imodel, icfg = b314.compute(inv)
    warmup = int(cfg.rank_len - 1)
    assert warmup == int(icfg.rank_len - 1)
    bull = audit_direction(model, 1, warmup)
    bear = audit_direction(model, -1, warmup)
    ibull = audit_direction(imodel, 1, warmup)
    ibear = audit_direction(imodel, -1, warmup)
    return {
        "warmup": warmup,
        "bull": clean(bull),
        "bear": clean(bear),
        "mirror": {
            "bull_vs_inverse_bear": mirror_compare(bull, ibear),
            "bear_vs_inverse_bull": mirror_compare(bear, ibull),
        },
    }


def clean(x: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in x.items() if not k.startswith("_")}


def build_report() -> dict[str, Any]:
    pairs = {name: analyze_pair(frame) for name, frame in phasea.load_frozen_pairs().items()}
    agg: dict[str, Any] = {
        "eligible_stale_overlap_bars": 0,
        "raw_advance_bars": 0,
        "raw_advance_episodes": 0,
        "followed_handoff_episodes": 0,
        "false_release_episodes": 0,
        "one_bar_false_release_episodes": 0,
        "observed_raw_transition_count": 0,
        "shadow_raw_transition_count": 0,
        "ma_runs": 0,
        "ma_runs_0_advance_episodes": 0,
        "ma_runs_1_advance_episode": 0,
        "ma_runs_gt1_advance_episodes": 0,
        "raw_advance_bars_with_new_range": 0,
        "max_break_reconstruction_error": 0.0,
        "max_observed_reconstruction_error": 0.0,
        "max_shadow_reconstruction_error": 0.0,
        "minimum_eligibility_mirror_agreement": 1.0,
        "minimum_advance_mirror_agreement": 1.0,
        "minimum_episode_outcome_mirror_agreement": 1.0,
        "minimum_transition_count_mirror_agreement": 1.0,
        "episode_durations": [],
        "followed_leads": [],
    }

    for p in pairs.values():
        for side in ("bull", "bear"):
            x = p[side]
            for key in (
                "eligible_stale_overlap_bars", "raw_advance_bars", "raw_advance_episodes",
                "followed_handoff_episodes", "false_release_episodes", "one_bar_false_release_episodes",
                "observed_raw_transition_count", "shadow_raw_transition_count", "ma_runs",
                "ma_runs_0_advance_episodes", "ma_runs_1_advance_episode", "ma_runs_gt1_advance_episodes",
                "raw_advance_bars_with_new_range",
            ):
                agg[key] += int(x[key])
            agg["max_break_reconstruction_error"] = max(agg["max_break_reconstruction_error"], float(x["break_reconstruction_error"]))
            agg["max_observed_reconstruction_error"] = max(agg["max_observed_reconstruction_error"], float(x["observed_reconstruction_error"]))
            agg["max_shadow_reconstruction_error"] = max(agg["max_shadow_reconstruction_error"], float(x["shadow_reconstruction_error"]))
            agg["episode_durations"].extend(int(e["duration"]) for e in x["episodes"])
            agg["followed_leads"].extend(int(e["lead_to_observed_handoff"]) for e in x["episodes"] if e["lead_to_observed_handoff"] is not None)
        for m in p["mirror"].values():
            agg["minimum_eligibility_mirror_agreement"] = min(agg["minimum_eligibility_mirror_agreement"], float(m["eligibility_agreement"]))
            agg["minimum_advance_mirror_agreement"] = min(agg["minimum_advance_mirror_agreement"], float(m["advance_agreement"]))
            agg["minimum_episode_outcome_mirror_agreement"] = min(agg["minimum_episode_outcome_mirror_agreement"], float(m["episode_outcome_agreement"]))
            agg["minimum_transition_count_mirror_agreement"] = min(agg["minimum_transition_count_mirror_agreement"], float(m["transition_count_agreement"]))

    durations = agg.pop("episode_durations")
    leads = agg.pop("followed_leads")
    total_eps = agg["raw_advance_episodes"]
    false_eps = agg["false_release_episodes"]
    agg["unexplained_episode_accounting"] = int(total_eps - agg["followed_handoff_episodes"] - false_eps)
    agg["false_release_share"] = float(false_eps / total_eps) if total_eps else 0.0
    agg["one_bar_false_release_share"] = float(agg["one_bar_false_release_episodes"] / false_eps) if false_eps else 0.0
    agg["episode_duration_median"] = float(np.median(durations)) if durations else None
    agg["episode_duration_p75"] = float(np.percentile(durations, 75)) if durations else None
    agg["episode_duration_max"] = int(np.max(durations)) if durations else None
    agg["followed_handoff_lead_median"] = float(np.median(leads)) if leads else None
    agg["followed_handoff_lead_p75"] = float(np.percentile(leads, 75)) if leads else None
    agg["followed_handoff_lead_max"] = int(np.max(leads)) if leads else None
    agg["transition_count_ratio"] = float(agg["shadow_raw_transition_count"] / agg["observed_raw_transition_count"]) if agg["observed_raw_transition_count"] else None
    agg["raw_advance_new_range_share"] = float(agg["raw_advance_bars_with_new_range"] / agg["raw_advance_bars"]) if agg["raw_advance_bars"] else 0.0

    gate = (
        agg["max_break_reconstruction_error"] <= TOL
        and agg["max_observed_reconstruction_error"] <= TOL
        and agg["max_shadow_reconstruction_error"] <= TOL
        and agg["minimum_eligibility_mirror_agreement"] >= GATE
        and agg["minimum_advance_mirror_agreement"] >= GATE
        and agg["minimum_episode_outcome_mirror_agreement"] >= GATE
        and agg["minimum_transition_count_mirror_agreement"] >= GATE
        and agg["unexplained_episode_accounting"] == 0
    )
    return {
        "issue": 68,
        "phase": "B3.17",
        "status": "GLOBAL_FALSE_RELEASE_CHURN_NO_PERFORMANCE",
        "primary_gate_pass": bool(gate),
        "aggregate": agg,
        "per_pair": {name: summarize_pair(p) for name, p in pairs.items()},
        "pairs": pairs,
        "boundary": "Global safety audit of the frozen B3.16 one-source shadow only; production C-2 and all parameters remain unchanged.",
    }


def summarize_pair(p: dict[str, Any]) -> dict[str, Any]:
    sides = [p["bull"], p["bear"]]
    return {
        "eligible_stale_overlap_bars": sum(x["eligible_stale_overlap_bars"] for x in sides),
        "raw_advance_bars": sum(x["raw_advance_bars"] for x in sides),
        "raw_advance_episodes": sum(x["raw_advance_episodes"] for x in sides),
        "followed_handoff_episodes": sum(x["followed_handoff_episodes"] for x in sides),
        "false_release_episodes": sum(x["false_release_episodes"] for x in sides),
        "observed_raw_transition_count": sum(x["observed_raw_transition_count"] for x in sides),
        "shadow_raw_transition_count": sum(x["shadow_raw_transition_count"] for x in sides),
        "ma_runs_gt1_advance_episodes": sum(x["ma_runs_gt1_advance_episodes"] for x in sides),
    }


def render_markdown(r: dict[str, Any]) -> str:
    a = r["aggregate"]
    lines = [
        "# Issue #68 Phase B3.17 — Global False-Release / Churn Audit",
        "",
        "Status: **diagnostic shadow only / frozen C-2 / no performance use**",
        "",
        f"Primary engineering gate: **{'PASS' if r['primary_gate_pass'] else 'FAIL'}**",
        f"- eligible stale-overlap bars: **{a['eligible_stale_overlap_bars']}**",
        f"- raw-advance bars / episodes: **{a['raw_advance_bars']} / {a['raw_advance_episodes']}**",
        f"- followed-handoff episodes: **{a['followed_handoff_episodes']}**",
        f"- false-release episodes: **{a['false_release_episodes']} ({100*a['false_release_share']:.1f}%)**",
        f"- one-bar false releases: **{a['one_bar_false_release_episodes']} ({100*a['one_bar_false_release_share']:.1f}% of false releases)**",
        "",
        "## Episode timing",
        "",
        f"- raw-advance episode duration: median **{a['episode_duration_median']}**, p75 **{a['episode_duration_p75']}**, max **{a['episode_duration_max']}**",
        f"- lead to later observed handoff: median **{a['followed_handoff_lead_median']}**, p75 **{a['followed_handoff_lead_p75']}**, max **{a['followed_handoff_lead_max']}**",
        "",
        "## Churn / transition safety",
        "",
        f"- observed raw transitions: **{a['observed_raw_transition_count']}**",
        f"- shadow raw transitions: **{a['shadow_raw_transition_count']}**",
        f"- transition-count ratio: **{a['transition_count_ratio']:.3f}x**" if a["transition_count_ratio"] is not None else "- transition-count ratio: **n/a**",
        f"- MA-side runs with 0 / 1 / >1 advance episodes: **{a['ma_runs_0_advance_episodes']} / {a['ma_runs_1_advance_episode']} / {a['ma_runs_gt1_advance_episodes']}**",
        f"- raw-advance bars with target NEW RANGE already present: **{a['raw_advance_bars_with_new_range']} / {a['raw_advance_bars']} ({100*a['raw_advance_new_range_share']:.1f}%)**",
        "",
        "## Engineering / reciprocal checks",
        "",
        f"- max Break / observed / shadow reconstruction error: **{a['max_break_reconstruction_error']:.3e} / {a['max_observed_reconstruction_error']:.3e} / {a['max_shadow_reconstruction_error']:.3e}**",
        f"- minimum reciprocal eligibility agreement: **{100*a['minimum_eligibility_mirror_agreement']:.3f}%**",
        f"- minimum reciprocal raw-advance agreement: **{100*a['minimum_advance_mirror_agreement']:.3f}%**",
        f"- minimum reciprocal episode-outcome agreement: **{100*a['minimum_episode_outcome_mirror_agreement']:.3f}%**",
        f"- minimum reciprocal transition-count agreement: **{100*a['minimum_transition_count_mirror_agreement']:.3f}%**",
        f"- unexplained episode accounting: **{a['unexplained_episode_accounting']}**",
        "",
        "## Per-pair summary",
        "",
        "| Pair | Eligible bars | Advance eps | Followed | False | Obs trans | Shadow trans | MA runs >1 eps |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, x in r["per_pair"].items():
        lines.append(
            f"| {name} | {x['eligible_stale_overlap_bars']} | {x['raw_advance_episodes']} | {x['followed_handoff_episodes']} | {x['false_release_episodes']} | {x['observed_raw_transition_count']} | {x['shadow_raw_transition_count']} | {x['ma_runs_gt1_advance_episodes']} |"
        )
    lines += ["", "## Boundary", "", r["boundary"], ""]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-json", type=Path, required=True)
    ap.add_argument("--report-md", type=Path, required=True)
    args = ap.parse_args()
    report = build_report()
    args.report_json.parent.mkdir(parents=True, exist_ok=True)
    args.report_md.parent.mkdir(parents=True, exist_ok=True)
    args.report_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    args.report_md.write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report))
    if not report["primary_gate_pass"]:
        raise SystemExit("B3.17 engineering gate failed")


if __name__ == "__main__":
    main()
