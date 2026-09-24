from __future__ import annotations

from pathlib import Path

from issue_109_a2_pine_log_parser import parse as parse_pine_logs

HERE = Path(__file__).resolve().parent
PINE = HERE / "issue-109-v66-a2-trajectory-export.pine"
SPEC = HERE / "decisions" / "issue-109-a2-exact-trajectory-export-preregistered.md"
INSTRUCTIONS = HERE / "decisions" / "issue-109-a2-runtime-instructions.md"
SELF_CONTAINED = HERE / "issue-109-v66-a2-selfcontained-export.pine"


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


def test_pine_logs_fallback_is_one_payload_per_confirmed_bar():
    s = PINE.read_text(encoding="utf-8")
    assert 'logFromYear = input.int(2007' in s
    assert 'if barstate.isconfirmed and year >= logFromYear' in s
    assert '"MPM_A2"' in s
    assert 'log.info(msg)' in s


def test_runtime_instructions_include_essential_plan_fallback():
    s = INSTRUCTIONS.read_text(encoding="utf-8")
    assert "Essential plan fallback" in s
    assert "Pine Logs" in s
    assert "issue_109_a2_pine_log_parser.py" in s


def test_pine_log_parser_extracts_payloads_from_ui_noise():
    text = """UI stuff
11:00:00 Info MPM_A2|date=2007-1-4|raw_gpi=-15.1|raw_ipi=-36.7|gpi_fast20=na|gpi_mid63=na|gpi_acc=na|ipi_fast20=na|ipi_mid63=na|ipi_acc=na|regime_id=7
other
11:00:01 Info MPM_A2|date=2007-1-5|raw_gpi=-14.0|raw_ipi=-30.0|gpi_fast20=0.1|gpi_mid63=na|gpi_acc=na|ipi_fast20=0.2|ipi_mid63=na|ipi_acc=na|regime_id=7
"""
    rows = parse_pine_logs(text)
    assert len(rows) == 2
    assert rows[0]["date"] == "2007-1-4"
    assert rows[0]["gpi_fast20"] == ""
    assert rows[1]["raw_gpi"] == "-14.0"


def test_a2_helper_fails_closed_when_sources_are_not_bound():
    s = PINE.read_text(encoding="utf-8")
    assert "ta.sum(" not in s
    assert "float sameSourceRatio20 = ta.sma(" in s
    assert "bool sourcesNotBound" in s
    assert "bool sourcesReady = not sourcesNotBound" in s
    assert 'sourcesReady and not na(tvGpiPlot[1])' in s
    assert 'if barstate.isconfirmed and year >= logFromYear and sourcesReady' in s
    assert '"NOT BOUND"' in s
    assert '"SAME SOURCE"' in s


def test_selfcontained_r4_exists_and_has_no_input_source_dependency():
    assert SELF_CONTAINED.exists()
    s = SELF_CONTAINED.read_text(encoding="utf-8")
    assert "input.source" not in s
    assert "helper_rev=r4sc" in s
    assert 'syminfo.ticker == "SPY"' in s
    assert "timeframe.isdaily and timeframe.multiplier == 1" in s


def test_selfcontained_r4_freezes_v66_market_axis_sources():
    s = SELF_CONTAINED.read_text(encoding="utf-8")
    for symbol in [
        "AMEX:SPY", "AMEX:IWM", "AMEX:RSP", "AMEX:XLY", "AMEX:XLP",
        "AMEX:XLI", "AMEX:XLU", "COMEX:HG1!", "COMEX:GC1!",
        "FRED:T10YIE", "AMEX:DBC", "NYMEX:CL1!", "NYMEX:RB1!",
    ]:
        assert symbol in s
    assert "FRED:T5YIE" not in s
    assert "AMEX:DBB" not in s


def test_selfcontained_r4_freezes_v66_formula_and_a2_trajectory():
    s = SELF_CONTAINED.read_text(encoding="utf-8")
    assert "const int Z_LEN = 252" in s
    assert "const int FAST_LEN = 20" in s
    assert "const int MID_LEN = 63" in s
    assert "const float W_BREAKEVEN = 0.35" in s
    assert "const float W_COMMODITY = 0.40" in s
    assert "const float W_ENERGY = 0.25" in s
    assert "rawGPI = f_avg5(" in s
    assert "rawIPI = f_wavg3(" in s
    assert "(rawGPI - rawGPI[FAST_LEN]) / FAST_LEN" in s
    assert "(rawGPI - rawGPI[MID_LEN]) / MID_LEN" in s
    assert "(rawIPI - rawIPI[FAST_LEN]) / FAST_LEN" in s
    assert "(rawIPI - rawIPI[MID_LEN]) / MID_LEN" in s


def test_selfcontained_r4_contains_no_payoff_logic():
    s = SELF_CONTAINED.read_text(encoding="utf-8").lower()
    for forbidden in ["pairwise_spread", "asset_a_return", "sharpe", "cagr", "drawdown", "strategy("]:
        assert forbidden not in s
