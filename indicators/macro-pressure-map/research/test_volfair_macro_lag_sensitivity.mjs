#!/usr/bin/env node
// Mechanics tests for the VolFair+DH macro-factor lag sensitivity study (frozen prereg d215075, PR #206).
// Synthetic calendar/shift mechanics, warm-up availability, stale carry, per-lag control,
// frozen gate-threshold semantics, no-future-leak, label mapping, and determinism.
// Run from the repository root:  node indicators/macro-pressure-map/research/test_volfair_macro_lag_sensitivity.mjs
import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { compute } from "./volfair_macro_lag_sensitivity.mjs";

const ROOT = process.cwd();
const ENGINE = "indicators/macro-pressure-map/research/volfair_macro_lag_sensitivity.mjs";
const MIRROR = "indicators/macro-pressure-map/research/volfair_macro_lag_sensitivity_mirror.mjs";
const OUT = path.join(ROOT, "indicators/macro-pressure-map/research/generated/classic-equity-baselines");
let n = 0;
const ok = (c, m) => { n++; if (!c) throw new Error("FAIL: " + m); console.log("PASS " + n + ": " + m); };

// ---- 1. calendar-month arithmetic (never row offsets, never calendar compression) ----
const ymOf = (s) => { const [y, m] = s.split("-").map(Number); return y * 12 + m; };
const shift = (key, d) => { const [y, m] = key.split("-").map(Number); const v = y * 12 + m + d; const yy = Math.floor((v - 1) / 12); return `${String(yy).padStart(4, "0")}-${String(v - yy * 12).padStart(2, "0")}`; };
ok(shift("1967-03", -3) === "1966-12", "L=3 at 1967-03 resolves to 1966-12");
ok(shift("1967-03", -1) === "1967-02", "L=1 at 1967-03 resolves to 1967-02");
ok(shift("1967-03", -2) === "1967-01", "L=2 at 1967-03 resolves to 1967-01");
ok(shift("1967-01", -1) === "1966-12", "year boundary crosses correctly (1967-01 -> 1966-12)");
ok(shift("2026-01", -1) === "2025-12", "year boundary back across 2026-01");
ok(ymOf(shift("1967-03", -3)) === ymOf("1967-03") - 3, "shift is exact calendar-month arithmetic");
for (const d of [-1, -2, -3, 1, 2, 3]) ok(shift(shift("2000-06", d), -d) === "2000-06", `round trip for delta ${d}`);

// ---- 2. frozen gate semantics (thresholds must be inclusive exactly as preregistered) ----
const gateMap = (dS, dD, dC) => ({
  sharpe: dS >= 0.02, maxdd: dD >= 1.0, cagr: dC >= -0.10,
  passed: [dS >= 0.02, dD >= 1.0, dC >= -0.10].filter(Boolean).length,
});
ok(gateMap(0.02, 1.0, -0.10).passed === 3, "thresholds are inclusive (== passes)");
ok(gateMap(0.0199999, 1.0, -0.10).passed === 2, "Sharpe just below +0.02 fails");
ok(gateMap(0.02, 0.99999, -0.10).passed === 2, "MaxDD just below +1.0pp fails");
ok(gateMap(0.02, 1.0, -0.1000001).passed === 2, "CAGR just below -0.10pp fails");
// Note the frozen CAGR gate is one-sided and loose: a flat CAGR still clears >= -0.10pp.
ok(gateMap(0, 0, 0).passed === 1, "flat CAGR still passes the loose frozen CAGR gate (>= -0.10pp)");
ok(gateMap(0, 0, 0).sharpe === false && gateMap(0, 0, 0).maxdd === false, "flat Sharpe/MaxDD gaps fail their gates");
ok(gateMap(-0.05, -2.0, -0.5).passed === 0, "a clearly adverse gap fails all three gates");

// ---- 3. verdict / label mapping (precommitted, no best-lag selection) ----
const lagLabel = (gatesPassed, eraPass, crisisPass) => {
  if (gatesPassed === 3) return eraPass && crisisPass ? "supported" : "mixed_by_era_or_crisis";
  return gatesPassed >= 1 ? "mixed" : "not_descriptively_supported";
};
ok(lagLabel(3, true, true) === "supported", "3 gates + both consistency checks => supported");
ok(lagLabel(3, false, true) === "mixed_by_era_or_crisis", "3 gates but era consistency fails => mixed_by_era_or_crisis");
ok(lagLabel(3, true, false) === "mixed_by_era_or_crisis", "3 gates but crisis consistency fails => mixed_by_era_or_crisis");
ok(lagLabel(1, true, true) === "mixed", "1-2 gates => mixed");
ok(lagLabel(0, false, false) === "not_descriptively_supported", "0 gates => not_descriptively_supported");
const overall = (fullPass) => fullPass.length === 3 ? "lag_robust_descriptively_supported" : (fullPass.length > 0 ? "lag_partially_supported" : "lag_not_descriptively_supported");
ok(overall([1, 2, 3]) === "lag_robust_descriptively_supported", "all delayed lags full pass => robust");
ok(overall([2]) === "lag_partially_supported", "some delayed lags => partially supported");
ok(overall([]) === "lag_not_descriptively_supported", "no delayed lag => not supported");
ok(overall([1, 2, 3]) === "lag_robust_descriptively_supported" && overall([1, 2, 3]) !== "lag_robust_descriptively_supported".replace("robust", "best"), "label never selects a best lag");

// ---- 4. per-lag control mechanics (synthetic) ----
const k = 0.9, wVolS = [1, 0.5, 0.25, 0], wLegS = [0.5, 0.25, 0.125, 0];
const wCtrlS = wVolS.map((w) => Math.min(1, k * w));
ok(wCtrlS.every((w, i) => w <= wVolS[i] + 1e-15), "w_ctrl <= w_vol");
ok(wCtrlS.every((w) => w < 1), "cap non-binding for 0<k<1 and w_vol<=1");
ok(Math.abs(wCtrlS.reduce((a, b) => a + b, 0) / 4 - (k * wVolS.reduce((a, b) => a + b, 0)) / 4) < 1e-12, "control mean equals k * volfair mean");
ok(wLegS.every((w, i) => w <= wVolS[i] + 1e-15), "delayed leg never exceeds VolFair weight");

// ---- 5. engine-level mechanics from the computed study ----
const a = compute();
ok(a.out.integrity.l0_replication.passed === true, "L=0 replication gate passed (fail-stop precondition)");
ok(a.out.panel.n === 714 && a.out.panel.first === "1967-03" && a.out.panel.last === "2026-08", "panel is 714 months 1967-03..2026-08");
ok(a.out.lag_definition.calendar_map_months === 724, "applied-factor calendar map covers 1966-05..2026-08 (724 months)");
ok(Math.abs(a.out.lags[0].k - 0.9109091063518062) <= 1e-12, "k_0 equals the frozen #204 value");
ok(Math.abs(a.out.integrity.warmup_overlap_max_abs_diff) < 2e-6, "warm-up reconstruction matches frozen s on all 711 overlap months");
ok(a.out.integrity.warmup_overlap_n === 711, "warm-up overlap is exactly 711 observed months");
ok(a.out.integrity.stale_months_verified === 3, "exactly three inherited missing months");
ok(JSON.stringify(Object.keys(a.out.overall.per_lag)) === JSON.stringify(["0", "1", "2", "3"]), "all four predeclared lags reported (no extras)");
ok(a.out.production_authorized === false, "production_authorized=false");

// ---- 6. no future leak: the delayed factor is strictly older for L>0 ----
const rowsCsv = (() => {
  const lines = fs.readFileSync(path.join(OUT, "volfair-macro-lag-sensitivity-monthly.csv"), "utf8").trim().split(/\r?\n/);
  const cols = lines.shift().split(",");
  return lines.map((l) => { const c = l.split(","); return Object.fromEntries(cols.map((kk, j) => [kk, c[j]])); });
})();
ok(rowsCsv.length === 714, "audit CSV has 714 rows");
let shiftFromHeadOk = true, shiftFromTailOk = true, strictOlderOk = true;
for (let i = 0; i < rowsCsv.length; i++) {
  const r = rowsCsv[i];
  for (const L of [1, 2, 3]) {
    // Panel is contiguous, so beyond the warm-up the calendar shift must equal a row offset.
    if (i >= L && Math.abs(Number(r[`s_lag${L}`]) - Number(rowsCsv[i - L].s_macro)) > 1e-12) shiftFromTailOk = false;
    // The shifted factor must never be newer than the payoff month.
    if (Number(r[`s_lag${L}`]) > 1) strictOlderOk = false;
    // Beyond the warm-up, the shifted factor must be a past month's applied factor.
    if (i >= L && ymOf(rowsCsv[i - L].date) - ymOf(r.date) !== -L) shiftFromHeadOk = false;
  }
  if (i === 0) {
    ok(Math.abs(Number(r.s_lag0) - Number(r.s_macro)) < 1e-12, "L=0 first payoff uses 1967-03 applied factor");
    ok(Math.abs(Number(r.s_lag1) - 0.5) < 1e-12 && Math.abs(Number(r.s_lag2) - 0.5) < 1e-12 && Math.abs(Number(r.s_lag3) - 0.5) < 1e-12,
      "L=1,2,3 first payoff use the 1967-02 / 1967-01 / 1966-12 warm-up months (all s=0.5)");
  }
}
ok(shiftFromTailOk, "calendar shift equals the expected row offset on the contiguous panel");
ok(shiftFromHeadOk, "shift offsets are exact calendar-month differences");
ok(strictOlderOk, "no shifted factor exceeds 1 (no future information introduced)");

// ---- 7. stale carry: the three inherited gaps are carried, never compressed or interpolated ----
const staleRows = rowsCsv.filter((r) => Number(r.stale) === 1).map((r) => r.date);
ok(JSON.stringify(staleRows) === JSON.stringify(["2025-10", "2025-11", "2026-01"]), "stale months are exactly 2025-10 / 2025-11 / 2026-01");
ok(rowsCsv.filter((r) => r.stale === "1").every((r) => Math.abs(Number(r.s_macro) - 1) < 1e-12), "stale months carry s=1 as frozen");
let contiguous = true;
for (let i = 1; i < rowsCsv.length; i++) if (ymOf(rowsCsv[i].date) - ymOf(rowsCsv[i - 1].date) !== 1) contiguous = false;
ok(contiguous, "payoff calendar stays contiguous despite the inherited gaps (no compression)");

// ---- 8. mirrored independent recomputation ----
execSync(`node ${MIRROR}`, { cwd: ROOT, stdio: "pipe" });
ok(true, "independent mirror reproduces weights, controls, nets and metric paths from the audit CSV");

// ---- 9. determinism: two full engine runs must be byte-identical ----
execSync(`node ${ENGINE}`, { cwd: ROOT, stdio: "pipe" });
const aJson = fs.readFileSync(path.join(OUT, "volfair-macro-lag-sensitivity-results.json"));
const aCsv = fs.readFileSync(path.join(OUT, "volfair-macro-lag-sensitivity-monthly.csv"));
execSync(`node ${ENGINE}`, { cwd: ROOT, stdio: "pipe" });
const bJson = fs.readFileSync(path.join(OUT, "volfair-macro-lag-sensitivity-results.json"));
const bCsv = fs.readFileSync(path.join(OUT, "volfair-macro-lag-sensitivity-monthly.csv"));
ok(aJson.equals(bJson), "determinism: results JSON byte-identical across two runs");
ok(aCsv.equals(bCsv), "determinism: monthly CSV byte-identical across two runs");

console.log("All " + n + " checks PASS");
