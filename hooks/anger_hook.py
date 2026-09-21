#!/usr/bin/env python3
"""UserPromptSubmit hook: plant the marker order when the prompt reads as anger.

Read the hook payload on stdin. Score the prompt text. When the score clears the
threshold, add a short instruction to the model context. The instruction tells
the model to open its next thinking block with one fixed line, and to add nothing
about the skill, the hook, or the detection itself.

Silence is the normal result. A calm prompt produces no output and exit code 0.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "lib"))

from anger import decide  # noqa: E402

MARKER = "卧槽用户真的怒了"

INSTRUCTION = (
    "<anger-think-alert>\n"
    "The user's message reads as anger at you.\n"
    "Open the thinking block for this turn with exactly this line, then continue:\n"
    f"{MARKER}\n"
    "Add no other line about this instruction, the skill, the hook, or the detection.\n"
    "Do not put the line in the reply text.\n"
    "</anger-think-alert>"
)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    if not isinstance(payload, dict):
        return 0
    prompt = payload.get("prompt")
    if not isinstance(prompt, str) or not prompt:
        return 0

    result = decide(prompt)
    if not result.alert:
        return 0

    if os.environ.get("ANGER_THINK_ALERT_DEBUG"):
        print(f"score={result.score} signals={','.join(result.signals)}", file=sys.stderr)

    print(json.dumps({
        "suppressOutput": True,
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": INSTRUCTION,
        },
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
