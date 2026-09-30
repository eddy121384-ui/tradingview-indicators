from __future__ import annotations

import pandas as pd

import build_issue78_equity_policy_oos3_universe as m


def candidate_frame():
    rows = []
    for sleeve in ("large", "mid", "small"):
        for sector in ("Energy", "Financials", "Industrials", "Utilities"):
            for i in range(90):
                ticker = f"{sleeve[:1]}{sector[:1]}{i:03d}"
                rows.append(
                    {
                        "sleeve": sleeve,
                        "source_index": "TEST Index",
                        "security": f"{ticker} US Equity",
                        "figi": f"BBG_{sleeve}_{sector}_{i:03d}",
                        "ticker": ticker,
                        "sector": sector,
                        "market_cap": 1000 + i,
                        "market_sector": "Equity",
                        "security_type": "Common Stock",
                        "primary_exchange": "US",
                        "metadata_error": None,
                    }
                )
    return pd.DataFrame(rows)


def prior_frame(candidates: pd.DataFrame):
    picks = []
    for sleeve in ("large", "mid", "small"):
        picks.extend(
            candidates[candidates["sleeve"] == sleeve].head(20).to_dict("records")
        )
    return pd.DataFrame(picks)


def test_oos3_is_deterministic_and_disjoint():
    candidates = candidate_frame()
    prior = prior_frame(candidates)

    a, da = m.build_oos3(candidates, prior)
    b, db = m.build_oos3(candidates, prior)

    assert a["figi"].tolist() == b["figi"].tolist()
    assert da["selected_rows"] == 300
    assert db["selected_rows"] == 300
    assert not (set(a["figi"]) & set(prior["figi"]))
    assert a["figi"].nunique() == 300


def test_oos3_has_100_per_sleeve():
    candidates = candidate_frame()
    prior = prior_frame(candidates)
    selected, _ = m.build_oos3(candidates, prior)
    assert selected["sleeve"].value_counts().to_dict() == {
        "large": 100,
        "mid": 100,
        "small": 100,
    }
