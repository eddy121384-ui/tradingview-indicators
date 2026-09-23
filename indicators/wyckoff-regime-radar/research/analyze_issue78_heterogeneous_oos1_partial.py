#!/usr/bin/env python3
"""Operational partial-cohort wrapper for Issue #78 Heterogeneous OOS1.

This does NOT change the six-market preregistration or its pass/fail gate.
It exists only to reproduce an explicitly incomplete four-market diagnostic
when NDX and XAUUSD exports are unavailable.
"""
from __future__ import annotations

import analyze_issue78_heterogeneous_oos1 as base

PARTIAL_MARKETS = (
    "TVC:SPX",
    "OANDA:XAGUSD",
    "BITSTAMP:BTCUSD",
    "BITSTAMP:ETHUSD",
)

def main():
    base.EXPECTED_MARKETS = PARTIAL_MARKETS
    base.main()

if __name__ == "__main__":
    main()
