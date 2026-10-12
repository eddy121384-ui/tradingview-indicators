#!/usr/bin/env node
// Issue #189 Phase 1B — addendum consistency tests (no returns, no network,
// no parent writes). Run: node test_issue_189_phase1b.mjs
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

const ROOT = process.cwd();
const RES = path.join(ROOT, "indicators/macro-pressure-map/research");
const P1B = path.join(RES, "generated/issue-189/phase1b");

// 1. originals frozen: prereg + Phase 1 finding + Phase 1 outputs untouched
{
  const st = execFileSync("git", ["status", "--short"], { cwd: ROOT }).toString();
  for (const l of st.trim().split("\n").filter(Boolean)) {
    assert.ok(l.includes("issue-189") || l.includes("issue_189"), "non-189 path touched: " + l);
  }
  const diff = execFileSync("git", ["diff", "--name-only", "HEAD"], { cwd: ROOT }).toString();
  assert.ok(!diff.includes("issue-189-pit-prereg.md"), "prereg modified");
  assert.ok(!diff.includes("issue-189-pit-feasibility-finding.md"), "Phase 1 finding modified");
  const diffCached = execFileSync("git", ["diff", "--cached", "--name-only"], { cwd: ROOT }).toString();
  const orig = ["generated/issue-189/source-manifest.csv", "generated/issue-189/vintage-coverage.csv", "generated/issue-189/publication-lag-audit.csv", "generated/issue-189/feasibility-summary.json"];
  for (const f of orig) assert.ok(!diffCached.includes(f), "Phase 1 output modified: " + f);
}
// 2. ISM spot evidence: required months + revision delta present, no database claim
{
  const t = fs.readFileSync(path.join(P1B, "ism-spot-evidence.csv"), "utf8");
  assert.ok(t.includes("2008-03") && t.includes("46.5"), "Mar-2008 value missing");
  assert.ok(t.includes("2009-02") && t.includes("33.1") && t.includes("32.8"), "Feb-2009 values missing");
  assert.ok(t.includes("not a vintage series"), "database disclaimer missing");
  assert.ok(!/continuous.*database|complete.*database/i.test(t.replace(/not a vintage series/g, "")), "must not claim a database");
}
// 3. ladder: 11 roles, closed L0-L3 set, G5 at L0, L3 count zero
{
  const t = fs.readFileSync(path.join(P1B, "confirmation-ladder.csv"), "utf8").trim().split("\n");
  assert.strictEqual(t.length, 12);
  const lv = t.slice(1).map((l) => l.split(",")[1]);
  assert.ok(lv.every((v) => ["L0", "L1", "L2", "L3"].includes(v)));
  assert.strictEqual(t.filter((l) => l.startsWith("G5,"))[0].split(",")[1], "L0");
  assert.strictEqual(lv.filter((v) => v === "L3").length, 0);
}
// 4. v2 summary: verdict label unchanged, blockers explicit
{
  const s = JSON.parse(fs.readFileSync(path.join(P1B, "feasibility-summary-v2.json"), "utf8"));
  assert.strictEqual(s.verdict, "partially_feasible");
  assert.strictEqual(s.etf_full_pit_identifiable, false);
  assert.strictEqual(s.etf_2006_2026_identifiable_roles, 10);
  assert.strictEqual(s.production_authorized, false);
}
// 5. correction JSON: warmup withdrawal + convention evidence present
{
  const s = JSON.parse(fs.readFileSync(path.join(P1B, "vintage-observation-correction.json"), "utf8"));
  assert.ok(JSON.stringify(s).includes("WITHDRAWN"));
  assert.ok(s.etf_window_2006_2026_roles.G5 === false);
  assert.strictEqual(Object.keys(s.etf_window_2006_2026_roles).filter((k) => s.etf_window_2006_2026_roles[k] === true).length, 10);
}
// 6. no return-file references in any phase1b file (filenames + contents)
{
  const ban = ["port" + "_ret", "impl" + "_pre", "monthly" + "-returns", "backtest" + "-monthly", "spx" + "-monthly", "spx" + "-daily"];
  const walk = (d) => fs.readdirSync(d, { withFileTypes: true }).flatMap((e) => e.isDirectory() ? walk(path.join(d, e.name)) : [path.join(d, e.name)]);
  for (const f of walk(P1B)) {
    const c = fs.readFileSync(f, "utf8");
    for (const b of ban) assert.ok(!c.includes(b) && !f.includes(b), "return reference in " + f + ": " + b);
  }
  const add = fs.readFileSync(path.join(RES, "decisions/issue-189-phase1b-evidence-addendum.md"), "utf8");
  for (const b of ban) assert.ok(!add.includes(b), "return reference in addendum: " + b);
}
console.log("6 Phase-1B consistency checks PASS");
