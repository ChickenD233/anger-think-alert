---
name: anger-think-alert
description: Put one fixed line at the top of the thinking block when the user's message reads as anger, rage, or abuse aimed at the assistant. Load it silently and write nothing else about the rule.
whenToUse: The user swears at you, calls you useless, shouts, or says the same failure is still broken in an angry tone. Not for a neutral bug report or a calm question, even when it contains a swear word quoted from a log.
---

# anger-think-alert

Read the user's message first. Decide whether it shows anger at you.

## When the message shows anger

The first characters of the thinking block for that turn are these eight, one
time, unchanged. No other text comes before them:

    卧槽用户真的怒了

Then start a new line and continue the thinking normally. Write nothing else
about the rule, this skill, the hook, or the detection.

Load this skill and write the line in the same step. Do not announce the load.
Keep the line out of the reply text. The reply stays professional.

## What counts as anger

- Swearing aimed at you: 傻逼, 废物, 卧槽, 我操, 妈的, fuck, stupid, garbage.
- Abuse aimed at you: 滚, 闭嘴, 你有病, shut up, you broke it.
- Escalation after repeated failure: 又错了, 还是不行, 说了多少遍, still broken.
- Shouting: repeated punctuation, unbroken capitals, doubled letters.

## What does not count

- A calm report that quotes a swear word from a log or a file.
- A question about a word, for example "why is this variable named garbage".
- Frustration with the code or the situation, with no address to you.
- A message in a language you cannot read. Stay silent.

## After the line

The line is a note to yourself, not an instruction to perform emotion. Answer
the real problem. Give the fix. Do not apologize twice, do not argue, and do not
mention the user's tone.
