#!/usr/bin/env python3
"""Issue #181 (Issue #78 A9) — conditional OOS4 secondary replication stage.

Frozen by §11 of `decisions/issue-78-market-structure-a9-preregistration.md`.
This stage runs IFF at least one of D3/D4 reached a KEEP candidate on OOS3
(that gate is checked by the caller/lead; the script additionally refuses to
run unless `--confirm-oos3-keep` is passed, so OOS4 cannot be touched by
accident).

All definitions are reused by import from `analyze_issue78_market_structure_a9`
— no formula, threshold, lookback or K is changed. The frozen OOS3 HMM is
transported (frozen scaler + frozen parameters, no refit) as a transport-only
readout. OOS4 was already contacted by A5 for Core-2, so it is a secondary
replication cohort, never pristine.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

import analyze_issue78_market_structure_a9 as a9
from analyze_issue78_oos4_validation_a5 import EXPECTED_OOS4_FIGI_SET_SHA

G6_SIGN_FRAC = 2 / 3
G6_REVERSAL_FRAC = 0.20


def g6_for_dimension(dim: str, oos3_sep: pd.DataFrame, oos4_sep: pd.DataFrame,
                     gate_eval: dict) -> dict:
    """Frozen §9 G6 rule for one dimension (pure function, testable).

    `≥⌈2/3⌉` of the OOS3 separated properties keep the same sign on OOS4, and
    no adequate OOS4 property reverses with |Δ| ≥ 0.20·sd_OOS4.
    """
    props = list(
        gate_eval["gates"][dim]["G4_separated_properties"]
    ) if gate_eval else []
    o3 = oos3_sep[(oos3_sep["dim"] == dim) & (oos3_sep["scope_kind"] == "ALL")]
    o4 = oos4_sep[(oos4_sep["dim"] == dim) & (oos4_sep["scope_kind"] == "ALL")]
    o3_sign = {
        str(r["property"]): np.sign(float(r["equal_stock_mean_delta"]))
        for _, r in o3.iterrows()
        if np.isfinite(r["equal_stock_mean_delta"])
    }
    rows = []
    same = 0
    evaluated = 0
    for prop in props:
        m = o4[o4["property"] == prop]
        if m.empty or int(m["stocks"].iloc[0]) < a9.MIN_AGG_STOCKS:
            rows.append({"property": prop, "oos4_stocks": 0, "same_sign": None})
            continue
        r = m.iloc[0]
        evaluated += 1
        s4 = np.sign(float(r["equal_stock_mean_delta"]))
        ok = bool(s4 != 0 and s4 == o3_sign.get(prop, 0))
        same += int(ok)
        rows.append(
            {
                "property": prop,
                "oos4_stocks": int(r["stocks"]),
                "oos3_delta": None,
                "oos4_delta": float(r["equal_stock_mean_delta"]),
                "oos4_abs_delta_over_sd": float(r["abs_delta_over_sd"]),
                "same_sign": ok,
            }
        )
    reversals = []
    for _, r in o4.iterrows():
        prop = str(r["property"])
        if int(r["stocks"]) < a9.MIN_AGG_STOCKS:
            continue
        s3 = o3_sign.get(prop)
        if s3 is None or s3 == 0:
            continue
        s4 = np.sign(float(r["equal_stock_mean_delta"]))
        if (
            s4 != 0
            and s4 != s3
            and np.isfinite(r["abs_delta_over_sd"])
            and float(r["abs_delta_over_sd"]) >= G6_REVERSAL_FRAC
        ):
            reversals.append(
                {
                    "property": prop,
                    "oos3_sign": float(s3),
                    "oos4_delta": float(r["equal_stock_mean_delta"]),
                    "oos4_abs_delta_over_sd": float(r["abs_delta_over_sd"]),
                }
            )
    need = math.ceil(G6_SIGN_FRAC * evaluated) if evaluated else 0
    available = evaluated >= 2
    passed = bool(
        available
        and same >= math.ceil(G6_SIGN_FRAC * len(props))
        and not reversals
    )
    return {
        "dim": dim,
        "oos3_separated_properties": props,
        "oos4_evaluated_properties": evaluated,
        "same_sign": same,
        "need_same_sign": int(math.ceil(G6_SIGN_FRAC * len(props))) if props else 0,
        "rows": rows,
        "reversals": reversals,
        "available": bool(available),
        "pass": passed,
    }


def frozen_model_from(centroids_path: Path) -> tuple[dict, np.ndarray, np.ndarray]:
    data = json.loads(centroids_path.read_text(encoding="utf-8"))
    model = {
        "K": int(data["K"]),
        "A": np.asarray(data["transition_model"], dtype=float),
        "mu": np.asarray(data["model_mu_std"], dtype=float),
        "var": np.asarray(data["model_var_std"], dtype=float),
        "pi": np.asarray(data["initial_model"], dtype=float),
    }
    mean = np.asarray(data["scaler_mean"], dtype=float)
    std = np.asarray(data["scaler_std"], dtype=float)
    return model, mean, std


def run(args) -> dict:
    universe_path = args.universe.resolve()
    manifest_path = args.manifest.resolve()
    raw_dir = args.raw_dir.resolve()
    out = args.out.resolve()
    discovery = args.discovery_out.resolve()

    if "oos4" not in str(universe_path).lower() or "snapshot" not in str(
        manifest_path
    ).lower():
        raise SystemExit("OOS4 stage must contact an OOS4 snapshot only")
    gate_eval = json.loads((discovery / "gate_eval.json").read_text(encoding="utf-8"))
    keep = [
        dim for dim in a9.DIMS
        if gate_eval["classification"].get(dim.upper()) == "KEEP_AS_ATLAS_DIMENSION"
        or gate_eval["classification"].get(dim.upper()) == "KEEP_AS_DESCRIPTIVE_ONLY"
    ]
    if not args.confirm_oos3_keep:
        raise SystemExit(
            "refusing to contact OOS4: pass --confirm-oos3-keep only after an "
            "OOS3 KEEP candidate exists (frozen §11)"
        )

    oos3_universe = set(
        pd.read_csv(args.discovery_universe)["figi"].astype(str).tolist()
    )
    oos4_universe_frame = pd.read_csv(universe_path)
    oos4_universe = set(oos4_universe_frame["figi"].astype(str).tolist())
    overlap = sorted(oos3_universe & oos4_universe)
    if overlap:
        raise SystemExit(f"OOS4 overlaps the discovery cohort: {len(overlap)} FIGIs")

    cohort = a9.collect_cohort(
        universe_path, manifest_path, raw_dir, args.classifier.resolve(),
        EXPECTED_OOS4_FIGI_SET_SHA, limit=args.limit, offset=args.offset,
    )
    out.mkdir(parents=True, exist_ok=True)

    redun_stock = cohort["redundancy_per_stock"]
    redun_sum = a9.redundancy_summary(redun_stock)
    redun_sleeve = a9.redundancy_sleeve_summary(redun_stock)
    sep_stock = cohort["separation_per_stock"]
    sep_sum = a9.separation_summary(sep_stock, cohort["pooled_sd"])
    cond_stock = cohort["conditional_per_stock"]
    cond_sum = a9.conditional_summary(cond_stock)
    breadth = a9.breadth_table(
        sep_sum, cohort["path_all_per_stock"], cohort["coverage"]
    )
    path_all_sum = a9.a1.aggregate_a1_cells(
        cohort["path_all_per_stock"], ["test", "state", "block", "horizon"]
    )
    map_sum = a9.a1.aggregate_a1_cells(
        cohort["map_per_stock"], ["test", "state", "block", "horizon"]
    )

    oos3_sep = pd.read_csv(discovery / "separation_summary.csv")
    classes = {
        dim: a9.evaluate_dimension(dim, redun_sum, sep_sum, cond_sum, breadth)
        for dim in a9.DIMS
    }
    g6 = {dim: g6_for_dimension(dim, oos3_sep, sep_sum, gate_eval) for dim in a9.DIMS}

    final = {}
    for dim in a9.DIMS:
        base = classes[dim]["classification"]
        if base == "KEEP_AS_ATLAS_DIMENSION":
            if g6[dim]["available"] and not g6[dim]["pass"]:
                final[dim] = "KEEP_AS_DESCRIPTIVE_ONLY"
            else:
                final[dim] = "KEEP_AS_ATLAS_DIMENSION"
        else:
            final[dim] = base
    d3_rule = a9.resolve_d3(classes["d3"], classes["d3_rob"])
    if final["d3"] == "KEEP_AS_ATLAS_DIMENSION":
        final["d3"] = d3_rule["headline"] if d3_rule["headline"] == "KEEP_AS_ATLAS_DIMENSION" else "KEEP_AS_DESCRIPTIVE_ONLY"
    classification = {
        "D3": final["d3"],
        "D4": final["d4"],
        "D3_primary_rv20": final["d3"],
        "D3_robustness_natr20": final["d3_rob"],
        "d3_rule": d3_rule,
        "oos3_gate_classification": gate_eval["classification"],
    }

    # ---- frozen OOS3 HMM transported to OOS4 (no refit) ----
    model, mean, std = frozen_model_from(discovery / "hmm_centroids.json")
    dec = a9.decode_hmm(model, cohort["hmm_entries"], mean, std)
    diag = a9.hmm_diagnostics(
        model, dec, cohort["hmm_entries"], mean, std,
        cohort["block_code"], cohort["sleeves"], cohort["pooled_sd"],
    )
    transport_verdict = a9.hmm_verdict(diag)

    def emit(name: str, frame: pd.DataFrame) -> None:
        frame.to_csv(out / name, index=False)

    emit("coverage.csv", cohort["coverage"])
    emit("redundancy_summary.csv", redun_sum)
    emit("redundancy_sleeve_summary.csv", redun_sleeve)
    emit("separation_per_stock.csv", sep_stock)
    emit("separation_summary.csv", sep_sum)
    emit("conditional_summary.csv", cond_sum)
    emit("path_summary.csv", path_all_sum)
    emit("map_summary.csv", map_sum)
    emit("breadth.csv", breadth)
    emit("oos4_hmm_state_summary.csv", a9.hmm_state_summary(diag))
    emit("oos4_hmm_transition.csv", a9.hmm_transition_table(diag))
    emit("oos4_hmm_stability.csv", a9.hmm_stability_table(diag))
    emit("oos4_hmm_path_summary.csv", a9.hmm_path_summary(diag, cohort["hmm_entries"]))
    emit("oos4_hmm_pair_separation.csv", a9.hmm_pair_table(diag))

    (out / "g6.json").write_text(json.dumps(g6, indent=2, default=str) + "\n",
                                 encoding="utf-8")
    (out / "gate_eval_oos4.json").write_text(
        json.dumps(
            {
                "gates": classes,
                "g6": g6,
                "classification": classification,
                "thresholds": gate_eval["thresholds"],
            },
            indent=2, default=str,
        ) + "\n",
        encoding="utf-8",
    )
    (out / "oos4_hmm_transport.json").write_text(
        json.dumps(transport_verdict, indent=2) + "\n", encoding="utf-8"
    )
    summary = {
        "integrity": {
            "issue": 78,
            "child_issue": 181,
            "stage": "A9 conditional OOS4 secondary replication (frozen §11)",
            "role": "secondary replication / transport; never pristine (A5 already contacted OOS4)",
            "figi_set_sha256": cohort["figi_set_sha256"],
            "universe_sha256": a9.sha256_file(universe_path),
            "manifest_sha256": a9.sha256_file(manifest_path),
            "classifier_blob": cohort["blob"],
            "stocks": int(len(cohort["universe"])),
            "overlap_with_discovery_figis": len(overlap),
            "atlas_ready_bars": int(cohort["coverage"]["atlas_ready_rows"].sum()),
            "oos5_touched": False,
        },
        "prereg_commit": gate_eval.get("prereg_commit", None),
        "frozen_discovery_gate_eval_sha256": a9.sha256_file(discovery / "gate_eval.json"),
        "classification": classification,
        "g6": g6,
        "oos4_transport_verdict": transport_verdict,
        "notes": [
            "All definitions reused by import from the frozen A9 analyzer.",
            "The OOS3 HMM was transported with the frozen scaler and parameters; no refit.",
            "OOS4 is a secondary replication cohort and not fresh production validation.",
        ],
    }
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8"
    )
    files = sorted(
        p.name for p in out.iterdir()
        if p.is_file() and p.name != "bundle_hashes.json"
    )
    (out / "bundle_hashes.json").write_text(
        json.dumps(
            {
                "figi_set_sha256": cohort["figi_set_sha256"],
                "universe_sha256": a9.sha256_file(universe_path),
                "manifest_sha256": a9.sha256_file(manifest_path),
                "classifier_blob": cohort["blob"],
                "files": {name: a9.sha256_file(out / name) for name in files},
            },
            indent=2, default=str,
        ) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, default=str))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--raw-dir", type=Path, required=True)
    ap.add_argument("--classifier", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--discovery-out", type=Path, required=True)
    ap.add_argument("--discovery-universe", type=Path, required=True)
    ap.add_argument("--confirm-oos3-keep", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--offset", type=int, default=0)
    args = ap.parse_args()
    run(args)


if __name__ == "__main__":
    main()
