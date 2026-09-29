# Issue #121 commodity source gate — pre-outcome status

Status: **SOURCE GATE OPEN; CORE A/B/C MAY PROCEED**

Target:
- Broad Commodities minus Cash
- >=50 years preferred
- investable futures total-return semantics required

Candidate institutional benchmark:
- S&P GSCI Total Return

Documented public facts:
- S&P GSCI first value date: 1969-12-31
- index launch date: 1991-04-11
- pre-launch history is methodology back-tested
- total return includes the excess-return futures component plus collateral yield

Research boundary:
- spot-only commodity prices are not acceptable
- modern ETF proxies are not acceptable for the ultra-long primary study
- a reproducible historical total-return transport must be frozen before payoff inspection

Current decision:
- do not block Equity-Treasury, Treasury-Cash, or Gold-Cash rematch
- do not compute Commodity-Cash payoff until source freeze succeeds

This file records source semantics only and contains no commodity-conditioned HMRA payoff.
