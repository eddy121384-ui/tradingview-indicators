# Issue #55 — Pre-final confidence calibration

Final OOS remains **SEALED / NOT COMPUTED**.

Low/medium/high confidence cut points are learned from Development only and applied unchanged to Exploratory OOS. Calibration is tested only for the unambiguous directional states: Markup (2) and Markdown (5). For Markdown the return sign is reversed, so a larger stage-aligned value is always better agreement with the regime direction.

## evidence_strength

High confidence beats low confidence in **3 / 24** comparable cases (12.5%).
Strict Low ≤ Medium ≤ High monotonicity appears in **1 / 24** cases with all three bins sufficiently populated (4.2%).

| Pair | Stage | H | Low/Med/High n | High − Low aligned return | High better? | Monotonic? |
|---|---:|---:|---|---:|---|---|
| EURUSD | 2 | 5 | 2/3/5 | — | — | — |
| EURUSD | 2 | 10 | 2/3/5 | — | — | — |
| EURUSD | 2 | 20 | 2/3/5 | — | — | — |
| EURUSD | 2 | 60 | 0/0/0 | — | — | — |
| EURUSD | 5 | 5 | 109/109/64 | -0.909% | no | no |
| EURUSD | 5 | 10 | 104/109/64 | -1.020% | no | no |
| EURUSD | 5 | 20 | 100/105/62 | -0.529% | no | no |
| EURUSD | 5 | 60 | 93/103/41 | -0.204% | no | no |
| USDJPY | 2 | 5 | 31/60/42 | -0.720% | no | no |
| USDJPY | 2 | 10 | 31/60/42 | -1.435% | no | no |
| USDJPY | 2 | 20 | 25/58/42 | -0.108% | no | no |
| USDJPY | 2 | 60 | 18/54/32 | 1.669% | yes | yes |
| USDJPY | 5 | 5 | 31/28/79 | -0.238% | no | no |
| USDJPY | 5 | 10 | 26/28/79 | -0.003% | no | no |
| USDJPY | 5 | 20 | 26/28/79 | -0.383% | no | no |
| USDJPY | 5 | 60 | 25/27/68 | 0.412% | yes | no |
| GBPUSD | 2 | 5 | 21/48/40 | -0.414% | no | no |
| GBPUSD | 2 | 10 | 21/48/40 | -0.596% | no | no |
| GBPUSD | 2 | 20 | 21/48/40 | -1.408% | no | no |
| GBPUSD | 2 | 60 | 21/48/40 | 0.130% | yes | no |
| GBPUSD | 5 | 5 | 100/21/101 | -0.405% | no | no |
| GBPUSD | 5 | 10 | 100/21/101 | -0.479% | no | no |
| GBPUSD | 5 | 20 | 95/21/101 | -1.130% | no | no |
| GBPUSD | 5 | 60 | 95/21/87 | -1.310% | no | no |
| AUDUSD | 2 | 5 | 2/0/1 | — | — | — |
| AUDUSD | 2 | 10 | 2/0/1 | — | — | — |
| AUDUSD | 2 | 20 | 2/0/1 | — | — | — |
| AUDUSD | 2 | 60 | 2/0/1 | — | — | — |
| AUDUSD | 5 | 5 | 116/41/165 | -0.237% | no | no |
| AUDUSD | 5 | 10 | 116/41/165 | -0.243% | no | no |
| AUDUSD | 5 | 20 | 112/41/163 | -0.007% | no | no |
| AUDUSD | 5 | 60 | 112/39/125 | -0.917% | no | no |

## top_gap

High confidence beats low confidence in **10 / 20** comparable cases (50.0%).
Strict Low ≤ Medium ≤ High monotonicity appears in **1 / 20** cases with all three bins sufficiently populated (5.0%).

| Pair | Stage | H | Low/Med/High n | High − Low aligned return | High better? | Monotonic? |
|---|---:|---:|---|---:|---|---|
| EURUSD | 2 | 5 | 2/0/8 | — | — | — |
| EURUSD | 2 | 10 | 2/0/8 | — | — | — |
| EURUSD | 2 | 20 | 2/0/8 | — | — | — |
| EURUSD | 2 | 60 | 0/0/0 | — | — | — |
| EURUSD | 5 | 5 | 128/154/0 | — | — | — |
| EURUSD | 5 | 10 | 126/151/0 | — | — | — |
| EURUSD | 5 | 20 | 123/144/0 | — | — | — |
| EURUSD | 5 | 60 | 117/120/0 | — | — | — |
| USDJPY | 2 | 5 | 32/60/41 | -0.223% | no | no |
| USDJPY | 2 | 10 | 32/60/41 | -0.986% | no | no |
| USDJPY | 2 | 20 | 29/59/37 | 1.026% | yes | no |
| USDJPY | 2 | 60 | 20/55/29 | 0.111% | yes | no |
| USDJPY | 5 | 5 | 28/18/92 | -0.108% | no | no |
| USDJPY | 5 | 10 | 28/17/88 | 0.149% | yes | no |
| USDJPY | 5 | 20 | 28/17/88 | 0.679% | yes | no |
| USDJPY | 5 | 60 | 27/17/76 | 0.992% | yes | no |
| GBPUSD | 2 | 5 | 38/34/37 | -0.230% | no | no |
| GBPUSD | 2 | 10 | 38/34/37 | 0.176% | yes | no |
| GBPUSD | 2 | 20 | 38/34/37 | -0.214% | no | no |
| GBPUSD | 2 | 60 | 38/34/37 | 1.811% | yes | no |
| GBPUSD | 5 | 5 | 108/50/64 | -0.887% | no | no |
| GBPUSD | 5 | 10 | 108/50/64 | -2.025% | no | no |
| GBPUSD | 5 | 20 | 105/50/62 | -2.940% | no | no |
| GBPUSD | 5 | 60 | 105/50/48 | -4.135% | no | no |
| AUDUSD | 2 | 5 | 3/0/0 | — | — | — |
| AUDUSD | 2 | 10 | 3/0/0 | — | — | — |
| AUDUSD | 2 | 20 | 3/0/0 | — | — | — |
| AUDUSD | 2 | 60 | 3/0/0 | — | — | — |
| AUDUSD | 5 | 5 | 68/48/206 | 0.119% | yes | no |
| AUDUSD | 5 | 10 | 68/48/206 | 0.180% | yes | yes |
| AUDUSD | 5 | 20 | 65/48/203 | 0.257% | yes | no |
| AUDUSD | 5 | 60 | 65/44/167 | -0.109% | no | no |

Boundary: Development-derived bins + Exploratory OOS outcomes only; final OOS remains sealed.
