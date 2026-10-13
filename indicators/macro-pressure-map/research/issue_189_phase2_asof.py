#!/usr/bin/env python3
"""Issue #189 Phase 2 — as-of vintage engine (imports FROZEN #160 code).

Pure, testable functions over vintage columns. No network. No asset returns.
No G5: engine REFUSES complete nine-state output without all five Growth roles.
"""
import math
import sys

sys.path.insert(0, "indicators/macro-pressure-map/research")
from issue_160_deep_history_v01 import (
    build_roles, pressure_score, shift_month, is_fin, NAN,
    LOOKBACK, SMA_FAST, SMA_SLOW,
)

MAX_OFFSETS = 74
MIN_OBS = 75

# Feed -> role input kind. Levels need 12m% computed (documented substitution
# for native-YoY roles); G3/G4 compute YoY exactly as frozen #160 does.
ROLE_KIND = {
    "G1": "yoy12", "G2": "level", "G3": "level12",
    "I1": "yoy12", "I2": "yoy12", "I3": "yoy12", "I4": "yoy12", "I5": "yoy12",
}  # G4n/G4d pass through as levels (frozen build_roles real-orders them itself)


def yoy12(levels):
    """levels: {ym: value} month keys. Returns {ym: 12m% or NAN}."""
    out = {}
    for ym, v in levels.items():
        y, m = int(ym[:4]), int(ym[5:7]) - 12
        while m < 1:
            m += 12
            y -= 1
        base = levels.get(f"{y:04d}-{m:02d}")
        if is_fin(v) and is_fin(base) and base != 0:
            out[ym] = 100.0 * (v - base) / base
        else:
            out[ym] = NAN
    return out


def latest_wins(columns, decision_ym):
    """columns: list of (vintage_ym, {obs_ym: value}). Returns {obs: value}
    using the newest vintage <= decision month. Never touches future vintages.
    Months are YYYY-MM strings (vintage month granularity, conservative)."""
    best = {}
    for vintage_ym, obs in columns:
        if vintage_ym > decision_ym:
            continue
        for m, v in obs.items():
            if m not in best or vintage_ym >= best[m][0]:
                best[m] = (vintage_ym, v)
    return {m: v for m, (_, v) in best.items()}


def asof_raw_10(feed_levels, decision_ym):
    """feed_levels: {role: {obs_ym: level}}. Returns TV-ticker-keyed raw dict
    for frozen build_roles, WITHOUT G5 (G5 key absent -> build_roles yields
    no complete Growth composite; callers must refuse nine-state output)."""
    from issue_160_deep_history_v01 import (
        T_G1, T_BP, T_DPI, T_PCEPI, T_G2, T_I1, T_I2, T_I3, T_I4, T_I5,
    )
    tickers = {
        "G1": T_G1, "G2": T_G2, "G3": T_BP, "G4n": T_DPI, "G4d": T_PCEPI,
        "I1": T_I1, "I2": T_I2, "I3": T_I3, "I4": T_I4, "I5": T_I5,
    }
    raw = {}
    for role, tic in tickers.items():
        lv = feed_levels.get(role, {})
        base = role[:-1] if role in ("G4n", "G4d") else role  # G4 legs pass through as levels
        kind = ROLE_KIND.get(base, "level")
        if kind == "level":
            vals = lv
        elif kind in ("yoy12", "level12"):
            vals = yoy12(lv)
        else:
            vals = lv
        raw[tic] = {"data": ",".join(
            f"{m}-01:{vals[m]:.10f}" for m in sorted(vals) if is_fin(vals[m]))}
    return raw


def real_dpi_levels(nom, dfx):
    """Frozen G4 order: real = nominal/deflator (levels), YoY later."""
    out = {}
    for m, v in nom.items():
        d = dfx.get(m)
        if is_fin(v) and is_fin(d) and d != 0:
            out[m] = v / d
        else:
            out[m] = NAN
    return out


def warmup_ok(months_present, scored_month):
    """True iff >=75 raw obs ending at scored month with no blocking gap.
    months_present: sorted list of raw YYYY-MM available. Conservative rule:
    requires the 75-month span [scored-74m, scored] fully present."""
    y, m = int(scored_month[:4]), int(scored_month[5:7])
    need = set()
    for k in range(75):
        mm = m - k
        yy = y
        while mm < 1:
            mm += 12
            yy -= 1
        need.add(f"{yy:04d}-{mm:02d}")
    return need.issubset(set(months_present))


def refuse_nine_state(roles_present):
    """Fail-closed: without all five Growth roles verified, no complete state."""
    return set(["G1", "G2", "G3", "G4", "G5"]).issubset(set(roles_present))
