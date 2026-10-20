#!/usr/bin/env python3
"""Fetch model-scoped weekly limits (e.g. "Fable") from the claude.ai OAuth usage API.

The status line payload only carries five_hour / seven_day. The usage API that
/usage itself calls also returns `limits[]`, including `kind=weekly_scoped` rows
with a model display name. This script prints a JSON list of those rows:
  [{"name": "Fable", "percent": 91, "resets_at": <epoch>, "severity": "critical"}]
It reads the OAuth token from ~/.claude/.credentials.json and never prints it.
Exit 0 with "[]" when nothing scoped is reported; non-zero on any failure.
"""
import datetime as dt
import json
import os
import sys
import urllib.request

CRED = os.path.join(os.path.expanduser("~"), ".claude", ".credentials.json")
URL = "https://api.anthropic.com/api/oauth/usage"


def epoch(s):
    if not s:
        return None
    try:
        return int(dt.datetime.fromisoformat(s).timestamp())
    except ValueError:
        return None


def main():
    with open(CRED) as f:
        tok = (json.load(f).get("claudeAiOauth") or {}).get("accessToken")
    if not tok:
        return 2
    req = urllib.request.Request(URL, headers={
        "Authorization": f"Bearer {tok}",
        "anthropic-beta": "oauth-2025-04-20",
        "User-Agent": "claude-usage-hook",
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        d = json.load(r)
    out = []
    for lim in d.get("limits") or []:
        if lim.get("kind") != "weekly_scoped":
            continue
        name = ((lim.get("scope") or {}).get("model") or {}).get("display_name")
        if not name or lim.get("percent") is None:
            continue
        out.append({"name": str(name), "percent": round(float(lim["percent"])),
                    "resets_at": epoch(lim.get("resets_at")), "severity": lim.get("severity")})
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(1)
