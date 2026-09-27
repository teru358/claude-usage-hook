#!/usr/bin/env bash
# Claude Code statusline shim: cache the rate limits Claude Code passes on stdin
# (`rate_limits.five_hour` / `seven_day`) so the prompt hook can read them.
# By default it changes NOTHING visible: it prints your existing status line
# (CLAUDE_USAGE_INNER) unchanged, or just the model name if you had none.
# A usage column is added only when you opt in with CLAUDE_USAGE_STATUSLINE=1.
#
# settings.json (installed by /claude-usage-hook:setup after your confirmation):
#   "statusLine": {"type": "command", "command": "CLAUDE_USAGE_INNER='<your old command>' <root>/bin/claude-usage-statusline.sh"}
# env:
#   CLAUDE_USAGE_DIR           cache dir (default: ${XDG_RUNTIME_DIR:-/tmp}/claude-usage-$UID)
#   CLAUDE_USAGE_INNER         your existing statusline command; its output is passed through
#   CLAUDE_USAGE_STATUSLINE=1  also append "C 5h%/7d% | X 5h%/7d%" to the status line (opt-in)
#   CLAUDE_USAGE_STATUSLINE=full  same, with reset times: "C 62%→18:30/71%→01 20:00"
#   CLAUDE_USAGE_CODEX=0       disable the codex (OpenAI Codex CLI) lookup
set -u
here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
D=${CLAUDE_USAGE_DIR:-${XDG_RUNTIME_DIR:-/tmp}/claude-usage-$(id -u)}; mkdir -p "$D"
input=$(cat)

# 1. cache Claude's rate limits for the hook
printf '%s' "$input" | python3 -c '
import json,sys,time
d=json.load(sys.stdin).get("rate_limits")
d and print(json.dumps({"ts":time.time(),"rate_limits":d}))' > "$D/claude-usage.json.tmp" 2>/dev/null \
  && [ -s "$D/claude-usage.json.tmp" ] && mv "$D/claude-usage.json.tmp" "$D/claude-usage.json"

# 2. refresh the codex cache in the background (app-server call takes ~6 s)
if [ "${CLAUDE_USAGE_CODEX:-1}" != "0" ] && command -v codex >/dev/null 2>&1; then
  cache=$D/codex-usage.json; age=999999
  [ -f "$cache" ] && age=$(( $(date +%s) - $(stat -c %Y "$cache") ))
  if [ "$age" -gt 300 ] && ! pgrep -f "[c]odex_usage.sh --json" >/dev/null; then
    setsid bash -c '"$1" --json > "$0.tmp" 2>/dev/null && mv "$0.tmp" "$0"' "$cache" "$here/codex_usage.sh" >/dev/null 2>&1 < /dev/null &
  fi
fi

# 3. render
inner=""
if [ -n "${CLAUDE_USAGE_INNER:-}" ]; then
  inner=$(printf '%s' "$input" | bash -c "$CLAUDE_USAGE_INNER" 2>/dev/null)
else
  inner=$(printf '%s' "$input" | python3 -c 'import json,sys;print("["+json.load(sys.stdin).get("model",{}).get("display_name","?")+"]")' 2>/dev/null)
fi
if [ "${CLAUDE_USAGE_STATUSLINE:-0}" = "1" ] || [ "${CLAUDE_USAGE_STATUSLINE:-0}" = "full" ]; then
  line=$(python3 "$here/claude-usage-hook.py" statusline "$D")
  [ -n "$line" ] && { echo "${inner:+$inner | }${line}"; exit 0; }
fi
echo "$inner"
