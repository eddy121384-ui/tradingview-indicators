#!/usr/bin/env node
// Issue #188 — Node mirror assertions (synthetic data only).
import assert from "node:assert";

const fin = (x) => typeof x === "number" && Number.isFinite(x);
function drawdowns(rets) {
  const v = rets.filter(fin);
  const out = [];
  let peak = 1, cum = 1;
  for (const r of v) { cum *= 1 + r; peak = Math.max(peak, cum); out.push(cum / peak - 1); }
  return out;
}
const ulcer = (rets) => {
  const dd = drawdowns(rets);
  return dd.length ? 100 * Math.sqrt(dd.reduce((a, d) => a + d * d, 0) / dd.length) : NaN;
};
assert.strictEqual(ulcer([0, 0, 0]), 0);
{
  const dd = drawdowns([0, 0, -0.5, 0, 0]);
  assert.ok(Math.abs(Math.min(...dd) + 0.5) < 1e-12);
  assert.ok(Math.abs(ulcer([0, 0, -0.5, 0, 0]) - 100 * Math.sqrt(0.75 / 5)) < 1e-9);
}
const pct = (v, arr) => {
  const worse = arr.filter((d) => d < v).length, ties = arr.filter((d) => d === v).length;
  return (100 * (worse + 0.5 * ties)) / arr.length;
};
assert.strictEqual(pct(5, [1, 2, 5, 9]), 62.5);
assert.strictEqual(pct(0, [1, 2, 3]), 0);
function mulberry32(seed) {
  let s = seed >>> 0;
  return () => {
    s = (s + 0x6d2b79f5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
{
  const a = mulberry32(188), b = mulberry32(188);
  assert.deepStrictEqual([a(), a(), a()], [b(), b(), b()]);
}
const shapley = (a, b, c, ap) => [0.5 * ((a - c) + (ap - b)), 0.5 * ((a - ap) + (c - b)), (a - ap) - (c - b)];
assert.deepStrictEqual(shapley(10, 4, 6, 8), [4, 2, 0]);
function verdict(f) {
  if (!f.assessable) return "deep_history_evidence_mixed_or_inconclusive";
  const g = [1, 2, 3, 4, 5, 6, 7, 8].map((i) => f["G" + i]);
  if (g.every(Boolean)) return "deep_history_macro_information_supported";
  if (f.G1 && !f.G4) return "deep_history_reducible_to_simpler_defense";
  if (!f.G6 || !f.G7) return "deep_history_exposure_or_availability_explained";
  return "deep_history_evidence_mixed_or_inconclusive";
}
const all = { assessable: true, G1: true, G2: true, G3: true, G4: true, G5: true, G6: true, G7: true, G8: true };
assert.strictEqual(verdict(all), "deep_history_macro_information_supported");
assert.strictEqual(verdict({ ...all, G4: false }), "deep_history_reducible_to_simpler_defense");
assert.strictEqual(verdict({ ...all, G6: false }), "deep_history_exposure_or_availability_explained");
assert.strictEqual(verdict({ ...all, G8: false }), "deep_history_evidence_mixed_or_inconclusive");

console.log("12 Node mirror assertions PASS");
