#!/usr/bin/env python3
"""Maintainer check: compare a Frisco run against the saved baseline, byte for byte.

The published Frisco results must not change by accident. After any change to
shared code (src/, config.py, analyze.py), run:

    python analyze.py --city frisco
    python compare_outputs.py          expect: 6 of 6 files identical to baseline

Exits non-zero if any file differs or is missing.

When a change is MEANT to alter the Frisco page or outputs, review the differences
this script prints, then refresh the baseline by copying the new files over
tests/baseline/frisco/ (index.html from docs/frisco/, the rest from output/frisco/)
and commit them with that change.
"""

import argparse
import difflib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASELINE = ROOT / "tests" / "baseline" / "frisco"
FILES = ["results.json", "hourly.csv", "intersections.csv",
         "intersection_contrast.csv", "top_intersections.csv"]


def compare(expected, actual):
    """None if identical; otherwise the first few differing lines."""
    if not actual.exists():
        return "missing"
    a, b = expected.read_bytes(), actual.read_bytes()
    if a == b:
        return None
    diff = difflib.unified_diff(
        a.decode(errors="replace").splitlines(),
        b.decode(errors="replace").splitlines(),
        "baseline", "new", n=0, lineterm="")
    return "\n".join(list(diff)[:12])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="output/frisco",
                   help="folder holding the run's JSON and CSV outputs")
    p.add_argument("--page", default="docs/frisco/index.html",
                   help="the run's generated results page")
    args = p.parse_args()

    pairs = [(BASELINE / f, ROOT / args.output / f) for f in FILES]
    pairs.append((BASELINE / "index.html", ROOT / args.page))

    failed = 0
    for expected, actual in pairs:
        result = compare(expected, actual)
        print(f"{'SAME' if result is None else 'DIFF'}  {actual}")
        if result:
            failed += 1
            print("      " + result.replace("\n", "\n      "))
    print(f"\n{len(pairs) - failed} of {len(pairs)} files identical to baseline")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
