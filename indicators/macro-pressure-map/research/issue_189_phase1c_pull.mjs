#!/usr/bin/env node
// Issue #189 Phase 1C — ALFRED vintage-span verification pulls (no key needed:
// alfredgraph.csv is public). For each feed: requested vintage dates ->
// records ACTUAL returned vintage date, obs span, rows, sha256. Saves full
// CSVs for first-vintages only; span+hash evidence otherwise. Macro sources
// ONLY. No asset returns touched.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

const ROOT = process.cwd();
const RES = path.join(ROOT, "indicators/macro-pressure-map/research");
const OUT = path.join(RES, "generated/issue-189/phase1c");
fs.mkdirSync(OUT, { recursive: true });
const sha256 = (b) => crypto.createHash("sha256").update(b).digest("hex");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const PLAN = [
  ["INDPRO", ["1960-01-01", "2000-08-01", "2006-06-01"]],
  ["UNRATE", ["1960-03-15", "2000-08-01", "2006-06-01"]],
  ["PERMIT", ["1999-08-17", "2000-08-01", "2006-06-01"]],
  ["DSPI", ["1979-12-18", "2000-08-01", "2006-06-01"]],
  ["PCEPI", ["2000-08-01", "2006-06-01"]],
  ["CPIAUCSL", ["1972-07-21", "2000-08-01", "2006-06-01"]],
  ["PCEPILFE", ["2000-08-01", "2006-06-01"]],
  ["PPIACO", ["1996-12-11", "2000-08-01", "2006-06-01"]],
  ["AHETPI", ["1999-08-06", "2000-08-01", "2006-06-01"]],
  ["CPIENGSL", ["1996-12-12", "2000-08-01", "2006-06-01"]],
];

const manifest = [];
for (const [sid, dates] of PLAN) {
  for (const vd of dates) {
    const url = `https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=${sid}&vintage_date=${vd}`;
    const r = await fetch(url, { headers: { "User-Agent": "Mozilla/5.0 (research audit; contact via repo)" } });
    const buf = Buffer.from(await r.arrayBuffer());
    const txt = buf.toString("utf8").trim().split("\n");
    const header = txt[0];
    const rows = txt.slice(1).filter((l) => l.trim().length);
    const hash = sha256(buf);
    manifest.push({
      series: sid, requested_vintage: vd, http: r.status,
      returned_column: header.split(",")[1] ?? header,
      obs_first: rows.length ? rows[0].split(",")[0] : null,
      obs_last: rows.length ? rows[rows.length - 1].split(",")[0] : null,
      obs_rows: rows.length, bytes: buf.length, sha256: hash,
    });
    console.log(sid, vd, "->", header.split(",")[1], rows.length ? `${rows[0].split(",")[0]}..${rows[rows.length - 1].split(",")[0]}` : "EMPTY", `n=${rows.length}`);
    await sleep(1200);
  }
}
fs.writeFileSync(path.join(OUT, "alfred-vintage-spans.json"), JSON.stringify({ fetched_at: new Date().toISOString(), pulls: manifest }, null, 2) + "\n");
console.log("saved manifest with", manifest.length, "pulls");
