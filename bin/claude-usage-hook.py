#!/usr/bin/env python3
"""Render usage lines from the caches written by claude-usage-statusline.sh.

modes: prompt (UserPromptSubmit) / stop (Stop) / statusline (one-line summary)
Cache layout in <dir>:
  claude-usage.json  {"ts":..., "rate_limits": {"five_hour": {"used_percentage", "resets_at"}, "seven_day": {...}}}
  codex-usage.json   {"primary": {"usedPercent", "resetsAt"}, "secondary": {...}}   (codex app-server rateLimits)
  claude-scoped.json [{"name": "Fable", "percent", "resets_at", "severity"}]   (model-scoped weekly limits, OAuth usage API)
  usage-hook-state.json  last prompt/stop snapshot, used for the per-turn delta
"""
import datetime as dt
import json
import os
import sys
import time

mode, D = sys.argv[1], sys.argv[2]
S = os.path.join(D, "usage-hook-state.json")
LANG = os.environ.get("CLAUDE_USAGE_LANG") or ("ja" if os.environ.get("LANG", "").startswith("ja") else "en")
STYLE = os.environ.get("CLAUDE_USAGE_STATUSLINE", "0")  # "1" = percentages, "full" = with reset times
CLOCK = os.environ.get("CLAUDE_USAGE_CLOCK", "1")  # "0" hides the [clock] line on each prompt


def clock_line():
    """Local wall-clock time in the machine's zone (honours TZ / /etc/localtime)."""
    now = dt.datetime.now().astimezone()
    offset = now.strftime("%z")
    offset = f"{offset[:3]}:{offset[3:]}" if offset else ""
    zone = now.tzname() or ""
    if LANG == "ja":
        wd = "月火水木金土日"[now.weekday()]
        return f"[clock] {now.strftime('%Y-%m-%d')} ({wd}) {now.strftime('%H:%M')} {zone} (UTC{offset})"
    return f"[clock] {now.strftime('%Y-%m-%d %a %H:%M')} {zone} (UTC{offset})"


def load(p):
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return None


def pct(v):
    return None if v is None else round(float(v))


c = (load(os.path.join(D, "claude-usage.json")) or {}).get("rate_limits") or {}
x = load(os.path.join(D, "codex-usage.json")) or {}
cur = {
    "ts": time.time(),
    "c5": pct(c.get("five_hour", {}).get("used_percentage")),
    "c7": pct(c.get("seven_day", {}).get("used_percentage")),
    "c5r": c.get("five_hour", {}).get("resets_at"),
    "c7r": c.get("seven_day", {}).get("resets_at"),
    "x5": pct((x.get("primary") or {}).get("usedPercent")),
    "x7": pct((x.get("secondary") or {}).get("usedPercent")),
    "x5r": (x.get("primary") or {}).get("resetsAt"),
    "x7r": (x.get("secondary") or {}).get("resetsAt"),
}
scoped = [r for r in (load(os.path.join(D, "claude-scoped.json")) or []) if isinstance(r, dict) and r.get("name")]
if os.environ.get("CLAUDE_USAGE_SCOPED", "1") == "0":
    scoped = []
for i, r in enumerate(scoped[:3]):
    cur[f"s{i}"] = pct(r.get("percent"))
    cur[f"s{i}r"] = r.get("resets_at")
    cur[f"s{i}n"] = r["name"]
st = load(S) or {}


def when(ts):
    if not ts:
        return "?"
    t = dt.datetime.fromtimestamp(ts).astimezone()  # local timezone (honours TZ)
    return t.strftime("%d日%H:%M") if LANG == "ja" else t.strftime("%d %H:%M")


def fmt(a, b, ra, rb):
    a = "-" if a is None else f"{a}%"
    b = "-" if b is None else f"{b}%"
    return f"5h {a} (reset {when(ra)}) / 7d {b} (reset {when(rb)})"


def delta(prev, key):
    if not prev or prev.get(key) is None or cur.get(key) is None:
        return None
    d = cur[key] - prev[key]
    return d if d >= 0 else None  # a reset happened in between: no delta


def save():
    tmp = S + ".tmp"
    with open(tmp, "w") as f:
        json.dump(st, f)
    os.replace(tmp, S)


have_codex = os.environ.get("CLAUDE_USAGE_CODEX", "1") != "0" and (cur["x5"] is not None or cur["x7"] is not None)

if mode == "statusline":
    def short(ts):
        if not ts:
            return ""
        t = dt.datetime.fromtimestamp(ts).astimezone()
        same_day = t.date() == dt.datetime.now().astimezone().date()
        if LANG == "ja":
            return "→" + (t.strftime("%H:%M") if same_day else t.strftime("%d日%H:%M"))
        return "→" + (t.strftime("%H:%M") if same_day else t.strftime("%d %H:%M"))

    def cell(v, r):
        if v is None:
            return "-"
        return f"{v}%" + (short(r) if STYLE == "full" else "")

    parts = []
    if cur["c5"] is not None or cur["c7"] is not None:
        parts.append(f"C {cell(cur['c5'], cur['c5r'])}/{cell(cur['c7'], cur['c7r'])}")
    if have_codex:
        parts.append(f"X {cell(cur['x5'], cur['x5r'])}/{cell(cur['x7'], cur['x7r'])}")
    print(" | ".join(parts))  # model-scoped limits are shown in the prompt line only (status line stays short)
    sys.exit(0)

if mode == "stop":
    p = st.get("prompt")
    if p:
        st["last_turn"] = {k: delta(p, k) for k in ("c5", "c7", "x5", "x7", "s0", "s1", "s2")}
        st["last_turn"]["names"] = {k: cur.get(f"{k}n") for k in ("s0", "s1", "s2") if cur.get(f"{k}n")}
        st["last_turn"]["sec"] = round(cur["ts"] - p["ts"])
    st["stop"] = cur
    save()
    sys.exit(0)

# mode == "prompt"
line = f"[usage] Claude: {fmt(cur['c5'], cur['c7'], cur['c5r'], cur['c7r'])}"
for i in range(3):
    if cur.get(f"s{i}") is not None:
        line += f" | {cur[f's{i}n']} 7d {cur[f's{i}']}% (reset {when(cur[f's{i}r'])})"
if have_codex:
    line += f" | codex: {fmt(cur['x5'], cur['x7'], cur['x5r'], cur['x7r'])}"
lines = ([clock_line()] if CLOCK != "0" else []) + [line]
lt = st.get("last_turn")
if lt:
    def pm(v):
        return "-" if v is None else f"+{v}pt"
    label = "前ターンの消費" if LANG == "ja" else "last turn"
    s = f"[usage] {label}: Claude 5h {pm(lt['c5'])} / 7d {pm(lt['c7'])}"
    for k, name in (lt.get("names") or {}).items():
        if lt.get(k) is not None:
            s += f", {name} 7d {pm(lt[k])}"
    if have_codex:
        s += f", codex 5h {pm(lt['x5'])} / 7d {pm(lt['x7'])}"
    s += f" ({lt['sec']} s)"
    lines.append(s)
st["prompt"] = cur
st.pop("last_turn", None)
save()
print("\n".join(lines))
