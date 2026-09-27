---
description: Wire the claude-usage-hook status line into ~/.claude/settings.json (plugins cannot set statusLine themselves)
---
The claude-usage-hook plugin's hooks are already active. The status line is the only piece a plugin cannot install, and it is what feeds the cache the hooks read, so do this once:

1. Locate this plugin's install directory: it is the directory that contains `bin/claude-usage-statusline.sh` under `~/.claude/plugins/cache/claude-usage-hook/` (pick the newest version directory). Call it `$ROOT`.
2. Read `~/.claude/settings.json`.
   - If it has no `statusLine`, add: `"statusLine": {"type": "command", "command": "$ROOT/bin/claude-usage-statusline.sh"}` (use the absolute path, no variables).
   - If it already has a `statusLine` command, keep it and wrap it instead: `"command": "CLAUDE_USAGE_INNER='<existing command>' $ROOT/bin/claude-usage-statusline.sh"`.
3. Show the user the exact JSON you changed and tell them the status line updates on the next render; the `[usage]` lines appear from the next prompt onward.

Do not modify anything else in settings.json. If the user prefers, offer the standalone route: `git clone` the repository and run `./install.sh --apply` (that copies the scripts to `~/.claude/hooks` and does not depend on the plugin cache path).
