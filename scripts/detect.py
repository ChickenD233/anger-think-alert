#!/usr/bin/env python3
"""Score a message from the command line. Useful for tuning and for debugging.

    python3 scripts/detect.py "你他妈到底会不会改"
    echo "这也能叫修好了？" | python3 scripts/detect.py
    python3 scripts/detect.py --json "fuck, you broke it again"

Exit codes: 0 = angry, 3 = ambiguous, 1 = possible, 2 = calm. The hook ignores
the exit code. This CLI exposes it so a shell script can branch on it.
"""

from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "lib"))

from anger import decide  # noqa: E402

EXIT = {"angry": 0, "ambiguous": 3, "possible": 1, "none": 2}


def main() -> int:
    argv = sys.argv[1:]
    as_json = "--json" in argv
    words = [a for a in argv if a != "--json"]
    text = " ".join(words) if words else sys.stdin.read()
    result = decide(text)
    if as_json:
        print(json.dumps({
            "score": result.score,
            "level": result.level,
            "alert": result.alert,
            "signals": result.signals,
        }, ensure_ascii=False))
    else:
        print(f"level={result.level} score={result.score} signals={','.join(result.signals) or '-'}")
    return EXIT.get(result.level, 2)


if __name__ == "__main__":
    sys.exit(main())
