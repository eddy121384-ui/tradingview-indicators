#!/usr/bin/env node
// Issue #189 I3/I4/I5 re-verify — vintage pulls (frozen prereg addendum).
// Grid: month-ends 2000-08 -> 2026-08 x 4 IDs + first-vintage span pulls.
// Same discipline as Phase 2: rate limit, retries, span/hash manifest, no raw commits.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

const ROOT = process.cwd();
const RES = path.join(ROOT, "indicators/macro-pressure-map/research");
const GEN2B = path.join(RES, "generated/issue-189/phase2b");
const SCRATCH = "C:\\Users\\EDDY\\AppData\\Local\\Temp\\opencode\\issue189p2b";
fs.mkdirSync(GEN2B, { recursive: true });
fs.mkdirSync(SCRATCH, { recursive: true });
const sha256 = (b) => crypto.createHash("sha256").update(b).digest("hex");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const FEEDS = {
  I3_FD: { sid: "PPIFIS", from: "2014-06" },
  I4_PAY: { sid: "A576RC1", from: "2010-06" },
  I5_NSA: { sid: "CPIENGNS", from: "2000-08" },
};
void 0; // I3_SOP (WPUSOP3000) REMOVED after recorded evidence: ALFRED vintage
// endpoint returns HTTP 404 for every vintage_date (10 consecutive, run aborted
// per design 2026-10-13). Discontinued SOP series has no ALFRED vintages.
// I3_FD scoped to 2014-06+ (boundary probes: 2014-01 and earlier 404;
// 2014-06-01 works, 55 obs from 2009-11). I4_PAY scoped to 2010-06+
// (2000-08-01 and 2009-01-01 404; 2010-06-01 works, 617 obs from 1959).
// See generated/issue-189/phase2b/no-vintage.json. Legs stay UNVERIFIED absent data.
function monthEnds(fromYM) {
  const out = [];
  let y = +fromYM.slice(0, 4), m = +fromYM.slice(5, 7);
  while (y < 2026 || (y === 2026 && m <= 8)) {
    out.push(new Date(Date.UTC(y, m, 0)).toISOString().slice(0, 10));
    m++;
    if (m > 12) { m = 1; y++; }
  }
  return out;
}
const FIRSTS = { I3_FD: [], I4_PAY: [], I5_NSA: ["1996-12-12"] };
const MANPATH = path.join(GEN2B, "vintage-manifest.json");
let manifest = { pulls: [] };
if (fs.existsSync(MANPATH)) {
  try { manifest = JSON.parse(fs.readFileSync(MANPATH, "utf8")); } catch { manifest = { pulls: [] }; }
}
const done = new Set(manifest.pulls.map((p) => p.key + "|" + p.vintage_date));
const jobs = [];
for (const [key, f] of Object.entries(FEEDS)) {
  for (const vd of [...FIRSTS[key], ...monthEnds(f.from)]) jobs.push([key, f.sid, vd]);
}
console.log("grid:", jobs.length, "pulls,", done.size, "already have");
let consecFail = 0, fetched = 0;
for (const [key, sid, vd] of jobs) {
  if (done.has(key + "|" + vd)) continue;
  const url = `https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=${sid}&vintage_date=${vd}`;
  let buf = null, tries = 0, status = 0;
  while (tries < 3 && buf === null) {
    tries++;
    try {
      const r = await fetch(url, { headers: { "User-Agent": "Mozilla/5.0 (research audit; contact via repo)" } });
      status = r.status;
      if (!r.ok) throw new Error("HTTP " + r.status);
      buf = Buffer.from(await r.arrayBuffer());
    } catch (e) {
      if (tries >= 3) console.log("FAIL", key, vd, String(e).slice(0, 80));
      await sleep(2000 * tries);
    }
  }
  if (buf === null) {
    consecFail++;
    if (consecFail >= 10) {
      fs.writeFileSync(MANPATH, JSON.stringify({ ...manifest, aborted_at: key + "|" + vd }, null, 1) + "\n");
      console.log("ABORT at", key, vd);
      process.exit(2);
    }
    continue;
  }
  consecFail = 0;
  const lines = buf.toString("utf8").trim().split("\n");
  const rows = lines.slice(1).filter((l) => l.trim().length);
  manifest.pulls.push({ key, sid, vintage_date: vd, http: status, returned_column: lines[0].split(",")[1] ?? lines[0], obs_first: rows.length ? rows[0].split(",")[0] : null, obs_last: rows.length ? rows[rows.length - 1].split(",")[0] : null, obs_rows: rows.length, bytes: buf.length, sha256: sha256(buf), retries: tries - 1 });
  fs.appendFileSync(path.join(SCRATCH, key + ".jsonl"), JSON.stringify({ vd, rows }) + "\n");
  done.add(key + "|" + vd);
  fetched++;
  if (fetched % 50 === 0) {
    fs.writeFileSync(MANPATH, JSON.stringify({ fetched_at: new Date().toISOString(), pulls: manifest.pulls }, null, 1) + "\n");
    console.log(`progress ${fetched} this run / ${done.size} total`);
  }
  await sleep(1000 + Math.random() * 500);
}
fs.writeFileSync(MANPATH, JSON.stringify({ fetched_at: new Date().toISOString(), pulls: manifest.pulls }, null, 1) + "\n");
console.log(`DONE: ${fetched} fetched this run, ${done.size} total`);
