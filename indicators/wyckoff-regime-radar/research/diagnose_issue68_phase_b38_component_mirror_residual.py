#!/usr/bin/env python3
"""One-shot Issue #68 B3.8 component reciprocal residual diagnostic."""
from __future__ import annotations

import json

import diagnose_issue66_reciprocal_symmetry as phasea
import diagnose_issue68_phase_b38_raw_feature_attribution as b38


def main() -> None:
    rows = {}
    maxima = {name: 0.0 for name in b38.COMPONENT_WEIGHTS}
    for pair, frame in phasea.load_frozen_pairs().items():
        result = b38.analyze_pair(frame)
        rows[pair] = result["component_mirror"]
        for name, stats in result["component_mirror"].items():
            maxima[name] = max(maxima[name], float(stats["mae_to_negative_inverse"]))
    print(json.dumps({"per_pair": rows, "max_mae_by_component": maxima}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
