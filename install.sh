#!/usr/bin/env bash
# Copy the scripts to ~/.claude/hooks and print (or apply) the settings.json snippet.
#   ./install.sh            copy + print snippet
#   ./install.sh --apply    copy + merge into ~/.claude/settings.json (backup kept)
set -eu
src=$(cd "$(dirname "$0")" && pwd)/bin
dst=${CLAUDE_HOOKS_DIR:-$HOME/.claude/hooks}; mkdir -p "$dst"
cp "$src"/claude-usage-hook.sh "$src"/claude-usage-hook.py "$src"/claude-usage-statusline.sh "$src"/codex_usage.sh "$dst"/
chmod +x "$dst"/*.sh "$dst"/*.py
echo "installed to $dst"
snippet=$(cat <<JSON
{
  "hooks": {
    "UserPromptSubmit": [{"hooks": [{"type": "command", "command": "$dst/claude-usage-hook.sh prompt", "timeout": 10}]}],
    "Stop":             [{"hooks": [{"type": "command", "command": "$dst/claude-usage-hook.sh stop",   "timeout": 10}]}]
  },
  "statusLine": {"type": "command", "command": "$dst/claude-usage-statusline.sh"}
}
JSON
)
if [ "${1:-}" = "--apply" ]; then
  f=$HOME/.claude/settings.json
  echo; echo "This will change $f (hooks + statusLine shim; the status line output itself stays as it is)."
  read -r -p "Proceed? [y/N] " ans; [ "$ans" = "y" ] || { echo "aborted; nothing written"; exit 1; }
  [ -f "$f" ] && cp "$f" "$f.bak.$(date +%Y%m%d%H%M%S)"
  python3 - "$f" "$snippet" <<'PY'
import json, sys
path, snip = sys.argv[1], json.loads(sys.argv[2])
try: cur = json.load(open(path))
except Exception: cur = {}
hooks = cur.setdefault("hooks", {})
for ev, entries in snip["hooks"].items():
    lst = hooks.setdefault(ev, [])
    lst[:] = [e for e in lst if not any("claude-usage-hook.sh" in h.get("command", "") for h in e.get("hooks", []))]
    lst.extend(entries)
old = (cur.get("statusLine") or {}).get("command", "")
if old and "claude-usage-statusline.sh" not in old:
    cur["statusLine"] = {"type": "command", "command": f"CLAUDE_USAGE_INNER='{old}' " + snip["statusLine"]["command"]}
    print(f"statusLine wrapped; your previous status line ({old}) is passed through unchanged")
elif not old:
    cur["statusLine"] = snip["statusLine"]
json.dump(cur, open(path, "w"), indent=2, ensure_ascii=False); open(path, "a").write("\n")
print(f"merged into {path}")
PY
else
  echo; echo "add to ~/.claude/settings.json:"; echo "$snippet"
fi
