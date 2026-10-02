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
import io
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


def _parse_dbiq_export(raw: bytes, filename: str) -> tuple[pd.DataFrame, dict]:
    attempts: list[tuple[str, pd.DataFrame]] = []
    lower = filename.lower()
    if lower.endswith((".xlsx", ".xls")) or raw[:2] == b"PK":
        try:
            attempts.append(("excel", pd.read_excel(io.BytesIO(raw))))
        except Exception:
            pass
    for sep in (",", ";", "\t"):
        try:
            frame = pd.read_csv(io.BytesIO(raw), sep=sep)
            if len(frame.columns) >= 2:
                attempts.append((f"csv:{sep!r}", frame))
        except Exception:
            pass

    diagnostics = []
    for parser_name, frame in attempts:
        diagnostics.append({"parser": parser_name, "columns": [str(x) for x in frame.columns], "rows": len(frame)})
        if frame.empty:
            continue

        date_candidates = []
        for col in frame.columns:
            parsed = pd.to_datetime(frame[col], errors="coerce")
            score = float(parsed.notna().mean())
            if score >= 0.80:
                date_candidates.append((score, col, parsed))
        if not date_candidates:
            continue
        _, date_col, parsed_dates = max(date_candidates, key=lambda x: x[0])

        level_candidates = []
        for col in frame.columns:
            if col == date_col:
                continue
            vals = pd.to_numeric(frame[col], errors="coerce")
            finite = vals.notna()
            if float(finite.mean()) < 0.80:
                continue
            name = str(col).lower()
            # Prefer explicit level / ticker columns; penalize volatility / return.
            name_score = 0
            if "level" in name or "dblcdbce" in name or "price" in name:
                name_score += 3
            if "vol" in name or "return" in name or "%" in name:
                name_score -= 3
            level_candidates.append((name_score, int(finite.sum()), col, vals))
        if not level_candidates:
            continue
        level_candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
        score, _, level_col, levels = level_candidates[0]
        if score < 0:
            continue

        out = pd.DataFrame({"date": parsed_dates, "level": levels}).dropna()
        out = out.loc[out["level"] > 0].sort_values("date").drop_duplicates("date", keep="last")
        if len(out) < 3000:
            continue
        if out["date"].min() > pd.Timestamp("1989-01-31"):
            continue
        if out["date"].max() < pd.Timestamp("2026-08-01"):
            continue
        return out.reset_index(drop=True), {
            "parser": parser_name,
            "date_column": str(date_col),
            "level_column": str(level_col),
            "raw_rows": int(len(frame)),
            "finite_level_rows": int(len(out)),
        }

    raise RuntimeError(f"could not identify DBIQ export date/level columns: {diagnostics}")


def extract_dbiq_monthly_returns() -> tuple[pd.DataFrame, dict, str, bytes, str]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1600, "height": 1200},
            accept_downloads=True,
        )
        page = context.new_page()
        page.goto(DBIQ_URL, wait_until="domcontentloaded", timeout=120_000)
        try:
            page.wait_for_load_state("networkidle", timeout=120_000)
        except Exception:
            pass
        page.wait_for_timeout(5_000)

        body_text = page.locator("body").inner_text(timeout=30_000)
        title = page.title()

        if "DBIQ Optimum Yield Diversified Commodity Index Excess Return" not in body_text:
            raise RuntimeError("DBIQ page did not render expected index name")
        if "Historical Inception Date" not in body_text or "02 December 1988" not in body_text:
            raise RuntimeError("DBIQ page did not render frozen historical inception metadata")
        if "DBLCDBCE" not in body_text:
            raise RuntimeError("DBIQ page did not render expected Bloomberg ticker")
        if "Historical Price and Volatility" not in body_text:
            raise RuntimeError("DBIQ page missing Historical Price and Volatility section")

        all_time = page.get_by_text("All Time", exact=True)
        if all_time.count() == 0:
            raise RuntimeError("DBIQ page missing All Time control")
        # DBIQ currently renders "All Time" as the default chart range. In
        # headless Chromium its label can be covered by the chart canvas, so
        # treat an unclickable label as already-selected rather than changing
        # the frozen source definition.
        try:
            all_time.last.click(timeout=5_000, force=True)
            page.wait_for_timeout(2_000)
        except Exception:
            pass

        export_buttons = page.get_by_role("button", name="Export", exact=True)
        if export_buttons.count() == 0:
            # Some DBIQ builds expose Export as a non-button clickable element.
            export_buttons = page.get_by_text("Export", exact=True)
        if export_buttons.count() == 0:
            raise RuntimeError("DBIQ page missing Export control")

        try:
            with page.expect_download(timeout=60_000) as download_info:
                export_buttons.last.click(timeout=10_000, force=True)
            download = download_info.value
        except Exception as exc:
            raise RuntimeError(
                f"DBIQ All-Time Export did not produce a download; controls={export_buttons.count()}: {exc}"
            ) from exc

        suggested = download.suggested_filename or "dbiq-export"
        temp_path = download.path()
        if temp_path is None:
            raise RuntimeError("DBIQ export download has no local path")
        export_raw = Path(temp_path).read_bytes()
        context.close()
        browser.close()

    daily, parse_meta = _parse_dbiq_export(export_raw, suggested)
    daily["period"] = daily["date"].dt.to_period("M")
    month_end = daily.groupby("period", as_index=False, sort=True).tail(1).copy()
    month_end = month_end.sort_values("period").reset_index(drop=True)
    month_end["return_pct"] = month_end["level"].pct_change() * 100.0
    month_end["dbiq_wealth"] = 100.0 * month_end["level"] / float(month_end["level"].iloc[0])
    month_end["date"] = month_end["period"].dt.to_timestamp("M")

    finite_returns = month_end["return_pct"].notna()
    if int(finite_returns.sum()) < 440:
        raise RuntimeError(f"DBIQ all-time export unexpectedly short: {int(finite_returns.sum())} monthly returns")
    if month_end["period"].min() > pd.Period("1988-12", "M"):
        raise RuntimeError(f"DBIQ export starts too late: {month_end['period'].min()}")
    if month_end["period"].max() < pd.Period("2026-08", "M"):
        raise RuntimeError(f"DBIQ export ends too early: {month_end['period'].max()}")

    canonical_rows = [
        {"period": str(p), "level": float(v)}
        for p, v in zip(month_end["period"], month_end["level"])
    ]
    meta = {
        "url": DBIQ_URL,
        "page_title": title,
        "index_name": "DBIQ Optimum Yield Diversified Commodity Index Excess Return",
        "ticker": "DBLCDBCE",
        "historical_inception": "1988-12-02",
        "benchmark_family": "Commodity Futures",
        "source_mode": "official_all_time_export",
        "export_suggested_filename": suggested,
        "export_raw_sha256": sha256_bytes(export_raw),
        "export_parse": parse_meta,
        "daily_rows": int(len(daily)),
        "monthly_level_rows": int(len(month_end)),
        "monthly_return_rows": int(finite_returns.sum()),
        "first_period": str(month_end["period"].min()),
        "last_period": str(month_end["period"].max()),
        "canonical_monthly_levels_sha256": sha256_bytes(
            json.dumps(canonical_rows, separators=(",", ":"), ensure_ascii=False).encode()
        ),
        "rendered_body_sha256": sha256_bytes(body_text.encode("utf-8")),
    }
    return month_end, meta, body_text, export_raw, suggested

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

    dbiq, dbiq_meta, dbiq_body, dbiq_export_raw, dbiq_export_name = extract_dbiq_monthly_returns()

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
    export_suffix = Path(dbiq_export_name).suffix or ".bin"
    (out / f"issue-145-dbiq-official-export{export_suffix}").write_bytes(dbiq_export_raw)

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
