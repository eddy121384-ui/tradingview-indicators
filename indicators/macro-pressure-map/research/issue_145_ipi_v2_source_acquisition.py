#!/usr/bin/env python3
"""Issue #145 Phase A — source-only acquisition for IPI Bridge v2.

Hard firewall:
- no exact V6.6 signal is loaded;
- no asset-return outcome is loaded.

Primary source families:
- Deutsche Bank DBIQ official rendered index page for DBLCDBCE monthly returns;
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
from playwright.sync_api import sync_playwright

import issue_141_source_acquisition as i141

DBIQ_URL = "https://index.db.com/dbiq-web/indices/95400"
MGASNYH_TEXT_URL = "https://fred.stlouisfed.org/data/MGASNYH.txt"

EXPECTED_I141_SHA = {
    "world_bank_monthly": "9fdcfa8a2aed9a1bb545a10c1a5ce036c6a0acd4766f450424ca800b4b5a0225",
    "cleveland_inflation_expectations": "20701ccf394d280fe1db38fa9def5628f2385dd0aef148ff989e33ff15caba95",
}

MONTHS = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
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


def parse_pct(text: str) -> float | None:
    s = text.strip().replace("%", "").replace(",", "")
    if not s or s in {"-", "—", "–", "N/A", "n/a"}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def extract_dbiq_monthly_returns() -> tuple[pd.DataFrame, dict, str]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 1200})
        page.goto(DBIQ_URL, wait_until="domcontentloaded", timeout=120_000)
        try:
            page.wait_for_load_state("networkidle", timeout=120_000)
        except Exception:
            # Some analytics connections can remain active; DOM content is the real gate.
            pass
        page.wait_for_timeout(5_000)

        body_text = page.locator("body").inner_text(timeout=30_000)
        title = page.title()
        tables = page.locator("table")
        candidates: list[list[list[str]]] = []
        for i in range(tables.count()):
            rows = tables.nth(i).locator("tr")
            matrix: list[list[str]] = []
            for j in range(rows.count()):
                cells = rows.nth(j).locator("th,td")
                vals = [cells.nth(k).inner_text().strip() for k in range(cells.count())]
                if vals:
                    matrix.append(vals)
            flat = " ".join(" ".join(r) for r in matrix)
            if "Jan" in flat and "Dec" in flat and any(str(y) in flat for y in (2024, 2025, 2026)):
                candidates.append(matrix)

        browser.close()

    if "DBIQ Optimum Yield Diversified Commodity Index Excess Return" not in body_text:
        raise RuntimeError("DBIQ page did not render expected index name")
    if "Historical Inception Date" not in body_text or "02 December 1988" not in body_text:
        raise RuntimeError("DBIQ page did not render frozen historical inception metadata")
    if "DBLCDBCE" not in body_text:
        raise RuntimeError("DBIQ page did not render expected Bloomberg ticker")
    if not candidates:
        raise RuntimeError("DBIQ rendered page contained no monthly-return table")

    # Choose the candidate with the most year rows.
    matrix = max(candidates, key=lambda m: sum(bool(r and re.fullmatch(r"\d{4}", r[0])) for r in m))
    header_idx = None
    for idx, row in enumerate(matrix):
        if row and row[0] == "Year" and all(m in row for m in MONTHS):
            header_idx = idx
            break
    if header_idx is None:
        raise RuntimeError("DBIQ monthly-return table missing Year/Jan..Dec header")

    header = matrix[header_idx]
    month_pos = {m: header.index(m) for m in MONTHS}
    records: list[dict] = []
    for row in matrix[header_idx + 1:]:
        if not row or not re.fullmatch(r"\d{4}", row[0]):
            continue
        year = int(row[0])
        for mon, month_num in MONTHS.items():
            pos = month_pos[mon]
            value = parse_pct(row[pos]) if pos < len(row) else None
            if value is None:
                continue
            records.append({
                "period": pd.Period(year=year, month=month_num, freq="M"),
                "return_pct": value,
            })

    if not records:
        raise RuntimeError("DBIQ monthly-return extraction produced zero rows")
    df = pd.DataFrame(records).drop_duplicates("period", keep=False).sort_values("period")
    if len(df) < 440:
        raise RuntimeError(f"DBIQ monthly history unexpectedly short: {len(df)} rows")
    if df["period"].min() > pd.Period("1989-01", "M"):
        raise RuntimeError(f"DBIQ history starts too late: {df['period'].min()}")
    if df["period"].max() < pd.Period("2026-08", "M"):
        raise RuntimeError(f"DBIQ history ends too early: {df['period'].max()}")

    # Reconstruct a strictly positive scale-free wealth index.
    mult = 1.0 + df["return_pct"].astype(float) / 100.0
    if (mult <= 0).any():
        raise RuntimeError("DBIQ monthly return <= -100%")
    df["dbiq_wealth"] = 100.0 * mult.cumprod()
    df["date"] = df["period"].dt.to_timestamp("M")

    canonical_rows = [
        {"period": str(p), "return_pct": float(r)}
        for p, r in zip(df["period"], df["return_pct"])
    ]
    meta = {
        "url": DBIQ_URL,
        "page_title": title,
        "index_name": "DBIQ Optimum Yield Diversified Commodity Index Excess Return",
        "ticker": "DBLCDBCE",
        "historical_inception": "1988-12-02",
        "benchmark_family": "Commodity Futures",
        "monthly_rows": int(len(df)),
        "first_period": str(df["period"].min()),
        "last_period": str(df["period"].max()),
        "canonical_monthly_rows_sha256": sha256_bytes(
            json.dumps(canonical_rows, separators=(",", ":"), ensure_ascii=False).encode()
        ),
        "rendered_body_sha256": sha256_bytes(body_text.encode("utf-8")),
    }
    return df.reset_index(drop=True), meta, body_text


def parse_fred_text(raw: bytes, series: str) -> pd.DataFrame:
    text = raw.decode("utf-8", errors="replace")
    rows = []
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r"^(\d{4}-\d{2}-\d{2})\s+([^\s]+)$", line)
        if not m:
            continue
        date_s, value_s = m.groups()
        if value_s == ".":
            value = np.nan
        else:
            try:
                value = float(value_s)
            except ValueError:
                continue
        rows.append((date_s, value))
    if not rows:
        raise RuntimeError(f"{series} static text contained no observations")
    df = pd.DataFrame(rows, columns=["date", series])
    df["date"] = pd.to_datetime(df["date"], errors="raise")
    df["period"] = df["date"].dt.to_period("M")
    df = df.sort_values("date").drop_duplicates("period", keep="last")
    return df.reset_index(drop=True)


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

    meta = {
        "world_bank_url": wb_url,
        "world_bank_monthly_sha256": observed["world_bank_monthly"],
        "world_bank_landing_sha256": sha256_bytes(wb_landing),
        "cleveland_url": cl_url,
        "cleveland_xlsx_sha256": observed["cleveland_inflation_expectations"],
        "cleveland_landing_sha256": sha256_bytes(cl_landing),
    }
    return panel, meta


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    dbiq, dbiq_meta, dbiq_body = extract_dbiq_monthly_returns()

    raw_gas = fetch_bytes(MGASNYH_TEXT_URL)
    gas = parse_fred_text(raw_gas, "gasoline")
    if gas["period"].min() > pd.Period("1986-06", "M"):
        raise RuntimeError(f"MGASNYH starts too late: {gas['period'].min()}")
    if gas["period"].max() < pd.Period("2026-08", "M"):
        raise RuntimeError(f"MGASNYH ends too early: {gas['period'].max()}")

    structural, structural_meta = load_structural_sources()

    panel = dbiq[["period", "dbiq_wealth", "return_pct"]].rename(
        columns={"return_pct": "dbiq_return_pct"}
    )
    panel = panel.merge(
        gas[["period", "gasoline"]],
        on="period", how="left", validate="one_to_one"
    )
    panel = panel.merge(
        structural,
        on="period", how="left", validate="one_to_one"
    ).sort_values("period").reset_index(drop=True)
    panel["date"] = panel["period"].dt.to_timestamp("M")

    panel_path = out / "issue-145-v2-source-panel.csv"
    dbiq_path = out / "issue-145-dbiq-monthly-returns.csv"
    gas_path = out / "issue-145-mgasnyh.csv"
    panel.drop(columns=["period"]).to_csv(panel_path, index=False, date_format="%Y-%m-%d", float_format="%.12g")
    dbiq.drop(columns=["period"]).to_csv(dbiq_path, index=False, date_format="%Y-%m-%d", float_format="%.12g")
    gas.drop(columns=["period"]).to_csv(gas_path, index=False, date_format="%Y-%m-%d", float_format="%.12g")
    (out / "issue-145-dbiq-rendered-body.txt").write_text(dbiq_body, encoding="utf-8")

    complete = panel[
        ["dbiq_wealth", "gasoline", "Crude oil, WTI", "expected_inflation_10y"]
    ].notna().all(axis=1)
    complete_periods = panel.loc[complete, "period"]

    manifest = {
        "schema_version": 1,
        "issue": 145,
        "phase": "A-source-only",
        "exact_v66_signal_loaded": False,
        "outcome_data_loaded": False,
        "dbiq": dbiq_meta,
        "mgasnyh": {
            "url": MGASNYH_TEXT_URL,
            "raw_sha256": sha256_bytes(raw_gas),
            "rows": int(gas["gasoline"].notna().sum()),
            "first_period": str(gas.loc[gas["gasoline"].notna(), "period"].min()),
            "last_period": str(gas.loc[gas["gasoline"].notna(), "period"].max()),
        },
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
