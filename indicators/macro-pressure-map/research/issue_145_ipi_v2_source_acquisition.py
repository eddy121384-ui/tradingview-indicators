#!/usr/bin/env python3
"""Issue #145 Phase A — source-only acquisition for IPI Bridge v2.

Hard firewall:
- no exact V6.6 signal is loaded;
- no asset-return outcome is loaded.

Frozen source families:
- Deutsche Bank DBIQ public REST data for DBLCDBCE;
- FRED/EIA MGASNYH monthly gasoline;
- frozen Issue #141 Cleveland expected inflation and World Bank WTI.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

import issue_141_source_acquisition as i141

DBIQ_BASE = "https://index.db.com/dbiq-web/rest/webdata/95400"
DBIQ_META_URL = DBIQ_BASE
DBIQ_GRAPH_URL = DBIQ_BASE + "/graphData"
DBIQ_MONTHLY_URL = DBIQ_BASE + "/monthlyReturns"
DBIQ_RETURN_URL = DBIQ_BASE + "/returnData"
GRETL_COMMIT = "65dc8bdfb56feb64a19c36d38f696e7797591eb6"
GRETL_IDX_URL = (
    "https://raw.githubusercontent.com/gretl-project/gretl/"
    + GRETL_COMMIT + "/share/bcih/fedstl.idx"
)
GRETL_DAT_URL = (
    "https://raw.githubusercontent.com/gretl-project/gretl/"
    + GRETL_COMMIT + "/share/bcih/fedstl.dat"
)
SOURCE_END = pd.Period("2026-03", "M")

EXPECTED_I141_SHA = {
    "world_bank_monthly": "9fdcfa8a2aed9a1bb545a10c1a5ce036c6a0acd4766f450424ca800b4b5a0225",
    "cleveland_inflation_expectations": "20701ccf394d280fe1db38fa9def5628f2385dd0aef148ff989e33ff15caba95",
}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def fetch_bytes(url: str, attempts: int = 4) -> bytes:
    last: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            r = requests.get(
                url,
                headers={"User-Agent": "tradingview-indicators-research/issue-145"},
                timeout=(15, 45),
            )
            r.raise_for_status()
            return r.content
        except Exception as exc:
            last = exc
            if attempt < attempts:
                time.sleep(2 ** (attempt - 1))
    raise RuntimeError(f"failed to fetch {url}: {last}")


def load_dbiq() -> tuple[pd.DataFrame, dict, dict[str, bytes]]:
    raw_meta = fetch_bytes(DBIQ_META_URL)
    raw_graph = fetch_bytes(DBIQ_GRAPH_URL)
    raw_monthly = fetch_bytes(DBIQ_MONTHLY_URL)
    raw_return = fetch_bytes(DBIQ_RETURN_URL)

    # Metadata response shape can evolve; fail closed on identity strings.
    meta_text = raw_meta.decode("utf-8", errors="replace")
    if "DBIQ Optimum Yield Diversified Commodity Index Excess Return" not in meta_text:
        raise RuntimeError("DBIQ metadata identity mismatch")
    if "DBLCDBCE" not in meta_text:
        raise RuntimeError("DBIQ metadata ticker mismatch")
    if "1988" not in meta_text:
        raise RuntimeError("DBIQ metadata no longer exposes 1988 historical inception")

    graph = json.loads(raw_graph)
    if not isinstance(graph, list) or not graph:
        raise RuntimeError("DBIQ graphData is not a non-empty list")
    daily = pd.DataFrame(graph)
    if not {"priceDate", "level"}.issubset(daily.columns):
        raise RuntimeError(f"DBIQ graphData columns changed: {daily.columns.tolist()}")
    daily["date"] = pd.to_datetime(daily["priceDate"], errors="raise")
    daily["level"] = pd.to_numeric(daily["level"], errors="coerce")
    daily = daily[["date", "level"]].dropna().sort_values("date")
    daily = daily.loc[daily["level"] > 0].drop_duplicates("date", keep="last").reset_index(drop=True)

    if daily.empty:
        raise RuntimeError("DBIQ graphData has no usable levels")
    if daily.iloc[0]["date"].date().isoformat() != "1988-12-02":
        raise RuntimeError(f"DBIQ first date drift: {daily.iloc[0]['date']}")
    if abs(float(daily.iloc[0]["level"]) - 100.0) > 1e-12:
        raise RuntimeError(f"DBIQ first level drift: {daily.iloc[0]['level']}")
    if daily["date"].max() < pd.Timestamp("2026-08-31"):
        raise RuntimeError(f"DBIQ graphData ends too early: {daily['date'].max()}")

    daily["period"] = daily["date"].dt.to_period("M")
    monthly = daily.groupby("period", as_index=False, sort=True).tail(1).copy()
    monthly = monthly.sort_values("period").reset_index(drop=True)
    monthly = monthly.loc[monthly["period"] <= SOURCE_END].copy()
    monthly["dbiq_return_pct"] = monthly["level"].pct_change() * 100.0
    monthly = monthly.rename(columns={"level": "dbiq_level"})
    monthly["date"] = monthly["period"].dt.to_timestamp("M")

    if monthly["period"].min() != pd.Period("1988-12", "M"):
        raise RuntimeError(f"DBIQ monthly first period drift: {monthly['period'].min()}")
    if monthly["period"].max() != SOURCE_END:
        raise RuntimeError(f"DBIQ monthly last period drift: {monthly['period'].max()}")

    # Cross-check official monthlyReturns against month-end returns computed
    # from the official graphData levels. monthlyReturns is rounded to 2 dp.
    mr = json.loads(raw_monthly)
    current_year = int(mr.get("currentYear"))
    matrix = mr.get("monthlyReturns")
    if not isinstance(matrix, list) or not matrix:
        raise RuntimeError("DBIQ monthlyReturns payload changed")
    start_year = current_year - len(matrix) + 1

    api_rows = []
    for yi, row in enumerate(matrix):
        if not isinstance(row, list):
            continue
        year = start_year + yi
        for mi, value in enumerate(row[:12], start=1):
            if value is None:
                continue
            api_rows.append({
                "period": pd.Period(year=year, month=mi, freq="M"),
                "api_return_pct": float(value),
            })
    api = pd.DataFrame(api_rows)
    chk = monthly[["period", "dbiq_return_pct"]].merge(api, on="period", how="inner")
    chk = chk.loc[
        chk["dbiq_return_pct"].notna()
        & chk["api_return_pct"].notna()
        & chk["period"].le(SOURCE_END)
    ].copy()
    if len(chk) < 430:
        raise RuntimeError(f"DBIQ monthly return cross-check too short: {len(chk)}")
    chk["abs_diff"] = (chk["dbiq_return_pct"] - chk["api_return_pct"]).abs()
    max_diff = float(chk["abs_diff"].max())
    if max_diff > 0.011:
        bad = chk.nlargest(5, "abs_diff").to_dict("records")
        raise RuntimeError(f"DBIQ graph/monthly-return mismatch max={max_diff}: {bad}")

    return monthly.reset_index(drop=True), {
        "index_id": 95400,
        "index_name": "DBIQ Optimum Yield Diversified Commodity Index Excess Return",
        "ticker": "DBLCDBCE",
        "benchmark_family": "Commodity Futures",
        "historical_inception": "1988-12-02",
        "source_mode": "public_official_rest_graphData",
        "meta_url": DBIQ_META_URL,
        "graph_url": DBIQ_GRAPH_URL,
        "monthly_returns_url": DBIQ_MONTHLY_URL,
        "return_data_url": DBIQ_RETURN_URL,
        "raw_sha256": {
            "metadata": sha256_bytes(raw_meta),
            "graphData": sha256_bytes(raw_graph),
            "monthlyReturns": sha256_bytes(raw_monthly),
            "returnData": sha256_bytes(raw_return),
        },
        "daily_level_rows": int(len(daily)),
        "daily_first_date": daily["date"].min().date().isoformat(),
        "daily_last_date": daily["date"].max().date().isoformat(),
        "monthly_level_rows_through_2026_08": int(len(monthly)),
        "monthly_first_period": str(monthly["period"].min()),
        "monthly_last_period": str(monthly["period"].max()),
        "monthly_return_crosscheck_rows": int(len(chk)),
        "monthly_return_crosscheck_max_abs_diff_pp": max_diff,
    }, {
        "metadata": raw_meta,
        "graphData": raw_graph,
        "monthlyReturns": raw_monthly,
        "returnData": raw_return,
    }


def load_mgasnyh_gretl() -> tuple[pd.DataFrame, dict]:
    raw_idx = fetch_bytes(GRETL_IDX_URL)
    raw_dat = fetch_bytes(GRETL_DAT_URL)
    idx_text = raw_idx.decode("utf-8", errors="strict")
    lines = idx_text.splitlines()

    offset_obs = 0
    total_obs = 0
    target = None
    i = 0
    while i < len(lines):
        line1 = lines[i].strip()
        i += 1
        if not line1 or line1.startswith("#"):
            continue
        if i >= len(lines):
            raise RuntimeError("gretl FRED index ended mid-entry")
        line2 = lines[i].strip()
        i += 1
        m = re.fullmatch(
            r"([A-Z])\s+(\S+)\s+-\s+(\S+)\s+n\s*=\s*(\d+)",
            line2,
        )
        if m is None:
            raise RuntimeError(f"unparseable gretl FRED index metadata: {line2!r}")
        freq, first, last, n_s = m.groups()
        n = int(n_s)
        name = line1.split()[0].lower()
        if name == "mgasnyh":
            target = {
                "name": name,
                "description": line1[len(line1.split()[0]):].strip(),
                "frequency": freq,
                "first": first,
                "last": last,
                "n": n,
                "offset_obs": offset_obs,
            }
        offset_obs += n
        total_obs += n

    if target is None:
        raise RuntimeError("gretl FRED mirror no longer contains mgasnyh")
    if target["frequency"] != "M":
        raise RuntimeError(f"mgasnyh frequency drift: {target['frequency']}")
    if target["first"] != "1986.06":
        raise RuntimeError(f"mgasnyh first-period drift: {target['first']}")
    if target["last"] != "2026.03" or target["n"] != 478:
        raise RuntimeError(
            f"mgasnyh mirror coverage drift: last={target['last']} n={target['n']}"
        )

    expected_min_bytes = total_obs * 4
    if len(raw_dat) < expected_min_bytes:
        raise RuntimeError(
            f"gretl FRED binary too short: bytes={len(raw_dat)} expected>={expected_min_bytes}"
        )
    vals = np.frombuffer(
        raw_dat,
        dtype="<f4",
        count=int(target["n"]),
        offset=int(target["offset_obs"]) * 4,
    ).astype(float)

    # Fail closed against the official FRED identity anchors:
    # 1986-06=0.420, 1986-07=0.340, 1986-08=0.426.
    anchors = np.array([0.420, 0.340, 0.426], dtype=float)
    if not np.allclose(vals[:3], anchors, rtol=0.0, atol=5e-7):
        raise RuntimeError(
            f"gretl MGASNYH binary identity check failed: first3={vals[:3].tolist()}"
        )
    if not np.isfinite(vals).all() or (vals <= 0).any() or (vals > 20).any():
        raise RuntimeError("gretl MGASNYH contains implausible or missing values")

    periods = pd.period_range("1986-06", "2026-03", freq="M")
    if len(periods) != len(vals):
        raise RuntimeError("gretl MGASNYH period/value length mismatch")
    df = pd.DataFrame({
        "period": periods,
        "gasoline": vals,
    })
    df["date"] = df["period"].dt.to_timestamp("M")
    meta = {
        "series_id": "MGASNYH",
        "series_name": "Conventional Gasoline Prices: New York Harbor, Regular",
        "source_provider": "U.S. Energy Information Administration via FRED",
        "mirror_provider": "gretl-project/gretl FRED database",
        "mirror_commit": GRETL_COMMIT,
        "idx_url": GRETL_IDX_URL,
        "dat_url": GRETL_DAT_URL,
        "idx_sha256": sha256_bytes(raw_idx),
        "dat_sha256": sha256_bytes(raw_dat),
        "binary_format": "gretl native database; little-endian float32 packed by variable",
        "offset_observations": int(target["offset_obs"]),
        "finite_rows": int(len(df)),
        "first_period": str(df["period"].min()),
        "last_period": str(df["period"].max()),
        "official_fred_identity_anchors": {
            "1986-06": 0.420,
            "1986-07": 0.340,
            "1986-08": 0.426,
        },
    }
    return df, meta

def load_structural_sources() -> tuple[pd.DataFrame, dict]:
    wb_url, wb_landing = i141.locate_world_bank_monthly_url()
    raw_wb = i141.fetch(wb_url)
    cl_url, cl_landing = i141.locate_cleveland_xlsx()
    raw_cl = i141.fetch(cl_url)

    observed = {
        "world_bank_monthly": sha256_bytes(raw_wb),
        "cleveland_inflation_expectations": sha256_bytes(raw_cl),
    }
    drift = {
        k: {"expected": EXPECTED_I141_SHA[k], "observed": observed[k]}
        for k in EXPECTED_I141_SHA if observed[k] != EXPECTED_I141_SHA[k]
    }
    if drift:
        raise RuntimeError(f"Issue #141 frozen source drift: {json.dumps(drift, sort_keys=True)}")

    wb = i141.selected_world_bank_panel(i141.wb_sheet(raw_wb, "Monthly Prices"))
    cl = i141.selected_cleveland_panel(raw_cl)
    wb["period"] = pd.to_datetime(wb["date"]).dt.to_period("M")
    cl["period"] = pd.to_datetime(cl["date"]).dt.to_period("M")
    panel = wb[["period", "Crude oil, WTI"]].merge(
        cl[["period", "expected_inflation_10y"]],
        on="period",
        how="inner",
        validate="one_to_one",
    ).sort_values("period").reset_index(drop=True)

    return panel, {
        "world_bank_url": wb_url,
        "world_bank_monthly_sha256": observed["world_bank_monthly"],
        "world_bank_landing_sha256": sha256_bytes(wb_landing),
        "cleveland_url": cl_url,
        "cleveland_xlsx_sha256": observed["cleveland_inflation_expectations"],
        "cleveland_landing_sha256": sha256_bytes(cl_landing),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    dbiq, dbiq_meta, dbiq_raw = load_dbiq()

    gas, gas_meta = load_mgasnyh_gretl()
    gas = gas.loc[gas["period"] <= SOURCE_END].copy()
    finite_gas = gas.loc[gas["gasoline"].notna()]
    if finite_gas["period"].min() != pd.Period("1986-06", "M"):
        raise RuntimeError(f"MGASNYH first finite period drift: {finite_gas['period'].min()}")
    if finite_gas["period"].max() != SOURCE_END:
        raise RuntimeError(f"MGASNYH last finite period drift: {finite_gas['period'].max()}")

    structural, structural_meta = load_structural_sources()

    panel = dbiq[["period", "dbiq_level", "dbiq_return_pct"]].copy()
    panel = panel.merge(gas[["period", "gasoline"]], on="period", how="left", validate="one_to_one")
    panel = panel.merge(structural, on="period", how="left", validate="one_to_one")
    panel = panel.sort_values("period").reset_index(drop=True)
    panel["date"] = panel["period"].dt.to_timestamp("M")

    source_cols = ["dbiq_level", "gasoline", "Crude oil, WTI", "expected_inflation_10y"]
    complete = panel[source_cols].notna().all(axis=1)
    complete_periods = panel.loc[complete, "period"]

    panel_path = out / "issue-145-v2-source-panel.csv"
    dbiq_path = out / "issue-145-dbiq-monthly-levels.csv"
    gas_path = out / "issue-145-mgasnyh.csv"

    panel.drop(columns=["period"]).to_csv(panel_path, index=False, date_format="%Y-%m-%d", float_format="%.12g")
    dbiq.drop(columns=["period"]).to_csv(dbiq_path, index=False, date_format="%Y-%m-%d", float_format="%.12g")
    gas.drop(columns=["period"]).to_csv(gas_path, index=False, date_format="%Y-%m-%d", float_format="%.12g")

    for name, raw in dbiq_raw.items():
        (out / f"issue-145-dbiq-{name}.json").write_bytes(raw)

    manifest = {
        "schema_version": 1,
        "issue": 145,
        "phase": "A-source-only",
        "exact_v66_signal_loaded": False,
        "outcome_data_loaded": False,
        "dbiq": dbiq_meta,
        "mgasnyh": gas_meta,
        "structural_sources": structural_meta,
        "v2_panel": {
            "csv_sha256": sha256_file(panel_path),
            "rows": int(len(panel)),
            "first_period": str(panel["period"].min()),
            "last_period": str(panel["period"].max()),
            "complete_rows": int(complete.sum()),
            "first_complete_period": str(complete_periods.min()) if len(complete_periods) else None,
            "last_complete_period": str(complete_periods.max()) if len(complete_periods) else None,
        },
        "files": {
            "dbiq_csv_sha256": sha256_file(dbiq_path),
            "mgasnyh_csv_sha256": sha256_file(gas_path),
        },
        "guardrail": "Source acquisition only; no exact V6.6 signal and no asset-return outcome loaded.",
    }
    (out / "issue-145-source-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
