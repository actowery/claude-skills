#!/usr/bin/env python3
"""
GitHub signal for ai-weekly-update.

Two modes:
  prs     — search PRs authored by the user (merged / open / all)
  commits — search commits authored by the user in the window

Both accept --ai-filter to post-filter results by AI-related keywords in
title / body / commit message (matching the user's ai_keywords config).

Requires `gh` CLI installed and authenticated with `repo` scope.

Usage:
  search_github.py prs \
      --config "${XDG_CONFIG_HOME:-$HOME/.config}/ai-weekly-update/user.json" \
      --start 2026-04-14 --end 2026-04-18 \
      [--state merged|open|all]     # default merged
      [--ai-filter]                 # restrict to AI-keyword matches
      [--dry-run]

  search_github.py commits \
      --config "${XDG_CONFIG_HOME:-$HOME/.config}/ai-weekly-update/user.json" \
      --start 2026-04-14 --end 2026-04-18 \
      [--ai-filter]
      [--dry-run]

Output is JSON on stdout; one object per result. PRs and commits have slightly
different shapes — both include `source`, `repo`, `author`, `url`,
`title_or_message`, `created_at`, and (PRs) `state` / `closed_at` / `is_draft`.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


PR_JSON_FIELDS = "number,title,url,repository,author,state,createdAt,closedAt,labels,isDraft,body"
COMMIT_JSON_FIELDS = "sha,commit,repository,author,url"


def have_gh():
    return shutil.which("gh") is not None


def load_config(path):
    return json.loads(Path(path).read_text())


def ai_keyword_regex(cfg):
    keywords = cfg.get("ai_keywords") or ["Claude", "Anthropic", "CLAUDE.md", "AI"]
    escaped = [re.escape(k) for k in keywords if k]
    if not escaped:
        return None
    return re.compile("|".join(escaped), re.IGNORECASE)


# ---------- PR mode ----------

def gh_search_prs(handle, orgs, start, end, state, dry_run):
    cmd = ["gh", "search", "prs",
           "--author", handle,
           "--json", PR_JSON_FIELDS,
           "--limit", "100"]
    if state == "merged":
        cmd += ["--merged", f"{start}..{end}"]
    elif state == "open":
        cmd += ["--state", "open", "--created", f"{start}..{end}"]
    elif state == "all":
        cmd += ["--created", f"{start}..{end}"]
    for org in orgs:
        cmd += ["--owner", org]

    if dry_run:
        print("DRY-RUN:", " ".join(cmd), file=sys.stderr)
        return []

    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"warn: gh prs failed for {handle}: {r.stderr.strip()}", file=sys.stderr)
        return []
    try:
        return json.loads(r.stdout or "[]")
    except json.JSONDecodeError as e:
        print(f"warn: could not parse prs output for {handle}: {e}", file=sys.stderr)
        return []


def normalize_pr(pr, display_name):
    repo = pr.get("repository") or {}
    repo_full = repo.get("nameWithOwner") or repo.get("name") or ""
    author = pr.get("author") or {}
    labels = [l.get("name") for l in (pr.get("labels") or []) if isinstance(l, dict)]
    return {
        "source": "pr",
        "author": author.get("login"),
        "display_name": display_name,
        "repo": repo_full,
        "number": pr.get("number"),
        "title_or_message": pr.get("title"),
        "body": pr.get("body"),
        "url": pr.get("url"),
        "state": pr.get("state"),
        "is_draft": pr.get("isDraft"),
        "created_at": pr.get("createdAt"),
        "closed_at": pr.get("closedAt"),
        "labels": labels,
    }


def handles_to_query(cfg, include_team):
    """Return list of (github_username, display_name) tuples to search.

    Always includes the primary user. If include_team is True and the config
    has team.members[], each member with a github_username is appended.
    Missing handles produce a warning and are skipped (not fatal).
    """
    pairs = []
    primary = cfg.get("github_username")
    if primary:
        pairs.append((primary, cfg.get("display_name", "")))
    else:
        print("error: config is missing github_username. Re-run init.", file=sys.stderr)
        sys.exit(2)

    if include_team:
        team = cfg.get("team") or {}
        missing = []
        for m in team.get("members") or []:
            h = m.get("github_username")
            if h:
                pairs.append((h, m.get("display_name", "")))
            else:
                missing.append(m.get("display_name", "(unknown)"))
        if missing:
            print(f"warn: no github_username for team members: {', '.join(missing)}. "
                  "Add via init to include them.", file=sys.stderr)

    return pairs


def cmd_prs(args):
    cfg = load_config(args.config)
    orgs = (cfg.get("github") or {}).get("orgs") or []
    if not args.dry_run and not have_gh():
        print("error: gh CLI not installed. https://cli.github.com/", file=sys.stderr)
        sys.exit(2)

    pairs = handles_to_query(cfg, args.include_team)
    seen_urls = set()
    normalized = []
    for handle, display_name in pairs:
        prs = gh_search_prs(handle, orgs, args.start, args.end, args.state, args.dry_run)
        for pr in prs:
            url = pr.get("url")
            if url and url in seen_urls:
                continue
            seen_urls.add(url)
            normalized.append(normalize_pr(pr, display_name))

    if args.ai_filter:
        rx = ai_keyword_regex(cfg)
        if rx:
            normalized = [
                n for n in normalized
                if rx.search((n.get("title_or_message") or "") + " " + (n.get("body") or ""))
            ]

    normalized.sort(key=lambda r: (r.get("closed_at") or r.get("created_at") or ""), reverse=True)
    print(json.dumps(normalized, indent=2))


# ---------- commits mode ----------

def gh_search_commits(handle, orgs, start, end, dry_run):
    cmd = ["gh", "search", "commits",
           "--author", handle,
           "--author-date", f"{start}..{end}",
           "--json", COMMIT_JSON_FIELDS,
           "--limit", "100"]
    for org in orgs:
        cmd += ["--owner", org]

    if dry_run:
        print("DRY-RUN:", " ".join(cmd), file=sys.stderr)
        return []

    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"warn: gh commits failed for {handle}: {r.stderr.strip()}", file=sys.stderr)
        return []
    try:
        return json.loads(r.stdout or "[]")
    except json.JSONDecodeError as e:
        print(f"warn: could not parse commits output for {handle}: {e}", file=sys.stderr)
        return []


def normalize_commit(c, display_name):
    repo = c.get("repository") or {}
    repo_full = repo.get("nameWithOwner") or repo.get("name") or ""
    commit = c.get("commit") or {}
    msg = commit.get("message") or ""
    commit_author = commit.get("author") if isinstance(commit.get("author"), dict) else {}
    api_author = c.get("author") if isinstance(c.get("author"), dict) else {}
    return {
        "source": "commit",
        "author": api_author.get("login") or commit_author.get("name") or display_name,
        "display_name": display_name,
        "repo": repo_full,
        "sha": c.get("sha"),
        "title_or_message": msg.split("\n", 1)[0][:200],
        "body": msg,
        "url": c.get("url"),
        "created_at": commit_author.get("date"),
    }


def cmd_commits(args):
    cfg = load_config(args.config)
    orgs = (cfg.get("github") or {}).get("orgs") or []
    if not args.dry_run and not have_gh():
        print("error: gh CLI not installed.", file=sys.stderr)
        sys.exit(2)

    pairs = handles_to_query(cfg, args.include_team)
    seen = set()
    normalized = []
    for handle, display_name in pairs:
        raw = gh_search_commits(handle, orgs, args.start, args.end, args.dry_run)
        for c in raw:
            sha = c.get("sha")
            if sha and sha in seen:
                continue
            if sha:
                seen.add(sha)
            normalized.append(normalize_commit(c, display_name))

    if args.ai_filter:
        rx = ai_keyword_regex(cfg)
        if rx:
            normalized = [
                n for n in normalized
                if rx.search((n.get("title_or_message") or "") + " " + (n.get("body") or ""))
            ]

    normalized.sort(key=lambda r: (r.get("created_at") or ""), reverse=True)
    print(json.dumps(normalized, indent=2))


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("prs")
    pr.add_argument("--config", required=True)
    pr.add_argument("--start", required=True)
    pr.add_argument("--end", required=True)
    pr.add_argument("--state", default="merged", choices=["merged", "open", "all"])
    pr.add_argument("--ai-filter", action="store_true")
    pr.add_argument("--include-team", action="store_true",
                    help="Fan out to config.team.members[].github_username")
    pr.add_argument("--dry-run", action="store_true")
    pr.set_defaults(func=cmd_prs)

    pc = sub.add_parser("commits")
    pc.add_argument("--config", required=True)
    pc.add_argument("--start", required=True)
    pc.add_argument("--end", required=True)
    pc.add_argument("--ai-filter", action="store_true")
    pc.add_argument("--include-team", action="store_true",
                    help="Fan out to config.team.members[].github_username")
    pc.add_argument("--dry-run", action="store_true")
    pc.set_defaults(func=cmd_commits)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
