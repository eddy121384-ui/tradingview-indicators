#!/usr/bin/env python3
"""Auto-locate the frozen OOS3 Bloomberg snapshot and run A0 discovery.

Designed for the workstation that already holds the Issue #78 OOS3 artifacts.
It searches an artifact root for the exact frozen OOS3 snapshot manifest and
universe file, verifies that all raw paths resolve, runs the discovery analyzer,
then creates a zip that can be handed back for review.

Recovery mode (2026-10-05): the original OOS3 universe byte identity
(EXPECTED_UNIVERSE_FILE_SHA) is unrecoverable on this workstation after the
local artifact-loss event documented in
`decisions/issue-78-oos3-local-artifact-recovery-note.md`. The recovered
snapshot carries byte SHA f6753c46... but the exact frozen 300-FIGI cohort
identity (EXPECTED_FIGI_SET_SHA). Discovery therefore accepts the original
byte identity first, and falls back to FIGI-set cohort identity with an
explicit warning. This is an operational path fix only; no factor formula,
horizon, bin, or adequacy rule is changed here.
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

from issue119_bbg_common import file_sha256

EXPECTED_UNIVERSE_FILE_SHA = (
    "9d4a14d163ed308238737647b94e722c62fd023b641e1015e6d97679f9ba3b44"
)
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
    payload = "\n".join(figis) + "\n"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _manifest_is_complete(manifest: dict) -> bool:
    return (
        isinstance(manifest.get("completed"), dict)
        and len(manifest["completed"]) == 300
        and not manifest.get("failures")
    )


def find_snapshot_manifest(root: Path) -> Path:
    matches = []
    for path in root.rglob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if (
            isinstance(data, dict)
            and data.get("universe_sha256") == EXPECTED_UNIVERSE_FILE_SHA
            and isinstance(data.get("completed"), dict)
            and len(data["completed"]) == 300
            and not data.get("failures")
        ):
            matches.append(path)
    if len(matches) == 1:
        return matches[0]
    if matches:
        raise RuntimeError(
            "expected exactly one frozen OOS3 raw manifest under "
            f"{root}, found {len(matches)}: {matches}"
        )
    # Recovery fallback: accept the recovered snapshot by exact FIGI-set
    # cohort identity instead of the unrecoverable original byte identity.
    # The manifest must still be internally consistent: its universe_sha256
    # must equal the byte SHA of a universe CSV carrying the frozen cohort.
    recovered = []
    for path in root.rglob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not _manifest_is_complete(data):
            continue
        if not isinstance(data.get("universe_sha256"), str):
            continue
        manifest_dir = path.parent
        for candidate in list(manifest_dir.glob("*.csv")) + [
            manifest_dir.parent / "issue78_equity_proof_policy_oos3_recovery_universe.csv"
        ]:
            if (
                candidate.is_file()
                and figi_set_sha_for_csv(candidate) == EXPECTED_FIGI_SET_SHA
                and file_sha256(candidate) == data["universe_sha256"]
            ):
                recovered.append(path)
                break
    if len(recovered) != 1:
        raise RuntimeError(
            "expected exactly one frozen OOS3 raw manifest under "
            f"{root}, found {len(matches)} by byte identity and "
            f"{len(recovered)} by recovered FIGI-set identity: {recovered}"
        )
    print(
        "[auto] WARNING: original OOS3 universe byte identity "
        f"{EXPECTED_UNIVERSE_FILE_SHA} not found; using recovered "
        f"snapshot {recovered[0]} by FIGI-set identity "
        f"{EXPECTED_FIGI_SET_SHA}."
    )
    return recovered[0]


def find_universe(root: Path) -> Path:
    matches = []
    for path in root.rglob("*.csv"):
        try:
            if file_sha256(path) == EXPECTED_UNIVERSE_FILE_SHA:
                matches.append(path)
        except OSError:
            continue
    if len(matches) == 1:
        return matches[0]
    if matches:
        raise RuntimeError(
            "expected exactly one frozen OOS3 universe CSV under "
            f"{root}, found {len(matches)}: {matches}"
        )
    recovered = [
        path
        for path in root.rglob("*.csv")
        if figi_set_sha_for_csv(path) == EXPECTED_FIGI_SET_SHA
    ]
    # Prefer the manifest-adjacent snapshot copy over the recovery copy when
    # both carry the identical cohort.
    recovered.sort(key=lambda p: (p.name.startswith("issue78_equity_proof_policy_oos3_recovery"), str(p)))
    if len(recovered) < 1:
        raise RuntimeError(
            "expected exactly one frozen OOS3 universe CSV under "
            f"{root}, found {len(matches)} by byte identity and "
            f"{len(recovered)} by recovered FIGI-set identity."
        )
    chosen = recovered[0]
    print(
        "[auto] WARNING: original OOS3 universe byte identity "
        f"{EXPECTED_UNIVERSE_FILE_SHA} not found; using recovered "
        f"universe {chosen} by FIGI-set identity "
        f"{EXPECTED_FIGI_SET_SHA}."
    )
    return chosen


def find_raw_dir(
    root: Path, manifest_path: Path, manifest: dict
) -> Path:
    completed = manifest["completed"]
    sample_paths = [
        str(diag["path"])
        for diag in list(completed.values())[:10]
        if diag.get("path")
    ]
    if not sample_paths:
        raise RuntimeError("manifest has no raw paths")

    candidates = [manifest_path.parent / "raw", manifest_path.parent]
    candidates.extend(manifest_path.parents)
    candidates.append(root)

    seen = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if all((candidate / rel).exists() for rel in sample_paths):
            if all(
                (candidate / str(diag["path"])).exists()
                for diag in completed.values()
            ):
                return candidate
    raise RuntimeError(
        "found the OOS3 manifest but could not resolve all 300 raw files"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--artifact-root",
        type=Path,
        default=Path("artifacts"),
        help="Root containing the existing OOS3 Bloomberg artifacts.",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("artifacts/issue78_factorized_classifier_discovery_a0"),
    )
    args = ap.parse_args()

    root = args.artifact_root.resolve()
    if not root.exists():
        raise FileNotFoundError(root)

    manifest_path = find_snapshot_manifest(root)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    universe_path = find_universe(root)
    raw_dir = find_raw_dir(root, manifest_path, manifest)

    here = Path(__file__).resolve().parent
    analyzer = here / "analyze_issue78_factorized_classifier_discovery.py"
    classifier = here / "generated" / "wyckoff-issue78-rc-python.py"

    print(f"[auto] universe: {universe_path}")
    print(f"[auto] manifest: {manifest_path}")
    print(f"[auto] raw dir:  {raw_dir}")
    print(f"[auto] output:   {args.out.resolve()}")

    cmd = [
        sys.executable,
        str(analyzer),
        "--universe",
        str(universe_path),
        "--manifest",
        str(manifest_path),
        "--raw-dir",
        str(raw_dir),
        "--classifier",
        str(classifier),
        "--out",
        str(args.out),
    ]
    subprocess.run(cmd, check=True)

    archive = shutil.make_archive(
        str(args.out.resolve()),
        "zip",
        root_dir=args.out.resolve(),
    )
    print(f"[auto] result zip: {archive}")


if __name__ == "__main__":
    main()
