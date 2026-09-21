#!/usr/bin/env python3
"""Measure the scorer against the labeled cases in tests/cases.json.

A false alert is worse than a miss here. A miss loses one marker line. A false
alert puts the marker on a calm message and tells the user the tool cries wolf.
So the report prints both rates and fails when precision drops.

    python3 scripts/eval.py            # report, exit 1 on any miss or false alert
    python3 scripts/eval.py --verbose  # print each case with its score
"""

from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "lib"))

from anger import decide  # noqa: E402


def main() -> int:
    verbose = "--verbose" in sys.argv
    with open(os.path.join(ROOT, "tests", "cases.json"), encoding="utf-8") as fh:
        cases = json.load(fh)

    hits = misses = false_alerts = correct_negative = 0
    for case in cases:
        result = decide(case["text"])
        wanted = bool(case["alert"])
        got = result.alert
        if wanted and got:
            hits += 1
            status = "hit "
        elif wanted and not got:
            misses += 1
            status = "MISS"
        elif not wanted and got:
            false_alerts += 1
            status = "FALSE"
        else:
            correct_negative += 1
            status = "ok  "
        if verbose or status.strip() != "hit":
            print(f"{status} {case['id']:9s} score={result.score:<2d} {','.join(result.signals)}")

    total_positive = hits + misses
    total_negative = false_alerts + correct_negative
    recall = hits / total_positive if total_positive else 1.0
    precision = hits / (hits + false_alerts) if (hits + false_alerts) else 1.0
    print(f"\ncases={len(cases)} recall={recall:.2f} precision={precision:.2f} "
          f"misses={misses} false_alerts={false_alerts} (negative cases={total_negative})")
    return 1 if (misses or false_alerts) else 0


if __name__ == "__main__":
    sys.exit(main())
