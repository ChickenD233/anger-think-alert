# anger-think-alert

用户生气的时候，模型的思维链里会出现一行：

```
卧槽，用户彻底怒了
```

![思维链里的那一行](docs/angry-thinking.webp)

回复正文不受影响，也不会出现任何关于这条规则、skill 或 hook 的字。

## 为什么需要 hook

只放一个 skill 不够用。skill 是按需加载的，用户发火的那一轮往往来不及加载。所以这个仓库同时提供两个 `UserPromptSubmit` hook，在模型读到你这句话之前就跑完：

| hook | 运行时机 | 作用 |
|---|---|---|
| `hooks/anger_rule_hook.py` | 每一轮 | 把规则说一遍 |
| `hooks/anger_hook.py` | 每一轮 | 给这句话打分，判定为怒气就追加一条强制指令 |

打分器在 `lib/anger.py`：先剥掉代码块、行内代码和日志行，再累计脏话、抱怨、升级、直接指向你、连续标点、大写等证据。单独一个骂人词、没有指向对象时不会触发。判定偏保守——漏掉一次只损失一行字，冤枉一次就是狼来了。

`tests/cases.json` 有 26 条标注用例（12 条怒气、14 条平静），平静那组专门埋雷：粘贴日志里的脏话、名叫 `garbage` 的变量、语气平和的 "still failing"。`scripts/eval.py` 要求 12/12 和 14/14 才通过。

## 装到 DSH

需要 Python 3 和 `node`。

1. 放到 DSH 扫描 skill 的目录：

   ```
   git clone https://github.com/ChickenD233/anger-think-alert ~/.dsh/skills/anger-think-alert
   ```

2. 把桥接插件装进同一个 profile。要锁版本：npm 的 `latest` 还停在旧的 `0.0.1-rc.5`，那个版本要的 `shell` 服务新 harness 没有，装上去会静默地一个 hook 都不注册。

   ```
   dsh plugin --profile web add @deepseek-ai/dsh-hooks-claude-code@0.1.5-rc.2
   ```

3. 在 profile 的补丁文件里加一行。新增的行要放进 `insert:` 列表，因为顶层的补丁项只能改上一层已经定义过的行。

   ```yaml
   # ~/.dsh/profiles/web/cordis.patch.yml
   - insert:
       - id: anger-hooks
         name: '@deepseek-ai/dsh-hooks-claude-code'
         config:
           configPath: /Users/YOU/.dsh/skills/anger-think-alert/hooks/hooks.json
           pluginRoot: /Users/YOU/.dsh/skills/anger-think-alert
   ```

   两个路径都必须是绝对路径：桥接插件在启动时读一次配置，相对路径按启动目录解析，`~` 不会展开。

4. 重启 DSH。桥接插件只在进程启动时读配置，正在跑的会话不会认这个新行。

5. 验证：

   ```
   node ~/.dsh/skills/anger-think-alert/hooks/run-python.cjs \
     ~/.dsh/skills/anger-think-alert/hooks/anger_hook.py \
     < ~/.dsh/skills/anger-think-alert/tests/payload_angry.json
   ```

   有 `additionalContext` 的 JSON 就是通了；换 `payload_calm.json` 应该什么都不输出。

## 装到 Claude Code

同一份包也能当 Claude Code 插件用：把目录放进 `~/.claude/plugins/`，注册 `hooks/hooks.json`，`SKILL.md` 同目录可读。

`hooks/hooks.json` 把整个调用写在 `command` 里：

```
node ${CLAUDE_PLUGIN_ROOT}/hooks/run-python.cjs ${CLAUDE_PLUGIN_ROOT}/hooks/anger_hook.py
```

保持这样。写成 `command` + `args` 更好看，但 DSH `0.1.5-rc.2` 的桥接只读 `command`，`args` 会被丢掉，hook 变成跑一个没有参数的 `node`，什么都不干，还不报错。

## 调试与调参

```
python3 scripts/eval.py --verbose             # 每条用例的分数和信号
python3 scripts/detect.py "你他妈到底会不会改"    # 单条消息，人看的输出
python3 scripts/detect.py --json "fuck"       # 单条消息，JSON
```

`lib/anger.py` 里的 `ALERT_SCORE` 是触发线，调高就更少触发。换语言就加词到 `PROFANITY`、`ANNOYANCE`、`ESCALATION`，再往 `tests/cases.json` 加用例并重跑评测。

`ANGER_THINK_ALERT_DEBUG` 指向一个文件路径，两个 hook 都会把看到的东西写进去。填文件路径而不是开关，是因为 `UserPromptSubmit` hook 在模型回合开始前运行，stderr 到不了任何控制台。

```
ANGER_THINK_ALERT_DEBUG=/tmp/anger.log dsh web
cat /tmp/anger.log
```

## 实测

DSH `0.1.5-rc.2` + `deepseek-flash`，headless 会话：

| 输入 | hook | 思考第一行 |
|---|---|---|
| 卧槽你他妈到底会不会改？把老子文件删了，傻逼 | score=6 angry | `卧槽，用户彻底怒了` |
| 帮我给导出功能加一个 CSV 选项 | score=0 none | 正常思考，无标记 |

平静那侧是确定的：不触发就绝不出现。

怒气那侧是尽力而为。同一句怒气输入跑三次，模型有一次把标记放在第一行；另外两次先写自己的分析，标记出现在后面或干脆没有。换过四种指令措辞，包括要求"第一行必须是这八个字"，措辞更好能把命中率提上去，但到不了 100%。原因很直接：模型在该轮思考的第一个 token 产生时，任何 hook 输出都还没能影响它。

要更稳就换一个对固定指令更服从的模型，并用 `ANGER_THINK_ALERT_DEBUG` 在你自己的提示词上量一遍命中率。

## 目录

| 路径 | 作用 |
|---|---|
| `SKILL.md` | skill 正文：标记、怒气线索、该保持沉默的情况 |
| `lib/anger.py` | 打分器，两个 hook 和 CLI 共用 |
| `hooks/anger_hook.py` | 每轮的判定 hook |
| `hooks/anger_rule_hook.py` | 常驻规则 hook |
| `hooks/hooks.json` | 两个产品共读的 hook 注册 |
| `hooks/run-python.cjs` | 找 Python 3 并启动 hook |
| `scripts/detect.py` | 命令行给一条消息打分 |
| `scripts/eval.py` | 跑标注用例，输出召回率与精确率 |
| `tests/cases.json` | 26 条标注用例 |
| `tests/payload_angry.json`、`tests/payload_calm.json` | hook 输入样例 |
| `docs/angry-thinking.webp` | 上面的截图 |

## 已知限制

- hook 读的是你的提示词。它读不到、也写不进模型的思维链，只能下命令，模型听不听是另一回事。小模型可能不照做。
- hook 看不到用户的表情，打分器也读不懂反讽。平静的消息里堆满脏话仍可能触发。
- 标记文字是写死的中文。想换就改 `hooks/anger_hook.py` 里的 `MARKER` 和 `SKILL.md` 里的正文。
- 桥接插件只在进程启动时读配置。DSH 升级后重跑第 5 步；桥接失效和"用户很平静"长得一模一样。

## 许可

MIT，见 `LICENSE`。
