from __future__ import annotations

import pandas as pd

import analyze_issue78_equity_early_proof_replication as m


def synthetic_rows():
    rows = []
    # Four stocks, each with clean separation and >=20 episodes for quintiles.
    for stock in range(4):
        for i in range(24):
            large = i >= 12
            usable = i >= 10
            quality = float(i - 12)
            rows.append(
                {
                    "figi": f"F{stock}",
                    "ticker": f"T{stock}",
                    "sector": "Energy",
                    "sleeve": "large" if stock < 2 else "mid",
                    "block": "2020-2026",
                    "direction": "Markup" if i % 2 == 0 else "Markdown",
                    "bars": 15 if i >= 4 else 4,
                    "trend_label": "Large" if large else "Failed",
                    "b3_label": "UsableB3" if usable else "NoUsableB3",
                    "r0_harvest": quality / 10.0,
                    "e5_cum_atr": quality,
                    "e5_mfe_atr": quality + 1.0,
                    "e5_giveback_atr": -quality,
                    "e5_dir_eff": quality / 20.0,
                    "e10_cum_atr": quality * 1.5,
                    "e10_mfe_atr": quality * 1.5 + 1.0,
                    "e10_giveback_atr": -quality * 1.5,
                    "e10_dir_eff": quality / 15.0,
                }
            )
    return pd.DataFrame(rows)


def test_frozen_feature_contract():
    assert set(m.FEATURES) == {
        "e5_cum_atr",
        "e5_mfe_atr",
        "e5_giveback_atr",
        "e5_dir_eff",
        "e10_cum_atr",
        "e10_mfe_atr",
        "e10_giveback_atr",
        "e10_dir_eff",
    }
    assert m.TARGETS["failed_vs_large"] == ("Large", "Failed")
    assert m.TARGETS["usable_b3_vs_no_b3"] == (
        "UsableB3",
        "NoUsableB3",
    )


def test_separation_detects_clean_synthetic_signal():
    out = m.separation_table(synthetic_rows())
    row = out[
        (out["target"] == "failed_vs_large")
        & (out["feature"] == "e5_cum_atr")
    ].iloc[0]
    assert row["stocks"] == 4
    assert row["equal_stock_mean_auc"] == 1.0
    assert row["fraction_stocks_auc_gt_0_5"] == 1.0

    giveback = out[
        (out["target"] == "failed_vs_large")
        & (out["feature"] == "e5_giveback_atr")
    ].iloc[0]
    assert giveback["equal_stock_mean_auc"] == 1.0


def test_survival_reports_decision_availability():
    out = m.survival_summary(synthetic_rows())
    failed = out[
        (out["label_family"] == "trend_label")
        & (out["label"] == "Failed")
    ].iloc[0]
    assert 0 < failed["survive_e5_fraction"] < 1
    assert failed["survive_e10_fraction"] == failed["survive_e5_fraction"]


def test_quintiles_preserve_quality_ordering():
    out = m.quintile_table(synthetic_rows())
    work = out[
        (out["target"] == "failed_vs_large")
        & (out["feature"] == "e5_cum_atr")
    ].sort_values("quality_quintile")
    assert len(work) == 5
    assert (
        work.iloc[-1]["equal_stock_positive_share"]
        > work.iloc[0]["equal_stock_positive_share"]
    )
    assert (
        work.iloc[-1]["equal_stock_r0_harvest"]
        > work.iloc[0]["equal_stock_r0_harvest"]
    )


def test_slice_reporting_requires_five_stocks():
    # Synthetic fixture has four stocks, so no slice should be emitted.
    out = m.sliced_auc_table(synthetic_rows())
    assert out.empty
