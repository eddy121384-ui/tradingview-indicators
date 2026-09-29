#!/usr/bin/env python3
"""Run a non-economic smoke test of the frozen Issue #78 classifier on #119 raw files.

This proves that every normalized Bloomberg security can execute through the
frozen Python classifier. It deliberately does not calculate R0, Warning-First,
returns, win rates, MFE slices, or any policy economics.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

FROZEN_CLASSIFIER_BLOB = "1eec08e791403453853b589373bb2270c508c3bb"
PROBABILITY_COLUMNS = (
    "prob_acc",
    "prob_markup",
    "prob_reacc",
    "prob_dist",
    "prob_markdown",
    "prob_redist",
)
REQUIRED_OUTPUT_COLUMNS = {
    "formal_id",
    "candidate_display_id",
    "sym_atr",
    *PROBABILITY_COLUMNS,
}


def git_blob_sha(path: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "hash-object", str(path)],
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"unable to hash frozen classifier with git: {exc.output}"
        ) from exc


def load_classifier(path: Path):
    blob = git_blob_sha(path)
    if blob != FROZEN_CLASSIFIER_BLOB:
        raise RuntimeError(
            "frozen classifier blob mismatch: "
            f"expected {FROZEN_CLASSIFIER_BLOB}, got {blob}"
        )

    module_name = "issue78_frozen_classifier_smoke"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to import classifier: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module, blob


def smoke(
    raw_dir: Path,
    classifier_path: Path,
    *,
    output: Path | None = None,
) -> dict:
    module, blob = load_classifier(classifier_path)
    files = sorted(raw_dir.glob("*.csv.gz"))
    if not files:
        raise RuntimeError(f"no raw security files found in {raw_dir}")

    failures: list[dict[str, str]] = []
    summaries: list[dict[str, object]] = []
    total_rows = 0
    total_post_warmup_rows = 0

    for index, path in enumerate(files, start=1):
        try:
            frame = pd.read_csv(path)
            required_input = {
                "stable_security_id",
                "ticker",
                "date",
                "open",
                "high",
                "low",
                "close",
                "volume",
            }
            missing_input = required_input.difference(frame.columns)
            if missing_input:
                raise ValueError(
                    f"missing normalized columns: {sorted(missing_input)}"
                )

            if frame["date"].duplicated().any():
                raise ValueError("duplicate dates in normalized raw file")

            result = module.compute_price_only(frame)
            missing_output = REQUIRED_OUTPUT_COLUMNS.difference(result.columns)
            if missing_output:
                raise ValueError(
                    f"classifier missing outputs: {sorted(missing_output)}"
                )
            if len(result) != len(frame):
                raise ValueError(
                    f"classifier row count changed {len(frame)} -> {len(result)}"
                )

            probabilities = result[list(PROBABILITY_COLUMNS)].apply(
                pd.to_numeric, errors="coerce"
            )
            finite_probs = np.isfinite(probabilities.to_numpy()).all(axis=1)
            finite_sym_atr = np.isfinite(
                pd.to_numeric(result["sym_atr"], errors="coerce").to_numpy()
            )
            post_warmup = finite_probs & finite_sym_atr

            formal = pd.to_numeric(
                result["formal_id"], errors="coerce"
            ).to_numpy()
            if not np.isfinite(formal).all():
                raise ValueError("formal_id contains non-finite values")
            if not np.isin(np.rint(formal).astype(int), np.arange(0, 7)).all():
                raise ValueError("formal_id outside frozen 0..6 domain")

            ticker = str(frame["ticker"].iloc[0])
            figi = str(frame["stable_security_id"].iloc[0])
            rows = int(len(frame))
            post_rows = int(post_warmup.sum())
            total_rows += rows
            total_post_warmup_rows += post_rows
            summaries.append(
                {
                    "figi": figi,
                    "ticker": ticker,
                    "rows": rows,
                    "post_warmup_rows": post_rows,
                    "classifier_completed": True,
                }
            )
            print(
                f"[issue119-smoke] {index}/{len(files)} {ticker} "
                f"rows={rows} post_warmup={post_rows}",
                flush=True,
            )
        except Exception as exc:
            failures.append(
                {
                    "file": path.name,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            print(
                f"[issue119-smoke] FAIL {path.name}: "
                f"{type(exc).__name__}: {exc}",
                flush=True,
            )

    report = {
        "issue": 119,
        "purpose": "frozen-classifier-structural-smoke-only",
        "classifier_path": str(classifier_path),
        "classifier_git_blob": blob,
        "classifier_blob_matches_frozen": blob == FROZEN_CLASSIFIER_BLOB,
        "raw_files": len(files),
        "completed_securities": len(summaries),
        "failures": failures,
        "total_rows": total_rows,
        "total_post_warmup_rows": total_post_warmup_rows,
        "min_post_warmup_rows": (
            min(int(x["post_warmup_rows"]) for x in summaries)
            if summaries
            else None
        ),
        "securities": summaries,
        "economics": {
            "computed": False,
            "fields": [],
        },
    }
    report["pass"] = (
        report["classifier_blob_matches_frozen"]
        and report["raw_files"] == 300
        and report["completed_securities"] == 300
        and not failures
    )

    if output:
        output.write_text(
            json.dumps(report, indent=2, default=str) + "\n",
            encoding="utf-8",
        )

    compact = {
        "pass": report["pass"],
        "classifier_git_blob": report["classifier_git_blob"],
        "raw_files": report["raw_files"],
        "completed_securities": report["completed_securities"],
        "failures": len(report["failures"]),
        "total_rows": report["total_rows"],
        "total_post_warmup_rows": report["total_post_warmup_rows"],
        "min_post_warmup_rows": report["min_post_warmup_rows"],
        "policy_economics_computed": False,
    }
    print(json.dumps(compact, indent=2))

    if not report["pass"]:
        raise SystemExit(2)
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-dir", type=Path, required=True)
    ap.add_argument(
        "--classifier",
        type=Path,
        default=Path("generated/wyckoff-issue78-rc-python.py"),
    )
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    smoke(args.raw_dir, args.classifier, output=args.output)


if __name__ == "__main__":
    main()
