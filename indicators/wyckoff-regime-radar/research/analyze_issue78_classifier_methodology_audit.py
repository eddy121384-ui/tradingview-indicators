#!/usr/bin/env python3
"""Issue #78 classifier methodology audit.

Diagnoses the frozen six-regime classifier as a classifier, not as a trading
strategy. The OOS3 equity cohort is already outcome-inspected; all forward
behavior here is descriptive methodology evidence only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

import analyze_issue78_bbg_equity_oos2 as base
from audit_issue119_bbg_oos2_snapshot import audit_snapshot
from smoke_issue119_frozen_classifier import (
    FROZEN_CLASSIFIER_BLOB,
    load_classifier,
)

EXPECTED_FIGI_SET_SHA = (
    "017e9360402afa002dc0970088649e7c411c4f02333dec550f2432be3c0dd701"
)
HORIZONS = (1, 5, 10, 20)
MIN_CELL_BARS = 5
MIN_AGG_STOCKS = 30

STAGES = {
    1: "Accumulation",
    2: "Markup",
    3: "Re-accumulation",
    4: "Distribution",
    5: "Markdown",
    6: "Re-distribution",
}
STAGE_KEYS = {
    1: "acc",
    2: "markup",
    3: "reacc",
    4: "dist",
    5: "markdown",
    6: "redist",
}

AGE_BUCKETS = (
    ("age_0_4", 0, 4),
    ("age_5_9", 5, 9),
    ("age_10_19", 10, 19),
    ("age_20_plus", 20, None),
)


def figi_set_sha(universe: pd.DataFrame) -> str:
    figis = sorted(universe["figi"].astype(str).tolist())
    payload = "\n".join(figis) + "\n"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def formal_age(formal_ids) -> np.ndarray:
    ids = np.asarray(formal_ids, dtype=int)
    age = np.zeros(len(ids), dtype=int)
    for i in range(1, len(ids)):
        if ids[i] != 0 and ids[i] == ids[i - 1]:
            age[i] = age[i - 1] + 1
        else:
            age[i] = 0
    return age


def family_scores(probabilities: np.ndarray) -> np.ndarray:
    """Return Up / Transition / Down family probabilities."""
    p = np.asarray(probabilities, dtype=float)
    up = p[:, 1] + p[:, 2]
    transition = p[:, 0] + p[:, 3]
    down = p[:, 4] + p[:, 5]
    return np.column_stack([up, transition, down])


def winner_ids(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Stable top and runner-up ids using left-to-right tie priority."""
    x = np.asarray(values, dtype=float)
    safe = np.where(np.isfinite(x), x, -np.inf)
    order = np.argsort(-safe, axis=1, kind="stable")
    return order[:, 0] + 1, order[:, 1] + 1


def build_frame(raw: pd.DataFrame, classifier) -> pd.DataFrame:
    frame = raw.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    if frame["date"].isna().any():
        raise ValueError("invalid date")
    if frame["date"].duplicated().any():
        raise ValueError("duplicate dates")
    frame = frame.sort_values("date").reset_index(drop=True)

    classified = classifier.compute_price_only(frame)
    if len(classified) != len(frame):
        raise AssertionError("classifier row drift")

    ohlc = frame[["open", "high", "low", "close"]].apply(
        pd.to_numeric, errors="coerce"
    )
    arr = ohlc.to_numpy(float)
    valid_ohlc = np.isfinite(arr).all(axis=1) & (arr > 0).all(axis=1)

    close = pd.to_numeric(frame["close"], errors="coerce").to_numpy(float)
    volume = pd.to_numeric(frame["volume"], errors="coerce").to_numpy(float)
    close_coord = np.where(valid_ohlc, np.log(close), np.nan)

    scale = pd.to_numeric(
        classified["sym_atr"], errors="coerce"
    ).to_numpy(float)

    valid_count_before = np.concatenate(
        [[0], np.cumsum(valid_ohlc.astype(int))[:-1]]
    )
    dollar_volume = close * volume
    finite_dv = np.isfinite(dollar_volume) & (dollar_volume >= 0)
    dv = pd.Series(
        np.where(finite_dv, dollar_volume, np.nan),
        dtype=float,
    )
    liq_count = (
        dv.rolling(
            base.LIQUIDITY_WINDOW,
            min_periods=base.LIQUIDITY_WINDOW,
        )
        .count()
        .to_numpy()
    )
    liq_median = (
        dv.rolling(
            base.LIQUIDITY_WINDOW,
            min_periods=base.LIQUIDITY_WINDOW,
        )
        .median()
        .to_numpy()
    )

    eligible = (
        valid_ohlc
        & frame["date"].between(base.EVENT_START, base.EVENT_END).to_numpy()
        & (valid_count_before >= base.MIN_PRIOR_VALID)
        & np.isfinite(close)
        & (close >= base.MIN_PRICE)
        & (liq_count >= base.LIQUIDITY_WINDOW)
        & np.isfinite(liq_median)
        & (liq_median >= base.MIN_MEDIAN_DOLLAR_VOLUME)
        & np.isfinite(scale)
        & (scale > 0)
    )

    out = pd.DataFrame(
        {
            "date": frame["date"],
            "eligible": eligible,
            "close_coord": close_coord,
            "scale": scale,
        }
    )

    raw_cols = []
    prob_cols = []
    for sid, key in STAGE_KEYS.items():
        raw_name = f"raw_{key}"
        prob_name = f"prob_{key}"
        out[raw_name] = pd.to_numeric(
            classified[f"{key}_raw"], errors="coerce"
        )
        out[prob_name] = pd.to_numeric(
            classified[f"prob_{key}"], errors="coerce"
        )
        raw_cols.append(raw_name)
        prob_cols.append(prob_name)

    raw_matrix = out[raw_cols].to_numpy(float)
    prob_matrix = out[prob_cols].to_numpy(float)
    ready = (
        eligible
        & np.isfinite(raw_matrix).all(axis=1)
        & np.isfinite(prob_matrix).all(axis=1)
    )
    out["ready"] = ready

    raw_top, raw_second = winner_ids(raw_matrix)
    out["raw_winner_id"] = raw_top
    out["raw_runnerup_id"] = raw_second

    out["effective_winner_id"] = (
        pd.to_numeric(classified["top_id"], errors="coerce")
        .fillna(0)
        .astype(int)
    )
    out["top_gap"] = pd.to_numeric(
        classified["top_gap"], errors="coerce"
    )
    out["strong_candidate"] = classified["strong_candidate"].astype(bool)
    out["weak_candidate"] = classified["weak_candidate"].astype(bool)
    out["chaos"] = classified["chaos"].astype(bool)
    out["coexist"] = classified["coexist"].astype(bool)
    out["candidate_conflict"] = classified["candidate_conflict"].astype(bool)
    out["formal_id"] = (
        pd.to_numeric(classified["formal_id"], errors="coerce")
        .fillna(0)
        .astype(int)
    )
    out["formal_age"] = formal_age(out["formal_id"].to_numpy(int))

    fam = family_scores(prob_matrix)
    out["family_up"] = fam[:, 0]
    out["family_transition"] = fam[:, 1]
    out["family_down"] = fam[:, 2]
    fam_top, _ = winner_ids(fam)
    # winner_ids returns 1/2/3 corresponding Up/Transition/Down.
    out["family_winner_id"] = fam_top

    for h in HORIZONS:
        future = pd.Series(close_coord).shift(-h).to_numpy(float)
        out[f"fwd_{h}"] = (future - close_coord) / scale

    return out


def _stats(values: np.ndarray) -> dict:
    vals = np.asarray(values, dtype=float)
    vals = vals[np.isfinite(vals)]
    if len(vals) == 0:
        return {
            "bars": 0,
            "mean": math.nan,
            "median": math.nan,
            "positive_fraction": math.nan,
            "mean_abs": math.nan,
        }
    return {
        "bars": int(len(vals)),
        "mean": float(np.mean(vals)),
        "median": float(np.median(vals)),
        "positive_fraction": float(np.mean(vals > 0)),
        "mean_abs": float(np.mean(np.abs(vals))),
    }


def _append_cell(
    rows,
    *,
    figi,
    horizon,
    mask,
    forward,
    direction=1.0,
    extra=None,
):
    vals = np.asarray(forward, dtype=float)[np.asarray(mask, dtype=bool)]
    vals = vals[np.isfinite(vals)] * float(direction)
    if len(vals) < MIN_CELL_BARS:
        return
    stat = _stats(vals)
    rows.append(
        {
            "figi": figi,
            "horizon": int(horizon),
            **(extra or {}),
            "bars": stat["bars"],
            "mean_move": stat["mean"],
            "median_move": stat["median"],
            "positive_fraction": stat["positive_fraction"],
            "mean_abs_move": stat["mean_abs"],
        }
    )


def aggregate_stock_cells(stock: pd.DataFrame, group_cols) -> pd.DataFrame:
    rows = []
    if stock.empty:
        return pd.DataFrame()
    for keys, group in stock.groupby(group_cols):
        if not isinstance(keys, tuple):
            keys = (keys,)
        vals = group["mean_move"].to_numpy(float)
        med = group["median_move"].to_numpy(float)
        hits = group["positive_fraction"].to_numpy(float)
        absvals = group["mean_abs_move"].to_numpy(float)
        rows.append(
            {
                **dict(zip(group_cols, keys)),
                "stocks": int(group["figi"].nunique()),
                "bars": int(group["bars"].sum()),
                "adequate": int(group["figi"].nunique() >= MIN_AGG_STOCKS),
                "equal_stock_mean_move": float(np.mean(vals)),
                "median_stock_median_move": float(np.median(med)),
                "equal_stock_positive_fraction": float(np.mean(hits)),
                "equal_stock_mean_abs_move": float(np.mean(absvals)),
            }
        )
    return pd.DataFrame(rows)


def stage_funnel(frames) -> pd.DataFrame:
    totals = {
        sid: {
            "raw_winner": 0,
            "effective_winner": 0,
            "strong_candidate": 0,
            "formal_label": 0,
        }
        for sid in STAGES
    }
    ready_total = 0
    no_clear_formal = 0

    for frame in frames.values():
        f = frame[frame["ready"]]
        ready_total += len(f)
        no_clear_formal += int((f["formal_id"] == 0).sum())
        for sid in STAGES:
            totals[sid]["raw_winner"] += int(
                (f["raw_winner_id"] == sid).sum()
            )
            totals[sid]["effective_winner"] += int(
                (f["effective_winner_id"] == sid).sum()
            )
            totals[sid]["strong_candidate"] += int(
                (
                    (f["effective_winner_id"] == sid)
                    & f["strong_candidate"]
                ).sum()
            )
            totals[sid]["formal_label"] += int(
                (f["formal_id"] == sid).sum()
            )

    rows = []
    for sid, name in STAGES.items():
        row = {"stage": name, "ready_bars": ready_total}
        for key, value in totals[sid].items():
            row[f"{key}_bars"] = value
            row[f"{key}_share"] = (
                value / ready_total if ready_total else math.nan
            )
        rows.append(row)

    rows.append(
        {
            "stage": "No clear regime",
            "ready_bars": ready_total,
            "raw_winner_bars": 0,
            "raw_winner_share": 0.0,
            "effective_winner_bars": 0,
            "effective_winner_share": 0.0,
            "strong_candidate_bars": 0,
            "strong_candidate_share": 0.0,
            "formal_label_bars": no_clear_formal,
            "formal_label_share": (
                no_clear_formal / ready_total if ready_total else math.nan
            ),
        }
    )
    return pd.DataFrame(rows)


def raw_correlations(frames) -> tuple[pd.DataFrame, pd.DataFrame]:
    per_stock = []
    raw_names = [f"raw_{STAGE_KEYS[sid]}" for sid in STAGES]
    for figi, frame in frames.items():
        f = frame.loc[frame["ready"], raw_names]
        if len(f) < 100:
            continue
        corr = f.corr(method="spearman")
        for a, b in combinations(raw_names, 2):
            value = corr.loc[a, b]
            if math.isfinite(float(value)):
                per_stock.append(
                    {
                        "figi": figi,
                        "stage_a": a.removeprefix("raw_"),
                        "stage_b": b.removeprefix("raw_"),
                        "spearman": float(value),
                        "bars": int(len(f)),
                    }
                )

    ps = pd.DataFrame(per_stock)
    if ps.empty:
        return ps, pd.DataFrame()

    rows = []
    for (a, b), g in ps.groupby(["stage_a", "stage_b"]):
        rows.append(
            {
                "stage_a": a,
                "stage_b": b,
                "stocks": int(g["figi"].nunique()),
                "equal_stock_mean_spearman": float(g["spearman"].mean()),
                "median_stock_spearman": float(g["spearman"].median()),
            }
        )
    return ps, pd.DataFrame(rows)


def raw_top_pairs(frames) -> pd.DataFrame:
    counts = {}
    total = 0
    for frame in frames.values():
        f = frame[frame["ready"]]
        total += len(f)
        pairs = zip(f["raw_winner_id"], f["raw_runnerup_id"])
        for a, b in pairs:
            key = (int(a), int(b))
            counts[key] = counts.get(key, 0) + 1
    rows = [
        {
            "winner": STAGES[a],
            "runner_up": STAGES[b],
            "bars": n,
            "share": n / total if total else math.nan,
        }
        for (a, b), n in sorted(
            counts.items(), key=lambda item: item[1], reverse=True
        )
    ]
    return pd.DataFrame(rows)


def directional_layer_cells(figi, frame):
    rows = []
    ready = frame["ready"].to_numpy(bool)

    for sid in (2, 5):
        key = STAGE_KEYS[sid]
        direction = 1.0 if sid == 2 else -1.0

        raw_score = frame[f"raw_{key}"].where(frame["ready"])
        raw_rank = raw_score.rank(method="average", pct=True)
        prob_score = frame[f"prob_{key}"].where(frame["ready"])
        prob_rank = prob_score.rank(method="average", pct=True)

        layers = {
            "raw_top_quintile": ready
            & (raw_rank.to_numpy(float) >= 0.80),
            "probability_top_quintile": ready
            & (prob_rank.to_numpy(float) >= 0.80),
            "effective_winner": ready
            & (frame["effective_winner_id"].to_numpy(int) == sid),
            "strong_candidate": ready
            & (frame["effective_winner_id"].to_numpy(int) == sid)
            & frame["strong_candidate"].to_numpy(bool),
            "formal_label": ready
            & (frame["formal_id"].to_numpy(int) == sid),
            "formal_age_ge10": ready
            & (frame["formal_id"].to_numpy(int) == sid)
            & (frame["formal_age"].to_numpy(int) >= 10),
        }

        for h in HORIZONS:
            fwd = frame[f"fwd_{h}"].to_numpy(float)
            for layer, mask in layers.items():
                _append_cell(
                    rows,
                    figi=figi,
                    horizon=h,
                    mask=mask,
                    forward=fwd,
                    direction=direction,
                    extra={
                        "stage": STAGES[sid],
                        "layer": layer,
                    },
                )
    return rows


def formal_stage_cells(figi, frame):
    rows = []
    ready = frame["ready"].to_numpy(bool)
    formal = frame["formal_id"].to_numpy(int)
    age = frame["formal_age"].to_numpy(int)

    for sid, stage in STAGES.items():
        mask = ready & (formal == sid)
        for h in HORIZONS:
            _append_cell(
                rows,
                figi=figi,
                horizon=h,
                mask=mask,
                forward=frame[f"fwd_{h}"].to_numpy(float),
                direction=1.0,
                extra={"stage": stage},
            )

        for label, lo, hi in AGE_BUCKETS:
            age_mask = mask & (age >= lo)
            if hi is not None:
                age_mask &= age <= hi
            for h in HORIZONS:
                _append_cell(
                    rows,
                    figi=figi,
                    horizon=h,
                    mask=age_mask,
                    forward=frame[f"fwd_{h}"].to_numpy(float),
                    direction=1.0,
                    extra={
                        "stage": stage,
                        "age_bucket": label,
                    },
                )
    return rows


def family_cells(figi, frame):
    rows = []
    ready = frame["ready"].to_numpy(bool)
    winner = frame["family_winner_id"].to_numpy(int)
    mapping = {
        1: ("Up", 1.0),
        2: ("Transition", 1.0),
        3: ("Down", -1.0),
    }
    for fam_id, (name, direction) in mapping.items():
        mask = ready & (winner == fam_id)
        for h in HORIZONS:
            _append_cell(
                rows,
                figi=figi,
                horizon=h,
                mask=mask,
                forward=frame[f"fwd_{h}"].to_numpy(float),
                direction=direction,
                extra={"family": name},
            )
    return rows


def inertia_state(frame: pd.DataFrame) -> np.ndarray:
    formal = frame["formal_id"].to_numpy(int)
    top = frame["effective_winner_id"].to_numpy(int)
    strong = frame["strong_candidate"].to_numpy(bool)
    weak = frame["weak_candidate"].to_numpy(bool)
    coexist = frame["coexist"].to_numpy(bool)
    chaos = frame["chaos"].to_numpy(bool)

    out = np.full(len(frame), "stale_or_other", dtype=object)
    same = top == formal
    out[same & strong] = "strong_same_stage"
    out[same & weak] = "weak_same_stage"
    out[(~same) & strong] = "strong_challenger"
    out[(~same) & weak] = "weak_challenger"
    out[coexist & ~(same & (strong | weak))] = "coexistence"
    out[chaos] = "chaos"
    return out


def inertia_cells(figi, frame):
    rows = []
    ready = frame["ready"].to_numpy(bool)
    formal = frame["formal_id"].to_numpy(int)
    state = inertia_state(frame)
    agree = frame["effective_winner_id"].to_numpy(int) == formal

    for sid in (2, 5):
        direction = 1.0 if sid == 2 else -1.0
        base_mask = ready & (formal == sid)
        for h in HORIZONS:
            fwd = frame[f"fwd_{h}"].to_numpy(float)
            for flag, label in ((True, "agree"), (False, "disagree")):
                _append_cell(
                    rows,
                    figi=figi,
                    horizon=h,
                    mask=base_mask & (agree == flag),
                    forward=fwd,
                    direction=direction,
                    extra={
                        "stage": STAGES[sid],
                        "inertia_view": "effective_agreement",
                        "state": label,
                    },
                )
            for label in (
                "strong_same_stage",
                "weak_same_stage",
                "strong_challenger",
                "weak_challenger",
                "coexistence",
                "chaos",
                "stale_or_other",
            ):
                _append_cell(
                    rows,
                    figi=figi,
                    horizon=h,
                    mask=base_mask & (state == label),
                    forward=fwd,
                    direction=direction,
                    extra={
                        "stage": STAGES[sid],
                        "inertia_view": "state",
                        "state": label,
                    },
                )
    return rows


def write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--raw-dir", type=Path, required=True)
    ap.add_argument(
        "--classifier",
        type=Path,
        default=Path("generated/wyckoff-issue78-rc-python.py"),
    )
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    audit = audit_snapshot(
        args.universe, args.manifest, args.raw_dir
    )
    if not audit["pass"]:
        raise SystemExit("snapshot audit failed")

    universe = pd.read_csv(args.universe)
    if len(universe) != 300 or universe["figi"].nunique() != 300:
        raise AssertionError("universe membership drift")
    cohort_sha = figi_set_sha(universe)
    if cohort_sha != EXPECTED_FIGI_SET_SHA:
        raise AssertionError(f"OOS3 FIGI-set drift: {cohort_sha}")

    classifier, blob = load_classifier(args.classifier)
    if blob != FROZEN_CLASSIFIER_BLOB:
        raise AssertionError("frozen classifier blob drift")

    frames = {}
    coverage = []
    layer_rows = []
    formal_rows = []
    age_rows = []
    family_rows = []
    inertia_rows = []

    for i, meta in enumerate(universe.itertuples(index=False), start=1):
        figi = str(meta.figi)
        raw_path = args.raw_dir / f"{figi}.csv.gz"
        if not raw_path.exists():
            raise FileNotFoundError(raw_path)
        raw = pd.read_csv(raw_path)
        frame = build_frame(raw, classifier)
        frames[figi] = frame

        coverage.append(
            {
                "figi": figi,
                "ticker": str(meta.ticker),
                "sector": str(meta.sector),
                "sleeve": str(meta.sleeve),
                "raw_rows": int(len(frame)),
                "eligible_rows": int(frame["eligible"].sum()),
                "classifier_ready_rows": int(frame["ready"].sum()),
            }
        )

        layer_rows.extend(directional_layer_cells(figi, frame))

        formal_all = formal_stage_cells(figi, frame)
        for row in formal_all:
            if "age_bucket" in row:
                age_rows.append(row)
            else:
                formal_rows.append(row)

        family_rows.extend(family_cells(figi, frame))
        inertia_rows.extend(inertia_cells(figi, frame))

        print(
            f"[methodology] {i}/{len(universe)} {meta.ticker} "
            f"eligible={int(frame['eligible'].sum())} "
            f"ready={int(frame['ready'].sum())}",
            flush=True,
        )

    funnel = stage_funnel(frames)
    corr_stock, corr_summary = raw_correlations(frames)
    pairs = raw_top_pairs(frames)

    layer_stock = pd.DataFrame(layer_rows)
    layer_summary = aggregate_stock_cells(
        layer_stock, ["stage", "layer", "horizon"]
    )

    formal_stock = pd.DataFrame(formal_rows)
    formal_summary = aggregate_stock_cells(
        formal_stock, ["stage", "horizon"]
    )

    age_stock = pd.DataFrame(age_rows)
    age_summary = aggregate_stock_cells(
        age_stock, ["stage", "age_bucket", "horizon"]
    )

    family_stock = pd.DataFrame(family_rows)
    family_summary = aggregate_stock_cells(
        family_stock, ["family", "horizon"]
    )

    inertia_stock = pd.DataFrame(inertia_rows)
    inertia_summary = aggregate_stock_cells(
        inertia_stock,
        ["stage", "inertia_view", "state", "horizon"],
    )

    # Compact headline tables for first inspection.
    layer10 = layer_summary[layer_summary["horizon"] == 10].to_dict("records")
    formal10 = formal_summary[formal_summary["horizon"] == 10].to_dict("records")
    family10 = family_summary[family_summary["horizon"] == 10].to_dict("records")

    summary = {
        "integrity": {
            "issue": 78,
            "study": "Classifier Methodology Audit",
            "role": "post-outcome classifier diagnostic; not policy OOS",
            "classifier_blob": blob,
            "figi_set_sha256": cohort_sha,
            "stocks": int(len(universe)),
            "raw_files": int(audit["completed"]),
            "raw_failures": int(audit["failures"]),
            "horizons": list(HORIZONS),
            "min_cell_bars": MIN_CELL_BARS,
            "min_aggregate_stocks": MIN_AGG_STOCKS,
        },
        "stage_funnel": funnel.to_dict("records"),
        "directional_layers_10bar": layer10,
        "formal_labels_10bar": formal10,
        "three_family_10bar": family10,
        "notes": [
            "All forward behavior is descriptive because OOS3 outcomes were already inspected.",
            "No classifier threshold, weight, stage definition, confirmation rule or persistence rule is changed.",
            "Continuous raw evidence, relative competition and formal state are evaluated as separate transformations.",
            "Re-accumulation / Re-distribution scarcity is localized across raw winner, effective winner, strong candidate and formal-label layers.",
        ],
    }

    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "coverage.csv", pd.DataFrame(coverage))
    write_csv(args.out / "stage_funnel.csv", funnel)
    write_csv(args.out / "raw_score_correlation_per_stock.csv", corr_stock)
    write_csv(args.out / "raw_score_correlation_summary.csv", corr_summary)
    write_csv(args.out / "raw_top_pairs.csv", pairs)
    write_csv(args.out / "directional_layer_per_stock.csv", layer_stock)
    write_csv(args.out / "directional_layer_summary.csv", layer_summary)
    write_csv(args.out / "formal_stage_per_stock.csv", formal_stock)
    write_csv(args.out / "formal_stage_summary.csv", formal_summary)
    write_csv(args.out / "formal_age_per_stock.csv", age_stock)
    write_csv(args.out / "formal_age_summary.csv", age_summary)
    write_csv(args.out / "family_per_stock.csv", family_stock)
    write_csv(args.out / "family_summary.csv", family_summary)
    write_csv(args.out / "inertia_per_stock.csv", inertia_stock)
    write_csv(args.out / "inertia_summary.csv", inertia_summary)

    (args.out / "summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
