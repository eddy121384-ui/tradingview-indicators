#!/usr/bin/env python3
"""Parse Issue #76 TradingView Pine Logs into deterministic event tables.

The Pine harness emits one marker row per formal-stage event bar, containing all
four preregistered forward horizons. This parser is intentionally independent of
the classifier: it only validates the frozen feed/schema contract, de-duplicates
log rows, expands horizons, labels event layers, and computes descriptive tables.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

MARKER = "ISSUE76|schema=1"
HORIZONS = (1, 5, 10, 20)
CANONICAL = {(1, 2), (2, 3), (3, 2), (4, 5), (5, 6), (6, 5)}
FEEDS = {
    "OANDA:EURUSD": ("EURUSD", "FX", "PRICE_LOG"),
    "OANDA:GBPUSD": ("GBPUSD", "FX", "PRICE_LOG"),
    "OANDA:USDJPY": ("USDJPY", "FX", "PRICE_LOG"),
    "TVC:US10Y": ("US10Y", "YIELD_10Y", "YIELD_LEVEL"),
    "TVC:DE10Y": ("DE10Y", "YIELD_10Y", "YIELD_LEVEL"),
    "TVC:FR10Y": ("FR10Y", "YIELD_10Y", "YIELD_LEVEL"),
    "TVC:GB10Y": ("GB10Y", "YIELD_10Y", "YIELD_LEVEL"),
    "TVC:AU10Y": ("AU10Y", "YIELD_10Y", "YIELD_LEVEL"),
    "TVC:JP10Y": ("JP10Y", "YIELD_10Y", "YIELD_LEVEL"),
}


def _float(value: str, key: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid float for {key}: {value!r}") from exc
    if not math.isfinite(out):
        raise ValueError(f"non-finite float for {key}: {value!r}")
    return out


def _int(value: str, key: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid integer for {key}: {value!r}") from exc


def parse_marker_text(text: str) -> dict[str, str] | None:
    """Return key/value fields from any cell containing an Issue-76 marker."""
    pos = text.find(MARKER)
    if pos < 0:
        return None
    payload = text[pos:].strip()
    fields: dict[str, str] = {}
    for token in payload.split("|"):
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        fields[key.strip()] = value.strip()
    if fields.get("schema") != "1":
        raise ValueError(f"unsupported Issue #76 log schema: {fields.get('schema')!r}")
    return fields


def iter_marker_fields(path: Path) -> Iterable[dict[str, str]]:
    """Scan every CSV cell so TradingView column naming does not matter."""
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh)
        for row in reader:
            for cell in row:
                parsed = parse_marker_text(cell)
                if parsed is not None:
                    yield parsed
                    break


def validate_event(fields: dict[str, str]) -> dict[str, object]:
    required_meta = {
        "ticker",
        "tf",
        "repr",
        "event_time",
        "event_bar",
        "stage",
        "prev",
        "fresh",
        "transition",
        "scale",
    }
    missing = sorted(required_meta - fields.keys())
    if missing:
        raise ValueError(f"marker row missing metadata fields: {missing}")

    ticker = fields["ticker"]
    if ticker not in FEEDS:
        raise ValueError(f"ticker outside frozen Issue #76 universe: {ticker}")
    market, asset_class, expected_repr = FEEDS[ticker]
    if fields["repr"] != expected_repr:
        raise ValueError(
            f"representation mismatch for {ticker}: expected {expected_repr}, got {fields['repr']}"
        )
    if fields["tf"] not in {"D", "1D"}:
        raise ValueError(f"non-D1 Issue #76 export for {ticker}: tf={fields['tf']}")

    event_time_ms = _int(fields["event_time"], "event_time")
    event_bar = _int(fields["event_bar"], "event_bar")
    stage = _int(fields["stage"], "stage")
    prev = _int(fields["prev"], "prev")
    fresh = _int(fields["fresh"], "fresh")
    scale = _float(fields["scale"], "scale")
    if stage not in range(1, 7):
        raise ValueError(f"formal stage outside S1..S6: {stage}")
    if prev not in range(0, 7):
        raise ValueError(f"previous formal stage outside 0..6: {prev}")
    if fresh not in (0, 1):
        raise ValueError(f"fresh must be 0/1, got {fresh}")
    if scale <= 0.0:
        raise ValueError(f"event-time scale must be positive, got {scale}")
    expected_transition = f"{prev}>{stage}"
    if fields["transition"] != expected_transition:
        raise ValueError(
            f"transition mismatch: expected {expected_transition}, got {fields['transition']}"
        )
    if bool(fresh) != (stage != prev):
        raise ValueError("fresh flag is inconsistent with stage/prev")

    metric_values: dict[str, float] = {}
    for h in HORIZONS:
        for stem in ("move", "norm", "mfe", "mae", "mfen", "maen", "rv", "rvn"):
            key = f"{stem}{h}"
            if key not in fields:
                raise ValueError(f"marker row missing metric {key}")
            metric_values[key] = _float(fields[key], key)

    event_time_iso = datetime.fromtimestamp(event_time_ms / 1000.0, tz=timezone.utc).isoformat()
    return {
        "ticker": ticker,
        "market": market,
        "asset_class": asset_class,
        "representation": expected_repr,
        "event_time_ms": event_time_ms,
        "event_time_utc": event_time_iso,
        "event_bar": event_bar,
        "stage": stage,
        "prev_stage": prev,
        "fresh": fresh,
        "transition": expected_transition,
        "scale": scale,
        **metric_values,
    }


def load_events(paths: list[Path]) -> tuple[list[dict[str, object]], dict[str, object]]:
    dedup: dict[tuple[str, int, int], dict[str, object]] = {}
    file_counts: dict[str, int] = {}
    total_markers = 0
    for path in paths:
        count = 0
        for fields in iter_marker_fields(path):
            event = validate_event(fields)
            key = (str(event["ticker"]), int(event["event_time_ms"]), int(event["event_bar"]))
            dedup[key] = event
            count += 1
            total_markers += 1
        file_counts[str(path)] = count

    events = sorted(
        dedup.values(),
        key=lambda r: (str(r["ticker"]), int(r["event_time_ms"]), int(r["event_bar"])),
    )
    metadata = {
        "schema": 1,
        "input_files": [str(p) for p in paths],
        "marker_rows_by_file": file_counts,
        "marker_rows_total_before_dedup": total_markers,
        "event_rows_after_dedup": len(events),
        "possible_10000_log_truncation_files": [p for p, n in file_counts.items() if n == 10000],
        "frozen_horizons": list(HORIZONS),
        "canonical_transitions": [f"S{a}->S{b}" for a, b in sorted(CANONICAL)],
    }
    return events, metadata


def expand_horizons(events: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for event in events:
        for h in HORIZONS:
            rows.append(
                {
                    "ticker": event["ticker"],
                    "market": event["market"],
                    "asset_class": event["asset_class"],
                    "representation": event["representation"],
                    "event_time_ms": event["event_time_ms"],
                    "event_time_utc": event["event_time_utc"],
                    "event_bar": event["event_bar"],
                    "stage": event["stage"],
                    "prev_stage": event["prev_stage"],
                    "fresh": event["fresh"],
                    "transition": event["transition"],
                    "scale": event["scale"],
                    "horizon": h,
                    "raw_move": event[f"move{h}"],
                    "norm_move": event[f"norm{h}"],
                    "mfe_raw": event[f"mfe{h}"],
                    "mae_raw": event[f"mae{h}"],
                    "mfe_norm": event[f"mfen{h}"],
                    "mae_norm": event[f"maen{h}"],
                    "future_rv_raw": event[f"rv{h}"],
                    "future_rv_norm": event[f"rvn{h}"],
                }
            )
    return rows


def quantile(values: list[float], q: float) -> float:
    if not values:
        return math.nan
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    pos = (len(xs) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return xs[lo]
    w = pos - lo
    return xs[lo] * (1.0 - w) + xs[hi] * w


def _mean(values: list[float]) -> float:
    return statistics.fmean(values) if values else math.nan


def _median(values: list[float]) -> float:
    return statistics.median(values) if values else math.nan


def _event_labels(row: dict[str, object]) -> list[tuple[str, str]]:
    stage = int(row["stage"])
    prev = int(row["prev_stage"])
    labels = [("occupancy", f"S{stage}")]
    if int(row["fresh"]) == 1:
        labels.append(("fresh_entry", f"S{stage}"))
    if (prev, stage) in CANONICAL:
        labels.append(("canonical_transition", f"S{prev}->S{stage}"))
    return labels


def build_summary(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str, int], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        for event_type, event_key in _event_labels(row):
            grouped[(str(row["ticker"]), event_type, event_key, int(row["horizon"]))].append(row)

    out: list[dict[str, object]] = []
    for (ticker, event_type, event_key, horizon), grp in sorted(grouped.items()):
        raw = [float(r["raw_move"]) for r in grp]
        norm = [float(r["norm_move"]) for r in grp]
        mfe_raw = [float(r["mfe_raw"]) for r in grp]
        mae_raw = [float(r["mae_raw"]) for r in grp]
        mfe_norm = [float(r["mfe_norm"]) for r in grp]
        mae_norm = [float(r["mae_norm"]) for r in grp]
        rv_raw = [float(r["future_rv_raw"]) for r in grp]
        rv_norm = [float(r["future_rv_norm"]) for r in grp]
        stage = int(grp[0]["stage"])
        direction = 1 if stage in (2, 3) else -1 if stage in (5, 6) else 0
        positive_rate = sum(x > 0.0 for x in raw) / len(raw)
        aligned_hit_rate = (
            sum((x * direction) > 0.0 for x in raw) / len(raw) if direction else math.nan
        )
        out.append(
            {
                "ticker": ticker,
                "market": grp[0]["market"],
                "asset_class": grp[0]["asset_class"],
                "event_type": event_type,
                "event_key": event_key,
                "destination_stage": stage,
                "horizon": horizon,
                "n": len(grp),
                "mean_raw_move": _mean(raw),
                "median_raw_move": _median(raw),
                "positive_rate": positive_rate,
                "direction_sign": direction,
                "aligned_hit_rate": aligned_hit_rate,
                "q10_raw_move": quantile(raw, 0.10),
                "q25_raw_move": quantile(raw, 0.25),
                "q75_raw_move": quantile(raw, 0.75),
                "q90_raw_move": quantile(raw, 0.90),
                "mean_norm_move": _mean(norm),
                "median_norm_move": _median(norm),
                "q10_norm_move": quantile(norm, 0.10),
                "q25_norm_move": quantile(norm, 0.25),
                "q75_norm_move": quantile(norm, 0.75),
                "q90_norm_move": quantile(norm, 0.90),
                "mean_mfe_raw": _mean(mfe_raw),
                "mean_mae_raw": _mean(mae_raw),
                "mean_mfe_norm": _mean(mfe_norm),
                "mean_mae_norm": _mean(mae_norm),
                "mean_future_rv_raw": _mean(rv_raw),
                "mean_future_rv_norm": _mean(rv_norm),
            }
        )
    return out


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description="Parse Issue #76 TradingView Pine Log CSV exports")
    ap.add_argument("inputs", nargs="+", type=Path, help="TradingView Pine Logs CSV export(s)")
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    events, metadata = load_events(args.inputs)
    if not events:
        raise SystemExit("no ISSUE76 schema=1 marker rows found")
    long_rows = expand_horizons(events)
    summary = build_summary(long_rows)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.out_dir / "issue76-events-wide.csv", events)
    write_csv(args.out_dir / "issue76-events-long.csv", long_rows)
    write_csv(args.out_dir / "issue76-summary-per-market.csv", summary)
    (args.out_dir / "issue76-parse-metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(f"events={len(events)} long_rows={len(long_rows)} summary_rows={len(summary)}")
    if metadata["possible_10000_log_truncation_files"]:
        print("WARNING: one or more files contain exactly 10,000 marker rows; collect an earlier time window")
    print("Issue #76 log parser PASS")


if __name__ == "__main__":
    main()
