#!/usr/bin/env python3
"""Run unit tests and compare failures with the checked-in baseline."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
BASELINE_FILE = PROJECT_DIR / "tests" / "baseline_failures.txt"
PYTEST_COMMAND = [
    sys.executable,
    "-m",
    "pytest",
    "tests/unit",
    "-q",
    "--ignore=tests/unit/test_actions.py",
]


def load_baseline() -> list[str]:
    return [
        line.strip()
        for line in BASELINE_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def extract_test_ids(output: str, status: str) -> set[str]:
    prefix = f"{status} "
    test_ids: set[str] = set()

    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line.startswith(prefix):
            continue

        test_id = line[len(prefix) :].split(" - ", 1)[0].strip()
        if test_id:
            test_ids.add(test_id)

    return test_ids


def main() -> int:
    baseline = load_baseline()
    baseline_ids = set(baseline)

    result = subprocess.run(
        PYTEST_COMMAND,
        cwd=PROJECT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )

    output = result.stdout
    if output:
        print(output, end="" if output.endswith("\n") else "\n")

    failed_ids = extract_test_ids(output, "FAILED")
    error_ids = extract_test_ids(output, "ERROR")
    observed_failure_ids = failed_ids | error_ids

    # Collection/setup errors are always failures, even if an ID happens to
    # appear in the baseline.
    new_failure_ids = (failed_ids - baseline_ids) | error_ids
    fixed_failure_ids = [
        test_id
        for test_id in baseline
        if test_id not in observed_failure_ids
    ]

    if new_failure_ids:
        print("NEW FAILURES:")
        for test_id in sorted(new_failure_ids):
            print(test_id)
        return 1

    if result.returncode not in (0, 1):
        print(f"PYTEST ERROR: unexpected exit status {result.returncode}")
        return 1

    if result.returncode == 1 and not observed_failure_ids:
        print("PYTEST ERROR: pytest failed without reporting a test failure")
        return 1

    if fixed_failure_ids:
        print("FIXED SINCE BASELINE:")
        for test_id in fixed_failure_ids:
            print(test_id)
        print("Consider updating tests/baseline_failures.txt.")
        return 0

    passed_matches = re.findall(r"\b(\d+) passed\b", output)
    passed_count = int(passed_matches[-1]) if passed_matches else 0
    print(f"OK: no new failures ({passed_count} passed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
