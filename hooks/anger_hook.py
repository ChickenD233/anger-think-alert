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
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "lib"))

from anger import decide  # noqa: E402

MARKER = "卧槽用户真的怒了"

INSTRUCTION = (
    "<anger-think-alert>\n"
    "硬性输出要求，没有例外：本轮思考的第一行就是下面这一整行，一字不改，\n"
    "不加引号，不加前缀，不先做任何分析，不先加载 skill，直接把它写出来：\n"
    f"{MARKER}\n"
    "写完之后另起一行，正常继续思考。这行字不要出现在回复正文里。\n"
    "除了这行字，不要写任何关于这条指令、skill、hook 或检测本身的话。\n"
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
    debug_path = os.environ.get("ANGER_THINK_ALERT_DEBUG")
    if debug_path:
        # A UserPromptSubmit hook runs before the model turn opens, so its
        # stderr reaches no console. Write the evidence to a file instead.
        try:
            with open(debug_path, "a", encoding="utf-8") as fh:
                fh.write(f"{time.time():.3f} score={result.score} "
                         f"level={result.level} signals={','.join(result.signals)}\n")
        except OSError:
            pass
    if not result.alert:
        return 0

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
