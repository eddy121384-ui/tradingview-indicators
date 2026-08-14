#!/usr/bin/env python3
"""Frozen Python research mirror of Macro Pressure Map V6.6 (Issue #59).

Source of truth:
indicators/macro-pressure-map/src/macro-pressure-map-v6.6.pine

Do not tune this mirror in response to historical results. Any redesign belongs
in a later V6.7 issue.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class V66Config:
    z_len_daily: int = 252
    z_len_weekly: int = 156
    z_len_macro: int = 60
    fast_len: int = 20
    mid_len: int = 63

    use_macro_data: bool = False
    use_official_fci: bool = False
    use_t5yie: bool = False
    use_industrial_metals_in_ipi: bool = False
    use_kre_stress_addon: bool = False
    use_smoothing: bool = True
    smooth_len: int = 5

    growth_threshold: float = 10.0
    inflation_threshold: float = 10.0
    growth_extreme_threshold: float = 60.0
    inflation_extreme_threshold: float = 60.0
    fc_threshold: float = 30.0
    stress_threshold: float = 60.0

    w_credit_stress: float = 0.40
    w_rates_dollar: float = 0.35
    w_vol_shock: float = 0.25

    w_breakeven: float = 0.35
    w_commodity: float = 0.40
    w_energy: float = 0.25
    w_industrial_metals: float = 0.10

    w_gpi_market: float = 0.70
    w_gpi_macro: float = 0.30
    w_ipi_market: float = 0.70
    w_ipi_macro: float = 0.30
    w_fcpi_market: float = 0.80
    w_fcpi_official: float = 0.20


SOURCE_COLUMNS = (
    "spy", "iwm", "rsp", "xly", "xlp", "xli", "xlu", "copper", "gold",
    "breakeven_10y", "breakeven_5y", "oil", "gasoline", "commodity_basket",
    "industrial_metals", "dxy", "vix", "move", "hyg", "ief", "kre",
    "hy_oas", "real_yield", "nfci", "stlfsi", "pmi", "cfnai",
    "building_permits", "initial_claims", "unemployment", "cpi", "core_cpi",
    "pce", "core_pce", "ppi", "wage",
)


def prepare_sources(frame: pd.DataFrame) -> pd.DataFrame:
    """Approximate request.security(..., gaps_off) on an aligned daily index."""
    out = frame.sort_index().copy()
    for col in SOURCE_COLUMNS:
        if col not in out:
            out[col] = np.nan
        out[col] = pd.to_numeric(out[col], errors="coerce").astype(float)
    out[list(SOURCE_COLUMNS)] = out[list(SOURCE_COLUMNS)].ffill()
    return out


def safe_ratio(a: pd.Series, b: pd.Series) -> pd.Series:
    return (a / b).where(a.notna() & b.notna() & (b != 0.0))


def zscore(src: pd.Series, length: int) -> pd.Series:
    mean = src.rolling(length, min_periods=length).mean()
    # Pine ta.stdev defaults to biased=true, so ddof=0.
    sd = src.rolling(length, min_periods=length).std(ddof=0)
    return ((src - mean) / sd).where(src.notna() & mean.notna() & sd.notna() & (sd != 0.0))


def _tanh_scalar(x: float) -> float:
    if pd.isna(x):
        return np.nan
    if x > 10.0:
        return 1.0
    if x < -10.0:
        return -1.0
    e2x = math.exp(2.0 * float(x))
    return (e2x - 1.0) / (e2x + 1.0)


def pine_tanh(src: pd.Series) -> pd.Series:
    return src.map(_tanh_scalar).astype(float)


def roc_percent(src: pd.Series, length: int) -> pd.Series:
    prev = src.shift(length)
    return (100.0 * (src - prev) / prev).where(src.notna() & prev.notna() & (prev != 0.0))


def component_score(src: pd.Series, invert: bool, z_len: int, cfg: V66Config) -> pd.Series:
    """Mirror Pine f_componentScore()."""
    lvl = zscore(src, z_len)
    mom_raw = 0.6 * roc_percent(src, cfg.fast_len) + 0.4 * roc_percent(src, cfg.mid_len)
    mom = zscore(mom_raw, z_len)

    sd = src.rolling(z_len, min_periods=z_len).std(ddof=0)
    fast = src.rolling(cfg.fast_len, min_periods=cfg.fast_len).mean()
    mid = src.rolling(cfg.mid_len, min_periods=cfg.mid_len).mean()
    direction = pine_tanh(((fast - mid) / sd).where(sd.notna() & (sd != 0.0)))

    raw = (0.5 * lvl + 0.3 * mom + 0.2 * direction).where(
        lvl.notna() & mom.notna() & direction.notna()
    )
    scaled = 100.0 * pine_tanh(raw / 2.0)
    return -scaled if invert else scaled


def avg_series(items: Iterable[pd.Series]) -> pd.Series:
    items = list(items)
    if not items:
        raise ValueError("avg_series requires at least one series")
    return pd.concat(items, axis=1).mean(axis=1, skipna=True)


def weighted_avg_series(items: Iterable[tuple[pd.Series, float]]) -> pd.Series:
    items = list(items)
    if not items:
        raise ValueError("weighted_avg_series requires at least one series")
    index = items[0][0].index
    num = pd.Series(0.0, index=index)
    den = pd.Series(0.0, index=index)
    for series, weight in items:
        if weight <= 0.0:
            continue
        valid = series.notna()
        num += series.fillna(0.0) * weight
        den += valid.astype(float) * weight
    return (num / den).where(den > 0.0)


def pine_ema(src: pd.Series, length: int) -> pd.Series:
    """Recursive EMA used only for displayed plot lines, not regime states."""
    alpha = 2.0 / (length + 1.0)
    result = []
    prev = np.nan
    for value in src.to_numpy(float):
        if np.isnan(value):
            result.append(prev)
            continue
        prev = value if np.isnan(prev) else alpha * value + (1.0 - alpha) * prev
        result.append(prev)
    return pd.Series(result, index=src.index, dtype=float)


def gpi_state(v: float, c: V66Config) -> str:
    if pd.isna(v): return "n/a"
    if v >= c.growth_extreme_threshold: return "Growth Euphoria"
    if v <= -c.growth_extreme_threshold: return "Severe Slowdown"
    if v > c.growth_threshold: return "Mild Growth"
    if v < -c.growth_threshold: return "Mild Slowdown"
    return "Growth Neutral"


def ipi_state(v: float, c: V66Config) -> str:
    if pd.isna(v): return "n/a"
    if v >= c.inflation_extreme_threshold: return "Inflation Shock"
    if v <= -c.inflation_extreme_threshold: return "Deflation Pressure"
    if v > c.inflation_threshold: return "Inflation Rising"
    if v < -c.inflation_threshold: return "Inflation Cooling"
    return "Stable Inflation"


def fcpi_state(v: float, c: V66Config) -> str:
    if pd.isna(v): return "n/a"
    if v >= c.stress_threshold: return "Financial Stress"
    if v <= -c.stress_threshold: return "Very Loose Conditions"
    if v > c.fc_threshold: return "Conditions Tightening"
    if v < -c.fc_threshold: return "Conditions Easing"
    return "Neutral Conditions"


def core_regime(g: float, i: float, c: V66Config) -> str:
    if pd.isna(g) or pd.isna(i): return "n/a"
    gp, gn = g > c.growth_threshold, g < -c.growth_threshold
    ip, inn = i > c.inflation_threshold, i < -c.inflation_threshold
    if gp and inn: return "Goldilocks / Disinflationary Expansion"
    if gp and not ip and not inn: return "Benign Expansion / Stable Inflation"
    if gp and ip: return "Reflation / Inflation Rising"
    if not gp and not gn and inn: return "Disinflationary Drift"
    if not gp and not gn and not ip and not inn: return "Neutral / Range-bound Macro"
    if not gp and not gn and ip: return "Inflation Pressure without Growth Confirmation"
    if gn and inn: return "Slowdown / Disinflation"
    if gn and not ip and not inn: return "Growth Slowdown / Stable Inflation"
    return "Stagflation Pressure"


def risk_note(g: float, i: float, f: float, c: V66Config) -> str:
    if pd.isna(g) or pd.isna(i) or pd.isna(f): return "n/a"
    if f >= c.stress_threshold: return "Financial stress overrides risk appetite"
    if i >= c.inflation_extreme_threshold and g <= c.growth_threshold:
        return "Inflation shock without strong growth confirmation"
    if ((g >= c.growth_extreme_threshold and i >= c.inflation_threshold)
            or (g > c.growth_threshold and i >= c.inflation_extreme_threshold)):
        return "Overheating risk rising"
    if g <= -c.growth_extreme_threshold: return "Severe growth slowdown risk"
    if i <= -c.inflation_extreme_threshold: return "Deflation or demand destruction risk"
    return "No major overlay"


def risk_posture(f: float, c: V66Config) -> str:
    if pd.isna(f): return "n/a"
    if f >= c.stress_threshold: return "Defensive posture"
    if f > c.fc_threshold: return "Risk budget reduced"
    if f < -c.fc_threshold: return "Risk-on allowed"
    return "Standard risk budget"


def compute_v66(frame: pd.DataFrame, config: V66Config | None = None) -> pd.DataFrame:
    """Compute the frozen V6.6 mirror from aligned source series."""
    c = config or V66Config()
    s = prepare_sources(frame)
    o = pd.DataFrame(index=s.index)

    # Ratios
    for name, a, b in (
        ("iwm_spy_ratio", "iwm", "spy"),
        ("rsp_spy_ratio", "rsp", "spy"),
        ("xly_xlp_ratio", "xly", "xlp"),
        ("xli_xlu_ratio", "xli", "xlu"),
        ("copper_gold_ratio", "copper", "gold"),
        ("hyg_ief_ratio", "hyg", "ief"),
        ("kre_spy_ratio", "kre", "spy"),
    ):
        o[name] = safe_ratio(s[a], s[b])

    # GPI
    for name, src in (
        ("score_iwm_spy", o["iwm_spy_ratio"]),
        ("score_rsp_spy", o["rsp_spy_ratio"]),
        ("score_xly_xlp", o["xly_xlp_ratio"]),
        ("score_xli_xlu", o["xli_xlu_ratio"]),
        ("score_copper_gold", o["copper_gold_ratio"]),
    ):
        o[name] = component_score(src, False, c.z_len_daily, c)

    # IPI
    o["score_t10yie"] = component_score(s["breakeven_10y"], False, c.z_len_daily, c)
    o["score_t5yie"] = component_score(s["breakeven_5y"], False, c.z_len_daily, c)
    o["score_breakeven_pressure"] = (
        avg_series([o["score_t10yie"], o["score_t5yie"]]) if c.use_t5yie else o["score_t10yie"]
    )
    for name, src in (
        ("score_commodity_basket", s["commodity_basket"]),
        ("score_oil", s["oil"]),
        ("score_gasoline", s["gasoline"]),
        ("score_industrial_metals", s["industrial_metals"]),
    ):
        o[name] = component_score(src, False, c.z_len_daily, c)
    o["score_energy_pressure"] = avg_series([o["score_oil"], o["score_gasoline"]])

    # FCPI
    o["score_hy_oas"] = component_score(s["hy_oas"], False, c.z_len_daily, c)
    o["score_hyg_ief_reversed"] = component_score(o["hyg_ief_ratio"], True, c.z_len_daily, c)
    o["score_kre_spy_reversed"] = component_score(o["kre_spy_ratio"], True, c.z_len_daily, c)
    for name, src in (
        ("score_real_yield", s["real_yield"]),
        ("score_dxy", s["dxy"]),
        ("score_vix", s["vix"]),
        ("score_move", s["move"]),
    ):
        o[name] = component_score(src, False, c.z_len_daily, c)

    # Macro / official optional paths
    macro_specs = {
        "score_pmi": ("pmi", False), "score_cfnai": ("cfnai", False),
        "score_building_permits": ("building_permits", False),
        "score_initial_claims_reversed": ("initial_claims", True),
        "score_unemployment_reversed": ("unemployment", True),
        "score_cpi": ("cpi", False), "score_core_cpi": ("core_cpi", False),
        "score_pce": ("pce", False), "score_core_pce": ("core_pce", False),
        "score_ppi": ("ppi", False), "score_wage": ("wage", False),
    }
    for name, (col, invert) in macro_specs.items():
        o[name] = component_score(s[col], invert, c.z_len_macro, c)
    o["score_nfci"] = component_score(s["nfci"], False, c.z_len_weekly, c)
    o["score_stlfsi"] = component_score(s["stlfsi"], False, c.z_len_weekly, c)

    o["gpi_market"] = avg_series([o[x] for x in (
        "score_iwm_spy", "score_rsp_spy", "score_xly_xlp", "score_xli_xlu", "score_copper_gold"
    )])
    o["gpi_macro"] = avg_series([o[x] for x in (
        "score_pmi", "score_cfnai", "score_building_permits",
        "score_initial_claims_reversed", "score_unemployment_reversed"
    )])
    o["GPI"] = (weighted_avg_series([(o["gpi_market"], c.w_gpi_market),
                                     (o["gpi_macro"], c.w_gpi_macro)])
                if c.use_macro_data else o["gpi_market"])

    o["ipi_market_base"] = weighted_avg_series([
        (o["score_breakeven_pressure"], c.w_breakeven),
        (o["score_commodity_basket"], c.w_commodity),
        (o["score_energy_pressure"], c.w_energy),
    ])
    o["ipi_market_with_metals"] = weighted_avg_series([
        (o["score_breakeven_pressure"], c.w_breakeven),
        (o["score_commodity_basket"], c.w_commodity),
        (o["score_energy_pressure"], c.w_energy),
        (o["score_industrial_metals"], c.w_industrial_metals),
    ])
    o["ipi_market"] = o["ipi_market_with_metals"] if c.use_industrial_metals_in_ipi else o["ipi_market_base"]
    o["ipi_macro"] = avg_series([o[x] for x in (
        "score_cpi", "score_core_cpi", "score_pce", "score_core_pce", "score_ppi", "score_wage"
    )])
    o["IPI"] = (weighted_avg_series([(o["ipi_market"], c.w_ipi_market),
                                     (o["ipi_macro"], c.w_ipi_macro)])
                if c.use_macro_data else o["ipi_market"])

    o["credit_stress_base"] = avg_series([o["score_hy_oas"], o["score_hyg_ief_reversed"]])
    o["credit_stress_with_kre"] = weighted_avg_series([
        (o["score_hy_oas"], 0.45), (o["score_hyg_ief_reversed"], 0.45),
        (o["score_kre_spy_reversed"], 0.10),
    ])
    o["CreditStress"] = o["credit_stress_with_kre"] if c.use_kre_stress_addon else o["credit_stress_base"]
    o["RatesDollarConstraint"] = avg_series([o["score_real_yield"], o["score_dxy"]])
    o["VolatilityShock"] = avg_series([o["score_vix"], o["score_move"]])
    o["fcpi_market"] = weighted_avg_series([
        (o["CreditStress"], c.w_credit_stress),
        (o["RatesDollarConstraint"], c.w_rates_dollar),
        (o["VolatilityShock"], c.w_vol_shock),
    ])
    o["fcpi_official"] = avg_series([o["score_nfci"], o["score_stlfsi"]])
    o["FCPI"] = (weighted_avg_series([(o["fcpi_market"], c.w_fcpi_market),
                                      (o["fcpi_official"], c.w_fcpi_official)])
                 if c.use_official_fci else o["fcpi_market"])

    # The dashboard uses raw axes; only plotted lines are smoothed.
    for axis in ("GPI", "IPI", "FCPI"):
        o[f"plot_{axis}"] = pine_ema(o[axis], c.smooth_len) if c.use_smoothing else o[axis]

    o["gpi_state"] = [gpi_state(v, c) for v in o["GPI"]]
    o["ipi_state"] = [ipi_state(v, c) for v in o["IPI"]]
    o["fcpi_state"] = [fcpi_state(v, c) for v in o["FCPI"]]
    o["core_regime"] = [core_regime(g, i, c) for g, i in zip(o["GPI"], o["IPI"])]
    o["risk_note"] = [risk_note(g, i, f, c) for g, i, f in zip(o["GPI"], o["IPI"], o["FCPI"])]
    o["risk_posture"] = [risk_posture(f, c) for f in o["FCPI"]]
    return o
