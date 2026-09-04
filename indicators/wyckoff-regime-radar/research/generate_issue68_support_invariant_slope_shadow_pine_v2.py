#!/usr/bin/env python3
"""Generate Issue #68 support-invariant slope-dulling shadow Pine (contract-fixed wrapper)."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_support_invariant_slope_shadow_pine as base
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent


def generate(source: Path) -> str:
    d1_text = base.phase_b.d1.generate(source)
    if d1_text.count(base.phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(base.phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, base.phase_b.D1_INDICATOR_DECL, base.AUDIT_DECL)
    out = core + "\n\n" + base.BODY + "\n"
    for token in (
        "Support-Invariant Slope-Dulling Shadow",
        "issue68SIBpRankFull",
        "Support-invariant shadow TOP",
        "S2 EFF > S1",
        "Common bp z avg",
        "SHADOW ONLY",
    ):
        if token not in out:
            raise RuntimeError(f"missing required audit token: {token}")
    if "strategy.entry" in out or "strategy.close" in out:
        raise RuntimeError("support-invariant shadow leaked strategy order logic")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=HERE / SOURCE_RELATIVE)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    text = generate(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
