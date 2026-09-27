# claude-usage-hook

Shows your Claude Code quota (5-hour / 7-day windows) **inside the conversation**, on every prompt, plus how much the previous turn consumed. Optionally shows OpenAI Codex CLI quota next to it.

```
[usage] Claude: 5h 53% (reset 27 18:30) / 7d 70% (reset 01 20:00) | codex: 5h 44% (reset 27 19:46) / 7d 20% (reset 04 09:45)
[usage] last turn: Claude 5h +1pt / 7d +0pt, codex 5h +0pt / 7d +0pt (68 s)
```

Why: the model can then pace itself (delegate to a cheaper lane, wait for a reset) without you pasting numbers in. Your status line is left as it is; a compact `C 53%/70% | X 44%/20%` column is available as an opt-in.

## How it works

Claude Code passes `rate_limits` (five_hour / seven_day, used_percentage, resets_at) to the **statusLine** command on stdin. Nothing else exposes it, so:

1. `claude-usage-statusline.sh` is a shim in front of your status line: it caches that JSON to `$CLAUDE_USAGE_DIR/claude-usage.json` and prints your existing status line unchanged (`CLAUDE_USAGE_INNER`). With `CLAUDE_USAGE_STATUSLINE=1` it also appends a usage column.
2. `claude-usage-hook.sh prompt` (**UserPromptSubmit** hook) prints the `[usage]` lines from the cache; Claude Code adds hook stdout to the context.
3. `claude-usage-hook.sh stop` (**Stop** hook) snapshots the values so the next prompt can show the per-turn delta.
4. Codex: `codex_usage.sh` asks `codex app-server` (JSON-RPC `account/rateLimits/read`), cached 5 minutes, refreshed in the background so nothing blocks.

The status line only updates while Claude Code is running, so the first prompt of a session may show stale or empty values.

## Install as a plugin

```
/plugin marketplace add teru358/claude-usage-hook
/plugin install claude-usage-hook@claude-usage-hook
/claude-usage-hook:setup
```

The plugin installs the two hooks. `setup` shows the `settings.json` change and applies it **only after you confirm** (plugins cannot set `statusLine`; the shim is what caches the rate limits, so the hooks print nothing until it is wired). Nothing visible changes in the status line unless you opt in to the column.

## Install standalone

```
git clone https://github.com/teru358/claude-usage-hook
cd claude-usage-hook && ./install.sh          # copies to ~/.claude/hooks and prints the settings snippet
./install.sh --apply                          # or merge it into ~/.claude/settings.json (asks first, backup kept)
```

Requires bash, python3, Claude Code with statusLine support. Codex column needs the `codex` CLI logged in; set `CLAUDE_USAGE_CODEX=0` to disable.

### Status line

The shim passes your existing status line through (`CLAUDE_USAGE_INNER`, set by `setup`/`install.sh`). To also show the usage column, opt in:

```json
"statusLine": {"type": "command", "command": "CLAUDE_USAGE_STATUSLINE=1 CLAUDE_USAGE_INNER='~/.claude/my-statusline.sh' ~/.claude/hooks/claude-usage-statusline.sh"}
```

### Options (environment)

| var | default | meaning |
|---|---|---|
| `CLAUDE_USAGE_DIR` | `${XDG_RUNTIME_DIR:-/tmp}/claude-usage-$UID` | cache directory |
| `CLAUDE_USAGE_STATUSLINE` | `0` | `1` appends `C 5h%/7d% \| X 5h%/7d%` to the status line |
| `CLAUDE_USAGE_CODEX` | `1` | `0` disables the Codex lookup/column |
| `CLAUDE_USAGE_LANG` | `en` | `ja` for Japanese labels |
| `TZ` | system | reset times are shown in local time |

## Files

- `bin/claude-usage-statusline.sh` — statusLine shim; caches rate limits, passes your status line through (usage column opt-in)
- `bin/claude-usage-hook.sh` — hook entry (`prompt` / `stop`)
- `bin/claude-usage-hook.py` — rendering and per-turn delta
- `bin/codex_usage.sh` — Codex rate limits via `codex app-server` (`--json` for the cache)
- `install.sh`

## Notes

- Percentages are what Claude Code reports; the per-turn delta is the difference between the value at prompt time and at Stop, so a turn that crosses a reset shows `-`.
- Codex values come from `codex app-server` (JSON-RPC `account/rateLimits/read`, tested with codex-cli 0.157). If a newer CLI renames the method, only `bin/codex_usage.sh` needs updating.
- Hook stdout is context for the model. If you don't want the model to see it, use only the status line.

## 日本語

Claude Code の残量 (5 時間枠 / 7 日枠) を毎プロンプトで会話に注入し、前ターンの消費量も出す hook です。statusLine の stdin にだけ `rate_limits` が来るので、statusline でキャッシュに落とし、UserPromptSubmit hook が読んで context に出します。Codex CLI の残量も並べられます。`./install.sh --apply` で `~/.claude/settings.json` に組み込み。`CLAUDE_USAGE_LANG=ja` で日本語ラベル。

MIT
