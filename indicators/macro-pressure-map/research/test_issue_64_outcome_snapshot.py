from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from issue_64_outcome_snapshot import load_frozen_prices, write_price_snapshot


def sample_prices() -> pd.DataFrame:
    index = pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06"])
    return pd.DataFrame(
        {
            "SPY": [320.0, 321.0, 322.0],
            "TLT": [140.0, 140.5, 141.0],
            "GLD": [145.0, 146.0, 147.0],
        },
        index=index,
    )


def test_snapshot_round_trip_and_date_slice(tmp_path: Path) -> None:
    csv_path = tmp_path / "prices.csv"
    manifest_path = tmp_path / "prices.json"
    original = sample_prices()
    manifest = write_price_snapshot(
        original,
        csv_path,
        manifest_path,
        source={"acquisition_mode": "unit_test"},
    )
    loaded, runtime = load_frozen_prices(
        "2020-01-03",
        "2020-01-07",
        snapshot_path=csv_path,
        manifest_path=manifest_path,
    )
    assert loaded.index.tolist() == pd.to_datetime(["2020-01-03", "2020-01-06"]).tolist()
    assert np.allclose(loaded.to_numpy(float), original.iloc[1:].to_numpy(float))
    assert runtime["snapshot_sha256"] == manifest["csv_sha256"]


def test_snapshot_hash_mismatch_fails_closed(tmp_path: Path) -> None:
    csv_path = tmp_path / "prices.csv"
    manifest_path = tmp_path / "prices.json"
    write_price_snapshot(
        sample_prices(),
        csv_path,
        manifest_path,
        source={"acquisition_mode": "unit_test"},
    )
    csv_path.write_text(csv_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="SHA mismatch"):
        load_frozen_prices(
            "2020-01-01",
            None,
            snapshot_path=csv_path,
            manifest_path=manifest_path,
        )


def test_committed_shards_reassemble_exact_frozen_panel() -> None:
    loaded, runtime = load_frozen_prices("2007-01-01", None)
    assert len(loaded) == 4941
    assert loaded.index.min() == pd.Timestamp("2007-01-03")
    assert loaded.index.max() == pd.Timestamp("2026-08-24")
    assert runtime["source_mode"] == "committed_frozen_snapshot"
    assert runtime["snapshot_csv_sha256"] == "3a7f590c146f9eda5920b6968fe86c9c3cc1887db35597f2d639a1c76b6e5a57"
    assert runtime["snapshot_archive_sha256"] == "d9d5f9e5ac171850c7c34739e45c60f41b195044bda81e25531c0dfa2bb22240"
    assert len(runtime["snapshot_shards"]) == 10
