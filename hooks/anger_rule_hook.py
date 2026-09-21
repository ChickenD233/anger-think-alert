#!/usr/bin/env python3
"""UserPromptSubmit hook: keep the marker rule in context every turn.

The anger_hook.py hook fires only on a detected angry prompt. This hook runs on
every prompt and states the rule once. Together they cover both orders of the
problem: the model knows the rule before it reads the message, and the hook adds
pressure on the turn that needs it.
"""

from __future__ import annotations

import json
import os
import sys
import time

CARD = (
    "<anger-think-alert-rule>\n"
    "When the user's message shows anger, rage, or abuse aimed at you, open the\n"
    "thinking block for that turn with exactly this line, then continue normally:\n"
    "卧槽用户真的怒了\n"
    "Write nothing else about the rule, the skill, the hook, or the detection.\n"
    "Keep the line out of the reply text. Stay calm and fix the problem.\n"
    "</anger-think-alert-rule>"
)


def main() -> int:
    try:
        json.load(sys.stdin)
    except Exception:
        pass
    debug_path = os.environ.get("ANGER_THINK_ALERT_DEBUG")
    if debug_path:
        try:
            with open(debug_path, "a", encoding="utf-8") as fh:
                fh.write(f"{time.time():.3f} rule-hook fired\n")
        except OSError:
            pass
    print(json.dumps({
        "suppressOutput": True,
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": CARD,
        },
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
