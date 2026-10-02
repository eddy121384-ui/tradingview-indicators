#!/usr/bin/env python3
"""Issue #143 — preregistered historical IPI bridge attribution.

Signal-only study. No asset-return outcome is loaded.
"""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd

from issue_141_signal_bridge import (
    add_turning,
    component_score as monthly_component_score,
    regime_id,
    trigger_match,
)
from v6_6_core import (
    V66Config,
    avg_series,
    component_score as daily_component_score,
    weighted_avg_series,
)

EXPECTED_DAILY_SHA = "2ecb4d6693031020cc550bc7ed4de071282dc8ed503ddb131f170ecdaaaa2eba"
EXPECTED_STRUCT_SHA = "d5d2a60e6a343fad7ba0a7a126ce3f7911715c8792ca186a0f3bc65602ac9ead"
EXPECTED_EXACT_SHA = "1d03923503e7fe82a69b033897484c48aa646279ecf70164d090ed62a5a70719"

DEV_START = pd.Period("2007-01", "M")
DEV_END = pd.Period("2016-12", "M")
HOLD_START = pd.Period("2017-01", "M")
HOLD_END = pd.Period("2026-08", "M")

VARIANTS = ("D0", "M0", "M-BE", "M-COM", "M-OIL", "M-GAS", "M-ALL")
METRIC_KEYS = (
    "ipi_correlation",
    "ipi_slope_agreement",
    "ipi_state_agreement",
    "regime_agreement",
    "r7_precision",
    "r7_recall",
    "trigger_f1",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_source_snapshot(source_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    daily_path = source_dir / "issue-143-public-exact-ipi-daily.csv"
    struct_path = source_dir / "issue-143-structural-monthly.csv"
    manifest_path = source_dir / "issue-143-source-manifest.json"
    if sha256_file(daily_path) != EXPECTED_DAILY_SHA:
        raise RuntimeError("Issue #143 frozen daily source-panel SHA drift")
    if sha256_file(struct_path) != EXPECTED_STRUCT_SHA:
        raise RuntimeError("Issue #143 frozen structural source-panel SHA drift")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["exact_v66_signal_loaded"] is not False:
        raise RuntimeError("source acquisition firewall violated: exact signal loaded")
    if manifest["outcome_data_loaded"] is not False:
        raise RuntimeError("source acquisition firewall violated: outcome loaded")

    daily = pd.read_csv(daily_path)
    daily["date"] = pd.to_datetime(daily["date"], errors="raise")
    daily = daily.sort_values("date").set_index("date")
    for c in ["spy", "breakeven_10y", "commodity_basket", "oil", "gasoline"]:
        daily[c] = pd.to_numeric(daily[c], errors="coerce")

    structural = pd.read_csv(struct_path)
    structural["date"] = pd.to_datetime(structural["date"], errors="raise")
    structural["period"] = structural["date"].dt.to_period("M")
    if structural["period"].duplicated().any():
        raise RuntimeError("duplicate structural monthly period")
    return daily, structural, manifest


def load_exact(issue133_root: Path) -> tuple[pd.DataFrame, dict]:
    data = issue133_root / "data"
    manifest = json.loads(
        (data / "issue-133-exact-monthly-manifest.json").read_text(encoding="utf-8")
    )
    if manifest["normalized_csv_sha256"] != EXPECTED_EXACT_SHA:
        raise RuntimeError("Issue #143 exact signal manifest SHA drift")
    gz = base64.b64decode(
        (data / "issue-133-exact-monthly.csv.gz.b64").read_text().strip(),
        validate=True,
    )
    if hashlib.sha256(gz).hexdigest() != manifest["deterministic_gzip_sha256"]:
        raise RuntimeError("Issue #143 exact gzip SHA drift")
    raw = gzip.decompress(gz)
    if hashlib.sha256(raw).hexdigest() != EXPECTED_EXACT_SHA:
        raise RuntimeError("Issue #143 exact CSV SHA drift")
    x = pd.read_csv(io.BytesIO(raw))
    if list(x.columns) != ["date", "gpi", "ipi", "regime"]:
        raise RuntimeError(f"unexpected exact columns: {list(x.columns)}")
    x["date"] = pd.to_datetime(x["date"], errors="raise")
    x["period"] = x["date"].dt.to_period("M")
    for c in ("gpi", "ipi"):
        x[c] = pd.to_numeric(x[c], errors="raise")
    x["regime"] = pd.to_numeric(x["regime"], errors="raise").astype(int)
    if x["period"].duplicated().any():
        raise RuntimeError("duplicate exact period")
    return x.sort_values("period").reset_index(drop=True), manifest


def build_daily_d0(daily: pd.DataFrame) -> pd.DataFrame:
    cfg = V66Config()
    idx = daily.index
    t10 = daily["breakeven_10y"].astype(float)
    dbc = daily["commodity_basket"].astype(float)
    oil = daily["oil"].astype(float)
    gas = daily["gasoline"].astype(float)

    s_be = daily_component_score(t10, False, cfg.z_len_daily, cfg)
    s_com = daily_component_score(dbc, False, cfg.z_len_daily, cfg)
    s_oil = daily_component_score(oil, False, cfg.z_len_daily, cfg)
    s_gas = daily_component_score(gas, False, cfg.z_len_daily, cfg)
    s_energy = avg_series([s_oil, s_gas])
    ipi = weighted_avg_series([
        (s_be, cfg.w_breakeven),
        (s_com, cfg.w_commodity),
        (s_energy, cfg.w_energy),
    ])

    out = pd.DataFrame({
        "date": idx,
        "D0": ipi.to_numpy(float),
        "d0_score_breakeven": s_be.to_numpy(float),
        "d0_score_commodity": s_com.to_numpy(float),
        "d0_score_oil": s_oil.to_numpy(float),
        "d0_score_gasoline": s_gas.to_numpy(float),
    })
    out["period"] = out["date"].dt.to_period("M")
    # Exact frozen convention: final SPY-calendar observation in each month.
    out = out.groupby("period", as_index=False, sort=True).tail(1)
    return out.reset_index(drop=True)


def month_end_public_inputs(daily: pd.DataFrame) -> pd.DataFrame:
    x = daily.reset_index().copy()
    x["period"] = x["date"].dt.to_period("M")
    x = x.groupby("period", as_index=False, sort=True).tail(1).copy()
    return x.reset_index(drop=True)


def structural_basket(structural: pd.DataFrame) -> pd.Series:
    cols = [
        "Crude oil, WTI",
        "Natural gas, US",
        "Aluminum",
        "Copper",
        "Wheat, US HRW",
        "Maize",
        "Coffee, Arabica",
        "Sugar, world",
    ]
    vals = structural[cols].astype(float)
    ok = vals.notna().all(axis=1) & vals.gt(0).all(axis=1)
    out = pd.Series(np.nan, index=structural.index, dtype=float)
    out.loc[ok] = np.exp(np.log(vals.loc[ok]).mean(axis=1))
    return out


def monthly_ipi(be: pd.Series, com: pd.Series, oil: pd.Series, energy2: pd.Series) -> pd.Series:
    s_be = monthly_component_score(be)
    s_com = monthly_component_score(com)
    s_oil = monthly_component_score(oil)
    s_e2 = monthly_component_score(energy2)
    energy = pd.concat([s_oil, s_e2], axis=1).mean(axis=1, skipna=False)
    return 0.35 * s_be + 0.40 * s_com + 0.25 * energy


def build_monthly_variants(
    daily: pd.DataFrame,
    structural: pd.DataFrame,
    d0_monthly: pd.DataFrame,
) -> pd.DataFrame:
    pub = month_end_public_inputs(daily)[
        ["period", "breakeven_10y", "commodity_basket", "oil", "gasoline"]
    ].copy()
    st = structural.copy()
    st["wb_commodity_basket"] = structural_basket(st)
    st = st[[
        "period",
        "expected_inflation_10y",
        "wb_commodity_basket",
        "Crude oil, WTI",
        "Natural gas, US",
    ]].copy()
    x = pub.merge(st, on="period", how="left", validate="one_to_one")
    x = x.merge(d0_monthly[["period", "D0"]], on="period", how="left", validate="one_to_one")
    x = x.sort_values("period").reset_index(drop=True)

    x["M0"] = monthly_ipi(
        x["breakeven_10y"], x["commodity_basket"], x["oil"], x["gasoline"]
    )
    x["M-BE"] = monthly_ipi(
        x["expected_inflation_10y"], x["commodity_basket"], x["oil"], x["gasoline"]
    )
    x["M-COM"] = monthly_ipi(
        x["breakeven_10y"], x["wb_commodity_basket"], x["oil"], x["gasoline"]
    )
    x["M-OIL"] = monthly_ipi(
        x["breakeven_10y"], x["commodity_basket"], x["Crude oil, WTI"], x["gasoline"]
    )
    x["M-GAS"] = monthly_ipi(
        x["breakeven_10y"], x["commodity_basket"], x["oil"], x["Natural gas, US"]
    )
    x["M-ALL"] = monthly_ipi(
        x["expected_inflation_10y"],
        x["wb_commodity_basket"],
        x["Crude oil, WTI"],
        x["Natural gas, US"],
    )
    return x


def state3(s: pd.Series) -> pd.Series:
    a = pd.to_numeric(s, errors="coerce")
    out = pd.Series(np.nan, index=s.index, dtype=float)
    out.loc[a < -10] = -1
    out.loc[(a >= -10) & (a <= 10)] = 0
    out.loc[a > 10] = 1
    return out


def slope_agreement(exact: pd.Series, variant: pd.Series, periods: pd.Series) -> tuple[int, float | None]:
    de = exact.diff()
    dv = variant.diff()
    consecutive = periods.map(lambda p: p.ordinal).diff().eq(1)
    ok = de.notna() & dv.notna() & consecutive
    n = int(ok.sum())
    if n < 12:
        return n, None
    return n, float(np.mean(np.sign(de.loc[ok].to_numpy()) == np.sign(dv.loc[ok].to_numpy())))


def corr(exact: pd.Series, variant: pd.Series) -> float | None:
    ok = exact.notna() & variant.notna()
    if int(ok.sum()) < 12:
        return None
    e = exact.loc[ok].astype(float)
    v = variant.loc[ok].astype(float)
    if e.std(ddof=1) == 0 or v.std(ddof=1) == 0:
        return None
    return float(e.corr(v))


def prf(exact_bool: pd.Series, variant_bool: pd.Series) -> tuple[float | None, float | None]:
    tp = int((exact_bool & variant_bool).sum())
    vp = int(variant_bool.sum())
    ep = int(exact_bool.sum())
    return (float(tp / vp) if vp else None, float(tp / ep) if ep else None)


def evaluate_variant(
    exact_full: pd.DataFrame,
    variants: pd.DataFrame,
    variant: str,
    start: pd.Period,
    end: pd.Period,
) -> dict:
    merged = exact_full[["period", "gpi", "ipi", "regime"]].merge(
        variants[["period", variant]],
        on="period",
        how="inner",
        validate="one_to_one",
    )
    merged = merged.loc[merged["period"].between(start, end)].copy()
    merged = merged.loc[
        merged["gpi"].notna() & merged["ipi"].notna() & merged[variant].notna()
    ].sort_values("period").reset_index(drop=True)

    merged["variant_regime"] = [
        regime_id(g, i) for g, i in zip(merged["gpi"].astype(float), merged[variant].astype(float))
    ]
    merged["ipi_state_exact"] = state3(merged["ipi"])
    merged["ipi_state_variant"] = state3(merged[variant])
    slope_n, slope = slope_agreement(merged["ipi"], merged[variant], merged["period"])
    r7_precision, r7_recall = prf(merged["regime"].eq(7), merged["variant_regime"].eq(7))

    exact_turn = add_turning(
        merged.rename(columns={"gpi": "g", "ipi": "i", "regime": "r"})[
            ["period", "g", "i", "r"]
        ],
        "g", "i", "r", "exact",
    )
    variant_turn = add_turning(
        merged.rename(columns={"gpi": "g", variant: "i", "variant_regime": "r"})[
            ["period", "g", "i", "r"]
        ],
        "g", "i", "r", "variant",
    )
    et = exact_turn.loc[exact_turn["exact_trigger"], "period"].tolist()
    vt = variant_turn.loc[variant_turn["variant_trigger"], "period"].tolist()
    tm = trigger_match(et, vt)

    return {
        "variant": variant,
        "start": str(start),
        "end": str(end),
        "common_eligible_months": int(len(merged)),
        "ipi_correlation": corr(merged["ipi"], merged[variant]),
        "ipi_slope_n": slope_n,
        "ipi_slope_agreement": slope,
        "ipi_state_agreement": float(
            (merged["ipi_state_exact"] == merged["ipi_state_variant"]).mean()
        ) if len(merged) else None,
        "regime_agreement": float(
            (merged["regime"].astype(int) == merged["variant_regime"].astype(int)).mean()
        ) if len(merged) else None,
        "r7_precision": r7_precision,
        "r7_recall": r7_recall,
        "exact_r7_months": int(merged["regime"].eq(7).sum()),
        "variant_r7_months": int(merged["variant_regime"].eq(7).sum()),
        "trigger_precision": tm["precision"],
        "trigger_recall": tm["recall"],
        "trigger_f1": tm["f1"],
        "trigger_count_ratio": tm["count_ratio"],
        "exact_trigger_n": tm["exact_n"],
        "variant_trigger_n": tm["analogue_n"],
        "matched_trigger_n": tm["matched"],
        "trigger_pairs": tm["pairs"],
    }


def metric_damage(parent: dict, child: dict) -> dict:
    raw = {}
    clipped = {}
    for k in METRIC_KEYS:
        p = parent.get(k)
        c = child.get(k)
        d = None if p is None or c is None else float(p - c)
        raw[k] = d
        clipped[k] = None if d is None else max(0.0, d)
    finite = [v for v in clipped.values() if v is not None and np.isfinite(v)]
    score = float(np.mean(finite)) if finite else None
    return {"raw": raw, "clipped": clipped, "score": score}


def primary_cause(damages: dict[str, dict], anchor_valid: bool) -> str | None:
    if not anchor_valid:
        return None
    atomic = {
        "frequency_translation_primary": damages["frequency"]["score"],
        "breakeven_proxy_primary": damages["breakeven"]["score"],
        "commodity_proxy_primary": damages["commodity"]["score"],
        "oil_provider_primary": damages["oil_provider"]["score"],
        "gasoline_proxy_primary": damages["gasoline_proxy"]["score"],
    }
    if any(v is None for v in atomic.values()):
        return "mixed_drivers"
    ranked = sorted(atomic.items(), key=lambda kv: (-float(kv[1]), kv[0]))
    top_label, top = ranked[0]
    second = ranked[1][1]
    if top < 0.03:
        return "no_single_material_driver"
    if top - second < 0.03:
        return "mixed_drivers"
    return top_label


def interaction_residual(
    m0: dict,
    mall: dict,
    source_damages: list[dict],
) -> dict:
    out = {}
    for k in METRIC_KEYS:
        if m0.get(k) is None or mall.get(k) is None:
            out[k] = None
            continue
        total = float(m0[k] - mall[k])
        parts = [d["raw"].get(k) for d in source_damages]
        if any(x is None for x in parts):
            out[k] = None
        else:
            out[k] = float(total - sum(parts))
    return out


def run(source_dir: Path, issue133_root: Path, outdir: Path) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    daily, structural, source_manifest = load_source_snapshot(source_dir)
    exact, exact_manifest = load_exact(issue133_root)

    d0 = build_daily_d0(daily)
    variants = build_monthly_variants(daily, structural, d0)

    dev = {
        v: evaluate_variant(exact, variants, v, DEV_START, DEV_END)
        for v in VARIANTS
    }
    hold = {
        v: evaluate_variant(exact, variants, v, HOLD_START, HOLD_END)
        for v in VARIANTS
    }

    d0h = hold["D0"]
    anchor_gates = {
        "1_common_months_ge_100": d0h["common_eligible_months"] >= 100,
        "2_correlation_ge_0_90": bool(d0h["ipi_correlation"] is not None and d0h["ipi_correlation"] >= 0.90),
        "3_slope_agreement_ge_0_80": bool(d0h["ipi_slope_agreement"] is not None and d0h["ipi_slope_agreement"] >= 0.80),
        "4_ipi_state_agreement_ge_0_75": bool(d0h["ipi_state_agreement"] is not None and d0h["ipi_state_agreement"] >= 0.75),
        "5_regime_agreement_ge_0_70": bool(d0h["regime_agreement"] is not None and d0h["regime_agreement"] >= 0.70),
        "6_r7_precision_ge_0_65": bool(d0h["r7_precision"] is not None and d0h["r7_precision"] >= 0.65),
        "7_r7_recall_ge_0_65": bool(d0h["r7_recall"] is not None and d0h["r7_recall"] >= 0.65),
        "8_trigger_f1_ge_0_60": bool(d0h["trigger_f1"] is not None and d0h["trigger_f1"] >= 0.60),
    }
    anchor_valid = all(anchor_gates.values())
    verdict = "ipi_attribution_valid" if anchor_valid else "ipi_attribution_anchor_failed"

    damages = {
        "frequency": metric_damage(hold["D0"], hold["M0"]),
        "breakeven": metric_damage(hold["M0"], hold["M-BE"]),
        "commodity": metric_damage(hold["M0"], hold["M-COM"]),
        "oil_provider": metric_damage(hold["M0"], hold["M-OIL"]),
        "gasoline_proxy": metric_damage(hold["M0"], hold["M-GAS"]),
        "total_full_proxy": metric_damage(hold["M0"], hold["M-ALL"]),
    }
    cause = primary_cause(damages, anchor_valid)
    interaction = interaction_residual(
        hold["M0"],
        hold["M-ALL"],
        [
            damages["breakeven"],
            damages["commodity"],
            damages["oil_provider"],
            damages["gasoline_proxy"],
        ],
    )

    result = {
        "schema_version": 1,
        "issue": 143,
        "phase": "ipi-bridge-attribution",
        "source_panel_sha256": EXPECTED_DAILY_SHA,
        "structural_panel_sha256": EXPECTED_STRUCT_SHA,
        "exact_signal_sha256": exact_manifest["normalized_csv_sha256"],
        "development": dev,
        "holdout": hold,
        "anchor_gates": anchor_gates,
        "verdict": verdict,
        "primary_cause": cause,
        "damage": damages,
        "interaction_residual": interaction,
        "outcome_data_loaded": False,
        "historical_outcome_testing_authorized": False,
        "production_authorized": False,
    }
    (outdir / "issue-143-result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    # Compact comparison table.
    rows = []
    for period_name, metrics in (("development", dev), ("holdout", hold)):
        for variant, m in metrics.items():
            rows.append({
                "period": period_name,
                **{k: v for k, v in m.items() if k != "trigger_pairs"},
            })
    pd.DataFrame(rows).to_csv(
        outdir / "issue-143-variant-metrics.csv", index=False, float_format="%.12g"
    )

    dmg_rows = []
    for name, d in damages.items():
        row = {"comparison": name, "damage_score": d["score"]}
        for k, v in d["raw"].items():
            row[f"{k}_raw_damage"] = v
        dmg_rows.append(row)
    pd.DataFrame(dmg_rows).to_csv(
        outdir / "issue-143-attribution-damage.csv", index=False, float_format="%.12g"
    )

    print(json.dumps({
        "verdict": verdict,
        "primary_cause": cause,
        "anchor_gates": anchor_gates,
        "holdout": {v: {k: hold[v][k] for k in [
            "common_eligible_months", "ipi_correlation", "ipi_slope_agreement",
            "ipi_state_agreement", "regime_agreement", "r7_precision", "r7_recall",
            "exact_trigger_n", "variant_trigger_n", "matched_trigger_n", "trigger_f1",
            "trigger_count_ratio",
        ]} for v in VARIANTS},
        "damage_scores": {k: v["score"] for k, v in damages.items()},
        "interaction_residual": interaction,
        "outcome_data_loaded": False,
    }, indent=2, ensure_ascii=False))
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-dir", type=Path, required=True)
    ap.add_argument("--issue133-root", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    run(args.source_dir, args.issue133_root, args.output_dir)


if __name__ == "__main__":
    main()
