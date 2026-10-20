#!/usr/bin/env node
// Mechanics tests for the frozen VolFair exposure control (synthetic + determinism).
import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const ENGINE = "indicators/macro-pressure-map/research/volfair_exposure_control.mjs";
const OUT = path.join(ROOT, "indicators/macro-pressure-map/research/generated/classic-equity-baselines");
const n0 = 0;
let n = n0;
const ok = (c, m) => { n++; if (!c) throw new Error("FAIL: " + m); console.log("PASS " + n + ": " + m); };

// Synthetic k-scaling mechanics
const k = 0.8;
const wVol = [1, 0.5, 0.25, 0];
const wVd = [0.8, 0.4, 0.2, 0];
const wCtrl = wVol.map((w) => Math.min(1, k * w));
ok(Math.abs(wCtrl.reduce((a, b) => a + b, 0) / wCtrl.length - wVd.reduce((a, b) => a + b, 0) / wVd.length) < 1e-12,
  "mean exposure equal by construction");
ok(wCtrl.every((w, i) => w <= wVol[i] + 1e-15), "w_ctrl <= w_vol");
ok(wCtrl.every((w) => w < 1), "cap non-binding when 0<k<1 and w_vol<=1");
ok(Math.abs(wCtrl[0] - 0.8) < 1e-12 && Math.abs(wCtrl[3]) < 1e-12, "uniform scaling incl. zero weight");
ok(Math.min(...wVd) >= 0 && Math.max(...wVd) <= 1, "control target in [0,1]");

// Determinism: two engine runs must be byte-identical
execSync(`node ${ENGINE}`, { cwd: ROOT, stdio: "pipe" });
const aJson = fs.readFileSync(path.join(OUT, "volfair-exposure-control-results.json"));
const aCsv = fs.readFileSync(path.join(OUT, "volfair-exposure-control-monthly.csv"));
execSync(`node ${ENGINE}`, { cwd: ROOT, stdio: "pipe" });
const bJson = fs.readFileSync(path.join(OUT, "volfair-exposure-control-results.json"));
const bCsv = fs.readFileSync(path.join(OUT, "volfair-exposure-control-monthly.csv"));
ok(aJson.equals(bJson), "determinism: results JSON byte-identical");
ok(aCsv.equals(bCsv), "determinism: monthly CSV byte-identical");

// Output assertions
const res = JSON.parse(fs.readFileSync(path.join(OUT, "volfair-exposure-control-results.json"), "utf8"));
const lines = fs.readFileSync(path.join(OUT, "volfair-exposure-control-monthly.csv"), "utf8").trim().split(/\r?\n/);
ok(lines.length - 1 === 714, "monthly CSV has 714 rows");
ok(res.panel.n === 714 && res.panel.first === "1967-03" && res.panel.last === "2026-08", "panel bounds");
ok(res.control.cap_binding_months === 0, "zero cap-binding months");
ok(Math.abs(res.control.mean_ctrl - res.control.mean_vd) < 1e-9, "mean exposure equality");
ok(res.control.k > 0 && res.control.k < 1, "0 < k < 1");
ok(res.production_authorized === false, "production_authorized=false");
console.log("All " + n + " checks PASS");
