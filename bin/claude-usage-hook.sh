#!/usr/bin/env bash
# Claude Code hook: inject Claude (and optionally Codex) quota usage into the
# conversation on every prompt, plus how much the previous turn consumed.
#   UserPromptSubmit -> claude-usage-hook.sh prompt
#   Stop             -> claude-usage-hook.sh stop
set -u
here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
D=${CLAUDE_USAGE_DIR:-${XDG_RUNTIME_DIR:-/tmp}/claude-usage-$(id -u)}; mkdir -p "$D"
if [ "${CLAUDE_USAGE_CODEX:-1}" != "0" ] && command -v codex >/dev/null 2>&1; then
  cache=$D/codex-usage.json; age=999999
  [ -f "$cache" ] && age=$(( $(date +%s) - $(stat -c %Y "$cache") ))
  if [ "$age" -gt 300 ] && ! pgrep -f "[c]odex_usage.sh --json" >/dev/null; then
    setsid bash -c '"$1" --json > "$0.tmp" 2>/dev/null && mv "$0.tmp" "$0"' "$cache" "$here/codex_usage.sh" >/dev/null 2>&1 < /dev/null &
  fi
fi
exec python3 "$here/claude-usage-hook.py" "${1:-prompt}" "$D"
