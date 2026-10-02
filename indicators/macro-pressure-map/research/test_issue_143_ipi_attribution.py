#!/usr/bin/env python3
from __future__ import annotations

import pandas as pd

from issue_143_ipi_attribution import (
    metric_damage,
    primary_cause,
    state3,
)


def test_state3_uses_exact_v66_thresholds():
    s = pd.Series([-11.0, -10.0, 0.0, 10.0, 11.0])
    assert state3(s).tolist() == [-1.0, 0.0, 0.0, 0.0, 1.0]


def test_metric_damage_clips_improvements_only_for_score():
    parent = {
        "ipi_correlation": 0.9,
        "ipi_slope_agreement": 0.8,
        "ipi_state_agreement": 0.7,
        "regime_agreement": 0.6,
        "r7_precision": 0.5,
        "r7_recall": 0.4,
        "trigger_f1": 0.3,
    }
    child = dict(parent)
    child["ipi_correlation"] = 0.8
    child["ipi_slope_agreement"] = 0.85
    d = metric_damage(parent, child)
    assert abs(d["raw"]["ipi_correlation"] - 0.1) < 1e-12
    assert abs(d["raw"]["ipi_slope_agreement"] + 0.05) < 1e-12
    assert d["clipped"]["ipi_slope_agreement"] == 0.0
    assert d["score"] > 0


def test_primary_cause_requires_anchor():
    damages = {
        "frequency": {"score": 0.20},
        "breakeven": {"score": 0.01},
        "commodity": {"score": 0.01},
        "oil_provider": {"score": 0.01},
        "gasoline_proxy": {"score": 0.01},
    }
    assert primary_cause(damages, False) is None
    assert primary_cause(damages, True) == "frequency_translation_primary"


def test_primary_cause_mixed_when_top_two_close():
    damages = {
        "frequency": {"score": 0.10},
        "breakeven": {"score": 0.08},
        "commodity": {"score": 0.01},
        "oil_provider": {"score": 0.01},
        "gasoline_proxy": {"score": 0.01},
    }
    assert primary_cause(damages, True) == "mixed_drivers"
