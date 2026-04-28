# Data sources

Same five sources as `ai-weekly-update`, with exec-framing notes on what to do with the signal once you have it.

## `${XDG_CONFIG_HOME:-$HOME/.config}/ai-exec-report/user.json` schema

```json
{
  "display_name": "Alex Example",
  "email": "alex.example@company.com",
  "atlassian_account_id": "712020:...",
  "slack_user_id": "U00...",
  "github_username": "alexexample",

  "boss_display_name": "Sam Boss",
  "boss_first_name": "Sam",
  "boss_email": "sam.boss@company.com",
  "boss_tone_preference": "balanced",
  "cc_list": [],

  "team": {
    "name": "Platform",
    "members": [
      {"display_name": "Taylor Example", "atlassian_account_id": "...",
       "slack_user_id": "...", "github_username": "taylor-example",
       "email": "taylor.example@company.com"}
    ]
  },

  "slack_search_mode": "public",
  "github": {"orgs": ["your-org"]},
  "ai_keywords": ["Claude", "Anthropic", "CLAUDE.md", "AI", "agent", "skill", "LLM"],
  "jira_ai_labels": ["AI", "Claude"],
  "scan_claude_logs": true,
  "claude_log_dir": "~/.claude/projects",

  "cached_at": "YYYY-MM-DD",
  "cache_source": "user_confirmed"
}
```

Boss fields are required (draft can't go anywhere without a recipient). Team is required (this skill only runs in manager mode). Everything else follows `ai-weekly-update`'s conventions.

## Jira

**Team + user AI-related activity:**
```
assignee in (currentUser(), <team_account_ids>)
AND (labels in (<jira_ai_labels>) OR text ~ "Claude" OR text ~ "Anthropic" OR text ~ "CLAUDE.md")
AND updated >= "<start>" AND updated <= "<end>"
```

**Team releases / closures:**
```
status in (Done, Closed, Resolved)
AND assignee in (<team_account_ids>)
AND resolved >= "<start>" AND resolved <= "<end>"
```

Shipped tickets matter more in this skill than in-flight, because leadership wants to know what actually landed. Prioritize closed/resolved tickets when selecting what to quote.

## Slack

Tool selected by `slack_search_mode`. Same opt-in rules as other skills.

**Team + user AI-related posts:**
```
(from:<@user> OR from:<@member1> OR from:<@member2> ...)
  (Claude OR Anthropic OR CLAUDE.md OR AI OR skill OR agent)
  after:<start> before:<end>
```

Useful **exclusively for framing and context** — the actual artifacts come from Jira and GitHub. If a member's best artifact is a Slack message ("Brónach's idea for the CI workflow was posted in #devx"), that's fine to mention but lead with the downstream PR/ticket.

## Outlook

Personal mailbox only. Useful for:
- **Escalation threads** the team resolved (leadership cares about customer-facing wins)
- **Inbound asks** about AI tooling the team fielded (shows the team being sought out)
- **Confluence notification emails** showing the team's work being referenced elsewhere

Skip Jira-notification emails (redundant with the Jira query).

## GitHub

Use `scripts/search_github.py` with `--include-team`:

```
scripts/search_github.py prs \
    --config "${XDG_CONFIG_HOME:-$HOME/.config}/ai-exec-report/user.json" \
    --start <date> --end <date> --state all --include-team

scripts/search_github.py commits \
    --config "${XDG_CONFIG_HOME:-$HOME/.config}/ai-exec-report/user.json" \
    --start <date> --end <date> --include-team
```

Run **both with and without `--ai-filter`**. This skill surfaces non-AI wins too when they're notable, because the audience cares about impact, not just the AI angle. But AI-tagged items are the headline.

**Merged PRs are the highest-signal artifact for this audience.** They represent "we shipped a thing." Prioritize them over open / draft PRs when picking what to quote.

## Claude Code logs

`scripts/scan_claude_logs.py --start <date> --end <date>` — same as other skills.

**How to use in exec context:** session counts and skill invocations are a useful *aggregate* indicator of AI adoption, but do NOT name-drop specific skills or tools in the email unless they were significant ("we built and use a `/provision-test-infra aws` skill for AWS testing"). Upper-management readers don't care about tool inventory; they care about outcomes.

Good use:
> The team ran 200+ Claude Code sessions across our four repos this week — Claude is now a daily tool, not an experiment.

Bad use:
> We made 221 `Bash` tool calls, 147 `Read` calls, and invoked `anthropic-skills:skill-creator` four times.

## Zoom meetings

Zoom AI Companion transcripts and summaries are available directly via the Zoom MCP. This is the **primary source** for surfacing cross-team collaboration, leadership commitments, and escalations discussed verbally that haven't landed in Jira/Slack yet.

### Primary: Zoom MCP

**Step 1 — Find meetings in the window:**
```
search_meetings(
  from: "<start>T00:00:00Z",
  to:   "<end>T23:59:59Z"
)
```
Note the `meeting_uuid` for each result. Prefer UUID over numeric `meeting_number` for recurring meetings.

**Step 2 — Pull assets per meeting:**
```
get_meeting_assets(meetingId: "<meeting_uuid>")
```
Key fields:
- `my_notes.transcript.transcript_items[]` — speaker-labeled transcript
- `meeting_summary` — AI-generated quick recap and next steps
- `participants` — attendee list (use to identify VP/director/cross-team presence)

**When to use in exec context:**
- `participants` including VP, director, or cross-team names → leadership touchpoints worth surfacing
- `meeting_summary.next_steps` → concrete commitments that can anchor an exec email paragraph
- `my_notes.transcript` → verify or quote a specific claim; don't fabricate from summaries alone

**Access note:** `has_transcript_permission: false` in search results can be misleading — call `get_meeting_assets` for any meeting you hosted regardless of that flag.

### Fallback: local transcript files

If Zoom MCP is unreachable, or for meetings predating the integration, check local files:
```
Glob: ~/Projects/Mgmt Assistant/transcripts/YYYY-MM-DD_*.md
```
Frontmatter fields: `date`, `participants`, `meeting_type` (`1on1`, `team`, `stakeholder`), `topics`, `action_items`. Read frontmatter for triage; read full body only to verify or quote.

## Parallelization and caching

Fire all six sources in parallel. Cache under `${XDG_CACHE_HOME:-$HOME/.cache}/ai-exec-report/<date>/` keyed by source. Re-runs within the same day reuse the cache. Cache is disposable.

## Selecting from the research output

Rich research will over-produce. When drafting, apply this hierarchy to pick what makes the email:

1. **Shipped artifacts** (closed Jira, merged PRs, landed CLAUDE.md files) — always lead with these
2. **Cross-team collaboration** (PR co-authored with another team, customer escalation resolved) — great for uplift
3. **In-flight work with near-term impact** (WIP PR, planned release next week) — include if it's notable
4. **Process / tooling shipped** (new CI workflow, new skill) — include once per email, not three times
5. **Slack-only activity** — only include if no downstream artifact exists AND the team member had nothing else

Per-member cap: **one paragraph, maximum**. Pick their top item and write about it. If two things are equally notable, one sentence each is better than two paragraphs.
