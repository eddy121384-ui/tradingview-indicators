#!/usr/bin/env python3
"""Issue #76 Phase-B regime-conditioned exposure-map analysis.

This is descriptive decision-support research, not a strategy backtest. It reuses
accepted Pine-log exports, compares each regime with each market's own all-formal
baseline, derives fixed regime-age buckets, and keeps FX and yield semantics
separate. A splice-screened sensitivity view is also emitted for obvious yield
feed discontinuities; the primary sample is never silently altered.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

MARKER = "ISSUE76|schema=1"
HORIZONS = (1, 5, 10, 20)
AGE_BUCKETS = ("age0", "age1_4", "age5_9", "age10_19", "age20p")
STAGE_NAMES = {
    1: "Accumulation",
    2: "Markup",
    3: "Reaccumulation",
    4: "Distribution",
    5: "Markdown",
    6: "Redistribution",
}
FEEDS = {
    "OANDA:EURUSD": ("EURUSD", "FX", "PRICE_LOG"),
    "OANDA:GBPUSD": ("GBPUSD", "FX", "PRICE_LOG"),
    "OANDA:USDJPY": ("USDJPY", "FX", "PRICE_LOG"),
    "TVC:US10Y": ("US10Y", "RATES", "YIELD_LEVEL"),
    "TVC:DE10Y": ("DE10Y", "RATES", "YIELD_LEVEL"),
    "TVC:FR10Y": ("FR10Y", "RATES", "YIELD_LEVEL"),
    "TVC:GB10Y": ("GB10Y", "RATES", "YIELD_LEVEL"),
    "TVC:AU10Y": ("AU10Y", "RATES", "YIELD_LEVEL"),
    "TVC:JP10Y": ("JP10Y", "RATES", "YIELD_LEVEL"),
}
METRIC_STEMS = ("move", "norm", "mfe", "mae", "mfen", "maen", "rv", "rvn")


def parse_marker(text: str) -> dict[str, str] | None:
    pos = text.find(MARKER)
    if pos < 0:
        return None
    out: dict[str, str] = {}
    for token in text[pos:].strip().split("|"):
        if "=" in token:
            key, value = token.split("=", 1)
            out[key.strip()] = value.strip()
    return out


def iter_fields(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        for row in csv.reader(fh):
            for cell in row:
                parsed = parse_marker(cell)
                if parsed is not None:
                    yield parsed
                    break


def finite_float(value: str, key: str, *, allow_nan: bool = False) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid float for {key}: {value!r}") from exc
    if math.isfinite(out):
        return out
    if allow_nan and math.isnan(out):
        return out
    raise ValueError(f"non-finite float for {key}: {value!r}")


def load_events(paths: list[Path]) -> tuple[list[dict[str, object]], dict[str, object]]:
    dedup: dict[tuple[str, int, int], dict[str, object]] = {}
    counts: dict[str, int] = {}
    for path in paths:
        count = 0
        for fields in iter_fields(path):
            ticker = fields.get("ticker", "")
            if ticker not in FEEDS:
                raise ValueError(f"ticker outside frozen universe: {ticker}")
            market, asset, expected_repr = FEEDS[ticker]
            if fields.get("tf") not in {"D", "1D"}:
                raise ValueError(f"non-D1 export for {ticker}: {fields.get('tf')}")
            if fields.get("repr") != expected_repr:
                raise ValueError(f"representation mismatch for {ticker}")
            event_time = int(fields["event_time"])
            event_bar = int(fields["event_bar"])
            stage = int(fields["stage"])
            prev = int(fields["prev"])
            fresh = int(fields["fresh"])
            if stage not in range(1, 7) or prev not in range(0, 7):
                raise ValueError("stage outside frozen range")
            if fresh not in (0, 1) or bool(fresh) != (stage != prev):
                raise ValueError("fresh flag mismatch")
            if fields.get("transition") != f"{prev}>{stage}":
                raise ValueError("transition mismatch")
            scale = finite_float(fields["scale"], "scale")
            if scale <= 0:
                raise ValueError("non-positive scale")
            rec: dict[str, object] = {
                "ticker": ticker,
                "market": market,
                "asset_class": asset,
                "representation": expected_repr,
                "event_time_ms": event_time,
                "event_bar": event_bar,
                "stage": stage,
                "prev_stage": prev,
                "fresh": fresh,
                "transition": f"{prev}>{stage}",
                "scale": scale,
            }
            for h in HORIZONS:
                for stem in METRIC_STEMS:
                    key = f"{stem}{h}"
                    if key not in fields:
                        raise ValueError(f"missing metric {key}")
                    # TradingView has emitted NaN only for rv/rvn on exactly-flat
                    # close paths. Repair is deferred until cross-row continuity is known.
                    rec[key] = finite_float(fields[key], key, allow_nan=stem in {"rv", "rvn"})
            dedup[(ticker, event_time, event_bar)] = rec
            count += 1
        counts[str(path)] = count

    events = sorted(dedup.values(), key=lambda r: (str(r["ticker"]), int(r["event_bar"])))
    repairs: list[dict[str, object]] = []
    by_ticker: dict[str, list[dict[str, object]]] = defaultdict(list)
    for event in events:
        by_ticker[str(event["ticker"])].append(event)
    for ticker, group in by_ticker.items():
        by_bar = {int(r["event_bar"]): r for r in group}
        for event in group:
            for h in HORIZONS:
                rv_key, rvn_key = f"rv{h}", f"rvn{h}"
                if math.isfinite(float(event[rv_key])) and math.isfinite(float(event[rvn_key])):
                    continue
                start = int(event["event_bar"])
                future_one_bar: list[float] = []
                for offset in range(h):
                    nxt = by_bar.get(start + offset)
                    if nxt is None:
                        raise ValueError(
                            f"cannot reconstruct non-finite RV: {ticker} bar={start} h={h} lacks contiguous event bar"
                        )
                    future_one_bar.append(float(nxt["move1"]))
                rv = math.sqrt(statistics.fmean(x * x for x in future_one_bar))
                divisor = float(event["scale"]) * (100.0 if event["representation"] == "YIELD_LEVEL" else 1.0)
                event[rv_key] = rv
                event[rvn_key] = rv / divisor
                repairs.append({"ticker": ticker, "event_bar": start, "horizon": h, "rv": rv})

    metadata = {
        "marker_rows_by_file": counts,
        "events_after_dedup": len(events),
        "possible_10000_log_truncation_files": [p for p, n in counts.items() if n == 10000],
        "nonfinite_rv_repairs": repairs,
    }
    return events, metadata


def age_bucket(age: int) -> str:
    if age == 0:
        return "age0"
    if age <= 4:
        return "age1_4"
    if age <= 9:
        return "age5_9"
    if age <= 19:
        return "age10_19"
    return "age20p"


def add_regime_age(events: list[dict[str, object]]) -> int:
    unknown = 0
    by_ticker: dict[str, list[dict[str, object]]] = defaultdict(list)
    for event in events:
        by_ticker[str(event["ticker"])].append(event)
    for group in by_ticker.values():
        last_fresh_bar: int | None = None
        last_fresh_stage: int | None = None
        for event in sorted(group, key=lambda r: int(r["event_bar"])):
            if int(event["fresh"]) == 1:
                last_fresh_bar = int(event["event_bar"])
                last_fresh_stage = int(event["stage"])
                age = 0
            elif last_fresh_bar is not None and int(event["stage"]) == last_fresh_stage:
                age = int(event["event_bar"]) - last_fresh_bar
            else:
                event["regime_age"] = None
                event["age_bucket"] = "unknown"
                unknown += 1
                continue
            event["regime_age"] = age
            event["age_bucket"] = age_bucket(age)
    return unknown


def splice_bars(events: list[dict[str, object]]) -> dict[str, set[int]]:
    """Diagnostic only: identify obvious G10 yield feed discontinuities.

    The rule is deliberately independent of regime outcome: a one-day yield move
    must exceed both 100 bp and 20 event-time ATR. These rows remain in the primary
    sample; a second sensitivity view excludes forward windows crossing them.
    """
    out: dict[str, set[int]] = defaultdict(set)
    for e in events:
        if e["representation"] != "YIELD_LEVEL":
            continue
        if abs(float(e["move1"])) > 100.0 and abs(float(e["norm1"])) > 20.0:
            out[str(e["ticker"])].add(int(e["event_bar"]))
    return dict(out)


def percentile(values: list[float], p: float) -> float:
    xs = sorted(values)
    if not xs:
        return math.nan
    if len(xs) == 1:
        return xs[0]
    pos = (len(xs) - 1) * p
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return xs[lo]
    w = pos - lo
    return xs[lo] * (1 - w) + xs[hi] * w


def describe(group: list[dict[str, object]], h: int) -> dict[str, float]:
    norm = [float(r[f"norm{h}"]) for r in group]
    raw = [float(r[f"move{h}"]) for r in group]
    return {
        "mean": statistics.fmean(norm),
        "median": statistics.median(norm),
        "positive_rate": sum(x > 0 for x in raw) / len(raw),
        "q10": percentile(norm, 0.10),
        "q25": percentile(norm, 0.25),
        "q75": percentile(norm, 0.75),
        "q90": percentile(norm, 0.90),
        "mfe": statistics.fmean(float(r[f"mfen{h}"]) for r in group),
        "mae": statistics.fmean(float(r[f"maen{h}"]) for r in group),
        "future_rv": statistics.fmean(float(r[f"rvn{h}"]) for r in group),
    }


def build_per_market(events: list[dict[str, object]], bad: dict[str, set[int]]) -> list[dict[str, object]]:
    by_ticker: dict[str, list[dict[str, object]]] = defaultdict(list)
    for e in events:
        by_ticker[str(e["ticker"])].append(e)
    rows: list[dict[str, object]] = []
    for ticker, all_events in sorted(by_ticker.items()):
        for h in HORIZONS:
            for variant in ("primary", "splice_screened"):
                if variant == "primary":
                    eligible = all_events
                else:
                    bset = bad.get(ticker, set())
                    eligible = [
                        e for e in all_events
                        if not any(int(e["event_bar"]) <= b < int(e["event_bar"]) + h for b in bset)
                    ]
                baseline = describe(eligible, h)
                groups: list[tuple[str, str, list[dict[str, object]]]] = []
                for stage in range(1, 7):
                    sg = [e for e in eligible if int(e["stage"]) == stage]
                    if not sg:
                        continue
                    groups.append(("occupancy", "all", sg))
                    for bucket in AGE_BUCKETS:
                        bg = [e for e in sg if e.get("age_bucket") == bucket]
                        if bg:
                            groups.append(("age", bucket, bg))
                for layer, bucket, group in groups:
                    d = describe(group, h)
                    stage = int(group[0]["stage"])
                    row: dict[str, object] = {
                        "variant": variant,
                        "ticker": ticker,
                        "market": group[0]["market"],
                        "asset_class": group[0]["asset_class"],
                        "stage": stage,
                        "stage_name": STAGE_NAMES[stage],
                        "layer": layer,
                        "age_bucket": bucket,
                        "horizon": h,
                        "n": len(group),
                    }
                    for key, value in d.items():
                        row[key] = value
                        row[f"baseline_{key}"] = baseline[key]
                        row[f"lift_{key}"] = value - baseline[key]
                    rows.append(row)
    return rows


def build_equal_market(per_market: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[object, ...], list[dict[str, object]]] = defaultdict(list)
    for row in per_market:
        key = (
            row["variant"], row["asset_class"], row["stage"], row["stage_name"],
            row["layer"], row["age_bucket"], row["horizon"],
        )
        grouped[key].append(row)
    out: list[dict[str, object]] = []
    metrics = ("mean", "median", "positive_rate", "q10", "q90", "mfe", "mae", "future_rv")
    for key, group in sorted(grouped.items(), key=lambda kv: tuple(str(x) for x in kv[0])):
        variant, asset, stage, stage_name, layer, bucket, horizon = key
        row: dict[str, object] = {
            "variant": variant,
            "asset_class": asset,
            "stage": stage,
            "stage_name": stage_name,
            "layer": layer,
            "age_bucket": bucket,
            "horizon": horizon,
            "markets": len(group),
            "n_total": sum(int(r["n"]) for r in group),
        }
        for metric in metrics:
            row[f"equal_market_{metric}"] = statistics.fmean(float(r[metric]) for r in group)
            row[f"equal_market_lift_{metric}"] = statistics.fmean(float(r[f"lift_{metric}"]) for r in group)
        row["markets_mean_above_baseline"] = sum(float(r["lift_mean"]) > 0 for r in group)
        row["markets_median_above_baseline"] = sum(float(r["lift_median"]) > 0 for r in group)
        row["markets_positive_rate_above_baseline"] = sum(float(r["lift_positive_rate"]) > 0 for r in group)
        out.append(row)
    return out


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+", type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    args = ap.parse_args()
    events, metadata = load_events(args.inputs)
    metadata["unknown_regime_age_rows"] = add_regime_age(events)
    bad = splice_bars(events)
    metadata["yield_splice_diagnostic_rule"] = "abs(move1)>100bp and abs(norm1)>20ATR"
    metadata["yield_splice_diagnostic_bars"] = {k: sorted(v) for k, v in bad.items()}
    per_market = build_per_market(events, bad)
    equal_market = build_equal_market(per_market)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.out_dir / "issue76-phase-b-per-market.csv", per_market)
    write_csv(args.out_dir / "issue76-phase-b-equal-market.csv", equal_market)
    (args.out_dir / "issue76-phase-b-metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"events={len(events)} per_market_rows={len(per_market)} equal_market_rows={len(equal_market)}")
    print(f"nonfinite_rv_repairs={len(metadata['nonfinite_rv_repairs'])}")
    print(f"unknown_regime_age_rows={metadata['unknown_regime_age_rows']}")
    print(f"yield_splice_diagnostic_bars={metadata['yield_splice_diagnostic_bars']}")
    print("Issue #76 Phase-B exposure-map analysis PASS")


if __name__ == "__main__":
    main()
