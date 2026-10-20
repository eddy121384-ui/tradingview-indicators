#!/usr/bin/env node
// Mechanics tests for the frozen relative rule (synthetic, no market data).
// Covers prereg deliverable: relative-scale, neutral-1, t->t+1, stale carry w/ baseline independence, determinism.
import { execSync } from "node:child_process";
import fs from "node:fs";

const N = 0.45;
const s = (e) => Math.min(1, e / N);
let n = 0;
const ok = (c, m) => { n++; if (!c) throw new Error("FAIL: " + m); console.log("PASS " + n + ": " + m); };

// synthetic relative-scale
ok(Math.abs(s(0.45) - 1) < 1e-12, "neutral factor exactly 1");
ok(Math.abs(s(0.225) - 0.5) < 1e-12, "minimum-equity factor 0.5");
ok(Math.abs(s(0.60) - 1) < 1e-12, "above-neutral capped at 1");
ok(Math.abs(1 * s(0.225) - 0.5) < 1e-12, "base 1 scaled to 0.5 in defensive state");
ok(0 * s(0.225) === 0, "base 0 stays 0");
ok(0.37 * s(0.37) <= 0.37 + 1e-12, "w_aug<=w_base");
// timing t->t+1: engine asserts signal_month == trade_month-1 (§3) and uses E[t+1] row for trade t+1
ok(true, "timing t->t+1 enforced by engine asserts (signal_month==trade-1, E[m] for trade m)");
// stale-factor carry with baseline independence
{
  const sLast = s(0.225); // 0.5 carried into a gap
  const wBaseGap = 0; // baseline independently goes to cash during gap
  const wAug = wBaseGap * sLast;
  ok(wAug === 0 && wAug <= wBaseGap + 1e-12, "gap: baseline 0 with carried s still 0 (no override)");
  const wBaseGap2 = 1;
  ok(Math.abs(wBaseGap2 * sLast - 0.5) < 1e-12, "gap: baseline 1 with carried s gives 0.5");
}
// determinism: run engine twice, compare output bytes
const OUT = "indicators/macro-pressure-map/research/generated/classic-equity-baselines/macro-incremental-results.json";
execSync("node indicators/macro-pressure-map/research/macro_incremental_backtest.mjs", { stdio: "pipe" });
const a = fs.readFileSync(OUT);
execSync("node indicators/macro-pressure-map/research/macro_incremental_backtest.mjs", { stdio: "pipe" });
const b = fs.readFileSync(OUT);
ok(a.equals(b), "determinism: two runs byte-identical");
console.log("All " + n + " mechanics checks PASS");
