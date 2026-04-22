#!/usr/bin/env python3
"""
Scan local Claude Code session logs for AI-activity signal.

Walks `~/.claude/projects/*/*.jsonl` (or `--claude-log-dir` override), filters
events to the given date window, and emits a per-session summary plus an
aggregate so the drafting model can write informed "I used Claude for X this
week" content.

Usage:
    scan_claude_logs.py --start 2026-04-14 --end 2026-04-18
    scan_claude_logs.py --start ... --end ... --claude-log-dir ~/.claude/projects

Output (JSON on stdout):
{
  "window": {"start": "...", "end": "..."},
  "projects_touched": ["Skills", "Mac-Maintenance", ...],
  "sessions": [
     {"session_id": "...", "project": "Skills", "started_at": "...",
      "ended_at": "...", "user_msg_count": N, "assistant_msg_count": N,
      "tool_counts": {"Bash": 12, "Edit": 3, ...},
      "skills_invoked": ["anthropic-skills:skill-creator", ...]}
  ],
  "aggregate": {
     "sessions_total": N,
     "active_days": N,
     "sessions_per_day": {"2026-04-14": N, ...},
     "tool_counts_total": {"Bash": N, "Edit": N, ...},
     "skills_invoked_total": {"skill-name": N, ...}
  }
}

Reads timestamps as ISO UTC. Events outside the window are skipped. Runs
with no external deps (stdlib only).
"""

import argparse
import collections
import datetime as dt
import json
import os
import sys
from pathlib import Path


def parse_iso(s):
    """Parse an ISO 8601 timestamp into a datetime (UTC). Returns None on failure."""
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return dt.datetime.fromisoformat(s)
    except Exception:
        return None


def slug_to_project(slug):
    """Turn a directory slug like `-Users-adrian-towery-Projects-Skills` into a short
    project name like `Skills`. Takes the final path segment after the last `/` or `-`."""
    if not slug:
        return ""
    s = slug.lstrip("-")
    # Split on `-` and use the last non-empty, non-lowercase-English-noise segment.
    parts = [p for p in s.split("-") if p]
    if parts:
        return parts[-1]
    return slug


def scan_file(path, start, end):
    """Yield parsed event dicts from a JSONL file whose timestamp falls within
    [start, end] (inclusive). Also yields timestampless events that carry useful
    metadata (e.g. user messages with cwd)."""
    try:
        with open(path, "r", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = parse_iso(ev.get("timestamp"))
                if ts is not None:
                    d = ts.date()
                    if d < start or d > end:
                        continue
                yield ev
    except OSError:
        return


def summarize_session(events):
    """Given an iterable of events from one session (already window-filtered),
    produce a summary dict."""
    user_count = 0
    assistant_count = 0
    tool_counts = collections.Counter()
    skills_invoked = []
    started = None
    ended = None
    cwd = None
    session_id = None

    for ev in events:
        ts = parse_iso(ev.get("timestamp"))
        if ts:
            if started is None or ts < started:
                started = ts
            if ended is None or ts > ended:
                ended = ts
        if not session_id and ev.get("sessionId"):
            session_id = ev.get("sessionId")
        if not cwd:
            c = ev.get("cwd")
            if c:
                cwd = c

        t = ev.get("type")
        if t == "user":
            user_count += 1
        elif t == "assistant":
            assistant_count += 1
            # Extract tool uses from the message content.
            msg = ev.get("message") or {}
            content = msg.get("content") or []
            if isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "tool_use":
                        name = block.get("name") or ""
                        tool_counts[name] += 1
                        if name == "Skill":
                            inp = block.get("input") or {}
                            sk = inp.get("skill")
                            if sk:
                                skills_invoked.append(sk)

    return {
        "session_id": session_id,
        "cwd": cwd,
        "started_at": started.isoformat() if started else None,
        "ended_at": ended.isoformat() if ended else None,
        "user_msg_count": user_count,
        "assistant_msg_count": assistant_count,
        "tool_counts": dict(tool_counts),
        "skills_invoked": skills_invoked,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--start", required=True, help="ISO date, e.g. 2026-04-14")
    p.add_argument("--end", required=True, help="ISO date, inclusive")
    p.add_argument("--claude-log-dir", default=None,
                   help="Default: ~/.claude/projects")
    args = p.parse_args()

    start_d = dt.date.fromisoformat(args.start)
    end_d = dt.date.fromisoformat(args.end)

    base = Path(os.path.expanduser(args.claude_log_dir or "~/.claude/projects"))
    if not base.exists():
        print(json.dumps({
            "window": {"start": args.start, "end": args.end},
            "error": f"claude log dir does not exist: {base}",
            "projects_touched": [],
            "sessions": [],
            "aggregate": {"sessions_total": 0},
        }, indent=2))
        return

    sessions = []
    projects = set()
    sessions_per_day = collections.Counter()
    tool_total = collections.Counter()
    skill_total = collections.Counter()

    for project_dir in sorted(base.iterdir()):
        if not project_dir.is_dir():
            continue
        project_name = slug_to_project(project_dir.name)
        # Each top-level .jsonl inside the project dir is one session log.
        for jsonl in sorted(project_dir.glob("*.jsonl")):
            events = list(scan_file(jsonl, start_d, end_d))
            if not events:
                continue
            summ = summarize_session(events)
            # Prefer the cwd basename when present — it's the directory name as
            # seen by Claude at session time, which is more reliable than
            # parsing the mangled slug.
            if summ.get("cwd"):
                summ["project"] = os.path.basename(summ["cwd"]) or project_name
            else:
                summ["project"] = project_name
            sessions.append(summ)
            projects.add(summ["project"])
            if summ["started_at"]:
                day = summ["started_at"][:10]
                sessions_per_day[day] += 1
            for name, n in summ["tool_counts"].items():
                tool_total[name] += n
            for s in summ["skills_invoked"]:
                skill_total[s] += 1

    sessions.sort(key=lambda s: s.get("started_at") or "")

    out = {
        "window": {"start": args.start, "end": args.end},
        "projects_touched": sorted(projects),
        "sessions": sessions,
        "aggregate": {
            "sessions_total": len(sessions),
            "active_days": len(sessions_per_day),
            "sessions_per_day": dict(sorted(sessions_per_day.items())),
            "tool_counts_total": dict(tool_total.most_common()),
            "skills_invoked_total": dict(skill_total.most_common()),
        },
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
