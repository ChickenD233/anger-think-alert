#!/usr/bin/env python3
"""Score how strongly a user message reads as anger at the assistant.

One public function, decide(text), returns a Result with the score, the matched
signals, and a level. The hook (hooks/anger_hook.py) and the CLI
(scripts/detect.py) share it, so the rule lives in one place.

The scorer is a weighted evidence counter, not a truth machine. A matched signal
is a fact about the text. The score is a reason to act, not a proof. The model
still reads the message and makes the last call.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# --- thresholds -------------------------------------------------------------

ALERT_SCORE = 2
LEVELS = ("none", "possible", "angry")

# --- lexicons ---------------------------------------------------------------

# Swearing. Heavy evidence when the message addresses the assistant.
PROFANITY = (
    "傻逼", "傻b", "煞笔", "废物", "智障", "脑残", "白痴", "弱智", "狗东西",
    "垃圾玩意", "妈的", "他妈的", "卧槽", "我操", "操你", "草你", "妈逼",
    "你妈", "cnm", "nmd", "tmd", "滚蛋",
    "fuck", "fucking", "fuk", "shitty", "bullshit", "useless", "garbage",
    "stupid", "idiot", "moron", "damn", "wtf",
)

# Complaints that carry emotion. Two of these, or one next to a direct address,
# are enough on their own.
ANNOYANCE = (
    "到底", "又错", "还是错", "还是不行", "根本没用", "有毛病", "烦死", "气死",
    "服了", "离谱", "别废话", "听不懂", "看不懂吗", "怎么回事", "多久了",
    "说了多少", "每次都", "要你何用", "你行不行", "你会不会", "谁让你",
    "为什么每次", "这也能叫", "也能叫", "这也叫", "不如不",
    "still", "wrong", "broken", "nonsense", "ridiculous", "again and again",
)

# Intensifiers raise a hit that already exists. They do nothing alone. Entries
# shared with ANNOYANCE are deliberate: the two signals stack for one phrase.
INTENSIFIERS = (
    "他妈的", "给我", "闭嘴", "受够了", "忍不了", "简直", "妈的",
    "never", "every time", "each time", "why do you",
)

# Escalation aimed at the assistant.
ESCALATION = (
    "滚", "闭嘴", "别干了", "退了", "装死", "瞎搞", "乱改", "搞坏", "改坏",
    "重写算了", "别废话",
    "shut up", "stop it", "give up", "you broke", "you ruined",
)

# Direct address of the assistant.
ADDRESS = ("你", "您", "assistant", "agent", "you", "your", "u ")

# Markers that the offending words come from pasted material, not from the user.
QUOTE_CONTEXT = (
    "日志", "报错", "记录里", "文档里", "原文", "注释里", "别人说", "他说",
    "评论说", "网友说", "需求文档", "quote", "someone said", "log:", "error:",
)

# Words that mean a code term sits next to a swearing word in a file name,
# symbol, or message string, not in a human sentence.
CODE_CONTEXT = (
    "变量", "函数", "字段", "文件名", "类名", "标识符", "命名",
    "variable", "function", "field", "class", "identifier", "literal",
)

ALLCAPS = re.compile(r"\b[A-Z]{4,}\b")
ELONGATION = re.compile(r"([a-zA-Z])\1{3,}")
PUNCTUATION_BURST = re.compile(r"[?？!！~～。]{3,}")
ASCII_WORD = re.compile(r"[a-zA-Z][a-zA-Z']*")
CODE_FENCE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE = re.compile(r"`[^`\n]*`")
LOG_LINE = re.compile(r"^\s*(?:\d{4}-\d{2}-\d{2}|\[[A-Z]+\]|at [\w.$]+\(|Traceback|\w+Error:)")


@dataclass
class Result:
    """Outcome of one scoring run."""

    score: int = 0
    level: str = "none"
    signals: list[str] = field(default_factory=list)
    masked_text: str = ""

    @property
    def alert(self) -> bool:
        return self.score >= ALERT_SCORE


def strip_quoted_blocks(text: str) -> tuple[str, bool]:
    """Remove code fences, inline code, and log lines.

    Returns the reduced text and a flag that says whether the message held
    machine output. That case is real: users paste a failing log, then add one
    angry sentence. Removing the noise keeps that sentence loud.
    """
    had_quoted = False
    reduced = CODE_FENCE.sub(" [code] ", text)
    if reduced != text:
        had_quoted = True
    inline = INLINE_CODE.sub(" [code] ", reduced)
    if inline != reduced:
        had_quoted = True
        reduced = inline
    kept = []
    for line in reduced.splitlines():
        if LOG_LINE.match(line):
            had_quoted = True
            kept.append(" [log] ")
        else:
            kept.append(line)
    return "\n".join(kept), had_quoted


def find_tokens(text: str, lexicon: tuple[str, ...]) -> list[str]:
    """Return the distinct lexicon entries present in the text."""
    low = text.casefold()
    return [token for token in lexicon if token.casefold() in low]


def near(text: str, needles: list[str], targets: tuple[str, ...], window: int) -> bool:
    """True when a needle sits within `window` characters of a target token."""
    low = text.casefold()
    target_positions = [low.find(t) for t in targets if t in low]
    if not target_positions:
        return False
    for needle in needles:
        start = low.find(needle.casefold())
        while start != -1:
            end = start + len(needle)
            for at in target_positions:
                if abs(at - start) <= window or abs(at - end) <= window:
                    return True
            start = low.find(needle.casefold(), start + 1)
    return False


def decide(text: str) -> Result:
    """Score one user message. Never raises on short, empty, or odd input."""
    result = Result()
    if not text or not text.strip():
        return result

    masked, had_quoted = strip_quoted_blocks(text)
    result.masked_text = masked

    profanity = find_tokens(masked, PROFANITY)
    annoyance = find_tokens(masked, ANNOYANCE)
    escalation = find_tokens(masked, ESCALATION)
    intensifier = find_tokens(masked, INTENSIFIERS)
    evidence = profanity + annoyance + escalation
    addressed = near(masked, evidence, ADDRESS, 24) if evidence else False

    # Pasted material that names the offending words weakens them, unless the
    # user also aims them at the assistant from up close.
    quoted = near(masked, evidence, QUOTE_CONTEXT, 40) if evidence else False
    aimed_profanity = bool(profanity) and addressed and not quoted

    score = 0
    signals: list[str] = []

    if profanity:
        score += min(len(profanity), 2) * (2 if aimed_profanity else 1)
        signals.append("profanity" + ("+aimed" if aimed_profanity else ""))
    if annoyance:
        score += min(len(annoyance), 2)
        signals.append("complaint")
    if escalation:
        score += min(len(escalation), 2)
        signals.append("escalation")
    if intensifier:
        score += 1
        signals.append("intensifier")
    if addressed and (profanity or annoyance):
        score += 1
        signals.append("direct-address")
    if PUNCTUATION_BURST.search(masked):
        score += 1
        signals.append("punctuation-burst")
    if ELONGATION.search(masked) or ALLCAPS.search(masked):
        score += 1
        signals.append("caps-or-elongation")
    if had_quoted:
        score -= 1
        signals.append("pasted-block")
    if quoted:
        # A quote marker next to the words means the message reports someone
        # else's words. Cut hard. The reader, not the hook, is the last judge.
        score -= 2
        signals.append("quote-context")
    if profanity and near(masked, profanity, CODE_CONTEXT, 20):
        score -= 1
        signals.append("code-context")
    if len(ASCII_WORD.findall(masked)) >= 8 and len(profanity) == 1:
        score -= 1
        signals.append("long-english")
    if len(annoyance) >= 2 and addressed and not quoted:
        score += 1
        signals.append("piling-on")

    score = max(score, 0)

    # A single swearing word, aimed at nobody, is not enough. It can sit in a
    # pasted log or name a code symbol. Require one more piece of evidence.
    weak_profanity_only = (
        bool(profanity) and not aimed_profanity
        and not annoyance and not escalation
        and not PUNCTUATION_BURST.search(masked)
    )

    if score >= ALERT_SCORE and not weak_profanity_only:
        level = "angry"
    elif score >= ALERT_SCORE:
        level = "ambiguous"
    elif score == 1:
        level = "possible"
    else:
        level = "none"

    result.score = score
    result.level = level
    result.signals = signals
    return result
