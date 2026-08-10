#!/usr/bin/env python3
"""Freeze a reproducible static D1 FX dataset for Issue #55.

The primary research fixture is sourced from the public
``ejtraderLabs/historical-data`` GitHub repository. The four source files are
pinned by their Git blob SHA, then normalized into ordinary FX price units and
committed to this repository as the exact evaluation inputs.

This choice is about reproducibility, not provider superiority. OANDA/Yahoo/
Dukascopy differences remain a separate robustness audit. No Wyckoff outcomes
are computed here and the final OOS remains sealed.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import urllib.request
from pathlib import Path

import pandas as pd


SOURCE_REPOSITORY = "ejtraderLabs/historical-data"
SOURCE_REF = "main"
FREEZE_DECISION_DATE = "2026-08-10"

SOURCE_FILES = {
    "EURUSD": {
        "path": "EURUSD/EURUSDd1.csv",
        "blob_sha": "790cd874846de3ec9d88c088ac02458d707ec09d",
        "price_scale": 100000.0,
    },
    "USDJPY": {
        "path": "USDJPY/USDJPYd1.csv",
        "blob_sha": "825510ca2ec567b3f78817197b86477e55f614b6",
        "price_scale": 1000.0,
    },
    "GBPUSD": {
        "path": "GBPUSD/GBPUSDd1.csv",
        "blob_sha": "47bcf0dbea4a7fda74757069f02edc595a30f923",
        "price_scale": 100000.0,
    },
    "AUDUSD": {
        "path": "AUDUSD/AUDUSDd1.csv",
        "blob_sha": "9f6571efa2f9508e7c36005d9df2ce254dc4a504",
        "price_scale": 100000.0,
    },
}


def source_url(path: str) -> str:
    return f"https://raw.githubusercontent.com/{SOURCE_REPOSITORY}/{SOURCE_REF}/{path}"


def git_blob_sha(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode("ascii")
    return hashlib.sha1(header + content).hexdigest()


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def fetch_source(path: str) -> bytes:
    request = urllib.request.Request(source_url(path), headers={"User-Agent": "Issue55Research/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def normalize_source(content: bytes, price_scale: float) -> pd.DataFrame:
    frame = pd.read_csv(io.BytesIO(content))
    lower = {str(column).lower(): column for column in frame.columns}
    required = ["date", "open", "high", "low", "close"]
    missing = [column for column in required if column not in lower]
    if missing:
        raise ValueError(f"source CSV missing columns {missing}: {list(frame.columns)}")

    out = frame.rename(columns={lower[name]: name for name in required})[required].copy()
    out["date"] = pd.to_datetime(out["date"], errors="raise").dt.date
    for column in ("open", "high", "low", "close"):
        out[column] = pd.to_numeric(out[column], errors="raise") / price_scale
    out = out.sort_values("date").drop_duplicates(subset=["date"], keep="last").reset_index(drop=True)
    validate_ohlc(out)
    return out


def validate_ohlc(frame: pd.DataFrame) -> None:
    if frame.empty:
        raise ValueError("frozen input is empty")
    if frame["date"].duplicated().any() or not frame["date"].is_monotonic_increasing:
        raise ValueError("dates are not unique and ascending")
    if (frame[["open", "high", "low", "close"]] <= 0).any().any():
        raise ValueError("non-positive FX price")
    high_bad = frame["high"] < frame[["open", "close", "low"]].max(axis=1)
    low_bad = frame["low"] > frame[["open", "close", "high"]].min(axis=1)
    if high_bad.any() or low_bad.any():
        index = high_bad[high_bad].index[0] if high_bad.any() else low_bad[low_bad].index[0]
        raise ValueError(f"OHLC envelope violation at {frame.loc[index].to_dict()}")


def serialize(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False, float_format="%.6f", lineterminator="\n").encode("utf-8")


def split_metadata(frame: pd.DataFrame) -> dict:
    n = len(frame)
    if n < 500:
        raise ValueError(f"insufficient daily history: {n} rows")
    dev_stop = int(n * 0.60)
    exploratory_stop = int(n * 0.80)
    definitions = {
        "development": (0, dev_stop - 1),
        "exploratory_oos": (dev_stop, exploratory_stop - 1),
        "final_oos": (exploratory_stop, n - 1),
    }
    result = {}
    for name, (start, end) in definitions.items():
        result[name] = {
            "start_index": start,
            "end_index": end,
            "start_date": str(frame.iloc[start]["date"]),
            "end_date": str(frame.iloc[end]["date"]),
            "rows": end - start + 1,
        }
    return result


def freeze(output_dir: Path, manifest_path: Path) -> dict:
    if manifest_path.exists():
        raise FileExistsError(f"manifest already exists; refusing to redefine frozen data: {manifest_path}")
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    pairs = {}
    for pair, spec in SOURCE_FILES.items():
        raw = fetch_source(spec["path"])
        actual_blob = git_blob_sha(raw)
        if actual_blob != spec["blob_sha"]:
            raise ValueError(
                f"upstream blob changed for {pair}: expected {spec['blob_sha']} got {actual_blob}; "
                "do not silently refresh the research fixture"
            )
        frame = normalize_source(raw, float(spec["price_scale"]))
        frozen_name = f"issue-55-{pair.lower()}-static-d1.csv"
        frozen_path = output_dir / frozen_name
        frozen = serialize(frame)
        frozen_path.write_bytes(frozen)
        pairs[pair] = {
            "source_repository": SOURCE_REPOSITORY,
            "source_ref_at_freeze": SOURCE_REF,
            "source_path": spec["path"],
            "source_url": source_url(spec["path"]),
            "source_git_blob_sha": spec["blob_sha"],
            "source_raw_sha256": sha256_bytes(raw),
            "source_price_scale_divisor": spec["price_scale"],
            "frozen_file": str(frozen_path.relative_to(manifest_path.parent)),
            "frozen_sha256": sha256_bytes(frozen),
            "rows": len(frame),
            "start_date": str(frame.iloc[0]["date"]),
            "end_date": str(frame.iloc[-1]["date"]),
            "splits": split_metadata(frame),
        }

    manifest = {
        "schema_version": 1,
        "issue": 55,
        "freeze_decision_date": FREEZE_DECISION_DATE,
        "canonical_fixture": "ejtraderLabs/historical-data static D1 CSV snapshot",
        "provider_claim_boundary": (
            "The upstream repository does not establish an authoritative dealer/broker provenance in its README. "
            "This dataset is used because its exact files can be pinned and reproduced. Provider/feed robustness "
            "is evaluated separately and no conclusion should rely on this fixture being a universal FX close."
        ),
        "normalization": {
            "columns": ["date", "open", "high", "low", "close"],
            "price_scaling": "divide stored integer-like prices by 100000 except USDJPY by 1000",
            "sort_ascending": True,
            "deduplicate_date_keep": "last",
            "csv_float_format": "%.6f",
            "ohlc_repair": "none; any envelope violation fails closed",
        },
        "split_rule": (
            "per-pair chronological 60% development / 20% exploratory OOS / 20% final OOS; "
            "floor boundaries by row count"
        ),
        "final_oos_status": "SEALED_DO_NOT_EVALUATE",
        "pairs": pairs,
        "research_boundary": (
            "The committed frozen CSV files are the exact primary Issue #55 evaluation inputs. "
            "Do not refresh or replace them after the experiment starts. This freeze computes no Wyckoff outcome "
            "and opens no final-OOS statistic."
        ),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def verify(manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("final_oos_status") != "SEALED_DO_NOT_EVALUATE":
        raise ValueError("final OOS seal missing")
    for pair, meta in manifest["pairs"].items():
        path = manifest_path.parent / meta["frozen_file"]
        content = path.read_bytes()
        if sha256_bytes(content) != meta["frozen_sha256"]:
            raise ValueError(f"frozen checksum mismatch for {pair}")
        frame = pd.read_csv(path)
        frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.date
        validate_ohlc(frame)
        if len(frame) != meta["rows"]:
            raise ValueError(f"row-count mismatch for {pair}")
        if str(frame.iloc[0]["date"]) != meta["start_date"] or str(frame.iloc[-1]["date"]) != meta["end_date"]:
            raise ValueError(f"date-range mismatch for {pair}")
        if split_metadata(frame) != meta["splits"]:
            raise ValueError(f"split metadata mismatch for {pair}")
    return manifest


def compact_summary(manifest: dict, mode: str) -> dict:
    return {
        "mode": mode,
        "canonical_fixture": manifest["canonical_fixture"],
        "final_oos_status": manifest["final_oos_status"],
        "pairs": {
            pair: {
                "rows": meta["rows"],
                "start_date": meta["start_date"],
                "end_date": meta["end_date"],
                "frozen_sha256": meta["frozen_sha256"],
                "development_end": meta["splits"]["development"]["end_date"],
                "exploratory_oos_end": meta["splits"]["exploratory_oos"]["end_date"],
                "final_oos_start": meta["splits"]["final_oos"]["start_date"],
            }
            for pair, meta in manifest["pairs"].items()
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    here = Path(__file__).resolve().parent
    parser.add_argument("mode", choices=["freeze", "verify"])
    parser.add_argument("--output-dir", type=Path, default=here / "data" / "frozen")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=here / "data" / "issue-55-static-fx-canonical-manifest.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = freeze(args.output_dir, args.manifest) if args.mode == "freeze" else verify(args.manifest)
    print(json.dumps(compact_summary(manifest, args.mode), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
