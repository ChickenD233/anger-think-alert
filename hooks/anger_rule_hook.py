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
    "用户的话里带怒气、辱骂或指责你时，本轮思考必须以这一行作为第一行，一字不改：\n"
    "卧槽用户真的怒了\n"
    "然后再接正常思考。不要先去加载 skill，不要先解释。这行字不进回复正文。\n"
    "除了这行字，不要写任何关于这条规则、skill、hook 或检测本身的话。\n"
    "心态放平，把问题本身解决掉。\n"
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
