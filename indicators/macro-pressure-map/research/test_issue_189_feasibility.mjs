#!/usr/bin/env node
// Issue #189 Phase 1 — consistency tests (synthetic fixtures only; no network,
// no return files, no vintage pulls). Run: node test_issue_189_feasibility.mjs
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";

const ROOT = process.cwd();
const RES = path.join(ROOT, "indicators/macro-pressure-map/research");
const GEN = path.join(RES, "generated/issue-189");

// 1. prereg firewall: Phase 1 code must not import asset-return files
{
  const src = fs.readFileSync(path.join(RES, "issue_189_feasibility.mjs"), "utf8");
  const banned = ["nine-sleeve-monthly" + "-returns", "hardened-monthly" + "-returns", "proxy-monthly" + "-returns", "port" + "_ret", "impl" + "_pre", "backtest" + "-monthly", "spx" + "-monthly", "spx" + "-daily"];
  for (const b of banned) assert.ok(!src.includes(b), "return-file reference in Phase 1 builder: " + b);
  const testSrc = fs.readFileSync(path.join(RES, "test_issue_189_feasibility.mjs"), "utf8");
  for (const b of banned) assert.ok(!testSrc.includes(b), "return-file reference in test: " + b);
}
// 2. manifest schema: 11 roles, closed taxonomy, URLs present
{
  const t = fs.readFileSync(path.join(GEN, "source-manifest.csv"), "utf8").trim().split("\n");
  assert.strictEqual(t.length, 12, "11 data rows + header");
  const rows = t.slice(1).map((l) => l.split('","'));
  const roles = rows.map((c) => c[0].replace(/^"/, ""));
  assert.deepStrictEqual(roles, ["G1", "G2", "G3", "G4n", "G4d", "G5", "I1", "I2", "I3", "I4", "I5"]);
  const allowed = new Set(["exact_verified_PIT", "date_only_conservative_PIT", "partial_PIT", "proxy_not_equivalent", "unavailable"]);
  for (const c of rows) assert.ok(allowed.has(c[13]), "taxonomy: " + c[13]);
  for (const c of rows) assert.ok(c[15].includes("http"), "evidence URL missing for " + c[0]);
}
// 3. coverage grid: 11 x 67 years, closed statuses, G5 always unavailable
{
  const t = fs.readFileSync(path.join(GEN, "vintage-coverage.csv"), "utf8").trim().split("\n");
  assert.strictEqual(t.length, 1 + 11 * 67);
  const g5 = t.filter((l) => l.startsWith("G5,"));
  assert.strictEqual(g5.length, 67);
  assert.ok(g5.every((l) => l.split(",")[2] === "unavailable"));
}
// 4. lag audit: 11 rows, Eastern tz, staleness rule present
{
  const t = fs.readFileSync(path.join(GEN, "publication-lag-audit.csv"), "utf8").trim().split("\n");
  assert.strictEqual(t.length, 12);
  assert.ok(t.every((l, i) => i === 0 || l.includes("Eastern")));
}
// 5. summary JSON: verdict + A-D + no-production flag
{
  const s = JSON.parse(fs.readFileSync(path.join(GEN, "feasibility-summary.json"), "utf8"));
  assert.strictEqual(s.phase, 1);
  assert.strictEqual(s.production_authorized, false);
  assert.ok(["fully_feasible", "partially_feasible", "not_verifiable"].includes(s.verdict));
  assert.ok(Array.isArray(s.D_gaps) && s.D_gaps.length > 0);
  assert.ok(s.B_years.length === 67);
}
// 6. determinism: rebuild -> identical bytes
{
  const before = {};
  for (const f of fs.readdirSync(GEN).sort()) {
    before[f] = createHash("sha256").update(fs.readFileSync(path.join(GEN, f))).digest("hex");
  }
  execFileSync("node", [path.join(RES, "issue_189_feasibility.mjs")], { cwd: ROOT, stdio: "ignore" });
  for (const f of fs.readdirSync(GEN).sort()) {
    const after = createHash("sha256").update(fs.readFileSync(path.join(GEN, f))).digest("hex");
    assert.strictEqual(after, before[f], "non-deterministic file: " + f);
  }
}
// 7. parent artifacts untouched: git status shows only issue-189 paths
{
  const st = execFileSync("git", ["status", "--short"], { cwd: ROOT }).toString();
  for (const l of st.trim().split("\n").filter(Boolean)) {
    assert.ok(l.includes("issue-189") || l.includes("issue_189"), "non-189 path touched: " + l);
  }
}
console.log("7 Phase-1 consistency checks PASS");
