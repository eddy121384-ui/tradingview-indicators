#!/usr/bin/env python3
"""Issue #154 — TradingView-native V6.6 reconstruction parity.

Uses repository-frozen TradingView Official MCP daily source snapshots.
Signal-only: no asset-return outcome data is loaded.
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

from v6_6_core import V66Config, compute_v66

EXPECTED_EXACT_SHA = "1d03923503e7fe82a69b033897484c48aa646279ecf70164d090ed62a5a70719"

SOURCE_MAP = {
    "AMEX:SPY": ("AMEX_SPY.csv", "spy", "e5ee0fb6087b9f0c89037160a312f39aa38ffc8daecd5d41fe3fcaaaeb79dde0"),
    "AMEX:IWM": ("AMEX_IWM.csv", "iwm", "67ebc35dcd7436764c1ac30f0f4be8420cc1f03c20c8d622aca3cae340b29947"),
    "AMEX:RSP": ("AMEX_RSP.csv", "rsp", "2170f3ea422be57c1447d7f0cda3f038cb5c52effbc0a1558b3cb38afca5d0dd"),
    "AMEX:XLY": ("AMEX_XLY.csv", "xly", "b51af9a8d525d760ceff2fb591ab9370648cbdfdd602766506ca4deeacd7da86"),
    "AMEX:XLP": ("AMEX_XLP.csv", "xlp", "8a5ad574a60370d89f4ce7bc78dc5e7a066188f43039277f42f821de289f23b4"),
    "AMEX:XLI": ("AMEX_XLI.csv", "xli", "32f0d0b64b578648f74f2c08a5f981accab3cdcef3fc1d1f6f32c4df9afde851"),
    "AMEX:XLU": ("AMEX_XLU.csv", "xlu", "a2f589f5b86b3d2ab48dd968f2d706e709a2f930e9593b93baa01316d6340788"),
    "COMEX:HG1!": ("COMEX_HG1_.csv", "copper", "479c6ab99b4a0d3297f7cdda73e9ee6867080d0d621c4d12b54208abfb58dbeb"),
    "COMEX:GC1!": ("COMEX_GC1_.csv", "gold", "1ee2cfb670906eb551723cdcf106eaff73d82d35d0064d40f34cc1c6c55eed36"),
    "FRED:T10YIE": ("FRED_T10YIE.csv", "breakeven_10y", "7475f58cefa2e1f8f0507dd5ebd5bacdb3990aa2fa700d8dc99560c957292928"),
    "AMEX:DBC": ("AMEX_DBC.csv", "commodity_basket", "8f5fa850595eab6c7289ced819f48b9fdfd663b3e86eda19b5c644c4ad8a8b2a"),
    "NYMEX:CL1!": ("NYMEX_CL1_.csv", "oil", "2d69b7873d71cce8ac5a511c318163976d594e5015cb08cfc048f07861c00172"),
    "NYMEX:RB1!": ("NYMEX_RB1_.csv", "gasoline", "ff674b492bb148337107715b7a2ac0448a260c138ca5faafd1cf1ae57d8518cd"),
}

GPI_COMPONENTS = [
    "score_iwm_spy",
    "score_rsp_spy",
    "score_xly_xlp",
    "score_xli_xlu",
    "score_copper_gold",
]
IPI_COMPONENTS = [
    "score_t10yie",
    "score_commodity_basket",
    "score_oil",
    "score_gasoline",
]


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_one_source(path: Path, expected_sha: str) -> pd.Series:
    raw = path.read_bytes()
    observed = sha256_bytes(raw)
    if observed != expected_sha:
        raise RuntimeError(f"source SHA drift for {path.name}: {observed} != {expected_sha}")
    x = pd.read_csv(io.BytesIO(raw))
    if list(x.columns) != ["date", "timestamp_utc", "close"]:
        raise RuntimeError(f"unexpected source columns in {path.name}: {list(x.columns)}")
    x["date"] = pd.to_datetime(x["date"], errors="raise")
    x["timestamp_utc"] = pd.to_numeric(x["timestamp_utc"], errors="raise").astype(np.int64)
    x["close"] = pd.to_numeric(x["close"], errors="raise").astype(float)
    x = x.sort_values(["date", "timestamp_utc"]).drop_duplicates("date", keep="last")
    if x["date"].duplicated().any():
        raise RuntimeError(f"duplicate normalized date in {path.name}")
    return x.set_index("date")["close"].sort_index()


def load_tv_panel(source_dir: Path) -> tuple[pd.DataFrame, dict]:
    manifest = json.loads(
        (source_dir / "issue-154-source-manifest.json").read_text(encoding="utf-8")
    )
    if manifest["exact_v66_signal_loaded"] is not False:
        raise RuntimeError("Issue #154 Phase-A firewall violation: exact signal loaded")
    if manifest["outcome_data_loaded"] is not False:
        raise RuntimeError("Issue #154 Phase-A firewall violation: outcome loaded")

    series: dict[str, pd.Series] = {}
    meta = {}
    for symbol, (filename, col, expected_sha) in SOURCE_MAP.items():
        s = load_one_source(source_dir / filename, expected_sha)
        series[col] = s
        meta[symbol] = {
            "column": col,
            "rows": int(len(s)),
            "first_date": s.index.min().date().isoformat(),
            "last_date": s.index.max().date().isoformat(),
            "sha256": expected_sha,
        }

    spy_dates = series["spy"].index
    union = spy_dates
    for s in series.values():
        union = union.union(s.index)
    union = union.sort_values()

    # Build on the union calendar first so Sunday-evening UTC futures daily bars
    # can become the most recent already-observed value for Monday's SPY bar.
    panel = pd.DataFrame(index=union)
    for col, s in series.items():
        panel[col] = s.reindex(union)
    panel = panel.sort_index().ffill()
    panel = panel.reindex(spy_dates)

    # No backward fill: before first true observation each source must stay NA.
    for col, s in series.items():
        panel.loc[panel.index < s.index.min(), col] = np.nan

    panel.index.name = "date"
    return panel, meta


def load_exact(issue133_root: Path) -> tuple[pd.DataFrame, dict]:
    data = issue133_root / "data"
    manifest = json.loads(
        (data / "issue-133-exact-monthly-manifest.json").read_text(encoding="utf-8")
    )
    if manifest["normalized_csv_sha256"] != EXPECTED_EXACT_SHA:
        raise RuntimeError("Issue #154 exact manifest SHA drift")
    gz = base64.b64decode(
        (data / "issue-133-exact-monthly.csv.gz.b64").read_text().strip(),
        validate=True,
    )
    if hashlib.sha256(gz).hexdigest() != manifest["deterministic_gzip_sha256"]:
        raise RuntimeError("Issue #154 exact gzip SHA drift")
    raw = gzip.decompress(gz)
    if hashlib.sha256(raw).hexdigest() != EXPECTED_EXACT_SHA:
        raise RuntimeError("Issue #154 exact CSV SHA drift")
    x = pd.read_csv(io.BytesIO(raw))
    if list(x.columns) != ["date", "gpi", "ipi", "regime"]:
        raise RuntimeError(f"unexpected exact columns: {list(x.columns)}")
    x["date"] = pd.to_datetime(x["date"], errors="raise")
    x["period"] = x["date"].dt.to_period("M")
    x["gpi"] = pd.to_numeric(x["gpi"], errors="raise")
    x["ipi"] = pd.to_numeric(x["ipi"], errors="raise")
    x["regime"] = pd.to_numeric(x["regime"], errors="raise").astype(int)
    if x["period"].duplicated().any():
        raise RuntimeError("duplicate exact month")
    return x.sort_values("period").reset_index(drop=True), manifest


def regime_id(gpi: float, ipi: float) -> int:
    g = 1 if gpi > 10.0 else (-1 if gpi < -10.0 else 0)
    i = 1 if ipi > 10.0 else (-1 if ipi < -10.0 else 0)
    mapping = {
        (1, -1): 1, (1, 0): 2, (1, 1): 3,
        (0, -1): 4, (0, 0): 5, (0, 1): 6,
        (-1, -1): 7, (-1, 0): 8, (-1, 1): 9,
    }
    return mapping[(g, i)]


def assign_episode_id(regime: pd.Series, periods: pd.Series) -> pd.Series:
    out = []
    eid = 0
    prev_r7 = False
    prev_ord = None
    for r, p in zip(regime, periods):
        is_r7 = pd.notna(r) and int(r) == 7
        ord_ = p.ordinal
        consecutive = prev_ord is not None and ord_ == prev_ord + 1
        if is_r7 and (not prev_r7 or not consecutive):
            eid += 1
        out.append(eid if is_r7 else 0)
        prev_r7 = is_r7
        prev_ord = ord_
    return pd.Series(out, index=regime.index, dtype=int)


def add_turning(frame: pd.DataFrame, gcol: str, icol: str, rcol: str, prefix: str) -> pd.DataFrame:
    x = frame.copy().sort_values("period").reset_index(drop=True)
    dg = x[gcol].diff()
    di = x[icol].diff()
    gturn = (dg > 0) & (dg.shift(1) <= 0)
    iturn = (di > 0) & (di.shift(1) <= 0)
    grecent = gturn.rolling(3, min_periods=3).max().fillna(0).astype(bool)
    irecent = iturn.rolling(3, min_periods=3).max().fillna(0).astype(bool)
    x[f"{prefix}_episode_id"] = assign_episode_id(x[rcol], x["period"])
    candidate = x[rcol].eq(7) & grecent & irecent & x[gcol].notna() & x[icol].notna()
    trigger = pd.Series(False, index=x.index, dtype=bool)
    for _, group in x.loc[x[f"{prefix}_episode_id"].gt(0)].groupby(
        f"{prefix}_episode_id", sort=True
    ):
        hits = group.index[candidate.loc[group.index]]
        if len(hits):
            trigger.loc[hits[0]] = True
    x[f"{prefix}_trigger"] = trigger
    return x


def trigger_match(exact_periods: list[pd.Period], recon_periods: list[pd.Period]) -> dict:
    candidates = []
    for e in exact_periods:
        for a in recon_periods:
            dist = abs(e.ordinal - a.ordinal)
            if dist <= 1:
                candidates.append((dist, e.ordinal, a.ordinal, e, a))
    candidates.sort(key=lambda z: (z[0], z[1], z[2]))
    used_e: set[int] = set()
    used_a: set[int] = set()
    pairs = []
    for dist, eo, ao, ep, ap in candidates:
        if eo in used_e or ao in used_a:
            continue
        used_e.add(eo)
        used_a.add(ao)
        pairs.append({"exact": str(ep), "reconstructed": str(ap), "month_distance": int(dist)})
    en, an, matched = len(exact_periods), len(recon_periods), len(pairs)
    precision = float(matched / an) if an else (0.0 if en else None)
    recall = float(matched / en) if en else None
    if precision is None or recall is None:
        f1 = None
    elif precision + recall == 0:
        f1 = 0.0
    else:
        f1 = float(2 * precision * recall / (precision + recall))
    return {
        "exact_n": en,
        "reconstructed_n": an,
        "matched": matched,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "count_ratio": float(an / en) if en else None,
        "pairs": pairs,
    }


def r7_precision_recall(x: pd.DataFrame) -> dict:
    e = x["regime"].eq(7)
    a = x["regime_r"].eq(7)
    tp = int((e & a).sum())
    ap = int(a.sum())
    ep = int(e.sum())
    return {
        "true_positive_months": tp,
        "reconstructed_r7_months": ap,
        "exact_r7_months": ep,
        "precision": float(tp / ap) if ap else None,
        "recall": float(tp / ep) if ep else None,
    }


def verdict_from_metrics(m: dict) -> tuple[str, dict]:
    gates = {
        "common_months_ge_180": m["common_months"] >= 180,
        "gpi_corr_ge_0_995": m["gpi_correlation"] >= 0.995,
        "ipi_corr_ge_0_995": m["ipi_correlation"] >= 0.995,
        "gpi_mae_le_1_50": m["gpi_mae"] <= 1.50,
        "ipi_mae_le_1_50": m["ipi_mae"] <= 1.50,
        "regime_agreement_ge_0_95": m["regime_agreement"] >= 0.95,
        "r7_precision_ge_0_90": m["r7"]["precision"] is not None and m["r7"]["precision"] >= 0.90,
        "r7_recall_ge_0_90": m["r7"]["recall"] is not None and m["r7"]["recall"] >= 0.90,
        "trigger_f1_ge_0_80": m["triggers"]["f1"] is not None and m["triggers"]["f1"] >= 0.80,
        "trigger_count_ratio_0_80_to_1_25": (
            m["triggers"]["count_ratio"] is not None
            and 0.80 <= m["triggers"]["count_ratio"] <= 1.25
        ),
    }
    if not gates["common_months_ge_180"]:
        verdict = "tv_native_reconstruction_inconclusive_sample"
    elif all(gates.values()):
        verdict = "tv_native_reconstruction_passed"
    else:
        verdict = "tv_native_reconstruction_failed"
    return verdict, gates


def run(source_dir: Path, issue133_root: Path, outdir: Path) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)

    panel, source_meta = load_tv_panel(source_dir)
    cfg = V66Config()
    daily = compute_v66(panel, cfg)

    full = daily[GPI_COMPONENTS + IPI_COMPONENTS].notna().all(axis=1)
    daily["full_composition"] = full
    daily["regime_r"] = [
        regime_id(g, i) if ok and np.isfinite(g) and np.isfinite(i) else np.nan
        for g, i, ok in zip(daily["GPI"], daily["IPI"], full)
    ]

    export = daily.copy()
    export.insert(0, "date", export.index.strftime("%Y-%m-%d"))
    export.to_csv(
        outdir / "issue-154-daily-reconstruction.csv",
        index=False,
        float_format="%.12g",
    )

    m = daily.copy()
    m["period"] = m.index.to_period("M")
    monthly = m.groupby("period", sort=True).tail(1).copy()
    monthly["period"] = monthly.index.to_period("M")
    monthly = monthly.loc[monthly["full_composition"]].copy()

    exact, exact_manifest = load_exact(issue133_root)
    recon = monthly.reset_index(names="recon_date")[
        ["period", "recon_date", "GPI", "IPI", "regime_r"]
    ]
    x = exact.merge(recon, on="period", how="inner", validate="one_to_one")
    if x.empty:
        raise RuntimeError("Issue #154 parity has zero common months")

    gerr = (x["GPI"] - x["gpi"]).abs()
    ierr = (x["IPI"] - x["ipi"]).abs()
    g_corr = float(x["GPI"].corr(x["gpi"]))
    i_corr = float(x["IPI"].corr(x["ipi"]))
    regime_agreement = float(x["regime_r"].astype(int).eq(x["regime"]).mean())
    r7 = r7_precision_recall(x)

    exact_turn = add_turning(
        x[["period", "gpi", "ipi", "regime"]], "gpi", "ipi", "regime", "exact"
    )
    recon_turn = add_turning(
        x[["period", "GPI", "IPI", "regime_r"]], "GPI", "IPI", "regime_r", "recon"
    )
    et = exact_turn.loc[exact_turn["exact_trigger"], "period"].tolist()
    rt = recon_turn.loc[recon_turn["recon_trigger"], "period"].tolist()
    triggers = trigger_match(et, rt)

    metrics = {
        "common_months": int(len(x)),
        "first_common_month": str(x["period"].min()),
        "last_common_month": str(x["period"].max()),
        "gpi_correlation": g_corr,
        "ipi_correlation": i_corr,
        "gpi_mae": float(gerr.mean()),
        "ipi_mae": float(ierr.mean()),
        "gpi_max_abs_error": float(gerr.max()),
        "ipi_max_abs_error": float(ierr.max()),
        "regime_agreement": regime_agreement,
        "r7": r7,
        "triggers": triggers,
    }
    verdict, gates = verdict_from_metrics(metrics)

    parity = x.copy()
    parity["gpi_abs_error"] = gerr
    parity["ipi_abs_error"] = ierr
    parity.to_csv(
        outdir / "issue-154-monthly-parity.csv",
        index=False,
        float_format="%.12g",
    )

    result = {
        "schema_version": 1,
        "issue": 154,
        "phase": "tv-native-reconstruction-parity",
        "source": {
            "connector": "TradingView Official MCP",
            "symbols": source_meta,
            "full_composition_first_daily_date": (
                daily.index[full].min().date().isoformat() if full.any() else None
            ),
            "full_composition_last_daily_date": (
                daily.index[full].max().date().isoformat() if full.any() else None
            ),
        },
        "exact_target_sha256": exact_manifest["normalized_csv_sha256"],
        "metrics": metrics,
        "gates": gates,
        "verdict": verdict,
        "autopsy_authorized": verdict == "tv_native_reconstruction_passed",
        "outcome_data_loaded": False,
        "production_authorized": False,
    }
    (outdir / "issue-154-parity-result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
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
