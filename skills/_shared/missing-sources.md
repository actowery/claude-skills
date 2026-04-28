# Missing sources — graceful degradation protocol

All skills in this repo treat every data source as optional. A missing or unconfigured source never blocks completion — the skill finishes with what it has, then appends a **"More signal available"** note at the very end of its output (after the preview/draft/HTML, never before).

## When to append the note

After the main output is delivered (preview rendered, HTML written, draft shown), check each source listed below. If ANY were skipped or returned no data, append the note. If all sources fired and returned results, omit the note entirely — don't add noise when everything worked.

## Format

Append a plain-text section (no emoji) titled **"More signal available"** with one bullet per missing or empty source. Each bullet names what's missing, what it would add, and one concrete action to fix it.

Example:
```
---
More signal available

- Zoom transcripts: no meeting transcripts found in ~/Projects/Mgmt Assistant/transcripts/.
  Paste Zoom AI transcript text into a Claude Code session in that project to save them.
  Once saved, this skill will pull action items, topics, and meeting context automatically.

- Jira: Atlassian MCP not reachable or account not configured.
  Run `init <skill-name>` to set up your Atlassian account ID, or connect the Atlassian MCP
  in your Claude Code settings. Adds ticket-level AI activity and release tracking.

- GitHub: no results — `gh` CLI may not be authenticated or no orgs are configured.
  Run `gh auth login` and add your org(s) to your config under `github.orgs`.
  Adds merged PRs, commits, and CLAUDE.md changes as AI adoption evidence.
```

Keep bullets tight — one sentence on what's missing, one on what it unlocks, one on how to fix it. No multi-paragraph explanations.

## Source checklist and what each one unlocks

Check each of these at the end of the research phase. Flag any that were skipped, empty, or errored.

| Source | Missing condition | What it unlocks |
|---|---|---|
| **Zoom transcripts** | `~/Projects/Mgmt Assistant/transcripts/` has no files in date window | Action items made in meetings, AI discussion context, 1:1 commitments |
| **Jira** | Atlassian MCP unreachable, or `atlassian_account_id` absent from config | Ticket-level AI activity, releases, escalations, in-progress work |
| **Slack (public)** | Slack MCP unreachable, or `slack_user_id` absent from config | Team AI discussions, announcements, @-mentions |
| **Slack (private)** | `slack_search_mode` is `"public"` | DMs, private channel threads — often where real decisions happen |
| **Outlook** | Outlook/M365 MCP unreachable | Read-but-unreplied emails, escalation threads, release notifications |
| **GitHub** | `gh` unauthenticated, or `github.orgs` empty in config | Merged PRs, commits, CLAUDE.md additions — the highest-signal shipped-work source |
| **Claude Code logs** | `~/.claude/projects/` empty, or `scan_claude_logs: false` | Day-to-day Claude session counts, skill invocations, projects touched |

## What "missing" means per source

- **Zoom transcripts**: `Glob` finds no `.md` files in `~/Projects/Mgmt Assistant/transcripts/` whose `date:` frontmatter falls in the window.
- **Jira**: MCP call throws or returns a connection error; OR config has no `atlassian_account_id`.
- **Slack (public)**: MCP call throws or returns a connection error; OR config has no `slack_user_id`.
- **Slack (private)**: `slack_search_mode` is not `"public_and_private"` in config.
- **Outlook**: MCP call throws or returns a connection error.
- **GitHub**: `gh` returns an auth error; OR `github.orgs` is empty/absent; OR the script isn't found.
- **Claude Code logs**: `~/.claude/projects/` has no `.jsonl` files in the window; OR `scan_claude_logs: false`.

A source that fires but returns zero results for the window is NOT missing — it ran clean, there was just nothing to find. Only flag sources that couldn't run at all, or whose config is absent.

## Tone

The note is informational, not alarming. The skill did its job. This section just lets the user know they could get more out of it. Write it as a quiet footnote, not a warning banner.
