#!/usr/bin/env node
// Issue #189 Phase 1C — correctness-audit tests (no returns, no network,
// no parent writes). Run: node test_issue_189_phase1c.mjs
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

const ROOT = process.cwd();
const RES = path.join(ROOT, "indicators/macro-pressure-map/research");
const P1C = path.join(RES, "generated/issue-189/phase1c");

// 1. originals frozen: prereg + findings + Phase 1/1B outputs untouched
{
  const status = () => execFileSync("git", ["status", "--short"], { cwd: ROOT }).toString();
  for (const l of status().trim().split("\n").filter(Boolean)) {
    if (l.includes("__pycache__")) continue;
    assert.ok(l.includes("issue-189") || l.includes("issue_189"), "non-189 path touched: " + l);
  }
  for (const args of [["diff", "--name-only", "HEAD"], ["diff", "--cached", "--name-only"]]) {
    const d = execFileSync("git", args, { cwd: ROOT }).toString();
    for (const f of ["issue-189-pit-prereg.md", "issue-189-pit-feasibility-finding.md", "issue-189-phase1b-evidence-addendum.md", "generated/issue-189/source-manifest.csv", "generated/issue-189/vintage-coverage.csv", "generated/issue-189/publication-lag-audit.csv", "generated/issue-189/feasibility-summary.json", "generated/issue-189/phase1b/"]) {
      assert.ok(!d.includes(f), "frozen original modified: " + f);
    }
  }
}
// 2. vintage spans: 28 pulls, all HTTP 200, exact-date headers
{
  const s = JSON.parse(fs.readFileSync(path.join(P1C, "alfred-vintage-spans.json"), "utf8"));
  assert.strictEqual(s.pulls.length, 28);
  assert.ok(s.pulls.every((p) => p.http === 200));
  assert.ok(s.pulls.every((p) => p.obs_rows > 0 && p.sha256 && p.bytes > 100));
}
// 3. Q1 contradiction test: NO vintage contains any post-date observation;
//    specifically nothing like 2003 obs inside a 2000 vintage
{
  const s = JSON.parse(fs.readFileSync(path.join(P1C, "alfred-vintage-spans.json"), "utf8"));
  const mo = (d) => +d.slice(0, 4) * 12 + (+d.slice(5, 7) - 1);
  for (const p of s.pulls) {
    const vd = p.requested_vintage;
    assert.ok(mo(p.obs_last.slice(0, 7)) < mo(vd.slice(0, 7)), `post-date obs in ${p.series}@${vd}: last=${p.obs_last}`);
    assert.ok(!p.obs_first.startsWith("2003") || mo(vd.slice(0, 7)) > mo("2003-10"), "stale 2003 claim pattern");
  }
  // every 2000-08-01 vintage reaches series origin era (full-history convention)
  const firsts = {};
  for (const p of s.pulls.filter((p) => p.requested_vintage === "2000-08-01")) firsts[p.series] = p.obs_first;
  assert.ok(mo(firsts.PCEPILFE.slice(0, 7)) <= mo("1959-06"), "PCEPILFE first vintage must reach 1959, got " + firsts.PCEPILFE);
  assert.ok(mo(firsts.PPIACO.slice(0, 7)) <= mo("1914-01"), "PPIACO span, got " + firsts.PPIACO);
  assert.ok(mo(firsts.AHETPI.slice(0, 7)) <= mo("1964-06"), "AHETPI span, got " + firsts.AHETPI);
}
// 4. truncated early vintages are real (CPIAUCSL 1972 = 19 obs)
{
  const s = JSON.parse(fs.readFileSync(path.join(P1C, "alfred-vintage-spans.json"), "utf8"));
  const cpi72 = s.pulls.find((p) => p.series === "CPIAUCSL" && p.requested_vintage === "1972-07-21");
  assert.strictEqual(cpi72.obs_rows, 19);
  assert.strictEqual(cpi72.obs_first.slice(0, 7), "1970-12");
}
// 5. warmup verification record: 74 months + DH-start cross-check
{
  const s = JSON.parse(fs.readFileSync(path.join(P1C, "warmup-verification.json"), "utf8"));
  assert.strictEqual(s.warmup_raw_months_minimum, 74);
  assert.ok(s.verified_against.includes("pressure_score"));
  assert.strictEqual(s.synthetic_results.g3_style_first_finite_raw_index, 74);
}
// 6. warmup script reruns green against frozen code (venv python)
{
  const out = execFileSync("C:\\Users\\EDDY\\.venvs\\shiori-bloomberg\\Scripts\\python.exe", [path.join(RES, "issue_189_phase1c_warmup.py")], { cwd: ROOT }).toString();
  assert.ok(out.includes("first finite raw index: 74"), "warmup rerun diverged:\n" + out);
}
// 7. no return-file references in any phase1c file (names + contents)
{
  const ban = ["port" + "_ret", "impl" + "_pre", "monthly" + "-returns", "backtest" + "-monthly", "spx" + "-monthly", "spx" + "-daily", "sharpe", "cagr", "maxdd"];
  const files = [path.join(P1C, "alfred-vintage-spans.json"), path.join(P1C, "warmup-verification.json"), path.join(RES, "issue_189_phase1c_pull.mjs"), path.join(RES, "issue_189_phase1c_warmup.py"), path.join(RES, "decisions/issue-189-phase1c-correctness-addendum.md")];
  for (const f of files) {
    const c = fs.readFileSync(f, "utf8");
    for (const b of ban) assert.ok(!c.toLowerCase().includes(b), `return/metric reference in ${f}: ${b}`);
  }
}
console.log("7 Phase-1C consistency checks PASS");
