#!/usr/bin/env node
// Issue #189 Phase 2 — YoY revision spreads (economically relevant units).
// For each feed: per benchmark obs, 12m% recomputed WITHIN each vintage,
// then spread across vintages. Reads scratch columns only. No returns.
import fs from "node:fs";
import path from "node:path";

const SCRATCH = "C:\\Users\\EDDY\\AppData\\Local\\Temp\\opencode\\issue189pit";
const RES = path.join(process.cwd(), "indicators/macro-pressure-map/research");
const fin = (x) => typeof x === "number" && Number.isFinite(x);
const SID = { G1: "INDPRO", G2: "UNRATE", G3: "PERMIT", G4n: "DSPI", G4d: "PCEPI", I1: "CPIAUCSL", I2: "PCEPILFE", I3: "PPIACO", I4: "AHETPI", I5: "CPIENGSL" };
const YOY_OK = new Set(["G1", "G3", "I1", "I2", "I3", "I4", "I5"]); // level/rate-like roles where 12m% is meaningful
const addM = (ym, k) => {
  let y = +ym.slice(0, 4), m = +ym.slice(5, 7) + k;
  while (m > 12) { m -= 12; y++; }
  while (m < 1) { m += 12; y--; }
  return `${y}-${String(m).padStart(2, "0")}`;
};
function loadCols(sid) {
  const p = path.join(SCRATCH, sid + ".jsonl");
  return fs.readFileSync(p, "utf8").trim().split("\n").filter(Boolean).map((l) => {
    const o = JSON.parse(l);
    const obs = {};
    for (const r of o.rows) {
      const c = r.split(",");
      const v = parseFloat(c[1]);
      if (c[0] && fin(v)) obs[c[0].slice(0, 7)] = v;
    }
    return { vd: o.vd, obs };
  });
}
const BENCH = [];
{ let y = 2002, m = 1; while (y < 2026 || (y === 2026 && m <= 1)) { BENCH.push(`${y}-${String(m).padStart(2, "0")}`); m += 12; if (m > 12) { m -= 12; y++; } } }
const out = {};
for (const role of Object.keys(SID)) {
  if (!YOY_OK.has(role)) { out[role] = { note: "level/rate role: YoY spread not applicable (see level spreads in revision-impact.json)" }; continue; }
  const cols = loadCols(SID[role]);
  const rows = BENCH.map((b) => {
    const base = addM(b, -12);
    const vals = [];
    for (const { obs } of cols) {
      if (fin(obs[b]) && fin(obs[base]) && obs[base] !== 0) vals.push(100 * (obs[b] - obs[base]) / obs[base]);
    }
    if (!vals.length) return { obs: b, n: 0 };
    return { obs: b, n: vals.length, min_pp: +Math.min(...vals).toFixed(3), max_pp: +Math.max(...vals).toFixed(3), spread_pp: +(Math.max(...vals) - Math.min(...vals)).toFixed(3) };
  });
  const sp = rows.filter((r) => r.n > 1).map((r) => r.spread_pp);
  out[role] = { obs: rows, median_spread_pp: +sp.sort((a, b) => a - b)[sp.length >> 1].toFixed(3), max_spread_pp: Math.max(...sp) };
}
fs.writeFileSync(path.join(RES, "generated/issue-189/phase2/revision-yoy.json"), JSON.stringify(out, null, 1) + "\n");
for (const r of Object.keys(out)) if (out[r].median_spread_pp !== undefined) console.log(r, "median YoY-revision spread:", out[r].median_spread_pp + "pp", "max:", out[r].max_spread_pp + "pp");
