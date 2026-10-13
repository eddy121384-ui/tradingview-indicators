#!/usr/bin/env node
// Issue #189 Phase 2 — as-of assembly + revision/staleness/definition/coverage
// analysis (NO asset returns anywhere in this file or its inputs).
// Reads: scratch vintage columns + vintage-manifest.json (Phase 2 pull job).
// Writes committed artifacts under generated/issue-189/phase2/.
// Frozen: lag table (Phase 1 upper bounds), 74/75 warmup, conservative clock.
import fs from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const RES = path.join(ROOT, "indicators/macro-pressure-map/research");
const GEN2 = path.join(RES, "generated/issue-189/phase2");
const SCRATCH = "C:\\Users\\EDDY\\AppData\\Local\\Temp\\opencode\\issue189pit";
const fin = (x) => typeof x === "number" && Number.isFinite(x);
const readLF = (rel) => fs.readFileSync(path.join(RES, rel), "utf8").replace(/\r/g, "");

// feed -> { sid, lagDays (Phase 1 upper bound, conservative), tvKind }
const FEEDS = {
  G1: { sid: "INDPRO", lag: 18, kind: "index-SA" },
  G2: { sid: "UNRATE", lag: 8, kind: "rate-SA" },
  G3: { sid: "PERMIT", lag: 22, kind: "units-SAAR" },
  G4n: { sid: "DSPI", lag: 32, kind: "bnUSD-SAAR" },
  G4d: { sid: "PCEPI", lag: 32, kind: "index-SA" },
  I1: { sid: "CPIAUCSL", lag: 15, kind: "index-SA" },
  I2: { sid: "PCEPILFE", lag: 32, kind: "index-SA" },
  I3: { sid: "PPIACO", lag: 14, kind: "index-NSA" },
  I4: { sid: "AHETPI", lag: 8, kind: "usd-per-hour-SA" },
  I5: { sid: "CPIENGSL", lag: 15, kind: "index-SA" },
};
const ROLES = Object.keys(FEEDS);
const lastDay = (ym) => new Date(Date.UTC(+ym.slice(0, 4), +ym.slice(5, 7), 0)).toISOString().slice(0, 10);
const addDays = (d, n) => new Date(Date.parse(d + "T00:00:00Z") + n * 86400000).toISOString().slice(0, 10);
// decision month-ends 2006-06 .. 2026-08
const DECISIONS = [];
{ let y = 2006, m = 6; while (y < 2026 || (y === 2026 && m <= 8)) { DECISIONS.push(lastDay(`${y}-${String(m).padStart(2, "0")}`)); m++; if (m > 12) { m = 1; y++; } } }

// load scratch columns: sid -> [{vd, rows:[[obs,val],...]}]
function loadCols(sid) {
  const p = path.join(SCRATCH, sid + ".jsonl");
  if (!fs.existsSync(p)) return [];
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
const COLS = {};
for (const r of ROLES) COLS[r] = loadCols(FEEDS[r].sid);
console.log("columns loaded:", ROLES.map((r) => `${r}:${COLS[r].length}`).join(" "));
// latest-wins per role at decision date D (vintage vd <= D) — incremental over
// sorted decisions (cumulative maps; vintages only added as D advances)
const COLS_SORTED = {};
for (const r of ROLES) COLS_SORTED[r] = [...COLS[r]].sort((a, b) => (a.vd < b.vd ? -1 : 1));
const DEC_SORTED = [...DECISIONS].sort();
const SNAPS = [];
{
  const cum = {}, ptr = {};
  for (const r of ROLES) { cum[r] = {}; ptr[r] = 0; }
  for (const D of DEC_SORTED) {
    const snap = {};
    for (const r of ROLES) {
      const cols = COLS_SORTED[r];
      while (ptr[r] < cols.length && cols[ptr[r]].vd <= D) {
        const { vd, obs } = cols[ptr[r]];
        for (const [m, v] of Object.entries(obs)) {
          if (!(m in cum[r]) || vd >= cum[r][m][0]) cum[r][m] = [vd, v];
        }
        ptr[r]++;
      }
      // SNAPSHOT ISOLATION (Phase 2 correction): deep-copy the cumulative map
      // so later decisions never mutate earlier snapshots. Aliasing here leaked
      // future vintages into past decisions (2420/2430 records violated).
      snap[r] = Object.fromEntries(Object.entries(cum[r]).map(([m, [vd, v]]) => [m, [vd, v]]));
    }
    SNAPS.push(snap);
  }
}
// eligible latest obs per role at decision D under conservative clock:
// latest obs m with month_end(m)+lag <= D AND vintage-covered by D
function eligibleAt(role, snap, D) {
  const lag = FEEDS[role].lag;
  let bestM = null;
  for (const m of Object.keys(snap).sort()) {
    if (addDays(lastDay(m), lag) <= D) bestM = m;
  }
  if (!bestM) return null;
  return { obs: bestM, vintage: snap[bestM][0], value: snap[bestM][1], age_mo: (Date.parse(D) - Date.parse(lastDay(bestM))) / 2592000000 };
}
// ---- R2 staleness + common month, all decisions
const stale = [];
DEC_SORTED.forEach((D, di) => {
  const snap = SNAPS[di];
  const legs = {};
  for (const r of ROLES) legs[r] = eligibleAt(r, snap[r], D);
  const avail = ROLES.filter((r) => legs[r] !== null);
  const common = avail.length ? avail.map((r) => legs[r].obs).sort()[0] : null;
  stale.push({ decision: D, common_obs: common, roles_covered: avail.length, legs: Object.fromEntries(ROLES.map((r) => [r, legs[r] ? { obs: legs[r].obs, vintage: legs[r].vintage, age_mo: +legs[r].age_mo.toFixed(2) } : null])) });
});
// naive clock diagnostic (obs month <= D-1mo regardless of lag) for BEA effect sizing
const staleNaive = [];
DEC_SORTED.forEach((D, di) => {
  const snap = SNAPS[di];
  const prevM = new Date(Date.parse(D) - 27 * 86400000).toISOString().slice(0, 7);
  const legs = {};
  for (const r of ROLES) {
    const cand = Object.keys(snap[r]).filter((m) => m <= prevM).sort();
    legs[r] = cand.length ? cand[cand.length - 1] : null;
  }
  const vals = ROLES.map((r) => legs[r]);
  staleNaive.push({ decision: D, common_obs: vals.some((v) => v === null) ? null : vals.sort()[0] });
});
// ---- R1 revision impact: benchmark obs across vintages
const BENCH = [];
{ let y = 2000, m = 1; while (y < 2026 || (y === 2026 && m <= 6)) { BENCH.push(`${y}-${String(m).padStart(2, "0")}`); m += 6; if (m > 12) { m -= 12; y++; } } }
const revImpact = {};
for (const r of ROLES) {
  revImpact[r] = BENCH.map((b) => {
    const vals = [];
    for (const { vd, obs } of COLS[r]) if (b in obs) vals.push({ vd, v: obs[b] });
    vals.sort((a, b2) => (a.vd < b2.vd ? -1 : 1));
    if (!vals.length) return { obs: b, n: 0 };
    const vv = vals.map((x) => x.v);
    return { obs: b, n: vals.length, first: vv[0], last: vv[vv.length - 1], min: Math.min(...vv), max: Math.max(...vv), distinct: new Set(vv).size, first_vd: vals[0].vd, last_vd: vals[vals.length - 1].vd };
  });
}
// ---- R3 definition checks (metadata-level, fail-closed; value pulls inform YoY computability only)
const defChecks = {
  G1: { verdict: "match", basis: "INDPRO monthly SA index; computed-12m% substitution for TV native YoY (documented; rounding-level)" },
  G2: { verdict: "match", basis: "UNRATE monthly SA U-3 rate, inverted per frozen code" },
  G3: { verdict: "match", basis: "PERMIT SAAR levels; 12m% invariant to SAAR scaling; frozen code computes YoY from levels itself" },
  G4: { verdict: "match", basis: "DSPI nominal SAAR + PCEPI chain SA; frozen real-order (ratio then YoY) reproduced exactly" },
  I1: { verdict: "match", basis: "CPIAUCSL monthly SA index; computed-12m% substitution (documented)" },
  I2: { verdict: "match", basis: "PCEPILFE monthly SA chain index; computed-12m% substitution (documented)" },
  I3: { verdict: "TBD-stays-partial", basis: "PPIACO is NSA all-commodities; TV USPPIYY index concept unverified; FD-ID break 2014 unmapped to TV series" },
  I4: { verdict: "TBD-stays-partial", basis: "AHETPI is production-worker concept from 1964; TV USWG concept unverified; 1960-63 gap" },
  I5: { verdict: "TBD-stays-partial", basis: "CPIENGSL broad-energy SA assumed; TV USEI concept unverified" },
  G5: { verdict: "unavailable", basis: "no public vintage archive (Phase 1B spots only)" },
};
// ---- coverage: decisions with full 10-role eligibility + 74/75 warmup feasibility
const coverage = stale.map((s) => {
  const ok10 = ROLES.every((r) => s.legs[r] !== null);
  return { decision: s.decision, common_obs: s.common_obs, roles10: ok10 };
});
fs.mkdirSync(path.join(RES, "generated/issue-189/phase2"), { recursive: true });
const W = (n, c) => fs.writeFileSync(path.join(RES, "generated/issue-189/phase2", n), c);
const J = (o) => JSON.stringify(o, null, 1) + "\n";
W("staleness.json", J({ clock: "conservative month-end (Phase 1 upper-bound lags)", naive: "obs<=D-1mo diagnostic", rows: stale, naive_rows: staleNaive }));
W("revision-impact.json", J(revImpact));
W("definition-checks.json", J(defChecks));
W("coverage.json", J({ decisions: coverage, warmup: { max_raw_lookback_offsets: 74, min_raw_observation_count: 75 }, note: "warmup feasibility per decision needs 74 offsets of vintage-covered raw obs ending at common_obs; evaluated in asof engine" }));
console.log("decisions:", DECISIONS.length, "full-10 eligible:", coverage.filter((c) => c.roles10).length);
