from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from evaluate_issue_74_defensive_overlay import episode_concentration as phase_ab_episode_concentration
from evaluate_issue_74_phase_c import episode_concentration as phase_c_episode_concentration
import issue_74_outcome_snapshot as outcome
import issue_74_severe_inflation as severe


def _sim(index: pd.DatetimeIndex, returns: list[float]) -> pd.DataFrame:
    return pd.DataFrame({"net_return": returns}, index=index)


def test_phase_ab_episode_concentration_uses_only_stagflation_rows() -> None:
    idx = pd.date_range("2020-01-01", periods=5, freq="D")
    simulations = {
        "lhs": _sim(idx, [0.01, 0.02, 0.20, 0.20, 0.20]),
        "rhs": _sim(idx, [0.00, 0.00, 0.00, 0.00, 0.00]),
    }
    lagged_regime = pd.Series(
        ["Stagflation Pressure", "Stagflation Pressure", "Other", "Other", "Other"],
        index=idx,
    )
    result = phase_ab_episode_concentration(
        simulations,
        lagged_regime,
        lhs="lhs",
        rhs="rhs",
        comparison="synthetic",
        stagflation_regime="Stagflation Pressure",
    )
    full = result.loc[result.segment.eq("full_reused_history")].iloc[0]
    expected = np.log1p(0.01) + np.log1p(0.02)
    assert np.isclose(full.active_log_return_all, expected)


def test_phase_c_episode_concentration_uses_only_active_rows() -> None:
    idx = pd.date_range("2020-01-01", periods=5, freq="D")
    active_log = pd.Series([0.01, 0.02, 0.50, 0.50, 0.50], index=idx)
    active_mask = pd.Series([True, True, False, False, False], index=idx)
    result = phase_c_episode_concentration(active_log, active_mask)
    full = result.loc[result.segment.eq("full_reused_history")].iloc[0]
    assert np.isclose(full.active_log_return_all, 0.03)


def test_legacy_full_daily_evidence_can_drive_positive_dates(tmp_path: Path) -> None:
    compact_data = tmp_path / "missing-positive.csv"
    compact_manifest = tmp_path / "missing-positive-manifest.json"
    legacy_data = tmp_path / "legacy.csv"
    legacy_manifest = tmp_path / "legacy-manifest.json"

    frame = pd.DataFrame(
        {
            "date": ["2007-01-04", "2007-01-05", "2007-01-08"],
            "IPI": [59.0, 60.0, 61.0],
            "severe_inflation": [False, True, True],
        }
    )
    frame.to_csv(legacy_data, index=False)
    manifest = {
        "issue": 74,
        "role": "frozen daily raw IPI for severe-inflation classification",
        "source_log_sha256": severe.EXPECTED_SOURCE_LOG_SHA256,
        "inflation_extreme_threshold": 60.0,
        "csv_sha256": severe.sha256_file(legacy_data),
    }
    legacy_manifest.write_text(json.dumps(manifest), encoding="utf-8")

    positive, loaded = severe.load_severe_positive_dates(
        compact_data,
        compact_manifest,
        legacy_data,
        legacy_manifest,
    )
    assert loaded["evidence_mode"] == "exact prior full-daily artifact"
    assert list(positive.index) == [pd.Timestamp("2007-01-05"), pd.Timestamp("2007-01-08")]
    assert positive.tolist() == [60.0, 61.0]


def test_explicit_validation_sha_override_supersedes_pr_event_head(monkeypatch, tmp_path: Path) -> None:
    event_head = "a" * 40
    validation_head = "b" * 40
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps({"pull_request": {"head": {"sha": event_head}}}), encoding="utf-8")

    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setenv("ISSUE_74_EXPECTED_CHECKOUT_SHA", validation_head)
    monkeypatch.setattr(outcome.subprocess, "check_output", lambda *args, **kwargs: validation_head + "\n")

    outcome._assert_github_pr_checkout_matches_trigger()
