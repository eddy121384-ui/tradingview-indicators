#!/usr/bin/env python3
"""Generate Issue #68 DownEx routing decomposition without relying on the stale SI generator token check."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_downex_routing_decomposition_pine as route
import generate_issue68_support_invariant_slope_shadow_pine as si
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent


def generate(source: Path) -> str:
    d1_text = si.phase_b.d1.generate(source)
    if d1_text.count(si.phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(si.phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, si.phase_b.D1_INDICATOR_DECL, route.AUDIT_DECL)

    si_body = si.BODY.replace(
        'showIssue68SITable = input.bool(true, "顯示 Support-Invariant Shadow 表", group=groupIssue68SI)',
        'showIssue68SITable = input.bool(false, "顯示 Support-Invariant Shadow 表", group=groupIssue68SI)',
    )
    out = core + "\n\n" + si_body + "\n" + route.BODY + "\n"

    for token in (
        "Downside-Exhaustion Routing Decomposition",
        "RAW-ONLY",
        "GATE-ONLY",
        "Delta avg S1 EFF",
        "double-route?",
        "S1 ONLY",
    ):
        if token not in out:
            raise RuntimeError(f"missing required routing token: {token}")
    if "strategy.entry" in out or "strategy.close" in out:
        raise RuntimeError("routing decomposition leaked strategy order logic")
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
