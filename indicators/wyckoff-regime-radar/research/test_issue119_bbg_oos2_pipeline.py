from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from build_issue119_bbg_oos2_universe import write_universe_artifacts
from download_issue119_bbg_oos2_ohlcv import download_universe
from issue119_bbg_common import (
    CALIBRATION_TICKERS,
    deterministic_stratified_sample,
    normalize_ohlcv,
)


SECTORS = [
    "Communication Services",
    "Consumer Discretionary",
    "Consumer Staples",
    "Energy",
    "Financials",
    "Health Care",
    "Industrials",
    "Information Technology",
    "Materials",
    "Real Estate",
    "Utilities",
]


def candidate_fixture(
    per_sector_per_sleeve: int = 12,
) -> pd.DataFrame:
    rows = []
    i = 0

    for sleeve in ("large", "mid", "small"):
        for sector in SECTORS:
            for _ in range(per_sector_per_sleeve):
                i += 1
                rows.append(
                    {
                        "sleeve": sleeve,
                        "source_index": f"{sleeve.upper()} Index",
                        "security": f"T{i} US Equity",
                        "figi": f"BBG{i:09d}",
                        "ticker": f"T{i}",
                        "sector": sector,
                        "market_cap": 1_000_000_000 + i,
                        "market_sector": "Equity",
                        "security_type": "Common Stock",
                        "primary_exchange": "NASDAQ",
                        "metadata_error": None,
                    }
                )

    for ticker in sorted(CALIBRATION_TICKERS):
        i += 1
        rows.append(
            {
                "sleeve": "large",
                "source_index": "SPX Index",
                "security": f"{ticker} US Equity",
                "figi": f"BBG{i:09d}",
                "ticker": ticker,
                "sector": "Information Technology",
                "market_cap": 3_000_000_000_000,
                "market_sector": "Equity",
                "security_type": "Common Stock",
                "primary_exchange": "NASDAQ",
                "metadata_error": None,
            }
        )

    return pd.DataFrame(rows)


def history_fixture(
    start: str = "2020-01-02",
    rows: int = 30,
) -> pd.DataFrame:
    dates = pd.bdate_range(start, periods=rows)
    return pd.DataFrame(
        {
            "DATE": dates,
            "PX_OPEN": np.linspace(100, 110, rows),
            "PX_HIGH": np.linspace(101, 111, rows),
            "PX_LOW": np.linspace(99, 109, rows),
            "PX_LAST": np.linspace(100.5, 110.5, rows),
            "PX_VOLUME": np.arange(rows) + 1_000_000,
        }
    )


def test_sample_is_deterministic_and_excludes_calibration():
    frame = candidate_fixture()

    a = deterministic_stratified_sample(frame)
    b = deterministic_stratified_sample(
        frame.sample(frac=1.0, random_state=17)
    )

    assert len(a) == 300
    assert a["figi"].tolist() == b["figi"].tolist()
    assert not (set(a["ticker"]) & CALIBRATION_TICKERS)
    assert a.groupby("sleeve").size().to_dict() == {
        "large": 100,
        "mid": 100,
        "small": 100,
    }
    assert a["sector"].nunique() == 11


def test_universe_artifacts_hash_and_counts(tmp_path):
    manifest = write_universe_artifacts(
        candidate_fixture(),
        tmp_path,
    )

    assert manifest["selected_rows"] == 300
    assert manifest["selected_unique_figi"] == 300
    assert len(
        manifest["artifacts"][
            "issue119_bbg_oos2_universe_manifest.csv"
        ]["sha256"]
    ) == 64


def test_normalize_ohlcv_rejects_duplicate_dates_and_repairs_impossible_high():
    frame = history_fixture()

    bad = pd.concat(
        [frame, frame.iloc[[-1]]],
        ignore_index=True,
    )
    with pytest.raises(ValueError, match="duplicate"):
        normalize_ohlcv(bad)

    bad2 = frame.copy()
    bad2.loc[0, "PX_HIGH"] = 1.0
    normalized, diagnostics = normalize_ohlcv(bad2)
    assert diagnostics["normalization_contract_version"] == 2
    assert diagnostics["ohlc_range_repairs"] == 1
    assert normalized.loc[0, "high"] == max(
        normalized.loc[0, "open"],
        normalized.loc[0, "close"],
        1.0,
    )


class FakeClient:
    def __init__(self):
        self.calls = 0

    def historical_data(
        self,
        securities,
        *,
        start_date,
        end_date,
        fields,
    ):
        self.calls += 1

        if self.calls == 1 and len(securities) > 1:
            return {securities[0]: history_fixture()}

        return {
            security: history_fixture()
            for security in securities
        }


def tiny_universe() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "security": "AAA US Equity",
                "figi": "BBGAAA",
                "ticker": "AAA",
            },
            {
                "security": "BBB US Equity",
                "figi": "BBGBBB",
                "ticker": "BBB",
            },
        ]
    )


def test_download_retry_checkpoint_and_resume(tmp_path):
    client = FakeClient()

    manifest = download_universe(
        client,
        tiny_universe(),
        tmp_path,
        batch_size=2,
        max_attempts=3,
        sleep=lambda _: None,
    )

    assert manifest["failures"] == {}
    assert len(manifest["completed"]) == 2
    assert manifest["normalization"]["contract_version"] == 2
    assert manifest["normalization"]["ohlc_range_repairs_total"] == 0
    assert client.calls == 2

    client2 = FakeClient()
    manifest2 = download_universe(
        client2,
        tiny_universe(),
        tmp_path,
        batch_size=2,
        max_attempts=3,
        sleep=lambda _: None,
    )

    assert client2.calls == 0
    assert len(manifest2["completed"]) == 2


class EmptyClient:
    def historical_data(
        self,
        securities,
        *,
        start_date,
        end_date,
        fields,
    ):
        return {}


def test_incomplete_snapshot_fails_closed(tmp_path):
    with pytest.raises(
        RuntimeError,
        match="snapshot incomplete",
    ):
        download_universe(
            EmptyClient(),
            tiny_universe(),
            tmp_path,
            batch_size=2,
            max_attempts=2,
            sleep=lambda _: None,
        )


def test_downloader_modules_do_not_import_classifier_or_policy():
    here = Path(__file__).parent
    forbidden = (
        "wyckoff",
        "warning",
        "second_entry",
        "policy",
    )

    for filename in (
        "issue119_bbg_common.py",
        "issue119_bbg_client.py",
        "build_issue119_bbg_oos2_universe.py",
        "download_issue119_bbg_oos2_ohlcv.py",
    ):
        tree = ast.parse(
            (here / filename).read_text(encoding="utf-8")
        )

        modules = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.extend(
                    alias.name.lower()
                    for alias in node.names
                )
            elif (
                isinstance(node, ast.ImportFrom)
                and node.module
            ):
                modules.append(node.module.lower())

        assert not any(
            any(token in module for token in forbidden)
            for module in modules
        )
