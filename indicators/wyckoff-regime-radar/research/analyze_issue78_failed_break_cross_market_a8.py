#!/usr/bin/env python3
"""Issue #78 A8: cross-market failed-break symmetry transport (FX + rates).

Transport / replication study, NOT fresh final validation. Reuses the
frozen A7 F0 event definition and A6 raw-break control EXACTLY (same
functions by import — no parameter, window, or threshold changes).

Per instrument: OHLC + frozen-classifier `sym_atr` (same code path as A7;
NaN volume where the source has none) give ATR-normalized outcomes
`fwd = (log close[t+h] − log close[t]) / sym_atr[t]`. The ONLY adaptation
vs A7, frozen in prereg: no equity liquidity/dollar-volume eligibility
gate (FX/rates have no volume); eligibility = valid OHLC + finite
positive sym_atr. Quote/yield series are NEVER inverted.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

import analyze_issue78_direction_decomposition_a1 as a1
import analyze_issue78_failed_break_a7 as a7
import analyze_issue78_trigger_layer_a6 as a6
from smoke_issue119_frozen_classifier import FROZEN_CLASSIFIER_BLOB, load_classifier

HORIZONS = (1, 5, 10, 20)
MIN_CELL_EVENTS = 5
MIN_FAMILY_INSTRUMENTS = 3


def _tail_stats(vals: np.ndarray) -> dict:
    return a1._tail_stats(np.asarray(vals, dtype=float))


def load_ohlc(path: Path | str) -> pd.DataFrame:
    """Read an instrument file; enforce clean OHLC field consistency."""
    path = Path(path)
    frame = pd.read_csv(path)
    cols = {str(c).strip().lower(): str(c) for c in frame.columns}
    for need in ("date", "open", "high", "low", "close"):
        if need not in cols:
            raise ValueError(f"{path.name}: missing required field {need}")
    out = pd.DataFrame(
        {
            "date": pd.to_datetime(frame[cols["date"]], errors="coerce"),
            "open": pd.to_numeric(frame[cols["open"]], errors="coerce"),
            "high": pd.to_numeric(frame[cols["high"]], errors="coerce"),
            "low": pd.to_numeric(frame[cols["low"]], errors="coerce"),
            "close": pd.to_numeric(frame[cols["close"]], errors="coerce"),
        }
    )
    if out["date"].isna().any():
        raise ValueError(f"{path.name}: invalid dates")
    out = out.sort_values("date").reset_index(drop=True)
    if out["date"].duplicated().any():
        raise ValueError(f"{path.name}: duplicate dates")
    return out


def build_instrument_frame(raw: pd.DataFrame, classifier) -> pd.DataFrame:
    """OHLC + frozen sym_atr + ATR-normalized forwards (no volume gate)."""
    frame = raw.copy()
    ohlc = frame[["open", "high", "low", "close"]].to_numpy(float)
    valid = np.isfinite(ohlc).all(axis=1) & (ohlc > 0).all(axis=1)
    work = frame.assign(volume=np.nan)
    classified = classifier.compute_price_only(work)
    if len(classified) != len(frame):
        raise AssertionError("classifier row drift")
    scale = pd.to_numeric(
        classified["sym_atr"], errors="coerce"
    ).to_numpy(float)
    close = frame["close"].to_numpy(float)
    close_coord = np.where(valid, np.log(close), np.nan)
    eligible = valid & np.isfinite(scale) & (scale > 0)
    out = pd.DataFrame(
        {
            "date": frame["date"],
            "eligible": eligible,
            "close_coord": close_coord,
            "scale": scale,
            "high": frame["high"].to_numpy(float),
            "low": frame["low"].to_numpy(float),
            "close": close,
            # Stand-ins: A8 never conditions on Core-2; NaN ranks keep
            # reused detectors' struct fields inert without redefinition.
            "rank_c_struct": np.full(len(frame), np.nan),
            "rank_c_ext": np.full(len(frame), np.nan),
            "rank_dir_structure": np.full(len(frame), np.nan),
            "rank_extension": np.full(len(frame), np.nan),
            "causal_ready": eligible,
            "ready": eligible,
            "block": "",
        }
    )
    year = frame["date"].dt.year.to_numpy(int)
    block = np.full(len(frame), "", dtype=object)
    for name, lo, hi in a1.BLOCKS:
        block[(year >= lo) & (year <= hi)] = name
    out["block"] = block
    levels = a6.structural_levels(out)
    out["prior_high_20"] = levels["prior_high_20"].to_numpy(float)
    out["prior_low_20"] = levels["prior_low_20"].to_numpy(float)
    for h in HORIZONS:
        future = pd.Series(close_coord).shift(-h).to_numpy(float)
        out[f"fwd_{h}"] = (future - close_coord) / scale
    return out


def instrument_events(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Frozen F0 + raw-T0 + non-reclaimed event tables (mutually exclusive)."""
    f0, non = a7.detect_failed_breaks(frame)
    trig = a6.detect_triggers(frame)
    raw = trig[trig["family"] == "T0"].copy()
    return f0, non, raw


def event_values(
    frame: pd.DataFrame, events: pd.DataFrame, sign_col: str = None
) -> dict:
    """Aligned outcome vectors per horizon for an event table."""
    out = {}
    for h in HORIZONS:
        fwd = frame[f"fwd_{h}"].to_numpy(float)
        per_side = {}
        for side, sign in (("bull", 1.0), ("bear", -1.0)):
            sub = events[events["side"] == side]
            if sub.empty:
                per_side[side] = np.array([], dtype=float)
                continue
            eidx = sub["e_primary"].to_numpy(int)
            ok = (eidx >= 0) & (eidx < len(frame))
            per_side[side] = fwd[eidx[ok]] * sign
        out[h] = per_side
    return out


def summarize(values: np.ndarray) -> dict:
    return _tail_stats(values)


def write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instruments", type=Path, required=True)
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument(
        "--classifier",
        type=Path,
        default=Path("generated/wyckoff-issue78-rc-python.py"),
    )
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    manifest = json.loads(args.instruments.read_text(encoding="utf-8"))
    classifier, blob = load_classifier(args.classifier)
    if blob != FROZEN_CLASSIFIER_BLOB:
        raise AssertionError("frozen classifier blob drift")

    inst_rows = []
    per_inst_rows = []
    for entry in manifest["instruments"]:
        name = entry["name"]
        path = args.data_dir / entry["file"]
        if not path.exists():
            raise FileNotFoundError(path)
        raw = load_ohlc(path)
        frame = build_instrument_frame(raw, classifier)
        f0, non, rawt = instrument_events(frame)
        inst_rows.append(
            {
                "family": entry["family"],
                "instrument": name,
                "source": entry.get("source", ""),
                "bars": int(len(frame)),
                "eligible_bars": int(frame["eligible"].sum()),
                "first_date": str(frame["date"].iloc[0].date()),
                "last_date": str(frame["date"].iloc[-1].date()),
                "f0_bull_events": int((f0["side"] == "bull").sum()),
                "f0_bear_events": int((f0["side"] == "bear").sum()),
                "raw_bull_events": int(
                    ((rawt["side"] == "bull") & (rawt["family"] == "T0")).sum()
                ),
                "raw_bear_events": int(
                    ((rawt["side"] == "bear") & (rawt["family"] == "T0")).sum()
                ),
                "nonreclaim_events": int(len(non)),
            }
        )
        for h in HORIZONS:
            fwd = frame[f"fwd_{h}"].to_numpy(float)
            for side in ("bull", "bear"):
                for label, evtab in (
                    ("failed", f0),
                    ("raw", rawt),
                    ("nonreclaimed", non),
                ):
                    sub = evtab[evtab["side"] == side]
                    if sub.empty:
                        continue
                    eidx = sub["e_primary"].to_numpy(int)
                    ok = (eidx >= 0) & (eidx < len(frame))
                    if not ok.any():
                        continue
                    vals = fwd[eidx[ok]] * (1.0 if side == "bull" else -1.0)
                    eblk = frame["block"].to_numpy()[eidx[ok]]
                    blocks = {"ALL": np.ones(ok.sum(), dtype=bool)}
                    for name, _, _ in a1.BLOCKS:
                        blocks[name] = eblk == name
                    for block, bmask in blocks.items():
                        st = _tail_stats(vals[bmask])
                        per_inst_rows.append(
                            {
                                "family": entry["family"],
                                "instrument": name,
                                "block": block,
                                "horizon": h,
                                "side": side,
                                "kind": label,
                                **st,
                            }
                        )
        print(
            f"[failed-break-a8] {entry['family']}/{name} "
            f"bars={len(frame)} f0={len(f0)}",
            flush=True,
        )

    per_inst = pd.DataFrame(per_inst_rows)
    # One-instrument-one-vote family aggregates (never event-pooled).
    fam_rows = []
    for (family, block, horizon, side, kind), group in per_inst.groupby(
        ["family", "block", "horizon", "side", "kind"], sort=True
    ):
        means = pd.to_numeric(group["mean"], errors="coerce")
        meds = pd.to_numeric(group["median"], errors="coerce")
        hits = pd.to_numeric(group["positive_fraction"], errors="coerce")
        valid = np.isfinite(means.to_numpy(float))
        n = int(valid.sum())
        fam_rows.append(
            {
                "family": family,
                "block": block,
                "horizon": int(horizon),
                "side": side,
                "kind": kind,
                "instruments": n,
                "adequate": int(n >= MIN_FAMILY_INSTRUMENTS),
                "equal_instrument_mean": (
                    float(means[valid].mean()) if n else math.nan
                ),
                "median_instrument_median": (
                    float(meds[np.isfinite(meds)].median())
                    if np.isfinite(meds).any()
                    else math.nan
                ),
                "equal_instrument_positive_fraction": (
                    float(hits[np.isfinite(hits)].mean())
                    if np.isfinite(hits).any()
                    else math.nan
                ),
            }
        )
    fam = pd.DataFrame(fam_rows)

    summary = {
        "integrity": {
            "issue": 78,
            "study": "Failed-Break Cross-Market Symmetry A8",
            "role": "transport replication; not fresh final validation",
            "classifier_blob": blob,
            "horizons": list(HORIZONS),
            "min_cell_events": MIN_CELL_EVENTS,
            "min_family_instruments": MIN_FAMILY_INSTRUMENTS,
            "oos4_touched": False,
            "oos5_touched": False,
        },
        "frozen_design": {
            "event": "A7 F0 verbatim (levels, 3-bar window, timing, dedup)",
            "controls": "A6 raw T0 + non-reclaimed, mutually exclusive",
            "normalization": "frozen sym_atr; no volume gate (preregistered)",
        },
        "notes": [
            "Quote/yield series used exactly as stored; never inverted.",
            "Family aggregates are one-instrument-one-vote, never pooled.",
        ],
    }

    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "instruments.csv", pd.DataFrame(inst_rows))
    write_csv(args.out / "per_instrument.csv", per_inst)
    write_csv(args.out / "family_summary.csv", fam)
    (args.out / "summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
