from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import issue_74_outcome_snapshot as snapshot


def sample_prices() -> pd.DataFrame:
    index = pd.bdate_range("2007-01-08", periods=7)
    return pd.DataFrame(
        {
            "SPY": np.linspace(100.0, 106.0, 7),
            "TLT": np.linspace(90.0, 92.0, 7),
            "SHV": np.linspace(100.0, 100.2, 7),
            "GSG": np.linspace(40.0, 42.0, 7),
        },
        index=index,
    )


def test_freeze_and_load_round_trip(tmp_path: Path) -> None:
    prices = sample_prices()
    manifest = snapshot.freeze_price_panel(
        prices,
        data_dir=tmp_path,
        source={"provider": "unit-test"},
        shard_chars=1000,
    )
    loaded, runtime = snapshot.load_frozen_prices(
        manifest_path=tmp_path / "issue-74-outcome-prices-manifest.json"
    )
    np.testing.assert_allclose(loaded.to_numpy(float), prices.to_numpy(float), rtol=1e-15, atol=0.0)
    assert manifest["rows"] == 7
    assert runtime["source_mode"] == "committed_frozen_snapshot"
    assert runtime["symbols"] == list(snapshot.ASSETS)


def test_freeze_refuses_overwrite(tmp_path: Path) -> None:
    prices = sample_prices()
    snapshot.freeze_price_panel(prices, data_dir=tmp_path, source={"provider": "unit-test"}, shard_chars=1000)
    with pytest.raises(FileExistsError):
        snapshot.freeze_price_panel(prices, data_dir=tmp_path, source={"provider": "unit-test"}, shard_chars=1000)


def test_tampered_shard_fails_closed(tmp_path: Path) -> None:
    prices = sample_prices()
    manifest = snapshot.freeze_price_panel(prices, data_dir=tmp_path, source={"provider": "unit-test"}, shard_chars=1000)
    first = tmp_path / Path(manifest["shards"][0]["path"]).name
    first.write_text(first.read_text(encoding="ascii").strip() + "A\n", encoding="ascii")
    with pytest.raises(ValueError):
        snapshot.load_frozen_prices(manifest_path=tmp_path / "issue-74-outcome-prices-manifest.json")


def test_manifest_identity_fails_closed(tmp_path: Path) -> None:
    snapshot.freeze_price_panel(sample_prices(), data_dir=tmp_path, source={"provider": "unit-test"}, shard_chars=1000)
    path = tmp_path / "issue-74-outcome-prices-manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["issue"] = 64
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError):
        snapshot.load_frozen_prices(manifest_path=path)
