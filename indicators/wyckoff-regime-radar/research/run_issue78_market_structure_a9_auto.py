#!/usr/bin/env python3
"""Auto-locate the frozen OOS3 snapshot and run the A9 dimension audit.

Issue #181 (Issue #78 A9). The discovery cohort is the recovered OOS3
Bloomberg snapshot (`artifacts/issue78_equity_proof_policy_oos3/snapshot/`),
whose exact 300-FIGI cohort identity is
`017e9360402afa002dc0970088649e7c411c4f02333dec550f2432be3c0dd701`.

OOS4 is deliberately NOT contacted here: A9 preregisters OOS3 as the primary
discovery cohort and only runs the OOS4 replication stage if at least one of
D3/D4 reaches KEEP_AS_ATLAS_DIMENSION.

The frozen preregistration commit is asserted to still be an ancestor of HEAD
and to be unmodified, so the analyzer can never silently run against an edited
preregistration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

PREREG_COMMIT = "df160addf8b363eba05c076a3372ab95f475d838"
PREREG_REL = "decisions/issue-78-market-structure-a9-preregistration.md"
EXPECTED_FIGI_SET_SHA = (
    "017e9360402afa002dc0970088649e7c411c4f02333dec550f2432be3c0dd701"
)


def figi_set_sha_for_csv(path: Path) -> str | None:
    try:
        frame = pd.read_csv(path, usecols=["figi"])
    except Exception:
        return None
    if frame.empty or frame["figi"].nunique() != 300 or len(frame) != 300:
        return None
    figis = sorted(frame["figi"].astype(str).tolist())
    return hashlib.sha256(("\n".join(figis) + "\n").encode("utf-8")).hexdigest()


def _complete_manifest_in(directory: Path) -> Path | None:
    for path in sorted(directory.glob("*.json")):
        name = path.name.lower()
        if "manifest" not in name or "checkpoint" in name:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if (
            isinstance(data, dict)
            and isinstance(data.get("completed"), dict)
            and len(data["completed"]) == 300
            and not data.get("failures")
        ):
            return path
    return None


def find_oos3_snapshot(root: Path) -> tuple[Path, Path, Path]:
    """Return (universe, manifest, raw_dir) for the frozen OOS3 cohort."""
    universe_hits: list[Path] = []
    for path in root.rglob("*.csv"):
        if "oos4" in str(path).lower():
            continue
        if "oos3" not in str(path).lower():
            continue
        if figi_set_sha_for_csv(path) == EXPECTED_FIGI_SET_SHA:
            universe_hits.append(path)
    if not universe_hits:
        raise RuntimeError("no OOS3 universe CSV with the frozen FIGI-set identity")

    # The recovered-cohort file and the snapshot copy carry identical content:
    # prefer the copy that sits next to the complete raw manifest.
    paired = [
        path for path in universe_hits
        if _complete_manifest_in(path.parent) is not None
    ]
    if len(paired) == 1:
        universe_path = paired[0]
    elif len(universe_hits) == 1:
        universe_path = universe_hits[0]
    else:
        raise RuntimeError(
            "ambiguous OOS3 universe CSV with the frozen FIGI-set identity: "
            f"{universe_hits}"
        )

    manifest_path = _complete_manifest_in(universe_path.parent)
    if manifest_path is None:
        raise RuntimeError(
            f"no complete OOS3 raw manifest next to {universe_path}"
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    raw_dir = None
    for candidate in (manifest_path.parent / "raw", manifest_path.parent):
        if candidate.is_dir() and all(
            (candidate / str(diag["path"])).exists()
            for diag in manifest["completed"].values()
        ):
            raw_dir = candidate
            break
    if raw_dir is None:
        raise RuntimeError("could not resolve all 300 OOS3 raw files")
    return universe_path, manifest_path, raw_dir


def assert_prereg_frozen(here: Path) -> str:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=here, capture_output=True, text=True,
        check=True,
    ).stdout.strip()
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", PREREG_COMMIT, "HEAD"],
        cwd=here, check=True,
    )
    rel = subprocess.run(
        ["git", "diff", "--name-only", PREREG_COMMIT, "--", PREREG_REL],
        cwd=here, capture_output=True, text=True, check=True,
    ).stdout.strip()
    if rel:
        raise RuntimeError(f"preregistration edited since {PREREG_COMMIT}: {rel}")
    sha = hashlib.sha256((here / PREREG_REL).read_bytes()).hexdigest()
    print(f"[auto] HEAD {head} descends from prereg {PREREG_COMMIT}")
    print(f"[auto] prereg file sha256 {sha}")
    return head


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact-root", type=Path, default=Path("artifacts"))
    ap.add_argument(
        "--out", type=Path, default=Path("artifacts/issue78_market_structure_a9")
    )
    ap.add_argument(
        "--limit",
        type=int,
        default=0,
        help="plumbing smoke test only; 0 = full frozen OOS3 cohort",
    )
    ap.add_argument(
        "--offset",
        type=int,
        default=0,
        help="plumbing smoke test only; only used together with --limit",
    )
    args = ap.parse_args()
    if args.limit:
        print(f"[auto] WARNING: smoke limit {args.limit}; NOT a frozen run")

    here = Path(__file__).resolve().parent
    assert_prereg_frozen(here)

    root = args.artifact_root.resolve()
    universe_path, manifest_path, raw_dir = find_oos3_snapshot(root)
    out = args.out.resolve()

    print(f"[auto] universe: {universe_path}")
    print(f"[auto] manifest: {manifest_path}")
    print(f"[auto] raw dir:  {raw_dir}")
    print(f"[auto] output:   {out}")

    cmd = [
        sys.executable,
        str(here / "analyze_issue78_market_structure_a9.py"),
        "--universe", str(universe_path),
        "--manifest", str(manifest_path),
        "--raw-dir", str(raw_dir),
        "--classifier", str(here / "generated" / "wyckoff-issue78-rc-python.py"),
        "--out", str(out),
        "--prereg-sha", PREREG_COMMIT,
    ]
    if args.limit:
        cmd.extend(["--limit", str(args.limit), "--offset", str(args.offset)])
    subprocess.run(cmd, check=True)

    archive = shutil.make_archive(str(out), "zip", root_dir=out)
    print(f"[auto] result zip: {archive}")


if __name__ == "__main__":
    main()
