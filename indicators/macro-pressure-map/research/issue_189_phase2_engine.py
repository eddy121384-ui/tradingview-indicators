#!/usr/bin/env python3
"""Issue #189 Phase 2 — as-of score engine (imports FROZEN #160 code).

Reads scratch vintage columns + analyzer staleness; writes as-of ledger with
scores/states/confusion. No network. No asset returns. No G5: nine-state
output refused wherever Growth is incomplete (always, in Phase 2 scope).
"""
import json
import math
import pathlib
import sys

RES = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(RES))
from issue_160_deep_history_v01 import build_roles, pressure_score, is_fin, NAN  # noqa: E402
from issue_189_phase2_asof import latest_wins, yoy12  # noqa: E402

SCRATCH = pathlib.Path("C:/Users/EDDY/AppData/Local/Temp/opencode/issue189pit")
GEN2 = RES / "generated" / "issue-189" / "phase2"
TICK = {"G1": "USIPYY", "G2": "USUR", "G3": "USBP", "G4n": "USDPI",
        "G4d": "USPCEPI", "I1": "USIRYY", "I2": "USCPCEPIAC",
        "I3": "USPPIYY", "I4": "USWG", "I5": "USEI"}
SID = {"G1": "INDPRO", "G2": "UNRATE", "G3": "PERMIT", "G4n": "DSPI",
       "G4d": "PCEPI", "I1": "CPIAUCSL", "I2": "PCEPILFE", "I3": "PPIACO",
       "I4": "AHETPI", "I5": "CPIENGSL"}


def load_cols(sid):
    p = SCRATCH / (sid + ".jsonl")
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").strip().split("\n"):
        if not line.strip():
            continue
        o = json.loads(line)
        obs = {}
        for r in o["rows"]:
            d, v = r.split(",", 1)
            try:
                f = float(v)
            except ValueError:
                continue
            if math.isfinite(f):
                obs[d[:7]] = f
        out.append((o["vd"][:7], obs))
    return out


def band(x):
    return "Low" if x < -10 else ("High" if x > 10 else "Neutral")


def main():
    cols = {r: load_cols(SID[r]) for r in TICK}
    print("cols:", {r: len(cols[r]) for r in cols})
    stale = json.loads((GEN2 / "staleness.json").read_text(encoding="utf-8"))["rows"]
    # revised reference: frozen #160 monthly G/I
    rev = {}
    for line in (RES / "generated" / "issue-160" / "deep-history-v01-monthly.csv").read_text(encoding="utf-8").replace("\r", "").strip().split("\n")[1:]:
        c = line.split(",")
        try:
            g, v = float(c[1]), float(c[2])
        except ValueError:
            continue
        if math.isfinite(g) and math.isfinite(v):
            rev[c[0][:7]] = (g, v)
    ledger = []
    for s in stale:
        D = s["decision"][:7]
        common = s["common_obs"]
        if common is None:
            ledger.append({"decision": D, "status": "gap-no-common-month"})
            continue
        # warmup: >=75 vintage-covered raw obs at/below common per role.
        # Isolated gaps do NOT fail here: frozen last_valid skips missing
        # months (verified: single-gap warmup extends, never fills). The
        # finiteness check at the common month below is authoritative.
        ok = True
        raw_by_role = {}
        for r in TICK:
            asof = latest_wins(cols[r], D)
            have = sorted(m for m in asof if m <= common)
            if len(have) < 75:
                ok = False
                break
            raw_by_role[r] = {x: asof[x] for x in have}
        if not ok:
            ledger.append({"decision": D, "common_obs": common, "status": "gap-warmup"})
            continue
        # frozen transforms via the single shared helper (incl. present-but-empty
        # G5 key so frozen build_roles runs unmodified and fail-closes Growth)
        from issue_189_phase2_asof import asof_raw_10
        feed_levels = {r: raw_by_role[r] for r in TICK}
        raw = asof_raw_10(feed_levels)
        months, roles = build_roles(raw)
        gscores = [pressure_score(roles[g]) for g in ("G1", "G2", "G3", "G4")]
        iscores = [pressure_score(roles[i]) for i in ("I1", "I2", "I3", "I4", "I5")]
        li = months.index(common + "-01") if (common + "-01") in months else None
        if li is None:
            ledger.append({"decision": D, "common_obs": common, "status": "gap-month-grid"})
            continue
        Ivals = [s[li] for s in iscores]
        if all(is_fin(v) for v in Ivals):
            I = sum(Ivals) / 5.0
            infl_state = band(I)
        else:
            I, infl_state = float("nan"), None
        Gvals = [s[li] for s in gscores]
        g_ok = all(is_fin(v) for v in Gvals)
        if not any(is_fin(v) for v in Ivals) and not any(is_fin(v) for v in Gvals):
            ledger.append({"decision": D, "common_obs": common, "status": "gap-insufficient"})
            continue
        # nine-state refused: G5 missing (fail-closed, always in Phase 2)
        r = rev.get(common)
        rf = {"G1": is_fin(gscores[0][li]), "G2": is_fin(gscores[1][li]), "G3": is_fin(gscores[2][li]), "G4": is_fin(gscores[3][li]), "G5": False}
        ledger.append({
            "decision": D, "common_obs": common, "status": "scored-partial",
            "roles_finite": rf,
            "I_asof": I, "I_state": infl_state,
            "I_revised": r[1] if r else None,
            "I_band_revised": band(r[1]) if r else None,
            "G_partial_mean": sum(v for v in Gvals if is_fin(v)) / max(1, sum(1 for v in Gvals if is_fin(v))) if g_ok else None,
            "G_revised": r[0] if r else None,
            "nine_state": None, "nine_state_reason": "G5-unavailable-fail-closed",
        })
    GEN2.mkdir(parents=True, exist_ok=True)
    def clean(x):
        if isinstance(x, float) and not math.isfinite(x):
            return None
        if isinstance(x, dict):
            return {k: clean(v) for k, v in x.items()}
        if isinstance(x, list):
            return [clean(v) for v in x]
        return x
    (GEN2 / "asof-ledger.json").write_text(json.dumps(clean(ledger), indent=1) + "\n", encoding="utf-8")
    n_ok = sum(1 for e in ledger if e["status"] == "scored-partial")
    print(f"ledger: {len(ledger)} decisions, {n_ok} scored-partial")


if __name__ == "__main__":
    main()
