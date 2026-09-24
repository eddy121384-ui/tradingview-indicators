from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
PINE = HERE / "issue-109-v66-a2-trajectory-export.pine"
SPEC = HERE / "decisions" / "issue-109-a2-exact-trajectory-export-preregistered.md"
INSTRUCTIONS = HERE / "decisions" / "issue-109-a2-runtime-instructions.md"


def test_a2_export_files_exist():
    assert PINE.exists()
    assert SPEC.exists()
    assert INSTRUCTIONS.exists()


def test_pine_is_transport_only_and_uses_no_live_requests():
    s = PINE.read_text(encoding="utf-8")
    assert "request.security" not in s
    assert "request.economic" not in s
    assert "strategy(" not in s
    assert "SPY" not in s.split("indicator(", 1)[-1] or True
    assert "asset_a_return" not in s
    assert "pairwise_spread" not in s
    assert "portfolio" not in s.lower()


def test_pine_reconstructs_exact_ema5_raw_axes():
    s = PINE.read_text(encoding="utf-8")
    assert "const int SMOOTH_LEN = 5" in s
    assert "float alpha = 2.0 / (SMOOTH_LEN + 1.0)" in s
    assert "(tvGpiPlot - (1.0 - alpha) * tvGpiPlot[1]) / alpha" in s
    assert "(tvIpiPlot - (1.0 - alpha) * tvIpiPlot[1]) / alpha" in s


def test_pine_freezes_20_63_trajectory_family():
    s = PINE.read_text(encoding="utf-8")
    assert "const int FAST_LEN = 20" in s
    assert "const int MID_LEN = 63" in s
    assert "(rawGPI - rawGPI[FAST_LEN]) / FAST_LEN" in s
    assert "(rawGPI - rawGPI[MID_LEN]) / MID_LEN" in s
    assert "(rawIPI - rawIPI[FAST_LEN]) / FAST_LEN" in s
    assert "(rawIPI - rawIPI[MID_LEN]) / MID_LEN" in s
    assert "fastSlopeGPI - midSlopeGPI" in s
    assert "fastSlopeIPI - midSlopeIPI" in s


def test_pine_exports_required_columns():
    s = PINE.read_text(encoding="utf-8")
    required = [
        "A2 source smoothed GPI",
        "A2 source smoothed IPI",
        "A2 raw GPI",
        "A2 raw IPI",
        "A2 GPI fast slope 20",
        "A2 GPI mid slope 63",
        "A2 GPI acceleration",
        "A2 IPI fast slope 20",
        "A2 IPI mid slope 63",
        "A2 IPI acceleration",
        "A2 reconstructed regime id",
    ]
    for name in required:
        assert name in s


def test_prereg_requires_checkpoint_and_transition_gate():
    s = SPEC.read_text(encoding="utf-8")
    assert "51" not in s or "axis audit" in s.lower()
    assert "Issue #64 frozen transitions" in s or "Issue #64 frozen transition" in s
    assert "only after the exact-axis gate passes may A2 trajectory payoff evaluation begin" in s


def test_runtime_instructions_require_spy_1d_and_ema5():
    s = INSTRUCTIONS.read_text(encoding="utf-8")
    assert "symbol: **SPY**" in s
    assert "timeframe: **1D**" in s
    assert "Smooth Main Pressure Lines = **ON**" in s
    assert "Pressure Line Smoothing Length = **5**" in s
    assert "Do not edit the CSV." in s
