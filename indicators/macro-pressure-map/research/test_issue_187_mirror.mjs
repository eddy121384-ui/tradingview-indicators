#!/usr/bin/env node
// Issue #187 — Node mirror assertions (synthetic data only).
import assert from "node:assert";

const EQ = ["sp500", "nasdaq", "russell"];
const SCAP = { sp500: 35, nasdaq: 20, russell: 15 };
const signal = (g2, g1, g0, i1, i0) =>
  g0 < -10 && g0 > g1 && g1 > g2 && i0 <= 10 && (i0 - i1) <= 5;
assert.strictEqual(signal(-14, -12, -11, 0, 5), true);
assert.strictEqual(signal(-14, -12, -9, 0, 5), false);
assert.strictEqual(signal(-14, -12, -12, 0, 5), false);
assert.strictEqual(signal(-14, -12, -11, 0, 11), false);
assert.strictEqual(signal(-14, -12, -11, 0, 6), false);

function sizeOverlay(base, req = 5) {
  const w = { ...base };
  const eq = EQ.filter((s) => w[s] > 0);
  const E = eq.reduce((a, s) => a + w[s], 0);
  const head = eq.reduce((a, s) => a + (SCAP[s] - w[s]), 0);
  let add = Math.min(req, Math.max(0, w.cash - 2), 60 - E, head);
  add = Math.max(0, add);
  if (E > 0 && add > 0) for (const s of eq) { const t = Math.min((add * w[s]) / E, SCAP[s] - w[s]); w[s] += t; w.cash -= t; }
  return { w, add };
}
const BASE = { sp500: 25, nasdaq: 12, russell: 8, cash: 15 };
assert.strictEqual(sizeOverlay(BASE).add, 5);
const LL = { sp500: 25.19, nasdaq: 12.09, russell: 8.05, cash: 5 };
const r = sizeOverlay(LL);
assert.ok(Math.abs(r.add - 3) < 1e-9);
assert.ok(r.w.cash >= 2 - 1e-9);

function exits(g1, g0, gm1, i0, im1, eRef, eNow, ePrev, n) {
  const f = [];
  if (eNow >= eRef + 5 - 1e-9) f.push("A");
  if (i0 > 10 || i0 - im1 > 5) f.push("B");
  if ((g0 - g1) <= 0 && (g1 - gm1) <= 0) f.push("C");
  if (eNow - ePrev <= -5 + 1e-9) f.push("D");
  if (n >= 6) f.push("E");
  return f;
}
assert.deepStrictEqual(exits(-4, -4, -3, 0, 0, 40, 45, 45, 2), ["A", "C"]); // C co-fires; order A-E wins in builder
assert.deepStrictEqual(exits(-5, -4, -6, 0, 0, 40, 40, 40, 6), ["E"]);

function gates(g) {
  if (g.n_act < 3 || g.overlap_y < 10) return "early_recovery_equity_overlay_not_assessable";
  const v = [1, 2, 3, 4, 5, 6, 7, 8].map((i) => g["G" + i]);
  if (v.every(Boolean)) return "early_recovery_equity_overlay_supported";
  if (g.G1 && v.filter((x) => !x).length <= 2 && g.G2 && g.G4)
    return "early_recovery_equity_overlay_suggestive_with_limitations";
  return "early_recovery_equity_overlay_not_supported";
}
const all = { G1: true, G2: true, G3: true, G4: true, G5: true, G6: true, G7: true, G8: true, n_act: 10, overlap_y: 60 };
assert.strictEqual(gates(all), "early_recovery_equity_overlay_supported");
assert.strictEqual(gates({ ...all, n_act: 2 }), "early_recovery_equity_overlay_not_assessable");
assert.strictEqual(gates({ ...all, G5: false, G7: false }), "early_recovery_equity_overlay_suggestive_with_limitations");
assert.strictEqual(gates({ ...all, G2: false }), "early_recovery_equity_overlay_not_supported");

console.log("12 Node mirror assertions PASS");
