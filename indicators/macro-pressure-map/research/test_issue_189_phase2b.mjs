#!/usr/bin/env node
// Issue #189 phase2b — re-verification tests (no returns, no network).
// Run: node test_issue_189_phase2b.mjs (after phase2b pulls + analysis)
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

const ROOT = process.cwd();
const RES = path.join(ROOT, "indicators/macro-pressure-map/research");
const GEN2B = path.join(RES, "generated/issue-189/phase2b");
const mo = (d) => +d.slice(0, 4) * 12 + (+d.slice(5, 7) - 1);

// 1. no-vintage record: SOP leg documented, 404 evidence + FD/PAY boundaries
{
  const nv = JSON.parse(fs.readFileSync(path.join(GEN2B, "no-vintage.json"), "utf8"));
  const sop = nv.legs.find((l) => l.leg.includes("I3_SOP"));
  assert.ok(sop, "I3_SOP leg record missing");
  assert.ok(JSON.stringify(sop).includes("404"), "404 evidence missing");
  assert.strictEqual(sop.definition_sanity_non_pit.sop_yoy_nov_1974, 19.57);
  const fd = nv.legs.find((l) => l.leg.includes("I3_FD"));
  assert.ok(fd && JSON.stringify(fd).includes("2014-06"), "FD boundary record missing");
  const pay = nv.legs.find((l) => l.leg.includes("I4_PAY"));
  assert.ok(pay && JSON.stringify(pay).includes("2010"), "PAY boundary record missing");
}
// 2. span discipline on every pulled vintage (no post-date obs)
{
  const m = JSON.parse(fs.readFileSync(path.join(GEN2B, "vintage-manifest.json"), "utf8"));
  assert.ok(m.pulls.length > 600, "expected ~650 pulls, got " + m.pulls.length);
  assert.ok(!("aborted_at" in m), "run aborted: " + m.aborted_at);
  for (const p of m.pulls) {
    assert.ok(p.http === 200);
    assert.ok(mo(p.obs_last.slice(0, 7)) < mo(p.vintage_date.slice(0, 7)), `${p.key}@${p.vintage_date} post-date obs ${p.obs_last}`);
  }
  const keys = new Set(m.pulls.map((p) => p.key));
  assert.ok(!keys.has("I3_SOP"), "I3_SOP must have no successful pulls");
  for (const k of ["I3_FD", "I4_PAY", "I5_NSA"]) assert.ok(keys.has(k), "missing feed " + k);
}
// 3. C1 verdicts follow frozen rules (SOP UNVERIFIED without data)
{
  const v = JSON.parse(fs.readFileSync(path.join(GEN2B, "verdicts.json"), "utf8"));
  for (const k of ["I3", "I4", "I5"]) assert.ok(["CONFIRMED", "UNVERIFIED"].includes(v.roles[k]), k);
  assert.strictEqual(v.production_authorized, false);
}
// 4. C2 not-identifiable recorded (SOP gap), never silently approximated
{
  const c = JSON.parse(fs.readFileSync(path.join(GEN2B, "comparison.json"), "utf8"));
  assert.strictEqual(c.status, "not-identifiable");
  assert.ok(c.reason.includes("I3_SOP"));
}
// 5. no-return-import scan over phase2b sources
{
  const ban = ["monthly" + "-returns", "port" + "_ret", "impl" + "_pre", "backtest" + "-monthly", "spx" + "-monthly", "spx" + "-daily"];
  for (const f of ["issue_189_phase2b_pull.mjs", "issue_189_phase2b_analyze.mjs", "test_issue_189_phase2b.mjs", "issue-189-i3i4i5-reverify-prereg.md"]) {
    const c = fs.readFileSync(path.join(RES, f), "utf8");
    for (const b of ban) assert.ok(!c.includes(b), `${f}: ${b}`);
  }
}
// 6. determinism: analyzer rerun -> identical phase2b bytes (excluding manifest timestamps is NOT exempted: manifest has no timestamps except fetched_at... check)
{
  const files = ["extreme-points.json", "alt-ledger.json", "comparison.json", "revision-spreads.json", "verdicts.json"];
  const before = {};
  for (const f of files) before[f] = fs.readFileSync(path.join(GEN2B, f), "utf8");
  execFileSync("node", [path.join(RES, "issue_189_phase2b_analyze.mjs")], { cwd: ROOT, stdio: "ignore" });
  for (const f of files) {
    const after = fs.readFileSync(path.join(GEN2B, f), "utf8");
    assert.strictEqual(after, before[f], "non-deterministic: " + f);
  }
}
console.log("6 phase2b checks PASS");
