#!/usr/bin/env node
// Issue #189 Phase 2 — Node mirror (independent pressure_score reimplementation
// cross-checked against frozen Python on shared vectors; no returns, no network).
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

const ROOT = process.cwd();
const RES = path.join(ROOT, "indicators/macro-pressure-map/research");
const fin = (x) => typeof x === "number" && Number.isFinite(x);

// independent reimplementation of frozen pressure_score (LOOKBACK 60, SMA 3/12,
// weights 0.5/0.3/0.2, 100*tanh(raw/2), biased sd, causal windows)
function meanSd(a) {
  const m = a.reduce((x, y) => x + y, 0) / a.length;
  return [m, Math.sqrt(a.reduce((x, y) => x + (y - m) ** 2, 0) / a.length)];
}
function lastValid(xs, i, n) {
  const o = [];
  for (let k = i; k >= 0 && o.length < n; k--) if (fin(xs[k])) o.unshift(xs[k]);
  return o;
}
function pressureScore(xs) {
  const out = new Array(xs.length).fill(NaN);
  for (let i = 0; i < xs.length; i++) {
    if (!fin(xs[i])) continue;
    const lv = lastValid(xs, i, 60);
    if (lv.length < 60) continue;
    const [mL, sL] = meanSd(lv);
    if (sL === 0) continue;
    const lz = (xs[i] - mL) / sL;
    const d1 = fin(xs[i - 1]) ? xs[i] - xs[i - 1] : NaN;
    const d3 = fin(xs[i - 3]) ? xs[i] - xs[i - 3] : NaN;
    if (!fin(d1) || !fin(d3)) continue;
    const momRaw = 0.6 * d1 + 0.4 * (d3 / 3);
    // momentum window: value per index j<=i, needs xs[j],xs[j-1],xs[j-3]
    const mv = [];
    for (let j = 0; j <= i; j++) {
      if (fin(xs[j]) && fin(xs[j - 1]) && fin(xs[j - 3])) mv.push([j, 0.6 * (xs[j] - xs[j - 1]) + 0.4 * ((xs[j] - xs[j - 3]) / 3)]);
    }
    const mw = mv.slice(-60);
    if (mw.length < 60) continue;
    const [mM, sM] = meanSd(mw.map((p) => p[1]));
    if (sM === 0) continue;
    const mz = (momRaw - mM) / sM;
    const s3 = lastValid(xs, i, 3), s12 = lastValid(xs, i, 12);
    if (s3.length < 3 || s12.length < 12) continue;
    const dir = Math.tanh(((s3.reduce((a, x) => a + x, 0) / 3) - (s12.reduce((a, x) => a + x, 0) / 12)) / sL);
    out[i] = 100 * Math.tanh((0.5 * lz + 0.3 * mz + 0.2 * dir) / 2);
  }
  return out;
}
// T10 cross-check: shared vectors vs frozen Python implementation
{
  const py = execFileSync("C:\\Users\\EDDY\\.venvs\\shiori-bloomberg\\Scripts\\python.exe",
    ["-c", "import sys,json,math; sys.path.insert(0,'indicators/macro-pressure-map/research'); from issue_160_deep_history_v01 import pressure_score,is_fin; xs=[100+0.5*i+2*math.sin(i/3) for i in range(200)]; print(json.dumps([None if (isinstance(v,float) and math.isnan(v)) else v for v in pressure_score(xs)]))"],
    { cwd: ROOT, maxBuffer: 1 << 20 }).toString();
  const ref = JSON.parse(py).map((v) => (v === null ? NaN : v));
  const xs = Array.from({ length: 200 }, (_, i) => 100 + 0.5 * i + 2 * Math.sin(i / 3));
  const got = pressureScore(xs);
  assert.strictEqual(got.length, ref.length);
  let maxd = 0, n = 0;
  for (let i = 0; i < got.length; i++) {
    if (fin(got[i]) && fin(ref[i])) { maxd = Math.max(maxd, Math.abs(got[i] - ref[i])); n++; }
    else assert.ok(!fin(got[i]) && !fin(ref[i]), "finite-mismatch at " + i);
  }
  assert.ok(n > 100 && maxd < 1e-9, `cross-check n=${n} maxdiff=${maxd}`);
  console.log(`T10 cross-check PASS (n=${n}, maxdiff=${maxd.toExponential(1)})`);
}
// T1 span discipline on frozen Phase 1C evidence (no post-date obs)
{
  const s = JSON.parse(fs.readFileSync(path.join(RES, "generated/issue-189/phase1c/alfred-vintage-spans.json"), "utf8"));
  assert.strictEqual(s.pulls.length, 28);
  const mo = (d) => +d.slice(0, 4) * 12 + (+d.slice(5, 7) - 1);
  for (const p of s.pulls) assert.ok(mo(p.obs_last.slice(0, 7)) < mo(p.requested_vintage.slice(0, 7)), p.series + "@" + p.requested_vintage);
  console.log("T1 span discipline PASS (28 pulls, no post-date obs)");
}
// T9 no-return-import scan over Phase 2 sources
{
  const ban = ["monthly" + "-returns", "port" + "_ret", "impl" + "_pre", "backtest" + "-monthly", "spx" + "-monthly", "spx" + "-daily"];
  for (const f of ["issue_189_phase2_asof.py", "test_issue_189_phase2.py", "test_issue_189_phase2_mirror.mjs", "issue-189-phase2-execution-manifest.md"]) {
    const c = fs.readFileSync(path.join(RES, f), "utf8");
    for (const b of ban) assert.ok(!c.includes(b), `${f}: ${b}`);
  }
  console.log("T9 no-return-import scan PASS");
}
// T11 phase2 artifacts: schema + fail-closed invariants (structural, not value-pinned)
{
  const D = path.join(RES, "generated/issue-189/phase2");
  for (const f of ["vintage-manifest.json", "staleness.json", "revision-impact.json", "revision-yoy.json", "definition-checks.json", "coverage.json", "asof-ledger.json", "g5-spots.json", "summary.json"]) {
    assert.ok(fs.existsSync(path.join(D, f)), "missing artifact: " + f);
  }
  const L = JSON.parse(fs.readFileSync(path.join(D, "asof-ledger.json"), "utf8"));
  assert.strictEqual(L.length, 243);
  assert.ok(L.every((e) => e.nine_state === null && e.nine_state_reason === "G5-unavailable-fail-closed"), "nine-state must be refused everywhere");
  assert.ok(L.every((e) => e.roles_finite && e.roles_finite.G5 === false), "G5 finite flag must be false");
  const S = JSON.parse(fs.readFileSync(path.join(D, "summary.json"), "utf8"));
  assert.strictEqual(S.nine_state_months, 0);
  assert.strictEqual(S.production_authorized, false);
  const C = JSON.parse(fs.readFileSync(path.join(D, "coverage.json"), "utf8"));
  assert.strictEqual(C.decisions.length, 243);
  console.log("T11 phase2 artifact invariants PASS");
}
// T12 no-return-import scan over ALL Phase 2 sources (incl. analyzer/engine/finding)
{
  const ban = ["monthly" + "-returns", "port" + "_ret", "impl" + "_pre", "backtest" + "-monthly", "spx" + "-monthly", "spx" + "-daily"];
  const files = ["issue_189_phase2_pull.mjs", "issue_189_phase2_analyze.mjs", "issue_189_phase2_engine.py", "issue_189_phase2_asof.py", "issue_189_phase2_revyoy.mjs", "test_issue_189_phase2.py", "test_issue_189_phase2_mirror.mjs", "decisions/issue-189-phase2-finding.md"];
  for (const f of files) {
    const c = fs.readFileSync(path.join(RES, f), "utf8");
    for (const b of ban) assert.ok(!c.includes(b), `${f}: ${b}`);
  }
  console.log("T12 Phase-2 no-return scan PASS");
}
// T13 snapshot isolation unit: mutating later state must not leak into earlier snaps
{
  const cum = { G1: { "2000-01": ["2000-08-31", 1.0] } };
  const snap0 = { G1: Object.fromEntries(Object.entries(cum.G1).map(([m, p]) => [m, [...p]])) };
  cum.G1["2000-01"] = ["2001-08-31", 9.9];
  cum.G1["2005-01"] = ["2005-02-28", 5.0];
  assert.strictEqual(snap0.G1["2000-01"][1], 1.0);
  assert.ok(!("2005-01" in snap0.G1));
  console.log("T13 snapshot isolation PASS");
}
// T14 ledger taxonomy + pairing recompute matches summary
{
  const D = path.join(RES, "generated/issue-189/phase2");
  const L = JSON.parse(fs.readFileSync(path.join(D, "asof-ledger.json"), "utf8"));
  assert.strictEqual(L.length, 243);
  const st = {};
  for (const e of L) {
    assert.ok(["scored", "partial", "gap-no-common-month", "gap-warmup", "gap-month-grid", "gap-insufficient"].includes(e.status), e.status);
    st[e.status] = (st[e.status] || 0) + 1;
    if (e.status === "partial") assert.ok(Array.isArray(e.missing_roles) && e.missing_roles.length > 0);
    assert.strictEqual(e.nine_state, null);
  }
  const paired = L.filter((e) => Number.isFinite(e.I_asof) && e.I_band_revised);
  const ag = paired.filter((e) => e.I_state === e.I_band_revised).length;
  const S = JSON.parse(fs.readFileSync(path.join(D, "summary.json"), "utf8"));
  assert.strictEqual(S.pairing, paired.length);
  assert.strictEqual(S.agree, ag);
  assert.ok(Math.abs(S.agree / S.pairing - ag / paired.length) < 1e-12);
  console.log(`T14 taxonomy+pairing PASS (status=${JSON.stringify(st)}, agree=${ag}/${paired.length})`);
}
console.log("Phase 2 Node mirror PASS");
