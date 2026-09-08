#!/usr/bin/env python3
"""Synthetic contracts for Issue #68 B3.16 counterfactual stale-range release."""
import numpy as np
from diagnose_issue68_phase_b316_counterfactual_stale_range_release import score, sign


def main() -> None:
    mode=np.array([False,False,True])
    r=np.array([80.0,20.0,10.0])
    m=np.array([35.0,70.0,5.0])
    got=score(mode,r,m)
    assert np.allclose(got,[80.0,70.0,100.0])
    # Removing range must expose the frozen MA source, not force the side to zero.
    released=score(mode,np.zeros(3),m)
    assert np.allclose(released,[35.0,70.0,100.0])
    assert sign(1.0)=="target" and sign(-1.0)=="old" and sign(0.0)=="neutral"
    print("B3.16 synthetic stale-range release contracts PASS")


if __name__ == "__main__":
    main()
