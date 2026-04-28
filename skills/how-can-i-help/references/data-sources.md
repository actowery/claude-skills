# Data sources

Query patterns per source, biased toward **silence/staleness** rather than activity. Fresh items are explicitly excluded — this skill scans for what the manager probably doesn't already know about.

## `${XDG_CONFIG_HOME:-$HOME/.config}/how-can-i-help/user.json` schema

```json
{
  "display_name": "Alex Example",
  "email": "alex.example@company.com",
  "atlassian_account_id": "712020:...",
  "slack_user_id": "U00...",
  "github_username": "alexexample",

  "team": {
    "name": "Platform",
    "members": [
      {
        "display_name": "Taylor Example",
        "atlassian_account_id": "712020:...",
        "slack_user_id": "U00...",
        "github_username": "taylor-example",
        "email": "taylor.example@company.com"
      }
    ]
  },

  "slack_search_mode": "public",
  "github": {"orgs": ["your-org"]},

  "staleness_thresholds": {
    "slack_thread_silent_days": 7,
    "email_unreplied_days": 5,
    "jira_comment_unanswered_days": 14,
    "jira_assignee_silent_days": 21,
    "pr_stale_days": 7,
    "cross_team_mention_unacked_days": 5
  },

  "scan_window_days": 14,
  "customer_escalation_labels": ["Escalation", "TAM", "Support", "CustomerPriority"],

  "cached_at": "YYYY-MM-DD",
  "cache_source": "user_confirmed"
}
```

Threshold defaults in this schema are conservative (longer = fewer results, higher signal). Tune down if the skill feels thin; tune up if it's surfacing items the user was already aware of.

## Jira — finding stale-but-not-dead tickets

The key JQL trick is combining `commented` (a conversation happened within the window) with `updated` (no recent movement). An item is a crack if someone talked about it, and then nobody did for a while.

**1. Tickets where a teammate asked a question and got no response:**
```jql
assignee in (<team_account_ids>)
AND commented >= "-<scan_window_days>d"
AND commented <= "-<jira_comment_unanswered_days>d"
AND updated <= "-<jira_comment_unanswered_days>d"
AND statusCategory != Done
ORDER BY updated ASC
```

The window makes sure we're looking at recent-ish items (not truly abandoned 3-year-old tickets). The double-`commented` clause pins "someone commented between N and window days ago." The `updated <= -Nd` clause excludes anything touched since.

**2. Customer-escalation tickets with silence from the team side:**
```jql
(labels in (<customer_escalation_labels>) OR project in (<customer_projects>))
AND comment ~ "<customer_name_or_role>"
AND updated <= "-<email_unreplied_days>d"
AND statusCategory != Done
ORDER BY updated ASC
```

When scanning, read the most recent comment per ticket. If the author is external or customer-facing (TAM/CSM/Support), and no team-side reply followed, it's a crack.

**3. Tickets assigned to a team member and genuinely untouched:**
```jql
assignee in (<team_account_ids>)
AND updated <= "-<jira_assignee_silent_days>d"
AND statusCategory = "In Progress"
ORDER BY updated ASC
```

These are tickets declared as "in progress" but not progressing. Often a teammate forgot they had the ticket, or switched to other work and never moved the state back.

## Slack — unanswered threads and buried @-mentions

**1. Threads where the last reply was external and no team reply followed:**

Slack search doesn't directly support "last reply by" filters, so we query broadly and post-filter. For each team-facing channel (from `slack_channels`) — and the user's DMs if `slack_search_mode: public_and_private` is set:

```
in:<channel> after:<scan_start>
```

Client-side filter: for each result thread, read the thread via `slack_read_thread`; if the last reply is from outside the team (or from a team member using "waiting"/"bump"/"any update"/"following up" with no subsequent reply), it's a candidate. Staleness clock starts at last reply.

**2. Buried @-mentions:**
```
(to:@<user> OR @<team_name>) after:<scan_start>
```

Post-filter for messages with no in-thread reply from the user or a team member in the configured window.

**3. Gone-quiet teammates:**

Not a search per se — a sanity check against activity baseline. For each team member, count Slack messages in the past 7 days vs the past 30 days. Outliers (much quieter than baseline) get flagged for the Phase 3 scorer as candidate gone-quiet signals. Don't flag on absolute zero — many good reasons for zero (vacation, deep focus).

## Outlook — read-but-not-replied inbound

Query inbound email in the scan window:
```
afterDateTime: <scan_start>
beforeDateTime: <email_unreplied_days ago>
```

For each thread returned, check whether the user has a sent message in the same conversation thread AFTER the most recent inbound message. If not, it's a crack candidate. Prioritize:

- External senders (not `@company.com`)
- Subject lines with question marks, "following up", "bump", "status"
- `isRead: true` (user saw it) but no reply sent
- Not auto-notifications (Jira/Confluence/CI emails → skip)

**Skip** Outlook meeting acceptances, shared-calendar notifications, out-of-office replies, and anything from auto-notification senders.

## GitHub — stale PRs

Via `scripts/search_github.py`:

```
scripts/search_github.py prs \
    --config "${XDG_CONFIG_HOME:-$HOME/.config}/how-can-i-help/user.json" \
    --start <scan_start> --end <today> \
    --state open --include-team
```

Post-filter: PR `updatedAt` > `pr_stale_days` ago. Further filter for "review requested but no review" by inspecting the PR's review state (requires a second `gh` call per candidate):

```
gh pr view <url> --json reviewDecision,reviews,requestedReviewers
```

PRs with `requestedReviewers` non-empty and no `reviews` in the window are the clearest crack type — someone asked for a review and didn't get one.

## Claude Code logs — gone-quiet sanity check

`scripts/scan_claude_logs.py --start <N days ago>` gives per-day session counts across projects. If you want to infer "quiet for the team" vs "quiet for just one person," compare this (your own usage) against no-signal from teammates elsewhere. Only useful as a weak secondary signal for the gone-quiet category.

## Zoom meetings

Zoom AI Companion transcripts and summaries are available directly via the Zoom MCP. In this skill, meeting transcripts are a **high-signal source for dropped commitments** — action items verbally agreed to in meetings that never appeared in Jira.

### Primary: Zoom MCP

**Step 1 — Find meetings in the scan window:**
```
search_meetings(
  from: "<scan_start>T00:00:00Z",
  to:   "<today>T23:59:59Z"
)
```
Note the `meeting_uuid` for each result. Prefer UUID over numeric `meeting_number` for recurring meetings.

**Step 2 — Pull assets per meeting:**
```
get_meeting_assets(meetingId: "<meeting_uuid>")
```
Key fields:
- `my_notes.transcript.transcript_items[]` — speaker-labeled transcript; scan for task language ("I'll", "you'll", "by next week", "can you", "I'll take care of")
- `meeting_summary.next_steps` — AI-extracted action items (faster scan; verify against transcript if used in the brief)
- `participants` — who was in the room

**What makes a crack in meeting context:**
- A commitment made by Adrian or a team member in a 1:1 (`meeting_type` + two attendees) with no downstream Jira ticket or Slack thread
- An ask from Adrian to a team member with no evidence of follow-through in Jira/Slack since
- 1:1 commitments are especially high-signal — they're personal, not tracked in tickets, and easy to forget

Treat an untracked verbal commitment the same priority as a buried @-mention — it's a real ask that fell through.

**Access note:** Do not pre-filter meetings by `has_transcript_permission` or `has_summary_permission` in search results — these flags are unreliable and will cause you to skip accessible transcripts. Call `get_meeting_assets` on **every** meeting in the window, regardless of those flags and regardless of whether you were the host. Check `my_notes.has_my_notes` in the response: `true` means content is available; `false` means Zoom AI Companion wasn't active for that meeting and there's nothing to retrieve. You don't need to be the host — you only need AI Companion to have been running in the meeting.

### Fallback: local transcript files

If Zoom MCP is unreachable, or for meetings predating the integration, check local files:
```
Glob: ~/Projects/Mgmt Assistant/transcripts/YYYY-MM-DD_*.md
```
Frontmatter `action_items` field is pre-extracted — faster than reading full transcripts. Read full body only to verify a specific claim.

## Source prioritization during Phase 3 scoring

When picking the top 3, favor sources in roughly this order — the further down the list, the higher the noise ratio and the more human judgment is needed:

1. **Jira customer-escalation tickets with team silence** (very high signal, low noise)
2. **Buried @-mentions of the team** (clear ask with clear silence)
3. **Read-but-not-replied inbound email** (concrete, actionable)
4. **Stale PRs with assigned reviewers** (single clear action: ping the reviewer)
5. **Cross-team dependency tickets** (requires manager-to-manager ping)
6. **Jira tickets with unanswered teammate questions** (requires reading the question)
7. **Gone-quiet teammate** (weakest signal — use only when 1-6 haven't filled the 3 slots, and then only with a soft-pressure framing)

A well-constructed brief ideally pulls from 2–3 different source categories. Three Jira tickets all about the same person is worse than Jira + Slack + email covering three different facets.
