---
name: how-can-i-help
description: Scans a manager's Jira / Slack / Outlook / GitHub footprint for items that have fallen through the cracks — conversations that went silent mid-flight, customer replies that were read but never responded to, stale @-mentions, forgotten escalations, PRs sitting in draft, old Jira comments with unanswered questions. Produces a short, honest brief (up to 3 items) with a description, the psychology of why helping matters to the affected person, the business benefit, and a specific low-effort management action the user can take. Output is an informational markdown brief — no drafting, no publishing, no approval gate. Use this skill whenever the user asks "how can I help today," wants to find forgotten items, wants to catch things falling through cracks, asks what's slipped their attention, or similar — even when they don't explicitly say "skill." Distinct from the weekly report skills (which summarize what happened) and the exec report skill (which communicates upward): this one scans for latent opportunities to act that the manager is probably NOT already aware of.
---

# How Can I Help

A manager-side scanner that surfaces **stuff that fell through the cracks** — not active pain your team already raises, but the silent, stale, forgotten items where a small management action could reactivate something worthwhile.

**The key framing**: your team is communicative. You already know about active fires. What you DON'T already know about is the conversation that stopped 10 days ago mid-flight, the customer email someone read and forgot, the ticket a teammate commented on 2 weeks ago and never heard back. That's the target zone.

Output is a **short honest brief** (up to 3 items) delivered in chat + mirrored to `/tmp/how-can-i-help-<date>.md`. Not a dashboard, not a list of everything — a curated short list with reasoning.

## Config & cache locations

- **User config**: `${XDG_CONFIG_HOME:-$HOME/.config}/how-can-i-help/user.json`
- **Research cache**: `${XDG_CACHE_HOME:-$HOME/.cache}/how-can-i-help/<YYYY-MM-DD>/`

On first run, if no config exists, Phase 0 bootstraps from `$XDG_CONFIG_HOME/ai-weekly-update/user.json` (team roster is the key overlap).

## Blast-radius table

| Action | Scope | When |
|---|---|---|
| Write `$XDG_CONFIG_HOME/how-can-i-help/user.json` | Local | Phase 0 init — path announced first |
| Write `/tmp/how-can-i-help-<date>.md` | Local | Phase 5 |
| Write research cache under `$XDG_CACHE_HOME/how-can-i-help/` | Local | Phase 2 |
| Read Jira / Slack / Outlook / GitHub | Remote reads only | Phase 2 |
| Send any message, reply to any email, comment on any ticket | **Never — informational skill, user takes all actions themselves** | — |
| Suggest actions targeting people outside the user's configured team or immediate collaborators | Avoid unless the signal is directly tied to the team | — |

If any data sources are missing, the skill still runs. After delivering the brief, follow `_shared/missing-sources.md` to append a **More signal available** note for any source that couldn't run or had no config.

## Invocation

```
how can I help?
```

Or: `how-can-i-help`, `what have I missed`, `what fell through the cracks this week`. All trigger the same workflow.

Optional argument: a look-back window. Default is **14 days** (longer than active-pain windows because we're hunting stale items). User can pass "past month" or explicit dates.

## Workflow

### Phase 0 — Init / bootstrap config (only if no config exists)

**Side effects:** read-only calls; writes `$XDG_CONFIG_HOME/how-can-i-help/user.json`.

If `$XDG_CONFIG_HOME/ai-weekly-update/user.json` exists, offer to import team roster, Slack mode, GitHub orgs from there. Otherwise collect minimum needed: team roster, GitHub orgs, optional staleness threshold overrides.

Threshold defaults (all in calendar days unless noted):

```
slack_thread_silent_days: 7      # reply stopped, no follow-up
email_unreplied_days: 5          # inbound from outside team, no reply sent
jira_comment_unanswered_days: 14 # teammate asked a question, no response
jira_assignee_silent_days: 21    # ticket assigned, no movement
pr_stale_days: 7                 # PR open, no activity
cross_team_mention_unacked_days: 5   # @-mention of team/user, no ack
```

These are the crack-finding thresholds. Shorter = more items (noisier). Longer = fewer (higher signal).

### Phase 1 — Determine window + load config

**Side effects:** none.

Default window: today minus 14 days → today. User can override.

Staleness thresholds determine "is this item stale enough to count" — items fresher than threshold are skipped (you already know about them).

### Phase 2 — Scan for candidate cracks

**Side effects:** read-only external searches. Writes candidates JSON + raw responses under `$XDG_CACHE_HOME/how-can-i-help/<date>/`.

Announce sources up front:
> Scanning past <window> for stale items. Sources: Jira (team assignees + watchers, >14d untouched), Slack (public + private per config, threads silent >7d), Outlook (inbound customer + external, no reply >5d), GitHub (team PRs + reviews waiting >7d). Pulling candidates now.

Fire queries in parallel. For each source, the scan is **biased toward silence**:

**Jira.** Two queries:
1. Tickets with team-member assignees where `commented` within window but `updated` > N days ago — i.e. conversation happened, then stopped.
   ```
   assignee in (<team>)
   AND commented >= "-<window>d" AND commented <= "-<jira_comment_unanswered_days>d"
   AND updated <= "-<jira_comment_unanswered_days>d"
   ORDER BY updated ASC
   ```
2. Customer-escalation tickets (labels: TAM, Escalation, Support, customer-facing projects) with recent external comments but no team response > N days.

**Slack.** Use `slack_search_public_and_private` if `slack_search_mode` is opted in. Look for:
- Threads where the last reply was from OUTSIDE the team, >N days ago, no team reply since. These are unanswered asks.
- Direct @-mentions of the user or a team member that were never acked, >N days old.
- Team-member messages containing "waiting", "blocked on", "any update", "bump" that didn't receive a follow-up reply.

**Outlook.** `outlook_email_search` for inbound mail the user received > N days ago that they haven't replied to (no sent message to same conversation thread). Prioritize:
- External senders (customers, partners, other orgs)
- Threads where the user was specifically asked something
- Emails that triggered `isRead: true` but no outbound reply

**GitHub.** Via `scripts/search_github.py`:
- Team members' open PRs with no activity > N days (`--state open --include-team`)
- PRs where the user or team member was assigned as reviewer and haven't reviewed

**Do not pull** fresh/active items. If Slack/Jira/PR/email touched within the freshness threshold, skip it — the whole point of this skill is to find what you don't already know about.

### Phase 3 — Score and select top items

**Side effects:** none — pure reasoning.

For each candidate, produce a rough score. Factors (no rigid formula — judgment):

- **Staleness**: older = more likely forgotten, higher weight
- **Substantive**: does it have a real unanswered question or a person waiting, or is it just an auto-notification ticket? (Auto-notifications = drop.)
- **Person affected**: is a specific teammate or external person actively blocked by this?
- **Manager-actionable**: can a 2-minute message or ping from the manager actually unblock it? If it needs engineering effort, skip (that's not this skill).
- **Cross-team signal**: items where an external team went silent on us rate higher (those are the exact cracks this skill is for).
- **Customer-facing**: customer-impacting items rate higher.

**Select up to 3 items** for the brief. Bias toward diversity (don't make all 3 items the same type — mix Jira / Slack / email if possible).

**Honest count rule**: if there are fewer than 3 genuine items, deliver fewer. Never fabricate to fill slots. An "I scanned and found nothing material this week — here's a quiet-week note" output is valid and valuable. The trust of the skill depends on the manager being able to believe the 3 items actually matter. One fake item poisons the whole output.

### Phase 4 — Compose the brief

**Side effects:** none — pure reasoning.

For each selected item, produce four fields:

1. **Description** (2–4 sentences, concrete):
   - What the item is, who's involved, when it went silent, what the unanswered question or blocked state is
   - Link to the artifact (Jira key, Slack permalink, email subject, PR URL)

2. **Why help matters to them** (1–2 sentences — the psychology):
   - Frame in terms of the affected person's experience. Avoid platitudes. See `references/management-psychology.md` for honest framings to draw from.
   - Don't invent emotion. If the signal is a ticket, you don't know they're distressed — frame it as "removing a friction they may not have mentioned" rather than "they're frustrated."

3. **Business benefit** (1–2 sentences — the org impact):
   - Concrete, outcome-focused. Customer-retention risk reduction, sprint velocity unblock, adoption acceleration, attrition insurance. See `references/management-psychology.md`.

4. **Suggested action** (1 sentence, specific):
   - Named (who to contact), concrete (what to say in 10 words or fewer), time-boxed (ideally ≤5 minutes of manager time).
   - Example: "Send `<name>` a one-line Slack: 'Saw this is stuck — can I help unblock?'"

### Phase 5 — Deliver

**Side effects:** writes `/tmp/how-can-i-help-<YYYY-MM-DD>.md` via `scripts/render_brief.py`; also prints the brief inline in the chat.

Print the brief inline as the primary delivery. Write the markdown file as reference — the user may want to come back to it during the day as they act on items.

No approval gate. This skill is informational — the user takes whatever actions they choose without the skill writing anything remote.

**Missing-sources check.** After printing the brief inline, follow `_shared/missing-sources.md`: check which of the seven sources (Zoom transcripts, Jira, Slack public, Slack private, Outlook, GitHub, Claude Code logs) were skipped or errored during Phase 2. If any were, append the **More signal available** note at the end of the brief — never before it.

## Safety rules

- **Read-only remote.** This skill never writes to Jira / Slack / email / GitHub.
- **No fabrication.** Every named item traces to a real artifact. Citations (ticket keys, URLs, timestamps) are required in the Description field.
- **No fabricated emotion.** Don't invent what a person is feeling from signal that doesn't support it. "You might check in" is fine; "They're probably demoralized" is not.
- **Honest count.** Deliver fewer than 3 items if fewer than 3 are genuine. Empty-week output is valid.
- **Respect team boundaries.** Don't suggest actions that are someone else's responsibility or that step on a peer manager's lane.
- **Private Slack opt-in.** Same as other skills — only uses `slack_search_public_and_private` when config says so.

## Files in this skill

- `references/pain-point-catalog.md` — categorized list of crack types with example signals and management-action patterns
- `references/management-psychology.md` — honest framings for "why help matters" — avoids platitudes
- `references/data-sources.md` — query patterns per source; user.json schema
- `scripts/search_github.py` — stale-PR detection (shared with other skills)
- `scripts/scan_claude_logs.py` — optional; gone-quiet detection via local session history
- `scripts/render_brief.py` — candidates JSON → markdown brief at `/tmp/how-can-i-help-<date>.md`
- `config/user.example.json` — schema template (real `user.json` is gitignored)
