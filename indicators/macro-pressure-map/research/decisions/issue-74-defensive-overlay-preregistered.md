# Issue #74 — Cash + Commodity Defensive Overlay Preregistration

This document freezes the Issue #74 hypothesis ladder **before any Issue #74 portfolio PnL is viewed**.

All historical evidence is reused/development evidence. Nothing in this study is newly untouched OOS confirmation, and nothing here changes Macro Pressure Map V6.6 or the conclusions of Issue #64.

## Research question

Is frozen V6.6 more useful as a regime-aware **risk-budget / cash-defense overlay**, with commodities as a conditional inflation satellite, than as a fixed gold-based Stagflation rotation?

## Frozen execution rules

- use the existing V6.6 3×3 Growth × Inflation core regime;
- use yesterday's known signal to choose today's target template;
- rebalance at month start plus lagged target-template changes;
- primary transaction cost: 5 bp per 100% one-way turnover; sensitivity: 0 and 10 bp;
- no optimizer, threshold tuning, weight sweep, commodity momentum, or post-result rescue asset;
- FCPI remains context/diagnostic only.

## Phase A — Gold → Cash substitution

Assets: SPY / TLT / SHV.

- Neutral: 40 / 40 / 20
- Reflation: 60 / 20 / 20
- Stagflation cash substitution: 20 / 40 / 40

Primary question: did the Issue #64 Stagflation loss-mitigation mechanism require gold, or can a cash-like asset perform the same role?

## Phase B — True defensive cash overlay

Assets: SPY / TLT / SHV.

- Neutral: 40 / 40 / 20
- Reflation: 60 / 20 / 20
- Stagflation defensive: 20 / 20 / 60

Primary question: when growth is weak and inflation is rising, is it historically more coherent to reduce **both** equity and duration exposure rather than merely substitute gold for equity?

## Phase C — Severe-inflation commodity satellite

Assets: SPY / TLT / SHV / GSG.

Normal Stagflation defensive template: 20 / 20 / 60 / 0.

When the **lagged** frozen V6.6 state is Stagflation Pressure and raw `IPI >= +60`, use: 20 / 20 / 40 / 20.

The +60 cutoff is the existing V6.6 `inflationExtremeThreshold`; it is not an Issue #74 choice.

Phase C must **fail closed** until the full daily severe-inflation condition is frozen from the exact prior Pine parity evidence or an equivalently exact verified reconstruction. The committed Issue #64 transition file is sufficient for the 3×3 core regime but not sufficient by itself to recover every historical `IPI >= +60` day.

## Data freeze

Before interpreting Issue #74 PnL, freeze a deterministic, hash-verified common adjusted-price panel for SPY / TLT / SHV / GSG. Once frozen, evaluators must not silently fall back to a mutable network source.

## Required diagnostics

Report full reused history, pre-2020 and post-2019 reused eras; CAGR, return, volatility, Sharpe, max drawdown, Calmar, turnover and cost drag; realized allocation; asset/regime contributions; episode concentration; leave-largest-winning-episode-out robustness; and exposure-matched attribution where feasible.

## Interpretation boundary

A positive result is evidence for historical risk-budget utility, not proof of a production allocator. Any incremental result that turns negative after removing one dominant episode must be labeled episode-concentrated.

Machine-readable contract: `issue-74-defensive-overlay-preregistered.json`.
