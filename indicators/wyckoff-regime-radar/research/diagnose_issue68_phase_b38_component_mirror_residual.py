#!/usr/bin/env python3
"""One-shot Issue #68 B3.8 component reciprocal residual diagnostic."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import diagnose_issue66_reciprocal_symmetry as phasea
import diagnose_issue68_phase_b38_raw_feature_attribution as b38


def build() -> dict:
    rows = {}
    maxima = {name: 0.0 for name in b38.COMPONENT_WEIGHTS}
    for pair, frame in phasea.load_frozen_pairs().items():
        result = b38.analyze_pair(frame)
        rows[pair] = result["component_mirror"]
        for name, stats in result["component_mirror"].items():
            maxima[name] = max(maxima[name], float(stats["mae_to_negative_inverse"]))
    return {"per_pair": rows, "max_mae_by_component": maxima}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    data = build()
    text = json.dumps(data, indent=2, sort_keys=True)
    print(text)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
