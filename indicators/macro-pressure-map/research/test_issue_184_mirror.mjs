#!/usr/bin/env node
// Issue #184 — Node mirror assertions for frozen specificity primitives.
// Synthetic data only. No parent returns inspected.
import assert from "node:assert";

const ORDER = ["sp500", "nasdaq", "russell", "treasury2y", "treasury10y", "longtreasury", "gold", "oil"];
const EQ = ["sp500", "nasdaq", "russell"];
const SCAP = { sp500: 35, nasdaq: 20, russell: 15, treasury2y: 15, treasury10y: 25, longtreasury: 15, gold: 12, oil: 8 };
const CASH_MIN = 2, CASH_MAX = 60, BUDGET = 5;
const D_PP = 3.051724137931045;

function overlayW(base, signal, budget = BUDGET) {
  const w = { ...base };
  const eq = EQ.filter((s) => w[s] > 0);
  const E = eq.reduce((a, s) => a + w[s], 0);
  if (signal === "risk-on") {
    const head = eq.reduce((a, s) => a + (SCAP[s] - w[s]), 0);
    let add = Math.min(budget, Math.max(0, w.cash - CASH_MIN), CASH_MAX - E, head);
    add = Math.max(0, add);
    if (E > 0 && add > 0) for (const s of eq) { const take = Math.min((add * w[s]) / E, SCAP[s] - w[s]); w[s] += take; w.cash -= take; }
  } else if (signal === "risk-off") {
    const cut = Math.min(budget, E);
    if (E > 0 && cut > 0) { for (const s of eq) w[s] -= (cut * w[s]) / E; w.cash += cut; }
  }
  return w;
}
function constantW(base, d = D_PP) {
  const w = { ...base };
  const eq = EQ.filter((s) => w[s] > 0);
  const E = eq.reduce((a, s) => a + w[s], 0);
  const cut = Math.min(d, E);
  if (E > 0 && cut > 0) { for (const s of eq) w[s] -= (cut * w[s]) / E; w.cash += cut; }
  return w;
}
const shiftSignals = (sigs, k) => sigs.map((_, i) => sigs[(i - k % sigs.length + sigs.length) % sigs.length]);

const BASE = { sp500: 25, nasdaq: 12, russell: 8, cash: 15, treasury2y: 8, treasury10y: 14, longtreasury: 8, gold: 6, oil: 4 };
const approx = (a, b, tol = 1e-9) => assert.ok(Math.abs(a - b) <= tol, `${a} != ${b}`);

// risk-off
{
  const w = overlayW(BASE, "risk-off");
  approx(EQ.reduce((a, s) => a + w[s], 0), 40);
  approx(w.cash, 20);
  approx(w.sp500 / w.nasdaq, 25 / 12);
}
// risk-on
{
  const w = overlayW(BASE, "risk-on");
  approx(EQ.reduce((a, s) => a + w[s], 0), 50);
  approx(w.cash, 10);
}
// neutral noop
assert.deepStrictEqual(overlayW(BASE, "neutral"), BASE);
// zeros preserved
{
  const b = { ...BASE, oil: 0 };
  assert.strictEqual(overlayW(b, "risk-off").oil, 0);
  assert.strictEqual(overlayW(b, "risk-on").oil, 0);
  assert.strictEqual(constantW(b).oil, 0);
}
// gross preserved
for (const sig of ["risk-on", "risk-off", "neutral"]) {
  const w = overlayW(BASE, sig);
  approx(ORDER.reduce((a, s) => a + w[s], 0) + w.cash, 100);
}
// constant cut
{
  const w = constantW(BASE);
  approx(45 - EQ.reduce((a, s) => a + w[s], 0), D_PP);
  approx(w.cash, 15 + D_PP);
}
// shifts
{
  const sigs = [...Array(35).fill("risk-on"), ...Array(163).fill("risk-off"), ...Array(34).fill("neutral")];
  assert.strictEqual(sigs.length, 232);
  for (const k of [1, 2, 115, 231]) {
    const sh = shiftSignals(sigs, k);
    assert.strictEqual(sh.length, 232);
    assert.deepStrictEqual([...sh].sort(), [...sigs].sort());
  }
  assert.notDeepStrictEqual(shiftSignals(Array.from({ length: 232 }, (_, i) => i), 1), shiftSignals(Array.from({ length: 232 }, (_, i) => i), 2));
}
// verdict tree mirror (logic duplicated from Python)
function verdict(s1, s2, s3, p, s4, s5) {
  if (s1 && s2 && s3 && s4 && s5) return "v66_overlay_specific_information_supported";
  if (!s1 || !s4 || !s5) return "v66_overlay_not_supported_after_controls";
  if (s1 && s2 && s4 && s5 && !s3) return "v66_overlay_risk_control_supported_but_timing_not_specific";
  if (s1 && s4 && s5 && (s2 || p)) return "v66_overlay_specificity_suggestive";
  return "v66_overlay_not_supported_after_controls";
}
assert.strictEqual(verdict(true, true, true, true, true, true), "v66_overlay_specific_information_supported");
assert.strictEqual(verdict(true, true, false, false, true, true), "v66_overlay_risk_control_supported_but_timing_not_specific");
assert.strictEqual(verdict(true, false, false, true, true, true), "v66_overlay_specificity_suggestive");
assert.strictEqual(verdict(false, true, true, true, true, true), "v66_overlay_not_supported_after_controls");

console.log("10 Node mirror assertions PASS");
