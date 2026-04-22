# Data sources

Five sources feed each draft. Fire them in parallel once the date window and the user's column targets are known.

## `${XDG_CONFIG_HOME:-$HOME/.config}/ai-weekly-update/user.json` schema

Per-user file, auto-produced by Phase 0 init and gitignored. Not meant to be hand-edited — re-run init instead.

```json
{
  "display_name": "Alex Example",
  "display_name_overrides": ["Alex R. Example"],
  "atlassian_account_id": "712020:...",
  "slack_user_id": "U00...",
  "github_username": "alexexample",
  "email": "alex.example@company.com",
  "slack_search_mode": "public",
  "github": {
    "orgs": ["your-org"]
  },
  "ai_keywords": ["Claude", "Anthropic", "CLAUDE.md", "AI", "agent", "skill", "LLM"],
  "jira_ai_labels": ["AI", "Claude", "Devx"],
  "scan_claude_logs": true,
  "claude_log_dir": "~/.claude/projects",
  "team": {
    "name": "DevX",
    "members": [
      {"display_name": "Member One", "atlassian_account_id": "...",
       "slack_user_id": "...", "github_username": "memone",
       "email": "member.one@company.com"}
    ]
  },
  "cached_at": "YYYY-MM-DD",
  "cache_source": "user_confirmed"
}
```

- `slack_search_mode`: `"public"` (default) or `"public_and_private"` — see Slack section for opt-in semantics.
- `ai_keywords`: post-filter on PR titles / commit messages / Slack text. Tune to your organization's vocabulary.
- `display_name_overrides`: any alternate names your row might appear under (middle initial, nickname).
- `scan_claude_logs`: if false, skip local log scanning entirely.
- `team`: **optional**. Set only if the user manages a team and wants team activity included in the Wins draft. Members need at least `display_name`; whichever IDs are present enable the matching source (missing `github_username` → skip GitHub for that member, etc.).

## Jira

### Your AI-related issues
```
assignee = currentUser()
AND (labels in (<jira_ai_labels>) OR text ~ "Claude" OR text ~ "Anthropic" OR text ~ "CLAUDE.md")
AND updated >= "<start>" AND updated <= "<end>"
```

### Team's AI-adjacent tickets (you're reporter or watcher)
```
(reporter = currentUser() OR watcher = currentUser())
AND labels in (<jira_ai_labels>)
AND updated >= "<start>" AND updated <= "<end>"
```

Use both; dedupe on issue key.

## Slack

Tool selection: per `slack_search_mode`. Announce at Phase 4 start; respect per-run `public only` downgrade.

Three scoped searches:

**Your AI-related messages:**
```
from:<@your_slack_id>
  (Claude OR Anthropic OR "AI" OR skill OR CLAUDE.md OR agent)
  after:<start> before:<end>
```

**Team-channel AI discussions:**
```
in:#<team-channel>
  (Claude OR Anthropic OR CLAUDE.md OR "AI adoption" OR agent OR /provision OR skill)
  after:<start> before:<end>
```

**Private threads you participated in** (only if private mode is on):
```
to:me (Claude OR Anthropic OR CLAUDE.md) after:<start> before:<end>
```

Dedupe by `message_ts`. Keep permalinks for citation.

## Outlook

`outlook_email_search` with keywords from `ai_keywords` + your team's common AI subjects. Useful patterns to surface: `CLAUDE.md`, `API key`, `Anthropic`, escalations mentioning AI tooling.

Skip auto-digests (e.g. Jira notification emails) when they don't add new signal beyond the Jira search.

## GitHub

Requires `gh` authenticated with `repo` scope. Two modes via `scripts/search_github.py`:

**PRs — authored PRs, optionally AI-filtered, optionally team-fanned-out:**
```
scripts/search_github.py prs \
  --config ${XDG_CONFIG_HOME:-$HOME/.config}/ai-weekly-update/user.json \
  --start <YYYY-MM-DD> --end <YYYY-MM-DD> \
  [--state merged|open|all] \
  [--ai-filter] \
  [--include-team]
```

Add `--include-team` to query every `team.members[].github_username` in addition to the user's handle. Results are deduplicated on PR URL; each result carries the `display_name` of the author so the drafting model can write "<name> shipped <PR>" sentences correctly.

Run twice:
1. `--state merged` (shipped work in window)
2. `--state open` (in-flight)

Add `--ai-filter` to restrict to PRs whose title/body match your `ai_keywords` — use this for the AI-weekly draft. Run without the filter too to check for non-AI work you may still want to mention.

**Commits — authored commits in window:**
```
scripts/search_github.py commits \
  --config ${XDG_CONFIG_HOME:-$HOME/.config}/ai-weekly-update/user.json \
  --start <YYYY-MM-DD> --end <YYYY-MM-DD> \
  [--ai-filter] \
  [--include-team]
```

Particularly valuable for finding `CLAUDE.md` changes, skill files, and AI integration commits that may not have their own PR (e.g. direct pushes, doc updates). With `--include-team`, surfaces team members' individual commits — a common case for "Brónach added `CLAUDE.md` to four repos this week" stories.

## Team fan-out query patterns

When `team.members[]` is present, the other three remote sources (Jira, Slack, Outlook) should also scale up. Outlook stays personal-only because Microsoft Graph search reads the authenticated user's mailbox only without delegated-access setup.

**Jira — team+user assignee:**
```jql
assignee in (currentUser(), "<member1_account_id>", "<member2_account_id>", ...)
AND (labels in (<jira_ai_labels>) OR text ~ "Claude" OR text ~ "Anthropic" OR text ~ "CLAUDE.md")
AND updated >= "<start>" AND updated <= "<end>"
```

**Slack — team+user authored:**
```
(from:<@user_slack_id> OR from:<@member1_slack_id> OR from:<@member2_slack_id> ...)
  (Claude OR Anthropic OR CLAUDE.md OR AI OR skill OR agent)
  after:<start> before:<end>
```

When drafting, tag every finding with the `display_name` from the matching source so the Wins paragraph can attribute correctly.

## Claude Code logs

Local-only. Scans `~/.claude/projects/*/*.jsonl` for session activity in the window:

```
scripts/scan_claude_logs.py --start <YYYY-MM-DD> --end <YYYY-MM-DD>
```

Output includes:
- Projects touched (unique `cwd` basenames)
- Session count total + per-day
- Tool invocation counts (`Bash`, `Edit`, `mcp__*`, etc.)
- Skill invocations by name (most valuable AI-adoption signal)
- Per-session summary: start/end, user/assistant message counts

**Story-bullet material:**
- "Used Claude across N sessions in M projects this week"
- "Invoked the `<skill-name>` skill X times"
- "Sessions touched <project-list>" (concrete proof of AI in daily workflow)

**Privacy note:** this is local-only; no log contents leave the machine. The draft will surface skill names, tool counts, and project names — never individual messages.

## Parallelization

All five sources are independent within a window. Fire them in one batched message when possible. Cache raw JSON under `${XDG_CACHE_HOME:-$HOME/.cache}/ai-weekly-update/<pageId>/<YYYY-MM-DD>/` so re-runs don't re-query. Cache is deleted on successful publish.

## Attribution discipline

Keep a mental map during drafting: every bullet traces to at least one source. Example internal mapping (don't render in preview):
```
"Shipped /provision-test-infra aws skill" ← [GitHub commit abc123, Claude log 2026-04-16]
"Team onboarded to Claude Code" ← [Slack #devx 2026-04-15, JIRA ITHELP-147782]
```

If a column's research comes up empty, say so in the preview ("insufficient signal for Blockers this week — fill manually") rather than fabricating filler.
