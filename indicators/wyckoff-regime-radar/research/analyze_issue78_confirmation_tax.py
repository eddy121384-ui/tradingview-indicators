#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, glob, math, statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

MARKER = "ISSUE76|schema=1"
TREND = {2: "Markup", 5: "Markdown"}
THRESHOLDS = (0.5, 1.0, 2.0)
ERAS = (("2010-2014", 2010, 2014), ("2015-2019", 2015, 2019), ("2020-2026", 2020, 2026))
EXPECTED_EVENTS = 68118
EXPECTED_EPISODES = 1624

def parse_marker(text):
    p = text.find(MARKER)
    if p < 0:
        return None
    out = {}
    for tok in text[p:].strip().split("|"):
        if "=" in tok:
            k, v = tok.split("=", 1)
            out[k] = v
    return out

def read_events(paths):
    dedup = {}
    for path in paths:
        with Path(path).open(encoding="utf-8-sig", newline="") as fh:
            for row in csv.reader(fh):
                f = None
                for cell in row:
                    f = parse_marker(cell)
                    if f:
                        break
                if not f:
                    continue
                rec = {
                    "ticker": f["ticker"], "repr": f["repr"],
                    "event_time": int(f["event_time"]), "event_bar": int(f["event_bar"]),
                    "stage": int(f["stage"]), "fresh": int(f["fresh"]),
                    "scale": float(f["scale"]), "move1": float(f["move1"]),
                }
                dedup[(rec["ticker"], rec["event_time"], rec["event_bar"])] = rec
    return sorted(dedup.values(), key=lambda r: (r["ticker"], r["event_bar"]))

def episodes(events):
    by = defaultdict(list)
    for e in events:
        by[e["ticker"]].append(e)
    out = []
    for ticker, group in by.items():
        group.sort(key=lambda r: r["event_bar"])
        i = 0
        episode_id = 0
        while i < len(group):
            row = group[i]
            stage = row["stage"]
            if stage in TREND and row["fresh"] == 1:
                j = i + 1
                while (
                    j < len(group)
                    and group[j]["stage"] == stage
                    and group[j]["event_bar"] == group[j - 1]["event_bar"] + 1
                ):
                    j += 1
                if j < len(group):
                    out.append((ticker, stage, episode_id, group[i:j]))
                    episode_id += 1
                i = j
            else:
                i += 1
    return out

def entry_atr_denom(row):
    return row["scale"] * (100.0 if row["repr"] == "YIELD_LEVEL" else 1.0)

def aligned_steps(stage, rows):
    d = 1.0 if stage == 2 else -1.0
    den = entry_atr_denom(rows[0])
    return [d * r["move1"] / den for r in rows]

def era_name(ms):
    year = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).year
    for name, start, end in ERAS:
        if start <= year <= end:
            return name
    return "other"

def time_bucket(t):
    if t <= 5:
        return "1-5"
    if t <= 10:
        return "6-10"
    if t <= 20:
        return "11-20"
    return "21+"

def episode_threshold_records(ep):
    ticker, stage, episode_id, rows = ep
    steps = aligned_steps(stage, rows)
    cum = []
    x = 0.0
    for step in steps:
        x += step
        cum.append(x)
    total_mfe = max([0.0] + cum)
    total_net = cum[-1] if cum else 0.0
    slice_name = "failed" if total_mfe < 4.0 else ("large" if total_mfe >= 8.0 else "middle")
    out = []
    for threshold in THRESHOLDS:
        hit_idx = next((i for i, v in enumerate(cum) if v >= threshold), None)
        if hit_idx is None:
            rec = {
                "ticker": ticker, "stage": TREND[stage], "episode_id": episode_id,
                "entry_time": rows[0]["event_time"], "era": era_name(rows[0]["event_time"]),
                "bars": len(steps), "threshold": threshold, "hit": 0,
                "time_to_proof": math.nan, "time_bucket": "never", "proof_cum_atr": math.nan,
                "total_mfe_atr": total_mfe, "total_net_atr": total_net,
                "future_net_atr": math.nan, "future_mfe_atr": math.nan, "future_mae_atr": math.nan,
                "future_plus1": math.nan, "future_plus2": math.nan, "future_plus4": math.nan,
                "remaining_bars": math.nan, "mfe_consumed_fraction": math.nan,
                "mfe_remaining_fraction": math.nan, "full_harvest": total_net,
                "probe_then_full_harvest": 0.25 * total_net,
                "harvest_delta_vs_full": 0.25 * total_net - total_net,
                "avg_exposure": 0.25, "underexposed_frac": 1.0, "slice": slice_name,
            }
        else:
            t = hit_idx + 1
            proof_cum = cum[hit_idx]
            future = steps[hit_idx + 1:]
            fx = 0.0
            hi = 0.0
            lo = 0.0
            for step in future:
                fx += step
                hi = max(hi, fx)
                lo = min(lo, fx)
            future_net = sum(future)
            harvest = 0.25 * sum(steps[:hit_idx + 1]) + sum(future)
            rec = {
                "ticker": ticker, "stage": TREND[stage], "episode_id": episode_id,
                "entry_time": rows[0]["event_time"], "era": era_name(rows[0]["event_time"]),
                "bars": len(steps), "threshold": threshold, "hit": 1,
                "time_to_proof": t, "time_bucket": time_bucket(t), "proof_cum_atr": proof_cum,
                "total_mfe_atr": total_mfe, "total_net_atr": total_net,
                "future_net_atr": future_net, "future_mfe_atr": hi, "future_mae_atr": -lo,
                "future_plus1": 1.0 if hi >= 1.0 else 0.0,
                "future_plus2": 1.0 if hi >= 2.0 else 0.0,
                "future_plus4": 1.0 if hi >= 4.0 else 0.0,
                "remaining_bars": len(future),
                "mfe_consumed_fraction": proof_cum / total_mfe if total_mfe > 0 else math.nan,
                "mfe_remaining_fraction": (total_mfe - proof_cum) / total_mfe if total_mfe > 0 else math.nan,
                "full_harvest": total_net, "probe_then_full_harvest": harvest,
                "harvest_delta_vs_full": harvest - total_net,
                "avg_exposure": (0.25 * (hit_idx + 1) + len(future)) / len(steps),
                "underexposed_frac": (hit_idx + 1) / len(steps), "slice": slice_name,
            }
        out.append(rec)
    return out

def finite(values):
    return [v for v in values if isinstance(v, (int, float)) and math.isfinite(v)]

def mean(values):
    v = finite(values)
    return statistics.fmean(v) if v else math.nan

def median(values):
    v = finite(values)
    return statistics.median(v) if v else math.nan

def summarize_equal_market(records, group_fields, metrics):
    grouped = defaultdict(list)
    for r in records:
        grouped[tuple(r[f] for f in group_fields)].append(r)
    out = []
    for keys, g in grouped.items():
        market_rows = []
        tickers = sorted({r["ticker"] for r in g})
        for ticker in tickers:
            mg = [r for r in g if r["ticker"] == ticker]
            row = {"ticker": ticker, "n": len(mg)}
            for m in metrics:
                row[m + "_mean"] = mean([r[m] for r in mg])
                row[m + "_median"] = median([r[m] for r in mg])
            market_rows.append(row)
        row = {f: v for f, v in zip(group_fields, keys)}
        row["markets"] = len(market_rows)
        row["pooled_n"] = len(g)
        for m in metrics:
            row[m + "_eq_market_mean"] = mean([r[m + "_mean"] for r in market_rows])
            row[m + "_eq_market_median"] = median([r[m + "_median"] for r in market_rows])
        out.append(row)
    return out

def write_csv(path, rows):
    if not rows:
        return
    with Path(path).open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--out", default="/mnt/data/issue78-confirmation-tax")
    args = ap.parse_args()
    paths = args.paths or sorted(glob.glob("/mnt/data/pine-logs-#76 Forward Logger*.csv"))
    if not paths:
        raise SystemExit("no Issue #76 Forward Logger CSVs found")

    events = read_events(paths)
    eps = episodes(events)
    if len(events) != EXPECTED_EVENTS:
        raise AssertionError(f"event count drift: expected {EXPECTED_EVENTS}, got {len(events)}")
    if len(eps) != EXPECTED_EPISODES:
        raise AssertionError(f"episode count drift: expected {EXPECTED_EPISODES}, got {len(eps)}")

    records = []
    for ep in eps:
        records.extend(episode_threshold_records(ep))

    common_metrics = [
        "hit", "time_to_proof", "proof_cum_atr", "future_net_atr", "future_mfe_atr",
        "future_mae_atr", "future_plus1", "future_plus2", "future_plus4", "remaining_bars",
        "mfe_consumed_fraction", "mfe_remaining_fraction", "probe_then_full_harvest",
        "full_harvest", "harvest_delta_vs_full", "avg_exposure", "underexposed_frac",
    ]

    universal = summarize_equal_market(records, ["threshold"], common_metrics)
    slices = summarize_equal_market(records, ["threshold", "slice"],
                                    ["hit", "time_to_proof", "proof_cum_atr", "future_mfe_atr",
                                     "future_plus2", "remaining_bars", "mfe_consumed_fraction",
                                     "mfe_remaining_fraction", "probe_then_full_harvest", "full_harvest",
                                     "harvest_delta_vs_full", "avg_exposure", "underexposed_frac"])
    speed = summarize_equal_market([r for r in records if r["hit"] == 1],
                                   ["threshold", "time_bucket"],
                                   ["future_net_atr", "future_mfe_atr", "future_mae_atr",
                                    "future_plus1", "future_plus2", "future_plus4",
                                    "remaining_bars", "mfe_remaining_fraction"])
    temporal = summarize_equal_market(records, ["era", "threshold"],
                                      ["hit", "probe_then_full_harvest", "full_harvest",
                                       "harvest_delta_vs_full", "avg_exposure"])
    speed_temporal = summarize_equal_market([r for r in records if r["hit"] == 1],
                                            ["era", "threshold", "time_bucket"],
                                            ["future_net_atr", "future_mfe_atr", "future_plus2",
                                             "remaining_bars", "mfe_remaining_fraction"])
    direction = summarize_equal_market(records, ["stage", "threshold"],
                                       ["hit", "probe_then_full_harvest", "full_harvest",
                                        "harvest_delta_vs_full"])

    per_market = []
    for threshold in THRESHOLDS:
        for slice_name in ("failed", "middle", "large"):
            g = [r for r in records if r["threshold"] == threshold and r["slice"] == slice_name]
            for ticker in sorted({r["ticker"] for r in g}):
                mg = [r for r in g if r["ticker"] == ticker]
                if not mg:
                    continue
                per_market.append({
                    "threshold": threshold, "slice": slice_name, "ticker": ticker, "n": len(mg),
                    "hit_rate": mean([r["hit"] for r in mg]),
                    "full_harvest_mean": mean([r["full_harvest"] for r in mg]),
                    "probe_then_full_harvest_mean": mean([r["probe_then_full_harvest"] for r in mg]),
                    "harvest_delta_vs_full_mean": mean([r["harvest_delta_vs_full"] for r in mg]),
                    "avg_exposure_mean": mean([r["avg_exposure"] for r in mg]),
                })

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "issue78-confirmation-tax-universal.csv", universal)
    write_csv(out / "issue78-confirmation-tax-slices.csv", slices)
    write_csv(out / "issue78-confirmation-tax-speed.csv", speed)
    write_csv(out / "issue78-confirmation-tax-temporal.csv", temporal)
    write_csv(out / "issue78-confirmation-tax-speed-temporal.csv", speed_temporal)
    write_csv(out / "issue78-confirmation-tax-direction.csv", direction)
    write_csv(out / "issue78-confirmation-tax-per-market.csv", per_market)

    print("events", len(events), "episodes", len(eps), "records", len(records))
    for threshold in THRESHOLDS:
        g = [r for r in records if r["threshold"] == threshold]
        print("threshold", threshold, "hit_rate", mean([r["hit"] for r in g]))
    print("wrote", out)

if __name__ == "__main__":
    main()
