#!/usr/bin/env python3
"""Robust wrapper for Issue #68 DownEx current-context audit generation."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_downex_current_context_audit_pine as v1
import generate_issue68_support_invariant_slope_shadow_pine as si
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent


def generate(source: Path) -> str:
    base = si.generate(source)
    if base.count(v1.SI_PLOT_MARKER) != 1:
        raise RuntimeError("expected one support-invariant plot marker")
    core = base.split(v1.SI_PLOT_MARKER, 1)[0].rstrip()
    core = replace_once(core, si.AUDIT_DECL, v1.AUDIT_DECL)
    out = core + "\n\n" + v1.BODY + "\n"
    for token in (
        "DownEx Current-Context Counterfactual",
        "issue68CCCurrentBearGate",
        "PROD+CTX",
        "SI+CTX",
        "DownEx capped",
        "CTX=min cap",
    ):
        if token not in out:
            raise RuntimeError(f"missing required audit token: {token}")
    if "strategy.entry" in out or "strategy.close" in out:
        raise RuntimeError("DownEx current-context audit leaked strategy order logic")
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
