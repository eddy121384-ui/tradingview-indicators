#!/usr/bin/env python3
"""Issue #91 Phase 0: long-history source audit.

This script intentionally does NOT compute historical regime labels, conditioned
asset returns, portfolio performance, or any allocation weights. It only audits
source accessibility, provenance, schema and date coverage before the historical
analogue is specified.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import urllib.request

import pandas as pd

HERE = Path(__file__).resolve().parent
DEFAULT_PLAN = HERE / "decisions" / "issue-91-phase0-source-plan.json"
USER_AGENT = "tradingview-indicators-issue-91-research/1.0"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def fetch_bytes(url: str, timeout: int = 8) -> tuple[bytes, str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310 - preregistered HTTPS sources
        payload = response.read()
        final_url = response.geturl()
    if not payload:
        raise RuntimeError(f"empty response from {url}")
    return payload, final_url


def flatten_columns(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    if isinstance(out.columns, pd.MultiIndex):
        cols = []
        for col in out.columns:
            parts = [str(x).strip() for x in col if str(x).strip() and not str(x).startswith("Unnamed")]
            cols.append(" | ".join(parts))
        out.columns = cols
    else:
        out.columns = [str(x).strip() for x in out.columns]
    return out


def first_last_numeric_year(values: pd.Series) -> tuple[int | None, int | None, int]:
    numeric = pd.to_numeric(values, errors="coerce")
    numeric = numeric[(numeric >= 1800) & (numeric <= 2200)]
    if numeric.empty:
        return None, None, 0
    return int(numeric.min()), int(numeric.max()), int(numeric.size)


def _promote_embedded_header(table: pd.DataFrame, required_tokens: tuple[str, ...]) -> pd.DataFrame | None:
    raw = table.copy()
    for pos in range(min(len(raw), 12)):
        row = [str(x).strip() for x in raw.iloc[pos].tolist()]
        joined = " | ".join(row).lower()
        if all(token in joined for token in required_tokens):
            headers = []
            seen: dict[str, int] = {}
            for i, value in enumerate(row):
                base = value if value and value.lower() != "nan" else f"column_{i}"
                count = seen.get(base, 0)
                seen[base] = count + 1
                headers.append(base if count == 0 else f"{base}__{count+1}")
            out = raw.iloc[pos + 1 :].copy()
            out.columns = headers
            return out
    return None


def audit_damodaran(payload: bytes) -> dict:
    tables = pd.read_html(io.BytesIO(payload), header=None)
    candidates = []
    for table in tables:
        frame = flatten_columns(table)
        all_text = " ".join(frame.astype(str).fillna("").to_numpy().ravel()).lower()
        if "s&p 500" not in all_text or "gold" not in all_text or "year" not in all_text:
            continue
        promoted = _promote_embedded_header(frame, ("year", "s&p 500", "gold"))
        if promoted is not None:
            candidates.append(promoted)
    if not candidates:
        raise RuntimeError("Damodaran return table not found")
    frame = max(candidates, key=len)
    year_col = next((c for c in frame.columns if "year" in c.lower()), None)
    if year_col is None:
        raise RuntimeError("Damodaran Year column missing")
    first, last, rows = first_last_numeric_year(frame[year_col])
    if first is None or last is None:
        raise RuntimeError("Damodaran has no numeric year rows")
    columns = [str(c) for c in frame.columns if str(c)]
    required_tokens = ("s&p 500", "3-month", "bond", "gold")
    missing = [token for token in required_tokens if not any(token in c.lower() for c in columns)]
    if missing:
        raise RuntimeError(f"Damodaran expected columns missing: {missing}")
    return {
        "first_year": first,
        "last_year": last,
        "numeric_year_rows": rows,
        "columns": columns,
        "series_semantics": {
            "equity":"S&P 500 return including dividends",
            "cash":"3-month T.Bill return",
            "government_bond":"10-year U.S. Treasury total return",
            "gold":"underlying gold return",
        },
    }


def audit_fred_csv(payload: bytes, series_id: str) -> dict:
    frame = pd.read_csv(io.BytesIO(payload))
    date_col = "observation_date" if "observation_date" in frame.columns else "DATE" if "DATE" in frame.columns else None
    if date_col is None or series_id not in frame.columns:
        raise RuntimeError(f"FRED {series_id} unexpected columns: {list(frame.columns)}")
    dates = pd.to_datetime(frame[date_col], errors="coerce")
    values = pd.to_numeric(frame[series_id].replace(".", pd.NA), errors="coerce")
    return _fred_coverage(dates, values, list(frame.columns), series_id)


def _fred_coverage(dates: pd.Series, values: pd.Series, columns: list[str], series_id: str) -> dict:
    valid = dates.notna() & values.notna()
    if not valid.any():
        raise RuntimeError(f"FRED {series_id} contains no usable observations")
    clean_dates = dates.loc[valid]
    return {
        "first_observation": clean_dates.min().date().isoformat(),
        "last_observation": clean_dates.max().date().isoformat(),
        "usable_observations": int(valid.sum()),
        "rows": int(len(dates)),
        "columns": columns,
    }


def audit_fred_table_page(payload: bytes, series_id: str) -> dict:
    tables = pd.read_html(io.BytesIO(payload), header=0)
    for table in tables:
        frame = flatten_columns(table)
        by_lower = {str(c).strip().lower(): str(c) for c in frame.columns}
        date_col = by_lower.get("date")
        value_col = by_lower.get("value")
        if date_col is None or value_col is None:
            continue
        dates = pd.to_datetime(frame[date_col], errors="coerce")
        values = pd.to_numeric(frame[value_col].replace(".", pd.NA), errors="coerce")
        if (dates.notna() & values.notna()).any():
            return _fred_coverage(dates, values, list(frame.columns), series_id)
    raise RuntimeError(f"FRED {series_id} DATE/VALUE table not found")


def _find_column(columns: list[str], aliases: tuple[str, ...]) -> str | None:
    by_lower = {str(c).strip().lower(): str(c) for c in columns}
    for alias in aliases:
        if alias.lower() in by_lower:
            return by_lower[alias.lower()]
    return None


def audit_jst_xlsx(payload: bytes) -> dict:
    book = pd.ExcelFile(io.BytesIO(payload), engine="openpyxl")
    if not book.sheet_names:
        raise RuntimeError("JST workbook has no sheets")
    best = None
    for sheet in book.sheet_names:
        frame = pd.read_excel(book, sheet_name=sheet, engine="openpyxl")
        cols = [str(c).strip() for c in frame.columns]
        if _find_column(cols, ("year",)) and (_find_column(cols, ("iso", "iso3")) or _find_column(cols, ("country",))):
            best = (sheet, frame)
            break
    if best is None:
        raise RuntimeError(f"JST data sheet not found; sheets={book.sheet_names}")
    sheet, frame = best
    cols = [str(c).strip() for c in frame.columns]
    iso_col = _find_column(cols, ("iso", "iso3"))
    country_col = _find_column(cols, ("country",))
    if iso_col is not None:
        mask = frame[iso_col].astype(str).str.upper().eq("USA")
    elif country_col is not None:
        country = frame[country_col].astype(str).str.strip().str.lower()
        mask = country.isin({"united states", "usa", "u.s.", "u.s.a."})
    else:
        raise RuntimeError("JST has no country identifier")
    us = frame.loc[mask].copy()
    if us.empty:
        raise RuntimeError("JST USA rows not found")
    year_col = _find_column(cols, ("year",))
    first, last, rows = first_last_numeric_year(us[year_col])
    candidate_aliases = {
        "cpi":("cpi",),
        "equity_total_return":("eq_tr",),
        "government_bond_total_return":("bond_tr",),
        "government_bill_rate":("bill_rate",),
        "short_rate":("stir",),
        "real_gdp_per_capita":("rgdppc","rgdp_pc"),
        "long_rate":("ltrate","lt_rate"),
    }
    coverage = {}
    for label, aliases in candidate_aliases.items():
        col = _find_column(cols, aliases)
        if col is None:
            coverage[label] = {"column":None,"usable_observations":0,"first_year":None,"last_year":None}
            continue
        values = pd.to_numeric(us[col], errors="coerce")
        years = pd.to_numeric(us[year_col], errors="coerce")
        valid = values.notna() & years.notna()
        coverage[label] = {
            "column":col,
            "usable_observations":int(valid.sum()),
            "first_year":int(years.loc[valid].min()) if valid.any() else None,
            "last_year":int(years.loc[valid].max()) if valid.any() else None,
        }
    return {
        "sheet":sheet,
        "first_year":first,
        "last_year":last,
        "usa_rows":rows,
        "columns":cols,
        "candidate_coverage":coverage,
    }


def audit_documentation_page(payload: bytes) -> dict:
    text = payload.decode("utf-8", errors="replace")
    years = [int(x) for x in re.findall(r"\b(?:18|19|20)\d{2}\b", text)]
    return {
        "bytes":len(payload),
        "mentions_1871":1871 in years,
        "documented_year_min":min(years) if years else None,
        "documented_year_max":max(years) if years else None,
    }


def audit_source(source: dict) -> dict:
    payload, final_url = fetch_bytes(source["url"])
    transport = source["transport"]
    if transport == "html_table":
        parsed = audit_damodaran(payload)
    elif transport == "fred_csv":
        parsed = audit_fred_csv(payload, source["series_id"])
    elif transport == "fred_table_page":
        parsed = audit_fred_table_page(payload, source["series_id"])
    elif transport == "xlsx":
        parsed = audit_jst_xlsx(payload)
    elif transport == "documentation_page":
        parsed = audit_documentation_page(payload)
    else:
        raise ValueError(f"unsupported transport: {transport}")
    return {
        "id":source["id"],
        "role":source["role"],
        "required":bool(source["required"]),
        "requested_url":source["url"],
        "final_url":final_url,
        "transport":transport,
        "raw_sha256":sha256_bytes(payload),
        "raw_bytes":len(payload),
        "etf":bool(source["etf"]),
        "audit_status":"ok",
        "parsed":parsed,
    }


def validate_plan(plan: dict) -> None:
    if plan.get("issue") != 91 or plan.get("phase") != "0-source-audit":
        raise ValueError("unexpected Issue #91 Phase 0 plan identity")
    if plan.get("created_before_regime_conditioned_asset_results") is not True:
        raise ValueError("Phase 0 must precede conditioned outcome analysis")
    if plan.get("etf_use_in_primary_long_history_analysis") is not False:
        raise ValueError("ETFs are forbidden in Issue #91 primary long-history analysis")
    for source in plan["sources"]:
        if source.get("etf") is not False:
            raise ValueError(f"ETF source leaked into Phase 0: {source['id']}")


def run(plan_path: Path, output_dir: Path) -> dict:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    validate_plan(plan)
    rows = []
    failures = []
    for source in plan["sources"]:
        print(f"AUDIT_START {source['id']} {source['url']}", flush=True)
        try:
            row = audit_source(source)
            rows.append(row)
            parsed = row.get("parsed", {})
            first = parsed.get("first_year") or parsed.get("first_observation") or parsed.get("documented_year_min")
            last = parsed.get("last_year") or parsed.get("last_observation") or parsed.get("documented_year_max")
            print(f"AUDIT_OK {source['id']} {first}->{last} {row.get('raw_sha256')}", flush=True)
        except Exception as exc:
            print(f"AUDIT_ERROR {source['id']} {type(exc).__name__}: {exc}", flush=True)
            row = {
                "id":source["id"],
                "role":source["role"],
                "required":bool(source["required"]),
                "requested_url":source["url"],
                "transport":source["transport"],
                "etf":bool(source["etf"]),
                "audit_status":"error",
                "error":f"{type(exc).__name__}: {exc}",
            }
            rows.append(row)
            if source["required"]:
                failures.append(row)

    output_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "schema_version":1,
        "issue":91,
        "phase":"0-source-audit",
        "purpose":"freeze source provenance, schema and coverage before historical regime analogue construction",
        "regime_conditioned_asset_results_computed":False,
        "portfolio_results_computed":False,
        "etfs_used":False,
        "raw_third_party_files_committed":False,
        "sources":rows,
        "required_source_failures":[x["id"] for x in failures],
    }
    (output_dir/"issue-91-phase0-source-audit.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8"
    )

    flat=[]
    for row in rows:
        parsed=row.get("parsed",{})
        flat.append({
            "id":row["id"],
            "required":row["required"],
            "status":row["audit_status"],
            "transport":row["transport"],
            "raw_sha256":row.get("raw_sha256"),
            "raw_bytes":row.get("raw_bytes"),
            "first":parsed.get("first_year") or parsed.get("first_observation") or parsed.get("documented_year_min"),
            "last":parsed.get("last_year") or parsed.get("last_observation") or parsed.get("documented_year_max"),
            "usable_rows":parsed.get("numeric_year_rows") or parsed.get("usable_observations") or parsed.get("usa_rows"),
            "error":row.get("error"),
        })
    pd.DataFrame(flat).to_csv(output_dir/"issue-91-phase0-source-audit.csv",index=False)

    report=[
        "# Issue #91 Phase 0 — long-history source audit","",
        "No regime-conditioned asset returns or portfolio results are computed in this phase.","",
        "| Source | Required | Status | Coverage | Raw SHA-256 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row, f in zip(rows,flat):
        coverage=f"{f['first']} → {f['last']}" if f["first"] is not None else "n/a"
        digest=row.get("raw_sha256","n/a")
        report.append(f"| {row['id']} | {row['required']} | {row['audit_status']} | {coverage} | {digest} |")
    (output_dir/"issue-91-phase0-source-audit.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    if failures:
        names=", ".join(x["id"] for x in failures)
        raise RuntimeError(f"required Issue #91 sources failed audit: {names}")
    return result


def main() -> int:
    parser=argparse.ArgumentParser(description="Issue #91 Phase 0 long-history source audit")
    parser.add_argument("--plan",type=Path,default=DEFAULT_PLAN)
    parser.add_argument("--output-dir",type=Path,required=True)
    args=parser.parse_args()
    result=run(args.plan,args.output_dir)
    print(json.dumps({
        "required_source_failures":result["required_source_failures"],
        "sources":[{"id":x["id"],"status":x["audit_status"],"sha256":x.get("raw_sha256")} for x in result["sources"]],
    },indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
