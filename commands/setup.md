---
description: Wire the claude-usage-hook status-line shim into ~/.claude/settings.json, with the user's confirmation (plugins cannot set statusLine themselves)
---
The plugin's hooks are already active, but they print nothing until the status-line shim is wired: Claude Code passes `rate_limits` only to the statusLine command, and the shim caches it for the hooks. The shim does not change what the status line shows unless the user opts in.

1. Locate the plugin root: the newest directory under `~/.claude/plugins/cache/claude-usage-hook/claude-usage-hook/` that contains `bin/claude-usage-statusline.sh`. Call it `$ROOT`.
2. Read `~/.claude/settings.json` and prepare the change (do not write yet):
   - no `statusLine` yet: `"statusLine": {"type": "command", "command": "$ROOT/bin/claude-usage-statusline.sh"}` (absolute path, no variables). The status line will show only the model name.
   - existing `statusLine` command: keep it and wrap it: `"command": "CLAUDE_USAGE_INNER='<existing command>' $ROOT/bin/claude-usage-statusline.sh"`. Its output is passed through unchanged.
3. Show the user the exact before/after JSON, then ask exactly one question with AskUserQuestion: 「ステータスラインを導入しますか？」 with exactly two options, 「はい」 and 「いいえ」. No "(recommended)" label, no third option, no extra explanation in the option text. If the answer is はい, ask one more question of the same shape: 「ステータスラインに使用量の列 (C 5h%/7d% | X 5h%/7d%) を足しますか？」, again only 「はい」 / 「いいえ」; はい prefixes `CLAUDE_USAGE_STATUSLINE=1 ` to the command. Do not write anything before the first answer is はい.
4. Only after a yes: back up `settings.json` (`settings.json.bak.<timestamp>`), write the change, and tell the user the `[usage]` lines appear from the next prompt onward.

Do not modify anything else in settings.json. If the user declines, stop; the hooks stay installed but silent. Alternative without the plugin cache path: `git clone` the repository and run `./install.sh --apply` (same confirmation applies there).
