#!/usr/bin/env python3
"""Synthetic contracts for Issue #68 B3.14 Break evidence-memory audit."""
from diagnose_issue68_phase_b314_break_evidence_memory import source_family


def main() -> None:
    assert source_family(True, 0.0, 0.0) == "mode"
    assert source_family(False, 80.0, 35.0) == "range"
    assert source_family(False, 20.0, 70.0) == "ma"
    assert source_family(False, 35.0, 35.0) == "tie"
    assert source_family(False, 0.0, 0.0) == "none"
    print("B3.14 synthetic source-family contracts PASS")


if __name__ == "__main__":
    main()
