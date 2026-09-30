#!/usr/bin/env python3
"""Export the frozen Issue #78 CRSP CIZ snapshot from WRDS.

This utility deliberately performs *data acquisition only*.  It does not run
the classifier and does not calculate R0 / Warning-First economics.

Requires institutional WRDS access and the `wrds` Python package.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Iterable

RAW_START = "1998-01-01"
RAW_END = "2026-08-31"
DEFAULT_SCHEMA = "crsp_m_stock"

TABLE_CANDIDATES = {
    "daily": ("dsf_v2", "stkdlysecuritydata"),
    "factors": ("stkdlycumulativeadjfactor",),
    "info_hist": ("stksecurityinfohist", "stocknames_v2"),
    "delists": ("stkdelists",),
}


def choose_table(available: Iterable[str], candidates: Iterable[str]) -> str:
    lookup = {str(x).lower(): str(x) for x in available}
    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]
    raise RuntimeError(
        f"none of the candidate tables {tuple(candidates)} exist; "
        f"available sample={sorted(lookup)[:40]}"
    )


def sha256_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def qident(value: str) -> str:
    if not value.replace("_", "").isalnum():
        raise ValueError(f"unsafe SQL identifier: {value!r}")
    return value


def _queries(schema: str, tables: dict[str, str]) -> dict[str, str]:
    s = qident(schema)
    t = {k: qident(v) for k, v in tables.items()}
    return {
        "daily": f"""
            select
                permno, dlycaldt, dlyopen, dlyhigh, dlylow, dlyclose,
                dlyprc, dlyvol, dlyretx, dlydelflg
            from {s}.{t["daily"]}
            where dlycaldt between '{RAW_START}' and '{RAW_END}'
            order by permno, dlycaldt
        """,
        "factors": f"""
            select permno, dlycaldt, dlycumfacpr, dlycumfacshr
            from {s}.{t["factors"]}
            where dlycaldt between '{RAW_START}' and '{RAW_END}'
            order by permno, dlycaldt
        """,
        "info_hist": f"""
            select *
            from {s}.{t["info_hist"]}
            where secinfoenddt >= '{RAW_START}'
              and secinfostartdt <= '{RAW_END}'
            order by permno, secinfostartdt
        """,
        "delists": f"""
            select *
            from {s}.{t["delists"]}
            where delistingdt between '{RAW_START}' and '{RAW_END}'
            order by permno, delistingdt
        """,
    }


def export_snapshot(output_dir: Path, schema: str) -> dict:
    try:
        import wrds  # type: ignore
    except ImportError as exc:
        raise RuntimeError("install the 'wrds' package in the WRDS-enabled environment") from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    db = wrds.Connection()
    available = db.list_tables(library=schema)
    tables = {
        name: choose_table(available, candidates)
        for name, candidates in TABLE_CANDIDATES.items()
    }
    queries = _queries(schema, tables)

    artifacts = {}
    for name, sql in queries.items():
        frame = db.raw_sql(sql, date_cols=["dlycaldt", "secinfostartdt", "secinfoenddt", "delistingdt"])
        path = output_dir / f"issue78_oos2_crsp_{name}.csv.gz"
        frame.to_csv(path, index=False, compression="gzip")
        date_candidates = [c for c in ("dlycaldt", "secinfostartdt", "delistingdt") if c in frame.columns]
        min_date = max_date = None
        if date_candidates and len(frame):
            series = frame[date_candidates[0]].dropna()
            if len(series):
                min_date = str(series.min())
                max_date = str(series.max())
        artifacts[name] = {
            "table": tables[name],
            "path": path.name,
            "rows": int(len(frame)),
            "columns": list(frame.columns),
            "min_date": min_date,
            "max_date": max_date,
            "sha256": sha256_file(path),
            "sql": " ".join(sql.split()),
        }

    manifest = {
        "issue": 78,
        "study": "cross-sectional-oos2",
        "provider": "CRSP US Stock & Indexes CIZ / WRDS",
        "schema": schema,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "raw_start": RAW_START,
        "raw_end": RAW_END,
        "artifacts": artifacts,
        "notes": [
            "Raw licensed files stay outside Git.",
            "Manifest hashes freeze the exact formal snapshot.",
            "No classifier or policy economics are run by this exporter.",
        ],
    }
    manifest_path = output_dir / "issue78_oos2_crsp_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--schema", default=DEFAULT_SCHEMA)
    args = ap.parse_args()
    manifest = export_snapshot(args.output_dir, args.schema)
    print(json.dumps({
        "provider": manifest["provider"],
        "schema": manifest["schema"],
        "artifacts": {
            k: {"rows": v["rows"], "sha256": v["sha256"]}
            for k, v in manifest["artifacts"].items()
        },
    }, indent=2))


if __name__ == "__main__":
    main()
