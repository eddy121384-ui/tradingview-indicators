#!/usr/bin/env node
// Issue #186 — Node mirror assertions for frozen turning-lag primitives.
// Synthetic data only. No parent prices, no allocation timeline.
import assert from "node:assert";

const monthDiff = (a, b) => (+b.slice(0, 4) - +a.slice(0, 4)) * 12 + (+b.slice(5, 7) - +a.slice(5, 7));
assert.strictEqual(monthDiff("2000-08", "2000-06"), -2);
assert.strictEqual(monthDiff("2000-08", "2000-10"), 2);
assert.strictEqual(monthDiff("2007-10", "2009-03"), 17);

function extractBears(months, closes, thresh = 0.20) {
  const n = months.length, events = [];
  let i = 0;
  while (i < n) {
    let peakI = i, peakP = closes[i], j = i + 1, rec = null;
    while (j < n) {
      if (closes[j] > peakP) { peakP = closes[j]; peakI = j; }
      else if (closes[j] <= (1 - thresh) * peakP) {
        for (let k = j + 1; k < n; k++) if (closes[k] >= peakP) { rec = k; break; }
        break;
      }
      j++;
    }
    if (rec === null) {
      if (j < n) {
        const seg = closes.slice(peakI);
        let ti = 0; for (let t = 1; t < seg.length; t++) if (seg[t] < seg[ti]) ti = t;
        events.push({ peakI, troughI: peakI + ti, recI: null, censored: true });
      }
      break;
    }
    const pre = closes.slice(i, rec);
    const pmax = Math.max(...pre);
    const peakI2 = i + pre.findIndex((v) => v === pmax);
    const seg2 = closes.slice(peakI2, rec);
    let ti = 0; for (let t = 1; t < seg2.length; t++) if (seg2[t] < seg2[ti]) ti = t;
    events.push({ peakI: peakI2, troughI: peakI2 + ti, recI: rec, censored: false });
    i = rec + 1;
  }
  return events;
}
const mk = (y0, n) => { const o = []; let y = y0[0], m = y0[1]; for (let k = 0; k < n; k++) { o.push(String(y).padStart(4, "0") + "-" + String(m).padStart(2, "0")); m++; if (m > 12) { m = 1; y++; } } return o; };

// single bear
{
  const ms = mk([2000, 1], 24);
  const cl = [90, 95, 100, 98, 92, 85, 78, 72, 70, 75, 82, 88, 93, 97, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108];
  const ev = extractBears(ms, cl);
  assert.strictEqual(ev.length, 1);
  assert.strictEqual(ms[ev[0].peakI], "2000-03");
  assert.strictEqual(ms[ev[0].troughI], "2000-09");
  assert.strictEqual(ms[ev[0].recI], "2001-04");
}
// no bear / sub-threshold / censored
assert.deepStrictEqual(extractBears(mk([2000, 1], 12), [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111]), []);
assert.deepStrictEqual(extractBears(mk([2000, 1], 12), [100, 102, 105, 100, 95, 90, 88, 92, 98, 104, 108, 112], 0.20), []);
assert.strictEqual(extractBears(mk([2000, 1], 12), [100, 102, 105, 100, 95, 90, 88, 92, 98, 104, 108, 112], 0.10).length, 1);
{
  const ev = extractBears(mk([2000, 1], 12), [100, 105, 110, 100, 90, 80, 75, 78, 82, 85, 88, 90]);
  assert.strictEqual(ev.length, 1);
  assert.strictEqual(ev[0].censored, true);
}
// matching smoke (peak early/late signs)
function matchPeak(T, em, E, th = 5) {
  const idx = new Map(em.map((m, i) => [m.slice(0, 7), i]));
  const ti = idx.get(T);
  const dE = E.map((v, i) => (i ? v - E[i - 1] : 0));
  let best = null;
  for (let m = Math.max(1, ti - 12); m <= ti; m++) if (dE[m] <= -th && E[ti] <= E[m - 1] - th) best = m;
  if (best !== null) return ["early_protection", monthDiff(T, em[best].slice(0, 7))];
  for (let m = ti + 1; m < Math.min(E.length, ti + 13); m++) if (dE[m] <= -th) return ["late_protection", monthDiff(T, em[m].slice(0, 7))];
  return [E[ti] <= 27.5 ? "already_defensive" : "no_action", null];
}
{
  const em = Array.from({ length: 12 }, (_, i) => `2000-${String(i + 1).padStart(2, "0")}-01`);
  assert.deepStrictEqual(matchPeak("2000-08", em, [50, 50, 50, 50, 50, 40, 40, 40, 40, 40, 40, 40]), ["early_protection", -2]);
  assert.deepStrictEqual(matchPeak("2000-08", em, [50, 50, 50, 50, 50, 50, 50, 50, 50, 40, 40, 40]), ["late_protection", 2]);
}
// verdict tree mirror
function verdict(mp, mt, dd) {
  const late = mp >= 4 || mt >= 6 || dd >= 0.6, ok = mp <= 2 && mt <= 4;
  if (late && !ok && (mp <= 2) !== (mt <= 4)) return "deep_history_timing_mixed_by_cycle";
  if (late && !ok) return "deep_history_timing_materially_late";
  if (ok) return "deep_history_timing_acceptable_with_limitations";
  return "deep_history_timing_mixed_by_cycle";
}
assert.strictEqual(verdict(5, 8, 0.7), "deep_history_timing_materially_late");
assert.strictEqual(verdict(1, 3, 0.4), "deep_history_timing_acceptable_with_limitations");
assert.strictEqual(verdict(1, 8, 0.4), "deep_history_timing_mixed_by_cycle");

console.log("12 Node mirror assertions PASS");
