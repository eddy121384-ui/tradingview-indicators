#!/usr/bin/env python3
"""Issue #109 Phase A1 — state-only pairwise Action Layer validation.

Uses only hash-frozen repository inputs. No live data access.
No trajectory features are loaded in A1.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from issue_64_outcome_snapshot import load_frozen_prices
from asset_allocation_phase_a import REGIMES

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
DECISIONS = HERE / "decisions"

TRANSITIONS = DATA / "issue-64-frozen-regime-transitions.csv"
NEW_PRICES = DATA / "issue-109-shv-gsg-adjusted-prices.csv"
CPI = DATA / "issue-109-cpi-u-nsa-monthly.csv"
SOURCE_CONTRACT = DECISIONS / "issue-109-phase-a0-source-contract.json"
SOURCE_FREEZE = DECISIONS / "issue-109-phase-a0-source-freeze-manifest.json"

EXPECTED_TRANSITION_SHA = "80446bbcb91be8b18eb0b95e62466edf892e4c04087696a04532f0fe214698af"
EXPECTED_NEW_PRICE_SHA = "7dbfe3cff58be172098aa09b9c86fd70a23672834f5829e4b650c94cf72d6833"
EXPECTED_CPI_SHA = "4afea21e4914a848a16fa9c77e51099534ce876aedb01dbbd77d95802531fc93"
EXPECTED_OLD_PRICE_SHA = "3a7f590c146f9eda5920b6968fe86c9c3cc1887db35597f2d639a1c76b6e5a57"

HORIZONS = {"1M": 21, "3M": 63, "6M": 126}
PRIMARY_HORIZON = "3M"
PRIMARY_ROWS = 63
BOOTSTRAP_REPS = 10_000
SIGNAL_CUTOFF = pd.Timestamp("2026-08-14")

LEG_SPECS = {
    "equity_vs_duration": ("SPY", "TLT"),
    "duration_vs_cash": ("TLT", "SHV"),
    "gold_vs_cash": ("GLD", "SHV"),
    "commodities_vs_cash": ("GSG", "SHV"),
}

ALLOWED_STATE_CLASSIFICATIONS = {
    "stable_directional_candidate",
    "era_dependent_candidate",
    "no_clear_state_edge",
    "inconclusive_insufficient_sample",
}
ALLOWED_LEG_SUMMARIES = {
    "stable_directional_relationship",
    "useful_but_era_dependent",
    "no_material_pairwise_information",
    "inconclusive_insufficient_sample",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_seed(*parts: object) -> int:
    payload = "|".join(str(x) for x in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") & 0xFFFFFFFF


def sign(x: float) -> int:
    if not np.isfinite(x) or x == 0.0:
        return 0
    return 1 if x > 0 else -1


def segment_for_date(ts: pd.Timestamp) -> str:
    if ts < pd.Timestamp("2020-01-01"):
        return "pre_2020"
    if ts <= pd.Timestamp("2022-12-31"):
        return "covid_inflation_2020_2022"
    return "post_2023"


def sample_label(n: int) -> str:
    if n < 3:
        return "insufficient_sample"
    if n < 10:
        return "sparse"
    return "regular"


def bootstrap_mean_ci(values: np.ndarray, *, seed: int, reps: int = BOOTSTRAP_REPS) -> tuple[float, float]:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return (math.nan, math.nan)
    if arr.size == 1:
        x = float(arr[0])
        return (x, x)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, arr.size, size=(reps, arr.size))
    means = arr[idx].mean(axis=1)
    lo, hi = np.quantile(means, [0.025, 0.975])
    return float(lo), float(hi)


def summarize(values: Iterable[float], *, seed: int) -> dict:
    arr = np.asarray(list(values), dtype=float)
    arr = arr[np.isfinite(arr)]
    n = int(arr.size)
    if n == 0:
        return {
            "n": 0,
            "sample_label": sample_label(0),
            "mean": math.nan,
            "median": math.nan,
            "std": math.nan,
            "positive_fraction": math.nan,
            "ci_low": math.nan,
            "ci_high": math.nan,
        }
    lo, hi = bootstrap_mean_ci(arr, seed=seed)
    return {
        "n": n,
        "sample_label": sample_label(n),
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "std": float(np.std(arr, ddof=1)) if n >= 2 else math.nan,
        "positive_fraction": float(np.mean(arr > 0.0)),
        "ci_low": lo,
        "ci_high": hi,
    }


def load_and_validate_sources() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    contract = json.loads(SOURCE_CONTRACT.read_text(encoding="utf-8"))
    freeze = json.loads(SOURCE_FREEZE.read_text(encoding="utf-8"))
    if contract["a1_authorized"] is not True:
        raise RuntimeError("Issue #109 A1 is not authorized by the frozen source contract")
    if contract["a2_trajectory_authorized"] is not False:
        raise RuntimeError("A1 must not open trajectory")

    if sha256_file(TRANSITIONS) != EXPECTED_TRANSITION_SHA:
        raise RuntimeError("Issue #64 transition hash mismatch")
    if sha256_file(NEW_PRICES) != EXPECTED_NEW_PRICE_SHA:
        raise RuntimeError("Issue #109 SHV/GSG snapshot hash mismatch")
    if sha256_file(CPI) != EXPECTED_CPI_SHA:
        raise RuntimeError("Issue #109 CPI snapshot hash mismatch")
    if freeze["prices"]["csv_sha256"] != EXPECTED_NEW_PRICE_SHA:
        raise RuntimeError("durable source-freeze manifest disagrees on SHV/GSG hash")
    if freeze["cpi"]["csv_sha256"] != EXPECTED_CPI_SHA:
        raise RuntimeError("durable source-freeze manifest disagrees on CPI hash")

    old_prices, old_meta = load_frozen_prices("2007-01-01", None)
    if old_meta["snapshot_csv_sha256"] != EXPECTED_OLD_PRICE_SHA:
        raise RuntimeError("Issue #64 frozen SPY/TLT/GLD snapshot hash mismatch")

    new_prices = pd.read_csv(NEW_PRICES)
    new_prices["date"] = pd.to_datetime(new_prices["date"], errors="raise")
    new_prices = new_prices.set_index("date").sort_index()
    new_prices = new_prices[["SHV", "GSG"]].apply(pd.to_numeric, errors="raise").astype(float)

    transitions = pd.read_csv(TRANSITIONS)
    transitions["start_date"] = pd.to_datetime(transitions["start_date"], errors="raise")
    transitions["regime_id"] = pd.to_numeric(transitions["regime_id"], errors="raise").astype(int)
    transitions = transitions.sort_values("start_date").reset_index(drop=True)
    if transitions["regime_id"].min() < 1 or transitions["regime_id"].max() > 9:
        raise RuntimeError("invalid regime id in frozen transition history")

    cpi = pd.read_csv(CPI)
    cpi["date"] = pd.to_datetime(cpi["date"], errors="raise")
    cpi["CPI_U_NSA"] = pd.to_numeric(cpi["CPI_U_NSA"], errors="raise").astype(float)
    cpi = cpi.drop_duplicates("date", keep="last").sort_values("date").set_index("date")

    provenance = {
        "old_prices": old_meta,
        "new_price_sha256": EXPECTED_NEW_PRICE_SHA,
        "cpi_sha256": EXPECTED_CPI_SHA,
        "transition_sha256": EXPECTED_TRANSITION_SHA,
    }
    return old_prices, new_prices, transitions, cpi, provenance


def state_on_date(transitions: pd.DataFrame, date: pd.Timestamp) -> tuple[int, str] | None:
    if date > SIGNAL_CUTOFF:
        return None
    starts = transitions["start_date"].to_numpy(dtype="datetime64[ns]")
    pos = int(np.searchsorted(starts, np.datetime64(date), side="right") - 1)
    if pos < 0:
        return None
    rid = int(transitions.iloc[pos]["regime_id"])
    return rid, REGIMES[rid - 1]


def build_pair_panel(old_prices: pd.DataFrame, new_prices: pd.DataFrame, leg: str) -> pd.DataFrame:
    a, b = LEG_SPECS[leg]
    series = {}
    for asset in (a, b):
        if asset in old_prices.columns:
            series[asset] = old_prices[asset]
        elif asset in new_prices.columns:
            series[asset] = new_prices[asset]
        else:
            raise KeyError(asset)
    panel = pd.concat(series.values(), axis=1, join="inner")
    panel.columns = [a, b]
    panel = panel.dropna().sort_index()
    if panel.empty:
        raise RuntimeError(f"empty pair panel for {leg}")
    if panel.index.duplicated().any():
        raise RuntimeError(f"duplicate pair dates for {leg}")
    if not np.isfinite(panel.to_numpy(float)).all() or (panel.to_numpy(float) <= 0).any():
        raise RuntimeError(f"invalid price panel for {leg}")
    return panel


def first_rows_each_month(index: pd.DatetimeIndex) -> list[int]:
    periods = index.to_period("M")
    positions: list[int] = []
    last = None
    for i, p in enumerate(periods):
        if p != last:
            positions.append(i)
            last = p
    return positions


def cpi_yoy_for_origin(cpi: pd.DataFrame, origin: pd.Timestamp) -> tuple[str | None, float]:
    target = (origin.to_period("M") - 2).to_timestamp()
    prev12 = (target.to_period("M") - 12).to_timestamp()
    if target not in cpi.index or prev12 not in cpi.index:
        return None, math.nan
    current = float(cpi.loc[target, "CPI_U_NSA"])
    prior = float(cpi.loc[prev12, "CPI_U_NSA"])
    if prior <= 0:
        return None, math.nan
    return target.strftime("%Y-%m"), 100.0 * (current / prior - 1.0)


def build_monthly_rows(
    leg: str,
    panel: pd.DataFrame,
    transitions: pd.DataFrame,
    cpi: pd.DataFrame,
) -> pd.DataFrame:
    a, b = LEG_SPECS[leg]
    rows: list[dict] = []
    positions = first_rows_each_month(panel.index)

    for pos in positions:
        if pos <= 0:
            continue
        origin = pd.Timestamp(panel.index[pos])
        prev_date = pd.Timestamp(panel.index[pos - 1])
        state = state_on_date(transitions, prev_date)
        if state is None:
            continue
        rid, regime = state
        cpi_month, cpi_yoy = cpi_yoy_for_origin(cpi, origin)

        for horizon_name, horizon in HORIZONS.items():
            end_pos = pos + horizon
            if end_pos >= len(panel):
                continue
            end_date = pd.Timestamp(panel.index[end_pos])
            ra = float(panel.iloc[end_pos][a] / panel.iloc[pos][a] - 1.0)
            rb = float(panel.iloc[end_pos][b] / panel.iloc[pos][b] - 1.0)
            rows.append({
                "leg": leg,
                "asset_a": a,
                "asset_b": b,
                "origin_date": origin,
                "origin_pos": pos,
                "signal_date": prev_date,
                "regime_id": rid,
                "regime": regime,
                "horizon": horizon_name,
                "horizon_rows": horizon,
                "end_date": end_date,
                "asset_a_return": ra,
                "asset_b_return": rb,
                "pairwise_spread": ra - rb,
                "segment": segment_for_date(origin),
                "cpi_source_month_m2": cpi_month,
                "cpi_yoy_m2": cpi_yoy,
                "cpi_bucket_4pct": (
                    "lt_4" if np.isfinite(cpi_yoy) and cpi_yoy < 4.0
                    else "ge_4" if np.isfinite(cpi_yoy)
                    else None
                ),
            })
    out = pd.DataFrame(rows)
    if out.empty:
        raise RuntimeError(f"no monthly A1 rows for {leg}")
    return out.sort_values(["horizon_rows", "origin_date"]).reset_index(drop=True)


def select_nonoverlap(group: pd.DataFrame, horizon_rows: int) -> pd.DataFrame:
    selected: list[int] = []
    last_pos: int | None = None
    for idx, row in group.sort_values("origin_pos").iterrows():
        pos = int(row["origin_pos"])
        if last_pos is None or pos - last_pos >= horizon_rows:
            selected.append(idx)
            last_pos = pos
    return group.loc[selected].sort_values("origin_date")


def mark_primary_inference(rows: pd.DataFrame) -> pd.DataFrame:
    result = rows.copy()
    result["primary_inference"] = False
    for (leg, horizon, rid), group in result.groupby(["leg", "horizon", "regime_id"], sort=False):
        h = int(group["horizon_rows"].iloc[0])
        selected = select_nonoverlap(group, h)
        result.loc[selected.index, "primary_inference"] = True
    return result


def aggregate_state_summaries(rows: pd.DataFrame) -> pd.DataFrame:
    records: list[dict] = []
    for (leg, horizon, rid, regime), group in rows.groupby(["leg", "horizon", "regime_id", "regime"], sort=False):
        selected = group.loc[group["primary_inference"]].sort_values("origin_date")
        scopes = [("full", selected)]
        for seg in ("pre_2020", "covid_inflation_2020_2022", "post_2023"):
            scopes.append((seg, selected.loc[selected["segment"].eq(seg)]))

        for scope, sample in scopes:
            stats = summarize(
                sample["pairwise_spread"].to_numpy(float),
                seed=stable_seed("issue109", "A1", leg, horizon, rid, scope),
            )
            records.append({
                "leg": leg,
                "horizon": horizon,
                "horizon_rows": int(group["horizon_rows"].iloc[0]),
                "regime_id": int(rid),
                "regime": regime,
                "scope": scope,
                **stats,
                "first_origin": sample["origin_date"].min().date().isoformat() if len(sample) else None,
                "last_origin": sample["origin_date"].max().date().isoformat() if len(sample) else None,
            })
    return pd.DataFrame(records).sort_values(["leg", "horizon_rows", "regime_id", "scope"]).reset_index(drop=True)


def aggregate_all_monthly(rows: pd.DataFrame) -> pd.DataFrame:
    records: list[dict] = []
    for (leg, horizon, rid, regime), group in rows.groupby(["leg", "horizon", "regime_id", "regime"], sort=False):
        stats = summarize(
            group["pairwise_spread"].to_numpy(float),
            seed=stable_seed("issue109", "A1", "allmonthly", leg, horizon, rid),
        )
        records.append({
            "leg": leg,
            "horizon": horizon,
            "horizon_rows": int(group["horizon_rows"].iloc[0]),
            "regime_id": int(rid),
            "regime": regime,
            **stats,
            "first_origin": group["origin_date"].min().date().isoformat(),
            "last_origin": group["origin_date"].max().date().isoformat(),
        })
    return pd.DataFrame(records).sort_values(["leg", "horizon_rows", "regime_id"]).reset_index(drop=True)


def assign_episode_ids(primary_monthly: pd.DataFrame) -> pd.DataFrame:
    g = primary_monthly.sort_values("origin_date").copy()
    episode_ids: list[int] = []
    episode = 0
    prev_state: int | None = None
    prev_period: pd.Period | None = None

    for _, row in g.iterrows():
        state = int(row["regime_id"])
        period = pd.Timestamp(row["origin_date"]).to_period("M")
        consecutive = prev_period is not None and period.ordinal == prev_period.ordinal + 1
        if prev_state is None or state != prev_state or not consecutive:
            episode += 1
        episode_ids.append(episode)
        prev_state = state
        prev_period = period

    g["episode_id"] = episode_ids
    return g


def episode_robustness(rows: pd.DataFrame, state_summaries: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    episodes_out: list[dict] = []
    robust_out: list[dict] = []

    primary = rows.loc[rows["horizon"].eq(PRIMARY_HORIZON)].copy()

    for leg, leg_rows in primary.groupby("leg", sort=False):
        with_ep = assign_episode_ids(leg_rows)
        for (episode_id, rid, regime), ep in with_ep.groupby(["episode_id", "regime_id", "regime"], sort=False):
            episodes_out.append({
                "leg": leg,
                "episode_id": int(episode_id),
                "regime_id": int(rid),
                "regime": regime,
                "start_origin": ep["origin_date"].min().date().isoformat(),
                "end_origin": ep["origin_date"].max().date().isoformat(),
                "months": int(len(ep)),
                "contribution_sum": float(ep["pairwise_spread"].sum()),
                "mean_spread": float(ep["pairwise_spread"].mean()),
            })

        ep_df = pd.DataFrame([x for x in episodes_out if x["leg"] == leg])

        for rid in range(1, 10):
            regime = REGIMES[rid - 1]
            state_rows = leg_rows.loc[leg_rows["regime_id"].eq(rid)].copy()
            full_summary = state_summaries.loc[
                state_summaries["leg"].eq(leg)
                & state_summaries["horizon"].eq(PRIMARY_HORIZON)
                & state_summaries["regime_id"].eq(rid)
                & state_summaries["scope"].eq("full")
            ]
            if full_summary.empty:
                continue
            full_mean = float(full_summary.iloc[0]["mean"])
            full_sign = sign(full_mean)

            state_eps = ep_df.loc[ep_df["regime_id"].eq(rid)].copy()
            if state_eps.empty or full_sign == 0:
                robust_out.append({
                    "leg": leg,
                    "regime_id": rid,
                    "regime": regime,
                    "full_mean_sign": full_sign,
                    "supporting_episode_id": None,
                    "supporting_episode_start": None,
                    "supporting_episode_end": None,
                    "supporting_episode_contribution": math.nan,
                    "top_supporting_share": math.nan,
                    "leaveout_n": 0,
                    "leaveout_mean": math.nan,
                    "leaveout_sign_retained": False,
                })
                continue

            state_eps["supporting_contribution"] = state_eps["contribution_sum"] * full_sign
            positive_support = state_eps.loc[state_eps["supporting_contribution"] > 0].copy()
            if positive_support.empty:
                robust_out.append({
                    "leg": leg,
                    "regime_id": rid,
                    "regime": regime,
                    "full_mean_sign": full_sign,
                    "supporting_episode_id": None,
                    "supporting_episode_start": None,
                    "supporting_episode_end": None,
                    "supporting_episode_contribution": math.nan,
                    "top_supporting_share": math.nan,
                    "leaveout_n": 0,
                    "leaveout_mean": math.nan,
                    "leaveout_sign_retained": False,
                })
                continue

            strongest = positive_support.sort_values("supporting_contribution", ascending=False).iloc[0]
            support_total = float(positive_support["supporting_contribution"].sum())
            top_share = float(strongest["supporting_contribution"] / support_total) if support_total > 0 else math.nan

            remove_id = int(strongest["episode_id"])
            episode_origin_dates = set(
                with_ep.loc[
                    with_ep["episode_id"].eq(remove_id)
                    & with_ep["regime_id"].eq(rid),
                    "origin_date",
                ]
            )
            leave = state_rows.loc[~state_rows["origin_date"].isin(episode_origin_dates)]
            leave_selected = select_nonoverlap(leave, PRIMARY_ROWS)
            leave_mean = float(leave_selected["pairwise_spread"].mean()) if len(leave_selected) else math.nan

            robust_out.append({
                "leg": leg,
                "regime_id": rid,
                "regime": regime,
                "full_mean_sign": full_sign,
                "supporting_episode_id": remove_id,
                "supporting_episode_start": strongest["start_origin"],
                "supporting_episode_end": strongest["end_origin"],
                "supporting_episode_contribution": float(strongest["contribution_sum"]),
                "top_supporting_share": top_share,
                "leaveout_n": int(len(leave_selected)),
                "leaveout_mean": leave_mean,
                "leaveout_sign_retained": sign(leave_mean) == full_sign and sign(leave_mean) != 0,
            })

    episodes = pd.DataFrame(episodes_out).sort_values(["leg", "start_origin"]).reset_index(drop=True)
    robustness = pd.DataFrame(robust_out).sort_values(["leg", "regime_id"]).reset_index(drop=True)
    return episodes, robustness


def classify_states(state_summaries: pd.DataFrame, robustness: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    records: list[dict] = []
    leg_summary: dict[str, str] = {}

    for leg in LEG_SPECS:
        leg_records: list[dict] = []
        for rid in range(1, 10):
            regime = REGIMES[rid - 1]
            full = state_summaries.loc[
                state_summaries["leg"].eq(leg)
                & state_summaries["horizon"].eq(PRIMARY_HORIZON)
                & state_summaries["regime_id"].eq(rid)
                & state_summaries["scope"].eq("full")
            ]
            if full.empty:
                continue
            full_row = full.iloc[0]
            n = int(full_row["n"])
            mean = float(full_row["mean"]) if np.isfinite(full_row["mean"]) else math.nan
            ci_low = float(full_row["ci_low"]) if np.isfinite(full_row["ci_low"]) else math.nan
            ci_high = float(full_row["ci_high"]) if np.isfinite(full_row["ci_high"]) else math.nan
            full_sign = sign(mean)
            ci_excludes_zero = np.isfinite(ci_low) and np.isfinite(ci_high) and (ci_low > 0 or ci_high < 0)

            temporal = state_summaries.loc[
                state_summaries["leg"].eq(leg)
                & state_summaries["horizon"].eq(PRIMARY_HORIZON)
                & state_summaries["regime_id"].eq(rid)
                & state_summaries["scope"].isin(["pre_2020", "covid_inflation_2020_2022", "post_2023"])
            ]
            eligible_temporal = temporal.loc[temporal["n"] >= 3]
            temporal_same_sign = True
            temporal_reversals: list[str] = []
            for _, row in eligible_temporal.iterrows():
                if sign(float(row["mean"])) != full_sign:
                    temporal_same_sign = False
                    temporal_reversals.append(str(row["scope"]))

            rob = robustness.loc[
                robustness["leg"].eq(leg) & robustness["regime_id"].eq(rid)
            ]
            if rob.empty:
                leaveout_retained = False
                top_share = math.nan
            else:
                rr = rob.iloc[0]
                leaveout_retained = bool(rr["leaveout_sign_retained"])
                top_share = float(rr["top_supporting_share"]) if np.isfinite(rr["top_supporting_share"]) else math.nan

            episode_pass = leaveout_retained and np.isfinite(top_share) and top_share <= 0.50

            if n < 10:
                classification = "inconclusive_insufficient_sample"
            elif ci_excludes_zero:
                if temporal_same_sign and episode_pass:
                    classification = "stable_directional_candidate"
                else:
                    classification = "era_dependent_candidate"
            else:
                classification = "no_clear_state_edge"

            assert classification in ALLOWED_STATE_CLASSIFICATIONS
            rec = {
                "leg": leg,
                "regime_id": rid,
                "regime": regime,
                "primary_n": n,
                "primary_mean": mean,
                "primary_ci_low": ci_low,
                "primary_ci_high": ci_high,
                "full_mean_sign": full_sign,
                "ci_excludes_zero": ci_excludes_zero,
                "eligible_temporal_segments": int(len(eligible_temporal)),
                "temporal_same_sign": temporal_same_sign,
                "temporal_reversals": ",".join(temporal_reversals),
                "leaveout_sign_retained": leaveout_retained,
                "top_supporting_share": top_share,
                "episode_pass": episode_pass,
                "classification": classification,
            }
            records.append(rec)
            leg_records.append(rec)

        classes = [x["classification"] for x in leg_records]
        regular_states = sum(x["primary_n"] >= 10 for x in leg_records)
        if "stable_directional_candidate" in classes:
            summary = "stable_directional_relationship"
        elif "era_dependent_candidate" in classes:
            summary = "useful_but_era_dependent"
        elif regular_states >= 5:
            summary = "no_material_pairwise_information"
        else:
            summary = "inconclusive_insufficient_sample"
        assert summary in ALLOWED_LEG_SUMMARIES
        leg_summary[leg] = summary

    return pd.DataFrame(records).sort_values(["leg", "regime_id"]).reset_index(drop=True), leg_summary


def inflation_diagnostic(rows: pd.DataFrame) -> pd.DataFrame:
    sample = rows.loc[
        rows["leg"].eq("duration_vs_cash")
        & rows["horizon"].eq(PRIMARY_HORIZON)
        & rows["primary_inference"]
        & rows["cpi_bucket_4pct"].notna()
    ].copy()

    records: list[dict] = []
    for (rid, regime, bucket), group in sample.groupby(["regime_id", "regime", "cpi_bucket_4pct"], sort=False):
        stats = summarize(
            group["pairwise_spread"].to_numpy(float),
            seed=stable_seed("issue109", "A1", "inflation", rid, bucket),
        )
        records.append({
            "regime_id": int(rid),
            "regime": regime,
            "cpi_bucket_4pct": bucket,
            **stats,
            "first_origin": group["origin_date"].min().date().isoformat(),
            "last_origin": group["origin_date"].max().date().isoformat(),
        })
    return pd.DataFrame(records).sort_values(["regime_id", "cpi_bucket_4pct"]).reset_index(drop=True)


def write_outputs(out_dir: Path) -> dict:
    old_prices, new_prices, transitions, cpi, provenance = load_and_validate_sources()
    out_dir.mkdir(parents=True, exist_ok=True)

    all_rows = []
    panel_meta = {}
    for leg in LEG_SPECS:
        panel = build_pair_panel(old_prices, new_prices, leg)
        panel_meta[leg] = {
            "rows": int(len(panel)),
            "first_date": panel.index.min().date().isoformat(),
            "last_date": panel.index.max().date().isoformat(),
        }
        all_rows.append(build_monthly_rows(leg, panel, transitions, cpi))

    rows = pd.concat(all_rows, ignore_index=True)
    rows = mark_primary_inference(rows)

    state_summaries = aggregate_state_summaries(rows)
    all_monthly = aggregate_all_monthly(rows)
    episodes, robustness = episode_robustness(rows, state_summaries)
    state_classification, leg_summary = classify_states(state_summaries, robustness)
    inflation = inflation_diagnostic(rows)

    files = {
        "monthly_origins": out_dir / "issue-109-a1-monthly-origins.csv",
        "state_summary": out_dir / "issue-109-a1-state-summary.csv",
        "all_monthly_summary": out_dir / "issue-109-a1-all-monthly-summary.csv",
        "episodes": out_dir / "issue-109-a1-episodes.csv",
        "episode_robustness": out_dir / "issue-109-a1-episode-robustness.csv",
        "state_classification": out_dir / "issue-109-a1-state-classification.csv",
        "inflation_diagnostic": out_dir / "issue-109-a1-duration-cash-inflation-diagnostic.csv",
    }

    serial_rows = rows.copy()
    for col in ("origin_date", "signal_date", "end_date"):
        serial_rows[col] = pd.to_datetime(serial_rows[col]).dt.strftime("%Y-%m-%d")
    serial_rows.to_csv(files["monthly_origins"], index=False, float_format="%.12g")
    state_summaries.to_csv(files["state_summary"], index=False, float_format="%.12g")
    all_monthly.to_csv(files["all_monthly_summary"], index=False, float_format="%.12g")
    episodes.to_csv(files["episodes"], index=False, float_format="%.12g")
    robustness.to_csv(files["episode_robustness"], index=False, float_format="%.12g")
    state_classification.to_csv(files["state_classification"], index=False, float_format="%.12g")
    inflation.to_csv(files["inflation_diagnostic"], index=False, float_format="%.12g")

    manifest = {
        "schema_version": 1,
        "issue": 109,
        "phase": "A1-state-only",
        "primary_horizon": PRIMARY_HORIZON,
        "primary_horizon_rows": PRIMARY_ROWS,
        "diagnostic_horizons": HORIZONS,
        "decision_frequency": "monthly_first_common_trading_row",
        "signal_timing": "one eligible trading row lag before origin",
        "bootstrap_reps": BOOTSTRAP_REPS,
        "trajectory_loaded": False,
        "fcpi_loaded_as_predictor": False,
        "portfolio_metrics_computed": False,
        "weights_optimized": False,
        "source_hashes": {
            "issue64_transition": EXPECTED_TRANSITION_SHA,
            "issue64_spy_tlt_gld": EXPECTED_OLD_PRICE_SHA,
            "issue109_shv_gsg": EXPECTED_NEW_PRICE_SHA,
            "issue109_cpi": EXPECTED_CPI_SHA,
        },
        "pair_panels": panel_meta,
        "legs": {k: list(v) for k, v in LEG_SPECS.items()},
        "leg_summary": leg_summary,
        "state_classification_counts": {
            leg: state_classification.loc[state_classification["leg"].eq(leg), "classification"].value_counts().to_dict()
            for leg in LEG_SPECS
        },
        "rows": {
            "monthly_origin_horizon_rows": int(len(rows)),
            "primary_inference_rows": int(rows["primary_inference"].sum()),
            "state_summary_rows": int(len(state_summaries)),
            "episode_rows": int(len(episodes)),
            "inflation_diagnostic_rows": int(len(inflation)),
        },
        "outputs": {
            key: {
                "file": path.name,
                "sha256": sha256_file(path),
            }
            for key, path in files.items()
        },
        "research_boundary": [
            "A1 uses exact frozen V6.6 states only.",
            "No GPI/IPI trajectory feature is loaded.",
            "No production tilt size is defined.",
            "No portfolio CAGR/Sharpe/drawdown optimization is performed.",
            "Modern history is reused historical evidence, not untouched OOS confirmation.",
        ],
        "provenance": provenance,
    }
    manifest_path = out_dir / "issue-109-a1-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({
        "leg_summary": leg_summary,
        "state_classification_counts": manifest["state_classification_counts"],
        "primary_inference_rows": manifest["rows"]["primary_inference_rows"],
        "manifest": manifest_path.name,
    }, indent=2))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    write_outputs(args.output_dir)


if __name__ == "__main__":
    main()
