# anger-think-alert

Mark a turn in the model's thinking when the user is angry at the model.

The user swears at the assistant. The model's next thinking block opens with one
fixed line:

```
卧槽用户真的怒了
```

Then the thinking continues as usual. The reply text stays clean. Nothing about
the rule, the skill, or the detection appears anywhere.

Works with DeepSeek Harness (DSH) and with Claude Code, because both run the
same `hooks.json` command-hook format and both read a `SKILL.md` bundle.

## The problem this solves

A skill alone cannot do this. A skill is loaded on demand, so the turn where the
user is angry is the turn where the load comes too late. `anger-think-alert`
adds two `UserPromptSubmit` hooks that run before the model reads the message:

| Hook | Runs | Effect |
|---|---|---|
| `hooks/anger_rule_hook.py` | every prompt | states the marker rule once |
| `hooks/anger_hook.py` | every prompt | scores the prompt, and on a detected anger hit adds a direct order for that turn |

The scorer in `lib/anger.py` is a weighted evidence counter. It strips code
fences, inline code, and log lines first, so a pasted stack trace does not fake a
hit. It then weighs swearing, complaints, escalation, direct address,
punctuation bursts, and capitals. A single swearing word aimed at nobody does
not fire on its own.

The scorer is deliberately conservative. A missed angry turn costs one line. A
marker on a calm turn tells the user the tool cries wolf. `tests/cases.json`
holds 26 labeled messages, 12 angry and 14 calm, with the calm set loaded with
traps: swearing inside a pasted log, a variable named `garbage`, a calm "still
failing" question. `scripts/eval.py` requires 12/12 and 14/14 to pass.

## Install in DSH

Prerequisite: Python 3 and `node` on PATH. The hook starts Python through
`hooks/run-python.cjs`, which finds `python3`, `python`, or Windows `py -3`.

1. Put the skill where DSH scans for skills:

   ```
   git clone https://github.com/ChickenD233/anger-think-alert ~/.dsh/skills/anger-think-alert
   ```

   DSH discovers it through its skill root. The path holds no spaces, which
   keeps the next step simple.

2. Install the hook bridge into the same profile. Pin the version to the one
   your harness ships. The npm `latest` tag still points at the old
   `0.0.1-rc.5`, which expects a `shell` service your harness may not provide,
   so an unpinned install silently registers no hooks.

   ```
   dsh plugin --profile web add @deepseek-ai/dsh-hooks-claude-code@0.1.5-rc.2
   ```

3. Add the hook row to the profile patch file. Replace `web` with your profile
   name. A new row goes in an `insert:` list, because a top-level patch entry
   only edits a row that an earlier layer already defined.

   ```yaml
   # ~/.dsh/profiles/web/cordis.patch.yml
   - insert:
       - id: anger-hooks
         name: '@deepseek-ai/dsh-hooks-claude-code'
         config:
           configPath: /Users/YOU/.dsh/skills/anger-think-alert/hooks/hooks.json
           pluginRoot: /Users/YOU/.dsh/skills/anger-think-alert
   ```

   `configPath` and `pluginRoot` must be absolute. The bridge reads the config
   one time at startup, so a relative path resolves against the launch
   directory, and `~` is not expanded.

4. Restart DSH. The bridge reads its config at process start, so a running
   session does not pick up the new row.

5. Check that the hooks fire:

   ```
   node ~/.dsh/skills/anger-think-alert/hooks/run-python.cjs \
     ~/.dsh/skills/anger-think-alert/hooks/anger_hook.py \
     < ~/.dsh/skills/anger-think-alert/tests/payload_angry.json
   ```

   The command prints one JSON line that holds `additionalContext`. The calm
   payload prints nothing.

## Install in Claude Code

The same bundle works as a Claude Code plugin. Point the plugin marketplace at
this repository, or copy the directory into `~/.claude/plugins/` and register
`hooks/hooks.json`. Claude Code reads `SKILL.md` from the same directory.

## Files

| Path | Role |
|---|---|
| `SKILL.md` | the skill body: the marker, the anger cues, the silence cues |
| `lib/anger.py` | the scorer, shared by both hooks and the CLI |
| `hooks/anger_hook.py` | the per-turn detection hook |
| `hooks/anger_rule_hook.py` | the standing rule hook |
| `hooks/hooks.json` | the hook registration both products read |
| `hooks/run-python.cjs` | finds a Python 3 interpreter and starts a hook |
| `scripts/detect.py` | score one message from the shell |
| `scripts/eval.py` | run the labeled cases and print recall and precision |
| `tests/cases.json` | 26 labeled messages |
| `tests/payload_angry.json`, `tests/payload_calm.json` | hook payload fixtures |

## Tune it

```
python3 scripts/eval.py --verbose          # per-case score and signals
python3 scripts/detect.py "你他妈到底会不会改"   # one message, human output
python3 scripts/detect.py --json "fuck"    # one message, JSON
```

`ALERT_SCORE` in `lib/anger.py` sets the firing threshold. Raise it to fire
less. Add words to `PROFANITY`, `ANNOYANCE`, or `ESCALATION` for a new language,
then add cases to `tests/cases.json` and rerun the eval.

Debug one hook run by pointing `ANGER_THINK_ALERT_DEBUG` at a file path. Both
hooks then write what they saw. The path is a file, not a flag, because a
`UserPromptSubmit` hook runs before the model turn opens and its stderr reaches
no console.

```
ANGER_THINK_ALERT_DEBUG=/tmp/anger.log dsh --profile web
cat /tmp/anger.log        # 16:11:02 score=3 level=angry signals=profanity+aimed,direct-address
```

## Limits

- The hook reads the prompt text. It does not read the model's thinking, and it
  cannot write into it. It plants an order, and the model obeys or does not.
- A hook cannot see the user's face, and the scorer cannot read sarcasm. A calm
  message with heavy swearing in it can still fire.
- The marker line is Chinese and fixed. Change `MARKER` in `hooks/anger_hook.py`
  and the text in `SKILL.md` if you want another line.

## License

MIT. See `LICENSE`.
