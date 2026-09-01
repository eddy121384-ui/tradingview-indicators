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

GATE = 0.99
TOL = 1e-9
SIGN_TOL = 1e-12


def contiguous_runs(mask: np.ndarray, start: int = 0) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    i, n = max(int(start), 0), len(mask)
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
    n = 0
    for i in range(max(warmup + 1, 1), len(v)):
        if np.isfinite(v[i - 1]) and np.isfinite(v[i]):
            n += int(bool(v[i - 1] > SIGN_TOL) != bool(v[i] > SIGN_TOL))
    return int(n)


def audit_direction(model: pd.DataFrame, direction: int, warmup: int) -> dict[str, Any]:
    x = b316.arrays(model, direction, warmup)
    obs = np.asarray(x["obs_d"], float)
    sh = np.asarray(x["sh_d"], float)
    n = len(obs)
    valid = np.arange(n) >= warmup
    eligible = valid & np.asarray(x["overlap"], bool)
    advance = eligible & np.isfinite(obs) & np.isfinite(sh) & (obs <= SIGN_TOL) & (sh > SIGN_TOL)
    new_range = np.asarray(x["new_range"], bool)
    ma_target = valid & np.asarray(x["ma_target"], bool)

    episodes: list[dict[str, Any]] = []
    ma_runs: list[dict[str, Any]] = []
    for run_id, (rs, re) in enumerate(contiguous_runs(ma_target, warmup)):
        eps = contiguous_runs(advance[rs:re])
        for ls, le in eps:
            es, ee = rs + ls, rs + le
            handoff = next((i for i in range(es, re) if np.isfinite(obs[i]) and obs[i] > SIGN_TOL), None)
            episodes.append({
                "ma_run_id": int(run_id), "ma_run_start": int(rs), "ma_run_end": int(re),
                "start": int(es), "end": int(ee), "duration": int(ee - es),
                "outcome": "followed_handoff" if handoff is not None else "false_release",
                "observed_handoff_index": None if handoff is None else int(handoff),
                "lead_to_observed_handoff": None if handoff is None else int(handoff - es),
                "new_range_bars": int(np.sum(new_range[es:ee])),
                "one_bar": bool(ee - es == 1),
            })
        ma_runs.append({"run_id": int(run_id), "start": int(rs), "end": int(re), "advance_episode_count": int(len(eps))})

    outcome = Counter(e["outcome"] for e in episodes)
    false_eps = [e for e in episodes if e["outcome"] == "false_release"]
    durations = [int(e["duration"]) for e in episodes]
    leads = [int(e["lead_to_observed_handoff"]) for e in episodes if e["lead_to_observed_handoff"] is not None]
    flip = Counter("0" if r["advance_episode_count"] == 0 else "1" if r["advance_episode_count"] == 1 else ">1" for r in ma_runs)
    obs_trans = positive_transition_count(obs, warmup)
    sh_trans = positive_transition_count(sh, warmup)
    advance_bars = int(np.sum(advance))

    return {
        "direction": "bull" if direction == 1 else "bear",
        "eligible_stale_overlap_bars": int(np.sum(eligible)),
        "raw_advance_bars": advance_bars,
        "raw_advance_episodes": int(len(episodes)),
        "followed_handoff_episodes": int(outcome.get("followed_handoff", 0)),
        "false_release_episodes": int(outcome.get("false_release", 0)),
        "unexplained_episode_accounting": int(len(episodes) - outcome.get("followed_handoff", 0) - outcome.get("false_release", 0)),
        "one_bar_false_release_episodes": int(sum(e["one_bar"] for e in false_eps)),
        "episode_durations": durations,
        "followed_leads": leads,
        "observed_raw_transition_count": obs_trans,
        "shadow_raw_transition_count": sh_trans,
        "ma_runs": int(len(ma_runs)),
        "ma_runs_0_advance_episodes": int(flip.get("0", 0)),
        "ma_runs_1_advance_episode": int(flip.get("1", 0)),
        "ma_runs_gt1_advance_episodes": int(flip.get(">1", 0)),
        "raw_advance_bars_with_new_range": int(np.sum(advance & new_range)),
        "break_reconstruction_error": float(x["break_err"]),
        "observed_reconstruction_error": float(x["obs_err"]),
        "shadow_reconstruction_error": float(x["shadow_err"]),
        "episodes": episodes,
        "_eligible": eligible,
        "_advance": advance,
    }


def _outcome_labels(x: dict[str, Any], n: int) -> np.ndarray:
    labels = np.zeros(n, dtype=np.int8)
    for e in x["episodes"]:
        labels[e["start"]:e["end"]] = 1 if e["outcome"] == "followed_handoff" else -1
    return labels


def _count_agreement(a: int, b: int) -> float:
    return float(1.0 - abs(int(a) - int(b)) / max(abs(int(a)), abs(int(b)), 1))


def mirror_compare(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    ea, eb = np.asarray(a["_eligible"], bool), np.asarray(b["_eligible"], bool)
    aa, ab = np.asarray(a["_advance"], bool), np.asarray(b["_advance"], bool)
    if len(ea) != len(eb):
        return {"eligibility_agreement": 0.0, "advance_agreement": 0.0, "episode_outcome_agreement": 0.0, "transition_count_agreement": 0.0}
    common = aa & ab
    la, lb = _outcome_labels(a, len(aa)), _outcome_labels(b, len(ab))
    obs_agree = _count_agreement(a["observed_raw_transition_count"], b["observed_raw_transition_count"])
    sh_agree = _count_agreement(a["shadow_raw_transition_count"], b["shadow_raw_transition_count"])
    return {
        "eligibility_agreement": float(np.mean(ea == eb)) if len(ea) else 1.0,
        "advance_agreement": float(np.mean(aa == ab)) if len(aa) else 1.0,
        "episode_outcome_agreement": float(np.mean(la[common] == lb[common])) if np.any(common) else 1.0,
        "episode_common_advance_bars": int(np.sum(common)),
        "transition_count_agreement": min(obs_agree, sh_agree),
        "observed_transition_count_agreement": obs_agree,
        "shadow_transition_count_agreement": sh_agree,
        "transition_counts_a": [a["observed_raw_transition_count"], a["shadow_raw_transition_count"]],
        "transition_counts_b": [b["observed_raw_transition_count"], b["shadow_raw_transition_count"]],
    }


def clean(x: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in x.items() if not k.startswith("_")}


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
        "bull": clean(bull), "bear": clean(bear),
        "mirror": {
            "bull_vs_inverse_bear": mirror_compare(bull, ibear),
            "bear_vs_inverse_bull": mirror_compare(bear, ibull),
        },
    }


def summarize_pair(p: dict[str, Any]) -> dict[str, Any]:
    s = [p["bull"], p["bear"]]
    keys = ("eligible_stale_overlap_bars", "raw_advance_bars", "raw_advance_episodes", "followed_handoff_episodes",
            "false_release_episodes", "observed_raw_transition_count", "shadow_raw_transition_count", "ma_runs_gt1_advance_episodes")
    return {k: int(sum(x[k] for x in s)) for k in keys}


def build_report() -> dict[str, Any]:
    pairs = {name: analyze_pair(frame) for name, frame in phasea.load_frozen_pairs().items()}
    sum_keys = ("eligible_stale_overlap_bars", "raw_advance_bars", "raw_advance_episodes", "followed_handoff_episodes",
                "false_release_episodes", "one_bar_false_release_episodes", "observed_raw_transition_count", "shadow_raw_transition_count",
                "ma_runs", "ma_runs_0_advance_episodes", "ma_runs_1_advance_episode", "ma_runs_gt1_advance_episodes", "raw_advance_bars_with_new_range")
    a: dict[str, Any] = {k: 0 for k in sum_keys}
    a.update({"max_break_reconstruction_error": 0.0, "max_observed_reconstruction_error": 0.0, "max_shadow_reconstruction_error": 0.0,
              "minimum_eligibility_mirror_agreement": 1.0, "minimum_advance_mirror_agreement": 1.0,
              "minimum_episode_outcome_mirror_agreement": 1.0, "minimum_transition_count_mirror_agreement": 1.0})
    durations: list[int] = []
    leads: list[int] = []
    for p in pairs.values():
        for side in ("bull", "bear"):
            x = p[side]
            for k in sum_keys:
                a[k] += int(x[k])
            a["max_break_reconstruction_error"] = max(a["max_break_reconstruction_error"], x["break_reconstruction_error"])
            a["max_observed_reconstruction_error"] = max(a["max_observed_reconstruction_error"], x["observed_reconstruction_error"])
            a["max_shadow_reconstruction_error"] = max(a["max_shadow_reconstruction_error"], x["shadow_reconstruction_error"])
            durations.extend(x["episode_durations"])
            leads.extend(x["followed_leads"])
        for m in p["mirror"].values():
            a["minimum_eligibility_mirror_agreement"] = min(a["minimum_eligibility_mirror_agreement"], m["eligibility_agreement"])
            a["minimum_advance_mirror_agreement"] = min(a["minimum_advance_mirror_agreement"], m["advance_agreement"])
            a["minimum_episode_outcome_mirror_agreement"] = min(a["minimum_episode_outcome_mirror_agreement"], m["episode_outcome_agreement"])
            a["minimum_transition_count_mirror_agreement"] = min(a["minimum_transition_count_mirror_agreement"], m["transition_count_agreement"])

    total, false_n = a["raw_advance_episodes"], a["false_release_episodes"]
    a["unexplained_episode_accounting"] = int(total - a["followed_handoff_episodes"] - false_n)
    a["false_release_share"] = float(false_n / total) if total else 0.0
    a["one_bar_false_release_share"] = float(a["one_bar_false_release_episodes"] / false_n) if false_n else 0.0
    a["episode_duration_median"] = float(np.median(durations)) if durations else None
    a["episode_duration_p75"] = float(np.percentile(durations, 75)) if durations else None
    a["episode_duration_max"] = int(np.max(durations)) if durations else None
    a["followed_handoff_lead_median"] = float(np.median(leads)) if leads else None
    a["followed_handoff_lead_p75"] = float(np.percentile(leads, 75)) if leads else None
    a["followed_handoff_lead_max"] = int(np.max(leads)) if leads else None
    a["transition_count_ratio"] = float(a["shadow_raw_transition_count"] / a["observed_raw_transition_count"]) if a["observed_raw_transition_count"] else None
    a["raw_advance_new_range_share"] = float(a["raw_advance_bars_with_new_range"] / a["raw_advance_bars"]) if a["raw_advance_bars"] else 0.0

    # IMPORTANT: transition-count reciprocity is a reported diagnostic, not a preregistered hard gate.
    gate = (
        a["max_break_reconstruction_error"] <= TOL
        and a["max_observed_reconstruction_error"] <= TOL
        and a["max_shadow_reconstruction_error"] <= TOL
        and a["minimum_eligibility_mirror_agreement"] >= GATE
        and a["minimum_advance_mirror_agreement"] >= GATE
        and a["minimum_episode_outcome_mirror_agreement"] >= GATE
        and a["unexplained_episode_accounting"] == 0
    )
    return {
        "issue": 68, "phase": "B3.17", "status": "GLOBAL_FALSE_RELEASE_CHURN_NO_PERFORMANCE",
        "primary_gate_pass": bool(gate), "aggregate": a,
        "per_pair": {name: summarize_pair(p) for name, p in pairs.items()}, "pairs": pairs,
        "boundary": "Global safety audit of the frozen B3.16 one-source shadow only; production C-2 and all parameters remain unchanged.",
    }


def render_markdown(r: dict[str, Any]) -> str:
    a = r["aggregate"]
    L = [
        "# Issue #68 Phase B3.17 — Global False-Release / Churn Audit", "",
        "Status: **diagnostic shadow only / frozen C-2 / no performance use**", "",
        f"Primary engineering gate: **{'PASS' if r['primary_gate_pass'] else 'FAIL'}**",
        f"- eligible stale-overlap bars: **{a['eligible_stale_overlap_bars']}**",
        f"- raw-advance bars / episodes: **{a['raw_advance_bars']} / {a['raw_advance_episodes']}**",
        f"- followed-handoff episodes: **{a['followed_handoff_episodes']}**",
        f"- false-release episodes: **{a['false_release_episodes']} ({100*a['false_release_share']:.1f}%)**",
        f"- one-bar false releases: **{a['one_bar_false_release_episodes']} ({100*a['one_bar_false_release_share']:.1f}% of false releases)**", "",
        "## Episode timing", "",
        f"- raw-advance episode duration: median **{a['episode_duration_median']}**, p75 **{a['episode_duration_p75']}**, max **{a['episode_duration_max']}**",
        f"- lead to later observed handoff: median **{a['followed_handoff_lead_median']}**, p75 **{a['followed_handoff_lead_p75']}**, max **{a['followed_handoff_lead_max']}**", "",
        "## Churn / transition safety", "",
        f"- observed raw transitions: **{a['observed_raw_transition_count']}**",
        f"- shadow raw transitions: **{a['shadow_raw_transition_count']}**",
        f"- transition-count ratio: **{a['transition_count_ratio']:.3f}x**" if a["transition_count_ratio"] is not None else "- transition-count ratio: **n/a**",
        f"- MA-side runs with 0 / 1 / >1 advance episodes: **{a['ma_runs_0_advance_episodes']} / {a['ma_runs_1_advance_episode']} / {a['ma_runs_gt1_advance_episodes']}**",
        f"- raw-advance bars with target NEW RANGE already present: **{a['raw_advance_bars_with_new_range']} / {a['raw_advance_bars']} ({100*a['raw_advance_new_range_share']:.1f}%)**", "",
        "## Engineering / reciprocal checks", "",
        f"- max Break / observed / shadow reconstruction error: **{a['max_break_reconstruction_error']:.3e} / {a['max_observed_reconstruction_error']:.3e} / {a['max_shadow_reconstruction_error']:.3e}**",
        f"- minimum reciprocal eligibility agreement: **{100*a['minimum_eligibility_mirror_agreement']:.3f}%**",
        f"- minimum reciprocal raw-advance agreement: **{100*a['minimum_advance_mirror_agreement']:.3f}%**",
        f"- minimum reciprocal episode-outcome agreement on common advance bars: **{100*a['minimum_episode_outcome_mirror_agreement']:.3f}%**",
        f"- minimum reciprocal transition-count agreement (diagnostic only): **{100*a['minimum_transition_count_mirror_agreement']:.3f}%**",
        f"- unexplained episode accounting: **{a['unexplained_episode_accounting']}**", "",
        "## Per-pair summary", "",
        "| Pair | Eligible bars | Advance eps | Followed | False | Obs trans | Shadow trans | MA runs >1 eps |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, x in r["per_pair"].items():
        L.append(f"| {name} | {x['eligible_stale_overlap_bars']} | {x['raw_advance_episodes']} | {x['followed_handoff_episodes']} | {x['false_release_episodes']} | {x['observed_raw_transition_count']} | {x['shadow_raw_transition_count']} | {x['ma_runs_gt1_advance_episodes']} |")
    L += ["", "## Boundary", "", r["boundary"], ""]
    return "\n".join(L)


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
