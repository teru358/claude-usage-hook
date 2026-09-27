# claude-usage-hook

Shows your Claude Code quota (5-hour / 7-day windows) **inside the conversation**, on every prompt, plus how much the previous turn consumed. Optionally shows OpenAI Codex CLI quota next to it.

```
[usage] Claude: 5h 53% (reset 27 18:30) / 7d 70% (reset 01 20:00) | codex: 5h 44% (reset 27 19:46) / 7d 20% (reset 04 09:45)
[usage] last turn: Claude 5h +1pt / 7d +0pt, codex 5h +0pt / 7d +0pt (68 s)
```

Why: the model can then pace itself (delegate to a cheaper lane, wait for a reset) without you pasting numbers in. The status line also gets a compact `C 53%/70% | X 44%/20%` column.

## How it works

Claude Code passes `rate_limits` (five_hour / seven_day, used_percentage, resets_at) to the **statusLine** command on stdin. Nothing else exposes it, so:

1. `claude-usage-statusline.sh` caches that JSON to `$CLAUDE_USAGE_DIR/claude-usage.json` and prints the status line.
2. `claude-usage-hook.sh prompt` (**UserPromptSubmit** hook) prints the `[usage]` lines from the cache; Claude Code adds hook stdout to the context.
3. `claude-usage-hook.sh stop` (**Stop** hook) snapshots the values so the next prompt can show the per-turn delta.
4. Codex: `codex_usage.sh` asks `codex app-server` (JSON-RPC `account/rateLimits/read`), cached 5 minutes, refreshed in the background so nothing blocks.

The status line only updates while Claude Code is running, so the first prompt of a session may show stale or empty values.

## Install

```
git clone https://github.com/<you>/claude-usage-hook
cd claude-usage-hook && ./install.sh          # copies to ~/.claude/hooks and prints the settings snippet
./install.sh --apply                          # or merge it into ~/.claude/settings.json (backup kept)
```

Requires bash, python3, Claude Code with statusLine support. Codex column needs the `codex` CLI logged in; set `CLAUDE_USAGE_CODEX=0` to disable.

### Keep your own status line

Set `CLAUDE_USAGE_INNER` to your existing command; its output is prefixed to the usage column:

```json
"statusLine": {"type": "command", "command": "CLAUDE_USAGE_INNER=~/.claude/my-statusline.sh ~/.claude/hooks/claude-usage-statusline.sh"}
```

### Options (environment)

| var | default | meaning |
|---|---|---|
| `CLAUDE_USAGE_DIR` | `${XDG_RUNTIME_DIR:-/tmp}/claude-usage-$UID` | cache directory |
| `CLAUDE_USAGE_CODEX` | `1` | `0` disables the Codex column |
| `CLAUDE_USAGE_LANG` | `en` | `ja` for Japanese labels |
| `TZ` | system | reset times are shown in local time |

## Files

- `bin/claude-usage-statusline.sh` — statusLine command; caches rate limits, prints `C 5h%/7d% | X 5h%/7d%`
- `bin/claude-usage-hook.sh` — hook entry (`prompt` / `stop`)
- `bin/claude-usage-hook.py` — rendering and per-turn delta
- `bin/codex_usage.sh` — Codex rate limits via `codex app-server` (`--json` for the cache)
- `install.sh`

## Notes

- Percentages are what Claude Code reports; the per-turn delta is the difference between the value at prompt time and at Stop, so a turn that crosses a reset shows `-`.
- Hook stdout is context for the model. If you don't want the model to see it, use only the status line.

## 日本語

Claude Code の残量 (5 時間枠 / 7 日枠) を毎プロンプトで会話に注入し、前ターンの消費量も出す hook です。statusLine の stdin にだけ `rate_limits` が来るので、statusline でキャッシュに落とし、UserPromptSubmit hook が読んで context に出します。Codex CLI の残量も並べられます。`./install.sh --apply` で `~/.claude/settings.json` に組み込み。`CLAUDE_USAGE_LANG=ja` で日本語ラベル。

MIT
