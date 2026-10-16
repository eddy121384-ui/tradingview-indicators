#!/usr/bin/env python3
"""Fail-closed reconciliation of independent #185 absolute OHLC and frozen #76 logs.

Read-only and outcome-free: checks timestamps and the pre-existing 1-bar
move1/mfe1/mae1 identities. NEVER fits parameters or computes trade PnL.
New OHLC remains local/private; only aggregate audit JSON may be shared.
"""
from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

OLD_MARKER = "ISSUE76|schema=1"
NEW_MARKER = "ISSUE185OHLC|schema=1"
REPRESENTATION = {
    "OANDA:EURUSD": "PRICE_LOG", "OANDA:GBPUSD": "PRICE_LOG",
    "OANDA:USDJPY": "PRICE_LOG", "TVC:US10Y": "YIELD_LEVEL",
    "TVC:DE10Y": "YIELD_LEVEL", "TVC:FR10Y": "YIELD_LEVEL",
    "TVC:GB10Y": "YIELD_LEVEL", "TVC:AU10Y": "YIELD_LEVEL",
    "TVC:JP10Y": "YIELD_LEVEL",
}
# Differences this large cannot be explained by text-rounding (12 dp OHLC,
# 10 dp #76 ratios/basis-point moves). These are parity, not tuning cutoffs.
EPS = {"PRICE_LOG": 5e-8, "YIELD_LEVEL": 5e-5}
DEFAULT_MANIFEST = (
    Path(__file__).parent / "artifacts" / "issue185_price_territory" /
    "issue185_real_cohort_manifest.json"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fields_from_cell(cell: str, marker: str) -> dict[str, str] | None:
    position = cell.find(marker)
    if position < 0:
        return None
    record = {}
    for token in cell[position:].strip().split("|"):
        if "=" in token:
            name, value = token.split("=", 1)
            record[name.strip()] = value.strip()
    if record.get("schema") != "1":
        raise ValueError("unrecognized schema: " + str(record.get("schema")))
    return record


def marker_rows(files: list[Path], marker: str):
    for path in files:
        with path.open(encoding="utf-8-sig", newline="") as fh:
            for row_number, row in enumerate(csv.reader(fh), 1):
                for cell in row:
                    found = fields_from_cell(cell, marker)
                    if found is not None:
                        yield path, row_number, found
                        break


def finite_float(value: str, field: str) -> float:
    try:
        answer = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field}: invalid number {value!r}") from exc
    if not math.isfinite(answer):
        raise ValueError(f"{field}: nonfinite {value!r}")
    return answer


def parse_old(files: list[Path]):
    old = {}
    duplicates = 0
    for path, number, row in marker_rows(files, OLD_MARKER):
        sym = row["ticker"]
        if sym not in REPRESENTATION or row.get("repr") != REPRESENTATION[sym]:
            raise ValueError(f"{path}:{number}: frozen ticker/repr mismatch")
        key = (sym, int(row["event_time"]))
        item = {
            "time": key[1],
            "bar": int(row["event_bar"]),
            "repr": row["repr"],
            "move1": finite_float(row["move1"], "move1"),
            "mfe1": finite_float(row["mfe1"], "mfe1"),
            "mae1": finite_float(row["mae1"], "mae1"),
        }
        if key in old:
            if old[key] != item:
                raise ValueError(f"{path}:{number}: conflicting old event {key}")
            duplicates += 1
        else:
            old[key] = item
    return old, duplicates


def parse_new(files: list[Path]):
    new = {}
    duplicates = 0
    for path, number, row in marker_rows(files, NEW_MARKER):
        sym = row["ticker"]
        if sym not in REPRESENTATION or row.get("repr") != REPRESENTATION[sym]:
            raise ValueError(f"{path}:{number}: forbidden ticker/repr")
        if row.get("tf") != "1D":
            raise ValueError(f"{path}:{number}: expected raw daily 1D bars")
        key = (sym, int(row["time"]))
        bar = int(row["bar"])
        prices = {k: finite_float(row[k], k) for k in ("o", "h", "l", "c")}
        o, h, l, c = (prices[k] for k in ("o", "h", "l", "c"))
        if h + 1e-9 < max(o, c, l) or l - 1e-9 > min(o, c, h):
            raise ValueError(f"{path}:{number}: OHLC envelope invalid {key}")
        if REPRESENTATION[sym] == "PRICE_LOG" and min(o, h, l, c) <= 0:
            raise ValueError(f"{path}:{number}: nonpositive FX absolute price")
        item = {"time": key[1], "bar": bar, **prices}
        if key in new:
            # A later export window can have a different chart bar_index even
            # though the exact same price candle is being repeated.
            if any(new[key][k] != prices[k] for k in prices):
                raise ValueError(f"{path}:{number}: conflicting absolute OHLC {key}")
            duplicates += 1
        else:
            new[key] = item
    return new, duplicates


def historical_identity(repr_name: str, event_close: float,
                        successor_price: float) -> float:
    if repr_name == "YIELD_LEVEL":
        return (successor_price - event_close) * 100.0
    if event_close <= 0 or successor_price <= 0:
        raise ValueError("PRICE_LOG requires positive native FX levels")
    return math.log(successor_price / event_close)


def audit(old: dict, new: dict, *, expected: set[str] | None = None) -> dict:
    expected = set(REPRESENTATION) if expected is None else set(expected)
    old_tickers = {sym for sym, _ in old}
    new_tickers = {sym for sym, _ in new}
    if not old or not new:
        return {"status": "INCOMPLETE", "old_events": len(old),
                "new_bars": len(new), "reason": "empty old or new logs"}

    by_symbol = defaultdict(list)
    for (sym, date), bar in new.items():
        by_symbol[sym].append(bar)
    next_by_time = {}
    for sym, bars in by_symbol.items():
        bars.sort(key=lambda x: x["time"])
        for first, second in zip(bars, bars[1:]):
            if second["bar"] == first["bar"] + 1:
                next_by_time[(sym, first["time"])] = second

    counts = Counter()
    symstats = defaultdict(Counter)
    examples = []
    offset_sets = defaultdict(set)
    for (sym, date), item in old.items():
        if (sym, date) not in new:
            counts["missing_event_price"] += 1
            symstats[sym]["missing_event_price"] += 1
            continue
        bar = new[(sym, date)]
        offset_sets[sym].add(bar["bar"] - item["bar"])
        successor = next_by_time.get((sym, date))
        if successor is None:
            counts["missing_next_price_bar"] += 1
            symstats[sym]["missing_next_price_bar"] += 1
            continue
        mismatch = False
        for key, actual in (("move1", successor["c"]),
                            ("mfe1", successor["h"]),
                            ("mae1", successor["l"])):
            predicted = historical_identity(item["repr"], bar["c"], actual)
            diff = abs(predicted - item[key])
            if diff > EPS[item["repr"]]:
                mismatch = True
                counts[key + "_mismatch"] += 1
                symstats[sym][key + "_mismatch"] += 1
                if len(examples) < 12:
                    examples.append({"symbol": sym, "time_ms": date,
                                     "field": key, "absolute_difference": diff})
        if not mismatch:
            counts["matched_event"] += 1
            symstats[sym]["matched_event"] += 1

    missing_tickers = sorted(expected - new_tickers)
    total_mismatch = sum(counts[k] for k in
                         ("move1_mismatch", "mfe1_mismatch", "mae1_mismatch"))
    valid = not missing_tickers and old_tickers == expected and (
        counts["missing_event_price"] == 0 and
        counts["missing_next_price_bar"] == 0 and total_mismatch == 0
    )
    return {
        "status": "PASS" if valid else "INCOMPLETE_OR_MISMATCH",
        "source": "ISSUE76 schema=1 vs ISSUE185OHLC schema=1",
        "old_events": len(old),
        "new_bars": len(new),
        "expected_symbols": sorted(expected),
        "new_symbols": sorted(new_tickers),
        "missing_symbols": missing_tickers,
        "matched_events": counts["matched_event"],
        "missing_event_price": counts["missing_event_price"],
        "missing_next_price_bar": counts["missing_next_price_bar"],
        "move1_mismatch": counts["move1_mismatch"],
        "mfe1_mismatch": counts["mfe1_mismatch"],
        "mae1_mismatch": counts["mae1_mismatch"],
        "bar_index_offset_varieties": {
            sym: len(values) for sym, values in sorted(offset_sets.items())
        },
        "per_symbol": {sym: dict(symstats[sym]) for sym in sorted(old_tickers)},
        "first_mismatches": examples,
        "note": (
            "Use timestamp to join; bar_index can change with chart history. "
            "PASS means source-event price parity, not C1 policy success. "
            "No outcomes, PnL, or MFE were recomputed."
        ),
    }


def verify_frozen_old_inputs(files: list[Path], manifest: Path) -> None:
    obj = json.loads(manifest.read_text(encoding="utf-8"))
    expected = Counter((f["sha256"], f["bytes"]) for f in obj["manifest"])
    actual = Counter((sha256_file(f), f.stat().st_size) for f in files)
    if expected != actual:
        raise ValueError(
            "Old #76 raw files do not exactly match the frozen nine-file "
            "SHA-256/byte-size manifest; do not mix datasets"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-glob", required=True,
                        help="quoted glob for original nine #76 CSV exports")
    parser.add_argument("--new-glob", required=True,
                        help="quoted glob for new #185 absolute OHLC CSVs")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out", type=Path,
                        help="write counts-only private JSON audit here")
    args = parser.parse_args()
    old_files = sorted(Path(p) for p in glob.glob(args.old_glob))
    new_files = sorted(Path(p) for p in glob.glob(args.new_glob))
    if len(old_files) != 9:
        parser.error(f"expected nine original CSV files, found {len(old_files)}")
    if not new_files:
        parser.error("no #185 absolute OHLC CSVs found")
    verify_frozen_old_inputs(old_files, args.manifest)
    old, d_old = parse_old(old_files)
    new, d_new = parse_new(new_files)
    result = audit(old, new)
    result.update({
        "frozen_input_hashes_verified": 9,
        "old_duplicate_log_rows": d_old,
        "new_duplicate_log_rows": d_new,
        "new_export_file_count": len(new_files),
    })
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(output)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
