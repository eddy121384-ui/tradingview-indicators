#!/usr/bin/env python3
"""Auto-locate the frozen OOS3 Bloomberg snapshot and run A0 discovery.

Designed for the workstation that already holds the Issue #78 OOS3 artifacts.
It searches an artifact root for the exact frozen OOS3 snapshot manifest and
universe file, verifies that all raw paths resolve, runs the discovery analyzer,
then creates a zip that can be handed back for review.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from issue119_bbg_common import file_sha256

EXPECTED_UNIVERSE_FILE_SHA = (
    "9d4a14d163ed308238737647b94e722c62fd023b641e1015e6d97679f9ba3b44"
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
    if len(matches) != 1:
        raise RuntimeError(
            "expected exactly one frozen OOS3 raw manifest under "
            f"{root}, found {len(matches)}: {matches}"
        )
    return matches[0]


def find_universe(root: Path) -> Path:
    matches = []
    for path in root.rglob("*.csv"):
        try:
            if file_sha256(path) == EXPECTED_UNIVERSE_FILE_SHA:
                matches.append(path)
        except OSError:
            continue
    if len(matches) != 1:
        raise RuntimeError(
            "expected exactly one frozen OOS3 universe CSV under "
            f"{root}, found {len(matches)}: {matches}"
        )
    return matches[0]


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

    candidates = [manifest_path.parent]
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
