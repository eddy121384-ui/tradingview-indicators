#!/usr/bin/env node
// Issue #189 Phase 2 — vintage batch pull worker (background, resumable).
// Grid: last-day-of-month 2000-08 -> 2026-08 x 10 feeds (G5 excluded: no endpoint).
// Writes: temp full columns (UNCOMMITTED scratch) + committed span/hash manifest.
// Macro sources ONLY. No asset returns touched. No credentials.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

const ROOT = process.cwd();
const RES = path.join(ROOT, "indicators/macro-pressure-map/research");
const GEN2 = path.join(RES, "generated/issue-189/phase2");
const SCRATCH = "C:\\Users\\EDDY\\AppData\\Local\\Temp\\opencode\\issue189pit";
fs.mkdirSync(GEN2, { recursive: true });
fs.mkdirSync(SCRATCH, { recursive: true });
const sha256 = (b) => crypto.createHash("sha256").update(b).digest("hex");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const FEEDS = ["INDPRO", "UNRATE", "PERMIT", "DSPI", "PCEPI", "CPIAUCSL", "PCEPILFE", "PPIACO", "AHETPI", "CPIENGSL"];
function monthEnds() {
  const out = [];
  let y = 2000, m = 8;
  while (y < 2026 || (y === 2026 && m <= 8)) {
    const last = new Date(Date.UTC(y, m, 0)).toISOString().slice(0, 10);
    out.push(last);
    m++;
    if (m > 12) { m = 1; y++; }
  }
  return out;
}
const DATES = monthEnds();
console.log("grid:", DATES.length, "dates x", FEEDS.length, "feeds =", DATES.length * FEEDS.length, "pulls");

const MANPATH = path.join(GEN2, "vintage-manifest.json");
let manifest = { pulls: [] };
if (fs.existsSync(MANPATH)) {
  try { manifest = JSON.parse(fs.readFileSync(MANPATH, "utf8")); } catch { manifest = { pulls: [] }; }
}
const done = new Set(manifest.pulls.map((p) => p.sid + "|" + p.vintage_date));
console.log("resume: already have", done.size);

const columnPath = (sid) => path.join(SCRATCH, sid + ".jsonl");
const colFiles = {};
for (const sid of FEEDS) {
  colFiles[sid] = fs.existsSync(columnPath(sid)) ? fs.readFileSync(columnPath(sid), "utf8").trim().split("\n").filter(Boolean).length : 0;
}

let consecFail = 0, fetched = 0;
const t0 = Date.now();
for (const sid of FEEDS) {
  for (const vd of DATES) {
    const key = sid + "|" + vd;
    if (done.has(key)) continue;
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
        if (tries >= 3) console.log("FAIL", key, String(e).slice(0, 80));
        await sleep(2000 * tries);
      }
    }
    if (buf === null) {
      consecFail++;
      if (consecFail >= 10) {
        console.log("ABORT: 10 consecutive failures at", key, "- partial manifest kept");
        fs.writeFileSync(MANPATH, JSON.stringify({ ...manifest, aborted_at: key }, null, 1) + "\n");
        process.exit(2);
      }
      continue;
    }
    consecFail = 0;
    const lines = buf.toString("utf8").trim().split("\n");
    const header = lines[0];
    const rows = lines.slice(1).filter((l) => l.trim().length);
    manifest.pulls.push({
      sid, vintage_date: vd, http: status, returned_column: header.split(",")[1] ?? header,
      obs_first: rows.length ? rows[0].split(",")[0] : null,
      obs_last: rows.length ? rows[rows.length - 1].split(",")[0] : null,
      obs_rows: rows.length, bytes: buf.length, sha256: sha256(buf), retries: tries - 1,
    });
    fs.appendFileSync(columnPath(sid), JSON.stringify({ vd, rows }) + "\n");
    done.add(key);
    fetched++;
    if (fetched % 50 === 0) {
      fs.writeFileSync(MANPATH, JSON.stringify({ fetched_at: new Date().toISOString(), pulls: manifest.pulls }, null, 1) + "\n");
      console.log(`progress ${fetched} this run / ${done.size} total, ${(Date.now() - t0) / 1000 | 0}s elapsed`);
    }
    await sleep(1000 + Math.random() * 500);
  }
}
fs.writeFileSync(MANPATH, JSON.stringify({ fetched_at: new Date().toISOString(), pulls: manifest.pulls }, null, 1) + "\n");
console.log(`DONE: ${fetched} fetched this run, ${done.size} total in manifest`);
