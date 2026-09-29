#!/usr/bin/env python3
"""Compare Issue #78 TradingView RC parity export with the scalable Python port.

The exact OHLCV rows exported by TradingView are replayed through Python. This
is implementation parity only; no R0 / Warning-First economics are calculated.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from .generate_issue78_rc_python import load_issue78_rc_namespace
except ImportError:
    from generate_issue78_rc_python import load_issue78_rc_namespace  # type: ignore


TV_TO_PY = {
    "PARITY formalId": "formal_id",
    "PARITY symATR": "sym_atr",
    "PARITY volumeQuality": "volume_quality_score",
    "PARITY volumeWeight": "volume_weight_applied",
    "PARITY volumeAbsorption": "volume_absorption_score",
    "PARITY volumeDistribution": "volume_distribution_score",
    "PARITY volumeBreakout": "volume_breakout_confirmation",
    "PARITY volumeBreakdown": "volume_breakdown_confirmation",
    "PARITY accGate": "acc_gate",
    "PARITY markupGate": "markup_gate",
    "PARITY reaccGate": "reacc_gate",
    "PARITY distGate": "dist_gate",
    "PARITY markdownGate": "markdown_gate",
    "PARITY redistGate": "redist_gate",
    "PARITY probAcc": "prob_acc",
    "PARITY probMarkup": "prob_markup",
    "PARITY probReacc": "prob_reacc",
    "PARITY probDist": "prob_dist",
    "PARITY probMarkdown": "prob_markdown",
    "PARITY probRedist": "prob_redist",
    "PARITY topId": "top_id",
    "PARITY topGap": "top_gap",
    "PARITY evidence": "evidence_strength",
    "PARITY candidateDisplayId": "candidate_display_id",
    "PARITY stalePressureBars": "stale_pressure_bars",
    "PARITY stalePressureReason": "stale_pressure_reason",
}

ID_FIELDS = {
    "formal_id",
    "top_id",
    "candidate_display_id",
    "stale_pressure_bars",
    "stale_pressure_reason",
}

GATE_FIELDS = {
    "acc_gate",
    "markup_gate",
    "reacc_gate",
    "dist_gate",
    "markdown_gate",
    "redist_gate",
}


def norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(name).lower()).strip()


def find_column(columns, wanted: str) -> str:
    w = norm(wanted)
    exact = [c for c in columns if norm(c) == w]
    if len(exact) == 1:
        return exact[0]
    suffix = [c for c in columns if norm(c).endswith(w)]
    if len(suffix) == 1:
        return suffix[0]
    contains = [c for c in columns if w in norm(c)]
    if len(contains) == 1:
        return contains[0]
    raise ValueError(f"could not uniquely locate {wanted!r}: {contains or suffix or exact}")


def compute_python(frame: pd.DataFrame) -> pd.DataFrame:
    ns = load_issue78_rc_namespace()
    return ns["compute_price_only"](frame)  # type: ignore[operator]


def state_sync_anchor(py_formal: np.ndarray, common: np.ndarray) -> int | None:
    """Return the first replay-owned nonzero formal confirmation after warm-up.

    TradingView Pine can enter a truncated parity capture carrying a recursive
    formal state from bars before the logged window, while Python deliberately
    cold-starts at neutral.  We therefore wait until the Python replay itself
    establishes a nonzero formal state after all parity channels are finite.

    The anchor depends only on Python replay state and finite-channel
    availability; it never inspects Pine's expected formal state or economics.
    """
    ids = np.flatnonzero(common)
    if not len(ids):
        return None
    start = int(ids[0])
    formal = np.rint(np.asarray(py_formal, dtype=float)).astype(int)
    for i in range(start, len(formal)):
        if not common[i]:
            continue
        previous = formal[i - 1] if i > 0 else 0
        if formal[i] != 0 and previous == 0:
            return i
    return None


def compare(path: Path) -> dict:
    raw = pd.read_csv(path)
    columns = list(raw.columns)
    mapping = {}
    for name in ("open", "high", "low", "close", "volume"):
        mapping[name] = find_column(columns, name)
    for tv in TV_TO_PY:
        mapping[tv] = find_column(columns, tv)

    ohlcv = pd.DataFrame(
        {
            name: pd.to_numeric(raw[mapping[name]], errors="coerce")
            for name in ("open", "high", "low", "close", "volume")
        }
    )
    py = compute_python(ohlcv)

    aligned = {}
    common = np.ones(len(raw), dtype=bool)
    comparisons = {}
    for tv_name, py_name in TV_TO_PY.items():
        tv = pd.to_numeric(raw[mapping[tv_name]], errors="coerce").to_numpy(float)
        pv = pd.to_numeric(py[py_name], errors="coerce").to_numpy(float)
        if py_name in GATE_FIELDS:
            pv = pv * 100.0
        valid = np.isfinite(tv) & np.isfinite(pv)
        common &= valid
        aligned[py_name] = (tv, pv)
        if valid.any():
            diff = np.abs(tv[valid] - pv[valid])
            entry = {
                "comparable_rows": int(valid.sum()),
                "max_abs_error": float(diff.max()),
                "mean_abs_error": float(diff.mean()),
                "p99_abs_error": float(np.quantile(diff, 0.99)),
            }
            if py_name in ID_FIELDS:
                entry["agreement_rate"] = float(
                    np.mean(np.rint(tv[valid]).astype(int) == np.rint(pv[valid]).astype(int))
                )
            comparisons[py_name] = entry
        else:
            comparisons[py_name] = {"comparable_rows": 0}

    ids = np.flatnonzero(common)
    py_formal = np.rint(aligned["formal_id"][1]).astype(int)
    tv_formal = np.rint(aligned["formal_id"][0]).astype(int)

    sync_anchor = state_sync_anchor(py_formal, common)
    analysis_mask = np.zeros(len(raw), dtype=bool)
    if sync_anchor is not None:
        analysis_mask[sync_anchor:] = common[sync_anchor:]

    common_cmp = {}
    if analysis_mask.any():
        for name, (tv, pv) in aligned.items():
            a = tv[analysis_mask]
            b = pv[analysis_mask]
            diff = np.abs(a - b)
            entry = {
                "comparable_rows": int(len(a)),
                "max_abs_error": float(diff.max()),
                "mean_abs_error": float(diff.mean()),
                "p99_abs_error": float(np.quantile(diff, 0.99)),
            }
            if name in ID_FIELDS:
                entry["agreement_rate"] = float(
                    np.mean(np.rint(a).astype(int) == np.rint(b).astype(int))
                )
            common_cmp[name] = entry

    formal = common_cmp.get("formal_id", {})
    candidate = common_cmp.get("candidate_display_id", {})

    # Fresh Markup / Markdown transitions must match exactly after the
    # replay-owned state synchronization anchor.
    transition_ok = False
    episode_start_ok = False
    transition_count = 0
    python_transition_count = 0
    if analysis_mask.any():
        prev_valid = np.zeros(len(analysis_mask), dtype=bool)
        prev_valid[1:] = analysis_mask[:-1]
        pair = analysis_mask & prev_valid
        tv_fresh = pair & np.isin(tv_formal, [2, 5]) & (tv_formal != np.roll(tv_formal, 1))
        py_fresh = pair & np.isin(py_formal, [2, 5]) & (py_formal != np.roll(py_formal, 1))
        transition_count = int(tv_fresh.sum())
        python_transition_count = int(py_fresh.sum())
        transition_ok = bool(np.array_equal(tv_fresh, py_fresh))
        episode_start_ok = transition_ok

    continuous = [
        name for name in TV_TO_PY.values()
        if name not in ID_FIELDS and name != "sym_atr"
    ]
    p99 = [common_cmp.get(name, {}).get("p99_abs_error", np.inf) for name in continuous]
    sym = common_cmp.get("sym_atr", {})
    acceptance = {
        "formal_id_agreement_at_least_99_99pct": formal.get("agreement_rate", 0.0) >= 0.9999,
        "candidate_id_agreement_at_least_99_99pct": candidate.get("agreement_rate", 0.0) >= 0.9999,
        "fresh_markup_markdown_transition_exact": transition_ok,
        "episode_start_exact": episode_start_ok,
        "sym_atr_max_abs_error_at_most_1e_10": sym.get("max_abs_error", np.inf) <= 1e-10,
        "continuous_field_p99_error_at_most_0_50": bool(p99) and max(p99) <= 0.50,
    }
    acceptance["pass"] = all(acceptance.values())

    return {
        "issue": 78,
        "gate": "Python classifier parity",
        "source_csv": str(path),
        "rows": int(len(raw)),
        "all_fields_finite_rows": int(common.sum()),
        "first_all_fields_finite_row_index": int(ids[0]) if len(ids) else None,
        "state_sync_anchor_row_index": int(sync_anchor) if sync_anchor is not None else None,
        "post_sync_comparable_rows": int(analysis_mask.sum()),
        "fresh_markup_markdown_transitions_pine": transition_count,
        "fresh_markup_markdown_transitions_python": python_transition_count,
        "column_mapping": mapping,
        "comparisons": comparisons,
        "common_window_comparisons": common_cmp,
        "acceptance": acceptance,
        "notes": [
            "TradingView OHLCV is replayed exactly in Python.",
            "The state-comparison window begins at the first replay-owned nonzero Python formal confirmation after all parity channels are finite.",
            "The synchronization anchor depends only on Python replay state, not Pine expected state or economics.",
            "A parity failure authorizes implementation fixes only, never classifier retuning.",
            "No R0 / Warning-First economics are computed by this comparator.",
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    report = compare(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["acceptance"], indent=2))
    if not report["acceptance"]["pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
