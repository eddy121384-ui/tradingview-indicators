#!/usr/bin/env python3
"""Issue #189 Phase 1C — warmup verification against FROZEN #160 code.

Synthetic data only. Imports pressure_score/build_roles from the frozen
issue_160 module (no network, no returns, no fetches on import).
"""
import math
import sys

sys.path.insert(0, "indicators/macro-pressure-map/research")
from issue_160_deep_history_v01 import pressure_score, build_roles, NAN, is_fin

# deterministic wiggle: nonzero sd everywhere, no gaps
X = [100.0 + 0.5 * i + 2.0 * math.sin(i / 3.0) for i in range(200)]
S = pressure_score(X)
first = next(i for i, v in enumerate(S) if is_fin(v))
print("pressure_score first finite index:", first, "(expect 62: 60 X + mom needs X[i-3])")
assert first == 62, first

# G3-style role: X needs raw[t] and raw[t-12]; full composite needs score on X.
# Simulate: raw 200 months -> X[t] = 12m% from t-12 -> score over X.
raw = [50.0 + 0.3 * i + 1.0 * math.sin(i / 4.0) for i in range(200)]
Xg = []
for t in range(200):
    if t >= 12 and raw[t - 12] != 0:
        Xg.append(100.0 * (raw[t] - raw[t - 12]) / raw[t - 12])
    else:
        Xg.append(NAN)
Sg = pressure_score(Xg)
firstg = next(i for i, v in enumerate(Sg) if is_fin(v))
print("G3-style first finite raw index:", firstg, "(expect 12 + 62 = 74)")
assert firstg == 74, firstg

# gap case: one missing raw month at t=50 -> warmup extends, finiteness kept
raw2 = list(raw)
raw2[50] = NAN
Xg2 = []
for t in range(200):
    if t >= 12 and is_fin(raw2[t]) and is_fin(raw2[t - 12]) and raw2[t - 12] != 0:
        Xg2.append(100.0 * (raw2[t] - raw2[t - 12]) / raw2[t - 12])
    else:
        Xg2.append(NAN)
Sg2 = pressure_score(Xg2)
firstg2 = next(i for i, v in enumerate(Sg2) if is_fin(v))
print("gap case first finite raw index:", firstg2, "(must be > 74 and < 90)")
assert 74 < firstg2 < 90, firstg2

# cross-check real DH start: raw 1960-01 + 74 months = 1966-03
y, m = 1960, 1
m += 74
y += (m - 1) // 12
m = (m - 1) % 12 + 1
print(f"raw 1960-01 + 74 months = {y:04d}-{m:02d} (DH first valued month is 1966-03)")
assert (y, m) == (1966, 3)

print("warmup verified: 74 raw months minimum (not 72); gaps extend, never interpolate")
