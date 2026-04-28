# Data sources

Query patterns scoped to a specific target person. The user's identity is the second filter — every query is "what did this person do, and what does it tell me about how to talk to them tomorrow."

## `${XDG_CONFIG_HOME:-$HOME/.config}/1on1-prep/user.json` schema

See SKILL.md for the full schema. Key shape: `team.members[]` (direct reports), `manager` (the user's own boss, single object), `peers[]` (peer managers / cross-team / skip-levels). Each person has a `relationship` field used to pick the brief template.

## Person resolution

When matching a name argument:
1. First try `team.members[]` (most common case — preparing for a direct report 1:1)
2. Then `manager`
3. Then `peers[]`
4. Fuzzy match: full first name, partial last name, full display name. Return all matches if more than one.

If matched person has no `slack_user_id` / `atlassian_account_id` / `github_username`, skip those sources and flag in the missing-sources note. The skill still runs.

## Zoom — the action-item source

Two distinct queries.

### A. The previous 1:1 transcript

```
search_meetings(
  q: "<target_person_first_name>",
  from: "<today minus 90 days>T00:00:00Z",
  to:   "<today>T23:59:59Z"
)
```

Filter results client-side:
- `attendees[]` includes both user email and target email
- `attendee_size` is 2 (or 1 in rare cases — Zoom doesn't always count the host)
- `meeting_category == "history"` (already happened)

Sort by `meeting_end_time` descending. Take the most recent. Note its `meeting_uuid` — this is the previous 1:1.

Then:
```
get_meeting_assets(meetingId: "<meeting_uuid>")
```

Don't pre-filter by `has_transcript_permission`. Check `my_notes.has_my_notes` in the response. If true, mine the transcript per `references/transcript-mining.md`.

### B. Other meetings in the window where target person attended

```
search_meetings(
  from: "<window_start>T00:00:00Z",
  to:   "<window_end>T23:59:59Z"
)
```

Filter to meetings where target person is in `attendees[]`. For each, call `get_meeting_assets`. This catches:
- Cross-team meetings they were in (signals what's on their plate)
- Standups, planning, retros (signals team-level commitments they made)
- Customer calls, escalations (signals customer-facing pressure)

For these meetings, prefer `meeting_summary.quick_recap` over the full transcript — they're context, not the primary source.

## Jira — what they're working on, and where they're stuck

### Their assigned tickets in window
```jql
assignee = "<target_account_id>"
AND updated >= "<window_start>"
ORDER BY updated DESC
```

Categorize by status:
- `Done / Closed / Resolved` → "shipped" candidates for the brief
- `In Progress` with recent updates → "active work"
- `In Progress` with no recent activity → "in flight, possibly stuck"
- `To Do / Backlog` → usually skip (low signal)

### Their voice on others' tickets
```jql
issueFunction in commented("by <target_account_id> after <window_start>")
```

If issueFunction isn't available, fall back to:
```jql
comment ~ "<target_first_name>" AND updated >= "<window_start>"
```

Then read the most recent comment per ticket; keep ones authored by the target person. Useful signals: their questions on tickets, their disagreements, their requests for info.

### Tickets where they're mentioned
```jql
text ~ "@<target_display_name>" AND updated >= "<window_start>"
```

If the ticket has a comment ending in an `@<target>` mention with no follow-up reply from the target — they're being asked something they haven't answered.

## Slack — discussion + tone

Tool selected by `slack_search_mode`. Announce mode at Phase 3 start.

### Their messages
```
from:<@target_slack_id>
  after:<window_start> before:<window_end>
```

Read for: what they're discussing, who they're collaborating with, whether they're posting wins or frustration. Look for keywords: `blocked`, `still waiting`, `any update`, `bump`, `no idea`, `confused`. These are friction signals — frame them neutrally in the brief.

### Mentions of them
```
to:<@target_slack_id>
  after:<window_start> before:<window_end>
```

For each mention, check whether the target replied in-thread. Unanswered mentions older than `prep_defaults.open_commitment_threshold_days` are conversation crack candidates — worth raising in the 1:1.

### DMs (private mode only)
```
to:me from:<@target_slack_id>
  after:<window_start>
```

Reverse search:
```
from:me to:<@target_slack_id>
  after:<window_start>
```

Look for asks the user made of the target with no follow-up from target, and vice versa.

## Outlook — explicit communication

```
sender: "<target_email>"
afterDateTime: "<window_start>"
beforeDateTime: "<window_end>"
```

```
recipient: "<target_email>"
afterDateTime: "<window_start>"
beforeDateTime: "<window_end>"
```

Skip auto-notification senders (Jira/Confluence/CI/calendar). Threads where the target sent something and the user hasn't replied = candidate "follow up" topic for the 1:1.

## GitHub — code work

Via `scripts/search_github.py`:

### Their PRs
```
scripts/search_github.py prs \
    --config "${XDG_CONFIG_HOME:-$HOME/.config}/1on1-prep/user.json" \
    --start <window_start> --end <window_end> \
    --author "<target_github_username>" \
    --state all
```

(Run with `--author` flag — see "Note on search_github.py" below.)

Categorize:
- Merged → shipped work, kudos candidates
- Open with recent commits → active
- Open with no activity past `pr_stale_days` → stale, possible blocker

### PRs requesting their review
```
gh pr list --search "review-requested:<target_github_username>" --state open --json url,title,createdAt,updatedAt
```

For each, check whether they've reviewed. Old un-reviewed PRs assigned to them = backlog item to acknowledge.

### Their commits
```
scripts/search_github.py commits \
    --config "${XDG_CONFIG_HOME:-$HOME/.config}/1on1-prep/user.json" \
    --start <window_start> --end <window_end> \
    --author "<target_github_username>"
```

Useful for catching `CLAUDE.md` adds, doc updates, direct-to-main commits that don't have a PR.

## Note on search_github.py

`search_github.py` in this skill needs an `--author` filter. The shared script as it exists in other skills (`how-can-i-help`, `ai-weekly-update`) takes `--include-team` to fan out to all team members. For 1:1 prep, we want the opposite — narrow to a single person. The script in this skill's `scripts/` directory accepts `--author <github_username>` to override the user's own handle and target the specific person.

## Parallelization

All sources are independent. Fire them in one batched message. Cache raw JSON under `${XDG_CACHE_HOME:-$HOME/.cache}/1on1-prep/<person-slug>/<YYYY-MM-DD>/` so re-prepping the same person same day reuses queries.

Cache contents per person-day:
- `zoom-prior-1on1.json` — the prior 1:1 transcript
- `zoom-other-meetings.json` — all other meetings target attended in window
- `jira-assigned.json`, `jira-comments.json`, `jira-mentions.json`
- `slack-from.json`, `slack-mentions.json`, `slack-dms.json` (if private mode)
- `outlook-from.json`, `outlook-to.json`
- `github-prs.json`, `github-reviews.json`, `github-commits.json`

## Attribution

Every claim in the brief must trace to at least one source. Keep a mental mapping during synthesis:
```
"Closed CAT-2598 NatWest TAM" ← [JIRA CAT-2598 status=Done updated=2026-04-23]
"Open homework on firewall PR review" ← [transcript 2026-04-21 0930 line 12-15, no Jira ticket created]
```

If a section comes up empty, OMIT it. Don't pad. The brief's value is its honesty.
