#!/usr/bin/env node
// Issue #189 Phase 1 — feasibility audit builder (NO asset-return imports).
// Frozen evidence table (public-catalog findings, URLs cited per row) ->
// source-manifest.csv, vintage-coverage.csv, publication-lag-audit.csv,
// feasibility-summary.json. Deterministic: fixed table, sorted output.
import fs from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const RES = path.join(ROOT, "indicators/macro-pressure-map/research");
const GEN189 = path.join(RES, "generated/issue-189");

// ---------------------------------------------------------------- frozen evidence (Phase 1 public-catalog audit, 2026-10-12)
const FEEDS = [
  { role: "G1", tv: "ECONOMICS:USIPYY", transform: "native YoY", counterpart: "INDPRO", org: "Federal Reserve G.17", freq: "monthly", obs_start: "1919-01", vintage_start: "1962-11", vintage_src: "RTDSM IPT vintages 1962:M11+; ALFRED metadata from 1927 (data-vintage list unconfirmed)", release_rule: "mid-month following reference month, 9:15am ET", lag_days: "14-18", tz: "US Eastern", definition: "Index SA (2017=100); rebasing across vintages noted", status: "partial_PIT", note: "ALFRED data-vintage list unconfirmed (needs key); RTDSM monthly vintage start is the hard evidence", urls: "https://fred.stlouisfed.org/series/INDPRO|https://alfred.stlouisfed.org/series?seid=INDPRO|https://www.federalreserve.gov/releases/g17|https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/ipt", license: "public series pages; bulk download terms apply" },
  { role: "G2", tv: "ECONOMICS:USUR", transform: "level, sign inverted", counterpart: "UNRATE", org: "BLS Employment Situation (LNS14000000, U-3)", freq: "monthly", obs_start: "1948-01", vintage_start: "1960-03", vintage_src: "ALFRED metadata from 1960-03-15; RTDSM RUC quarterly vintages 1965:Q4+", release_rule: "first Friday after reference month, 8:30am ET", lag_days: "4-8", tz: "US Eastern", definition: "SA %; pre-1967-02 universe 14+ vs 16+ splice flagged", status: "date_only_conservative_PIT", note: "partial 1960-03..1967-01 (definition splice); Jan-Feb 1960 vintages unknown", urls: "https://fred.stlouisfed.org/series/UNRATE|https://alfred.stlouisfed.org/series?seid=UNRATE|https://www.bls.gov/schedule/news_release/empsit.htm", license: "public series pages" },
  { role: "G3", tv: "ECONOMICS:USBP", transform: "level -> causal 12m %", counterpart: "PERMIT", org: "Census/HUD New Residential Construction", freq: "monthly", obs_start: "1960-01", vintage_start: "1999-08", vintage_src: "ALFRED metadata from 1999-08-17; pre-1999 machine vintages unknown (FRASER PDFs possible future work)", release_rule: "~12th workday after reference month, 8:30am ET", lag_days: "16-22", tz: "US Eastern", definition: "SAAR thousands units; 12m% invariant to SAAR scaling; 2005 universe 19k->20k places noted", status: "date_only_conservative_PIT", note: "unavailable pre-1999-08 via ALFRED; SAAR-vs-PSN immaterial for YoY", urls: "https://fred.stlouisfed.org/series/PERMIT|https://alfred.stlouisfed.org/series?seid=PERMIT|https://www.census.gov/construction/nrc/", license: "public series pages" },
  { role: "G4n", tv: "ECONOMICS:USDPI", transform: "level / PCEPI -> 12m real %", counterpart: "DSPI", org: "BEA Personal Income and Outlays (A067RC)", freq: "monthly", obs_start: "1959-01", vintage_start: "1979-12", vintage_src: "ALFRED metadata from 1979-12-18; comprehensive NIPA revisions rewrite history", release_rule: "end of month following reference month, 8:30am ET", lag_days: "28-32", tz: "US Eastern", definition: "bn USD SAAR nominal; real = DSPI/PCEPI*100", status: "date_only_conservative_PIT", note: "paired with G4d; G4 jointly unavailable pre-2000-08 (PCEPI binding)", urls: "https://fred.stlouisfed.org/series/DSPI|https://alfred.stlouisfed.org/series?seid=DSPI|https://www.bea.gov/news/schedule", license: "public series pages" },
  { role: "G4d", tv: "ECONOMICS:USPCEPI", transform: "deflator level", counterpart: "PCEPI", org: "BEA chain-type price index (DPCERG)", freq: "monthly", obs_start: "1959-01", vintage_start: "2000-08", vintage_src: "ALFRED metadata from 2000-08-01; rescalings 1996/2000/2005/2009/2012/2017", release_rule: "end of month following reference month, 8:30am ET", lag_days: "28-32", tz: "US Eastern", definition: "SA chain index; YoY invariant to rescaling within consistent vintage", status: "date_only_conservative_PIT", note: "binding constraint for G4 and I2 warmup; pre-2000 vintages need SCB/FRASER (unverified)", urls: "https://fred.stlouisfed.org/series/PCEPI|https://alfred.stlouisfed.org/series?seid=PCEPI", license: "public series pages" },
  { role: "G5", tv: "ECONOMICS:USMNO", transform: "diffusion level, 50 NOT subtracted", counterpart: "UNKNOWN", org: "ISM Report On Business (proprietary)", freq: "monthly", obs_start: "unverified-publicly", vintage_start: "none-found", vintage_src: "no public archive URL found; history via vendors (Haver/Moody's); % Higher/Same/Lower pre-2000s unverified", release_rule: "first business day after reference month, 10:00am ET (January: second)", lag_days: "1-4", tz: "US Eastern", definition: "diffusion = %Higher + 0.5x%Same; SA via X-13-ARIMA with annual factor revisions; pre-1980 backfill methodology unverified", status: "unavailable", note: "BLOCKS full five-finite PIT in every month including ETF window; purchase terms unverified", urls: "https://www.ismworld.org/supply-management-news-and-reports/reports/ism-pmi-reports/|https://fred.stlouisfed.org/tags/series?t=manufacturing%3Bnew+orders", license: "ISM data proprietary; do not scrape/store" },
  { role: "I1", tv: "ECONOMICS:USIRYY", transform: "native YoY", counterpart: "CPIAUCSL", org: "BLS CPI-U All Items, SA", freq: "monthly", obs_start: "1947-01", vintage_start: "1972-07", vintage_src: "ALFRED from 1972-07-21; early vintages truncated to ~1.5y history; 1967=100 -> 1982-84=100 rescale Feb-1988", release_rule: "mid-month following reference month, 8:30am ET", lag_days: "11-15", tz: "US Eastern", definition: "SA index; rescale breaks cross-vintage LEVELS not within-vintage YoY", status: "date_only_conservative_PIT", note: "partial 1972-07..1972-12 (truncated YoY base); date_only from 1973", urls: "https://fred.stlouisfed.org/series/CPIAUCSL|https://alfred.stlouisfed.org/series?seid=CPIAUCSL|https://www.bls.gov/schedule/news_release/cpi.htm", license: "public series pages" },
  { role: "I2", tv: "ECONOMICS:USCPCEPIAC", transform: "native annual %", counterpart: "PCEPILFE", org: "BEA core PCE chain index (DPCCRG), SA", freq: "monthly", obs_start: "1959-01", vintage_start: "2000-08", vintage_src: "ALFRED metadata from 2000-08-01; pre-2000 vintages need BEA archives (unverified)", release_rule: "end of month following reference month, 8:30am ET", lag_days: "28-32", tz: "US Eastern", definition: "SA chain index ex food+energy; YoY invariant to rescaling", status: "date_only_conservative_PIT", note: "unavailable pre-2000-08; 1959 obs start refutes late-start hypothesis", urls: "https://fred.stlouisfed.org/series/PCEPILFE|https://alfred.stlouisfed.org/series?seid=PCEPILFE", license: "public series pages" },
  { role: "I3", tv: "ECONOMICS:USPPIYY", transform: "native YoY (index TBD)", counterpart: "PPIACO?", org: "BLS PPI (SOP->FD-ID overhaul Jan-2014)", freq: "monthly", obs_start: "1913-01", vintage_start: "1996-12", vintage_src: "ALFRED from 1996-12-11 (NSA all-commodities continuity); FD-ID headline only from Nov-2009", release_rule: "mid-month following reference month, 8:30am ET", lag_days: "10-14", tz: "US Eastern", definition: "TV index concept UNKNOWN (PPIACO NSA all-commodities assumed; 4-month BLS revisions; no SA PPIACO)", status: "partial_PIT", note: "capped at partial: TV definition unverified; FD-ID break means post-2014 headline concept differs", urls: "https://fred.stlouisfed.org/series/PPIACO|https://alfred.stlouisfed.org/series?seid=PPIACO|https://www.bls.gov/ppi/faqs/questions-and-answers.htm", license: "public series pages" },
  { role: "I4", tv: "ECONOMICS:USWG", transform: "native YoY (concept TBD)", counterpart: "AHETPI?", org: "BLS CES production/nonsupervisory hourly earnings", freq: "monthly", obs_start: "1964-01", vintage_start: "1999-08", vintage_src: "ALFRED from 1999-08-06; all-employee series only from 2006 (CES0500000003)", release_rule: "first Friday after reference month, 8:30am ET (Employment Situation)", lag_days: "4-8", tz: "US Eastern", definition: "production-worker concept (~80% private), NOT all-employee; 1960-63 no single-series coverage", status: "partial_PIT", note: "capped at partial: TV wage concept unverified + 1960-63 gap + splice risk", urls: "https://fred.stlouisfed.org/series/AHETPI|https://alfred.stlouisfed.org/series?seid=AHETPI|https://www.bls.gov/opub/hom/ces/history.htm", license: "public series pages" },
  { role: "I5", tv: "ECONOMICS:USEI", transform: "native % (concept TBD)", counterpart: "CPIENGSL?", org: "BLS CPI Energy component, SA", freq: "monthly", obs_start: "1957-01", vintage_start: "1996-12", vintage_src: "ALFRED metadata from 1996-12-12 (all fields)", release_rule: "mid-month following reference month, 8:30am ET (with CPI)", lag_days: "11-15", tz: "US Eastern", definition: "broad energy (household fuels + motor fuel) assumed; TV concept unverified; pin SA monthly", status: "partial_PIT", note: "capped at partial: TV energy concept unverified", urls: "https://fred.stlouisfed.org/series/CPIENGSL|https://alfred.stlouisfed.org/series?seid=CPIENGSL", license: "public series pages" },
];

// per-role year status rules (frozen here; applied mechanically below)
function yearStatus(f, y) {
  if (f.role === "G5") return "unavailable";
  if (f.role === "I4" && y < 1964) return "unavailable";
  const vs = parseInt(f.vintage_start.slice(0, 4), 10);
  if (y < vs) return "unavailable";
  if (f.role === "G2" && y < 1967) return "partial_PIT";
  if (f.role === "I1" && y === 1972) return "partial_PIT";
  if (f.role === "I3" || f.role === "I4" || f.role === "I5") return "partial_PIT";
  if (f.role === "G1") return "partial_PIT"; // metadata-start evidence only; data-vintage list unconfirmed
  return "date_only_conservative_PIT";
}

fs.mkdirSync(GEN189, { recursive: true });
const W = (n, c) => fs.writeFileSync(path.join(GEN189, n), c);
// 1. source-manifest.csv
{
  const cols = ["role", "tv_symbol", "transform", "counterpart_id", "org", "freq", "obs_start", "vintage_start", "vintage_source", "release_rule", "lag_days_typical", "tz", "definition_match", "status", "status_note", "evidence_urls", "license_note"];
  const q = (s) => `"${String(s).replace(/"/g, '""')}"`;
  const lines = [cols.join(",")];
  for (const f of FEEDS) lines.push([f.role, f.tv, f.transform, f.counterpart, f.org, f.freq, f.obs_start, f.vintage_start, f.vintage_src, f.release_rule, f.lag_days, f.tz, f.definition, f.status, f.note, f.urls, f.license].map(q).join(","));
  W("source-manifest.csv", lines.join("\n") + "\n");
}
// 2. vintage-coverage.csv (role x year 1960-2026)
{
  const lines = ["role,year,status,vintage_start,note"];
  for (const f of FEEDS) for (let y = 1960; y <= 2026; y++) lines.push([f.role, y, yearStatus(f, y), f.vintage_start, ""].join(","));
  W("vintage-coverage.csv", lines.join("\n") + "\n");
}
// 3. publication-lag-audit.csv
{
  const lines = ["role,agency_release,schedule_rule,typical_lag_days,timezone,conservative_staleness_at_month_end,evidence_url"];
  const lag = [
    ["G1", "Fed G.17 IP", "mid-month, 9:15am", "14-18", "US Eastern", "1 month (prior-month value released mid-current-month)", "https://www.federalreserve.gov/releases/g17"],
    ["G2", "BLS Employment Situation", "first Friday, 8:30am", "4-8", "US Eastern", "1 month", "https://www.bls.gov/schedule/news_release/empsit.htm"],
    ["G3", "Census/HUD NRC", "~12th workday, 8:30am", "16-22", "US Eastern", "1 month", "https://www.census.gov/construction/nrc/"],
    ["G4n", "BEA PI&O", "end of following month, 8:30am", "28-32", "US Eastern", "1-2 months (borderline at month-end close; conservative rule pushes to next session)", "https://www.bea.gov/news/schedule"],
    ["G4d", "BEA PI&O (PCE)", "end of following month, 8:30am", "28-32", "US Eastern", "1-2 months (same borderline)", "https://www.bea.gov/news/schedule"],
    ["G5", "ISM ROB mfg", "first business day, 10:00am (Jan: second)", "1-4", "US Eastern", "1 month IF archived (it is not publicly)", "https://www.ismworld.org/supply-management-news-and-reports/reports/rob-report-calendar"],
    ["I1", "BLS CPI", "mid-month, 8:30am", "11-15", "US Eastern", "1 month", "https://www.bls.gov/schedule/news_release/cpi.htm"],
    ["I2", "BEA PI&O (core PCE)", "end of following month, 8:30am", "28-32", "US Eastern", "1-2 months (same borderline)", "https://www.bea.gov/news/schedule"],
    ["I3", "BLS PPI", "mid-month, 8:30am", "10-14", "US Eastern", "1 month", "https://www.bls.gov/schedule/news_release/ppi.htm"],
    ["I4", "BLS Employment Situation (earnings)", "first Friday, 8:30am", "4-8", "US Eastern", "1 month", "https://www.bls.gov/schedule/news_release/empsit.htm"],
    ["I5", "BLS CPI (energy comp.)", "mid-month, 8:30am", "11-15", "US Eastern", "1 month", "https://www.bls.gov/schedule/news_release/cpi.htm"],
  ];
  for (const r of lag) lines.push(r.map((s) => `"${s}"`).join(","));
  W("publication-lag-audit.csv", lines.join("\n") + "\n");
}
// 4. feasibility-summary.json (answers A-D machine-readable; NO returns used)
{
  const rolesAvail = (y0, y1, pred) => {
    const out = {};
    for (const f of FEEDS) {
      let ok = 0, tot = 0;
      for (let y = y0; y <= y1; y++) { tot++; if (pred(yearStatus(f, y))) ok++; }
      out[f.role] = { ok, tot };
    }
    return out;
  };
  const nonUnav = (s) => s !== "unavailable";
  const exactish = (s) => s === "date_only_conservative_PIT" || s === "exact_verified_PIT";
  const years = [];
  for (let y = 1960; y <= 2026; y++) {
    const st = FEEDS.map((f) => yearStatus(f, y));
    years.push({ year: y, fully: st.every((s) => s === "date_only_conservative_PIT" || s === "exact_verified_PIT"), roles_ok: st.filter(nonUnav).length });
  }
  const etfRoles = rolesAvail(2006, 2026, nonUnav);
  const etfExact = rolesAvail(2006, 2026, exactish);
  W("feasibility-summary.json", JSON.stringify({
    issue: 189, phase: 1, generated_from: "frozen public-catalog evidence table (no vintage pulls, no returns)",
    A_exact_mapping_count: { exact_verified_PIT: 0, date_only_conservative_PIT: 6, partial_PIT: 4, proxy_not_equivalent: 0, unavailable: 1, note: "no intraday timestamps verified anywhere; G5 blocks full PIT in all months" },
    B_years: years,
    C_etf_2006_2026: { roles_non_unavailable: etfRoles, roles_exactish: etfExact, full_pit_identifiable: false, reason: "G5 ISM has no public vintage archive in any month; G4/I2 warmup truncated at window start (vintages from 2000-08)" },
    D_gaps: ["G5 all months (no public ISM vintage archive)", "G4 pre-2000-08 (PCEPI binding)", "I2 pre-2000-08", "G3 pre-1999-08 (ALFRED; FRASER PDFs unverified future work)", "I1 pre-1972-07", "I3 pre-1996-12 + definition TBD", "I4 1960-63 + pre-1999-08 + concept TBD", "I5 pre-1996-12 + concept TBD", "G1 data-vintage list unconfirmed (API key needed)", "G2 Jan-Feb 1960 + pre-1967 splice"],
    D_lawful_remedies: ["ALFRED API vintage-date pull with key (env-only, Phase 2)", "FRASER/SCB/BLS archive digitization for pre-1999/2000 gaps", "ISM history license or documented exclusion analysis (new issue if concept changes)", "no revised-value fills, no proxy swaps, no requirement loosening"],
    verdict: "partially_feasible",
    verdict_note: "10/11 roles identifiable from 2000-08 with stated caveats; full five-finite PIT identifiable in ZERO months 1960-2026 (G5); pre-2000 full PIT not verifiable",
    production_authorized: false,
  }, null, 2) + "\n");
}
console.log("wrote", fs.readdirSync(GEN189).length, "files");
