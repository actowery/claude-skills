---
name: 1on1-prep
description: Prepare for a specific 1:1 meeting by researching the other person's recent Jira / Slack / Outlook / GitHub / Zoom activity, mining the previous 1:1 transcript for open commitments, and producing a structured prep brief. Tailors output to the relationship — direct reports get a "what to know about them" brief with growth topics; the user's own manager gets a "what to communicate upward" brief with status headlines, blockers, and decisions needing input; peers get a lighter collaboration-focused brief. Use this skill whenever the user mentions 1:1 prep, prepping for a 1:1, getting ready for their next 1:1, or asks for talking points before a specific meeting — even when they don't say "skill." Triggers include `1on1`, `1:1 prep <name>`, `prep for my 1:1 with <name>`, `1on1 next` (looks at Outlook calendar for the next upcoming 1:1 and preps that person automatically). Distinct from `how-can-i-help` (which scans the whole team for cracks): this skill is person-specific and forward-looking — it prepares for a single conversation rather than triaging team-wide issues.
---

# 1:1 Prep

Prepare for a specific 1:1 by researching one person's footprint across all available sources, then producing a brief tuned to your relationship with them.

**The killer feature**: mining the previous 1:1 transcript for action items and commitments, then cross-checking against current Jira/Slack/PR state to filter out things that are already closed. What's left is what's actually worth bringing up again.

**Output**: a markdown brief printed inline + saved to `/tmp/1on1-prep-<person-slug>-<date>.md`. Informational — no remote writes, no approval gate. User reads, takes notes, walks into the meeting.

## Config & cache locations

- **User config**: `${XDG_CONFIG_HOME:-$HOME/.config}/1on1-prep/user.json`
- **Research cache**: `${XDG_CACHE_HOME:-$HOME/.cache}/1on1-prep/<person-slug>/<YYYY-MM-DD>/`

Per-person cache directories so re-prepping the same person on the same day reuses queries.

On first run, if no config exists, Phase 0 bootstraps from `$XDG_CONFIG_HOME/ai-weekly-update/user.json` or `$XDG_CONFIG_HOME/how-can-i-help/user.json` (team roster overlap).

## Blast-radius table

| Action | Scope | When |
|---|---|---|
| Write `$XDG_CONFIG_HOME/1on1-prep/user.json` | Local | Phase 0 init — path announced first |
| Write `<prep_output_dir>/1on1-prep-<person>-<date>.md` (default from workspace config, or CWD) | Local | Phase 5 |
| Write research cache under `$XDG_CACHE_HOME/1on1-prep/` | Local | Phase 3 |
| Read Jira / Slack / Outlook / GitHub / Zoom | Remote reads only | Phase 3 |
| Read Outlook calendar (only for `1on1` / `1on1 next` invocations) | Remote read only | Phase 1 |
| Send any message, reply to any email, comment on any ticket, schedule any meeting | **Never — informational skill, user takes all actions themselves** | — |

If any data sources are missing, the skill still runs. After delivering the brief, follow `_shared/missing-sources.md` to append a **More signal available** note for any source that couldn't run or had no config.

## Prerequisites

- Atlassian MCP (Jira)
- Slack MCP
- Outlook / M365 MCP (also used for calendar lookup on `1on1 next`)
- Zoom MCP (for previous 1:1 transcript and meeting summaries)
- `gh` CLI authenticated with `repo` scope

If any are missing, the skill still runs and falls back to the sources that are available.

## Invocation

```
1on1                    # bare — pull next upcoming 1:1 from Outlook calendar, prep that person
1on1 next               # same as bare
1on1 prep <name>        # explicit name lookup
1:1 prep <name>         # alias
prep for my 1:1 with <name>
prep me for <name>
```

The name argument matches against `team.members[]` and `peers[]` (fuzzy first-name match). Multiple matches → ask. No match → fail-fast with "I don't have a config record for X — add them via `init 1on1-prep`."

Optional second argument: an explicit date window (`since 2026-04-21`, `past month`). Default window is "since the last 1:1 with this person, or 14 days if no prior 1:1 found."

## Workflow

### Phase 0 — Init / bootstrap config (only on first run)

**Side effects:** read-only MCP calls; writes `$XDG_CONFIG_HOME/1on1-prep/user.json`.

1. If `$XDG_CONFIG_HOME/ai-weekly-update/user.json` or `how-can-i-help/user.json` exists, offer to import: user identity, team roster, GitHub orgs, slack mode.
2. Confirm or collect: user's display name, email, Atlassian/Slack/GitHub IDs.
3. **Team roster** — confirm `team.members[]`. For each member, set `relationship: "direct_report"` (default for team members).
4. **Manager** — ask for the user's own manager: display name, email, Atlassian/Slack IDs. Set `relationship: "manager"`. Stored in `manager` field, NOT in `team.members[]`.
5. **Peers** — optional list of peer managers, cross-team collaborators, skip-levels the user has regular 1:1s with. For each, set `relationship: "peer"`. Stored in `peers[]`.
6. **Pronouns** (optional but recommended) — for each person (team members, manager, peers), capture pronouns if known (`he/him`, `she/her`, `they/them`). Field is `pronouns` on each person record. **If pronouns are not set, the brief MUST use the person's name only and never gendered pronouns.** Don't guess from name — names are not reliable signals.
6. Confirm `transcript_dir` (default from workspace config `~/.config/claude-skills/workspace.json`, or CWD if not configured — see `_shared/workspace-config.md`).
7. Threshold defaults — see config schema below.
8. Announce the XDG path, then write `user.json`. Create parent dirs.

### Phase 1 — Identify the person

**Side effects:** read-only Outlook calendar call, only if invocation is bare `1on1` or `1on1 next`.

Two paths:

**Path A — name provided** (`1on1 david`, `1:1 prep barr`):
1. Fuzzy match the name against `team.members[]`, then `manager`, then `peers[]`.
2. If multiple matches, list them and ask the user to pick.
3. If no match, fail with the message above.
4. Note the person's `relationship` field — drives the brief template in Phase 4.

**Path B — calendar lookup** (`1on1`, `1on1 next`):
1. Call `outlook_calendar_search` for the next upcoming meeting in the user's calendar where `attendee_count == 2` (user + one other) AND the meeting is not yet ended.
2. Extract the other attendee's email.
3. Match that email against `team.members[]`, `manager`, `peers[]`.
4. If matched, proceed with that person. If not matched, prompt: "Next 1:1 is with `<name>` (`<email>`) — they're not in your config. Add them as direct report / peer / manager / skip?"
5. Always announce who you're prepping for: "Prepping for your 1:1 with <name> at <time>."

### Phase 2 — Determine window

**Side effects:** read-only Outlook + Zoom + filesystem.

**Why Outlook-first:** Zoom `search_meetings` only filters by topic/agenda keywords — there is no attendee filter parameter, and topic matching is fragile (e.g. `1on1` vs `1:1`, slash/colon tokenization issues, recurring meetings indexed as `schedule_expired`). Outlook calendar events have accurate attendee lists and always contain the Zoom join URL, making them the reliable source for finding a specific person's recurring 1:1.

**Step 1 — Outlook calendar (primary path):**
1. Call `outlook_calendar_search` with `attendee: <person_email>` and `beforeDateTime: today`, `afterDateTime: 90 days ago`.
2. From results, filter client-side for events where `attendee_count == 2` (just the user and the target person). These are 1:1 candidates.
3. Sort by date descending. Take the most recent completed occurrence.
4. Extract the Zoom meeting number from the join URL in the event body (e.g. `zoom.us/j/91491970034` → `91491970034`).
5. Call `get_meeting_assets(<meeting_number>)` directly — for a recurring meeting number this returns assets for the most recent completed occurrence.

**Step 2 — Zoom search (fallback if Step 1 finds nothing):**
Try multiple query variants in sequence, stopping at first hit:
- `"<person_first_name>/<user_first_name> 1:1"` or `"<user_first_name>/<person_first_name> 1:1"` (exact topic variants)
- `"1:1"` with a narrow time window (±30 min around the expected recurring slot if known)
- `"<person_first_name>"` alone — filter results client-side for `attendee_size <= 2`

For any Zoom result: do NOT pre-filter by `has_transcript_permission` or `has_transcript` — these flags are unreliable. Call `get_meeting_assets` on every candidate and check `my_notes.has_my_notes` in the response.

**Step 3 — Local transcripts (fallback if Steps 1–2 find nothing):**
`Glob: <transcript_dir>/*.md`, frontmatter `meeting_type: 1on1` AND target person in `participants`. Sort by `date` descending.

**Step 4 — Prior prep files:**
`Glob: <prep_output_dir>/1on1-prep-<person-slug>-*.md`. The most recent prior prep brief can supplement or confirm the window even if no transcript is found.

**Window resolution:**
- Window = (most recent prior 1:1 date + 1 day) → today.
- If no prior 1:1 found anywhere: window = today minus `prep_defaults.fallback_window_days` (default 14 days) → today.
- User can override with explicit dates from the invocation.

Note the prior 1:1's meeting number / UUID / local file path — Phase 3 will mine it for action items.

### Phase 3 — Research

**Side effects:** read-only external searches. Writes raw JSON cache under `$XDG_CACHE_HOME/1on1-prep/<person-slug>/<YYYY-MM-DD>/`.

Announce sources up front:
> Prepping for `<name>`. Window: `<start>` → `<end>`. Sources: Zoom (prior 1:1 transcript + meetings in window), Jira (their tickets + recent comments), Slack (their messages + mentions), Outlook (mail to/from), GitHub (their PRs + reviews + commits). Pulling now.

Fire all sources in parallel. Full query patterns live in `references/data-sources.md`. Summary:

**Zoom (primary action-item source).** Two distinct pulls:
1. **The prior 1:1 transcript itself** — `get_meeting_assets` on the meeting found in Phase 2. Extract action items via `references/transcript-mining.md` patterns.
2. **All other meetings in the window** where this person was an attendee — for context on what they discussed across other meetings, and to find any cross-team commitments.

Do NOT pre-filter by `has_transcript_permission` — call `get_meeting_assets` on every match and check `my_notes.has_my_notes` in the response.

**Jira.**
- Tickets where `assignee = <person>` updated in window
- Tickets where `comment by <person>` in window (their voice on others' tickets)
- Tickets where `<person>` is mentioned in comments (signals they may be waiting on something)

**Slack.**
- `from:<@person_slack_id>` in window — what they've been talking about
- Mentions of `<@person_slack_id>` by others — who's been pinging them and whether they responded
- DMs between user and person (only if `slack_search_mode: public_and_private`) — look for unanswered asks

**Outlook.**
- `sender:<person_email>` in window
- `recipient:<person_email>` in window (mail user sent them)
- Skip auto-notification senders.

**GitHub.** Via `scripts/search_github.py` with the person's `github_username`:
- Their PRs (open + merged) in window
- PRs where they're the requested reviewer (state of those reviews)
- Their commits in configured orgs

### Phase 4 — Synthesize the brief

**Side effects:** none — pure reasoning.

Pick the brief template based on the person's `relationship` field. See `references/brief-structure.md` for full section specs.

#### Template: `direct_report`
Use for `team.members[]` people. Sections:
1. **Open from last 1:1** — action items from prior 1:1 transcript, classified as Closed / In flight / Stale (loose closure detection — see `references/transcript-mining.md`)
2. **Recent shipped work** — closed Jira tickets, merged PRs with concrete artifacts
3. **In flight & potentially blocked** — open PRs no movement, in-progress tickets with no recent updates
4. **Friction signals** — Slack/Jira comments suggesting frustration ("blocked on", "still waiting"). Frame neutrally — observable behavior, not speculative emotion.
5. **Kudos worth giving** — concrete wins to call out specifically in the meeting (toggleable via `prep_defaults.include_kudos`)
6. **Growth & development topics** — career/development angle if signal exists. Never fabricate. Only include if `prep_defaults.include_growth_topics_for_direct_reports: true`.

#### Template: `manager`
Use for the `manager` field — the user's own boss. Fundamentally different framing: this is "what to communicate upward and ask for," not "what to know about the person." Sections:
1. **Open from last 1:1** — same logic, but framed as "things you committed to / things they committed to you"
2. **Status headlines** — terse, 3–5 bullets the manager would actually want to hear. Lead with shipped work; flag in-flight items with risk.
3. **Blockers needing escalation** — things only they can unblock (cross-team asks, headcount, leadership messaging)
4. **Decisions needing their input** — things you're holding pending their call
5. **Questions for them** — things you've been waiting on, things they previously said they'd come back to
6. **Cross-team asks affecting your team** — anything coming from their world (other teams, leadership) that lands on yours

#### Template: `peer`
Use for `peers[]` people. Lighter than direct report, no growth topics, no upward asks. Sections:
1. **Open from last 1:1** — collaboration items left hanging
2. **Recent collaboration** — shared projects, joint discussions
3. **Alignment topics** — things where your two teams should be in sync
4. **Mutual asks** — anything either of you has been waiting on the other for

**Closure detection rule (loose):** for each action item from the prior 1:1, check if ANY downstream activity exists in any source that plausibly relates to the topic. Loose match — Jira ticket with similar wording, Slack thread mentioning the topic, PR with related title. If any match, classify as Closed or In flight. Only items with zero detectable activity get classified as Stale.

**Honest count rule:** if a section has no real content, omit it from the brief. Empty sections kill trust. A short brief is better than a padded one.

**No fabricated emotion.** Friction signals frame observable behavior, never invented internal state. "He commented twice asking for an update" — fine. "He's frustrated with the team" — not fine.

### Phase 5 — Deliver

**Side effects:** writes `<prep_output_dir>/1on1-prep-<person-slug>-<YYYY-MM-DD>.md` via `scripts/render_brief.py`; prints the brief inline.

Output directory: resolve `prep_output_dir` in this order: (1) `prep_output_dir` from skill `user.json`, (2) `prep_output_dir` from workspace config (`~/.config/claude-skills/workspace.json`), (3) `<workspace_dir>/1on1-preps` if `workspace_dir` is set in workspace config, (4) current working directory. Fall back to `/tmp/` only if none of the above produce a usable path. See `_shared/workspace-config.md`. Preps persist across sessions for easy reference but are never committed to any repo.

Print the brief inline as the primary delivery. The markdown file is for reference during the meeting itself and for future prep runs (prior preps can be used as additional context when re-prepping the same person).

After saving the brief to `prep_output_dir`, also copy it to `/tmp/<filename>` and output a clickable sidebar link. The `/tmp/` copy is required because `prep_output_dir` contains spaces which break the link format.

Copy command: `cp "<prep_output_dir>/1on1-prep-<slug>-<date>.md" /tmp/1on1-prep-<slug>-<date>.md`

Then output the link using this exact format — full path as BOTH the display text and the href:

```
[/tmp/1on1-prep-<slug>-<date>.md](/tmp/1on1-prep-<slug>-<date>.md)
```

This is the last line of output before any missing-sources note.

No approval gate. The user reads, takes whatever notes they want into the meeting, and the skill is done.

**Missing-sources check.** After printing the brief inline, follow `_shared/missing-sources.md`: check which of the seven sources (Zoom, Jira, Slack public, Slack private, Outlook, GitHub, Claude Code logs) were skipped or errored during Phase 3. If any were, append the **More signal available** note at the end — never before the brief.

## Safety rules

- **Read-only remote.** This skill never writes to Jira / Slack / email / GitHub / Zoom / calendar.
- **No fabrication.** Every named item traces to a real artifact. Citations (ticket keys, URLs, transcript timestamps, message permalinks) are required for every concrete claim.
- **No fabricated emotion.** Don't invent what a person is feeling. Frame behavior as observable, not speculative.
- **Honest count.** Omit empty sections. A two-section brief is valid if that's all the signal supports.
- **Relationship boundaries.** Don't put growth/development framing in a peer brief. Don't put upward-ask framing in a direct report brief. The template-by-relationship rule is a real safety rail.
- **Calendar privacy.** Calendar lookup runs only when explicitly invoked via bare `1on1` or `1on1 next` — never on a named-person invocation.
- **Private Slack opt-in.** Same as other skills — only uses `slack_search_public_and_private` when config says so.

## Config schema

```json
{
  "display_name": "Adrian Example",
  "email": "adrian.example@company.com",
  "atlassian_account_id": "712020:...",
  "slack_user_id": "U00...",
  "github_username": "adrianexample",

  "team": {
    "name": "DevX",
    "members": [
      {
        "display_name": "Person Name",
        "atlassian_account_id": "...",
        "slack_user_id": "...",
        "github_username": "...",
        "email": "person@company.com",
        "pronouns": "they/them",
        "relationship": "direct_report"
      }
    ]
  },

  "manager": {
    "display_name": "Boss Name",
    "atlassian_account_id": "...",
    "slack_user_id": "...",
    "github_username": "...",
    "email": "boss@company.com",
    "relationship": "manager"
  },

  "peers": [
    {
      "display_name": "Peer Name",
      "atlassian_account_id": "...",
      "slack_user_id": "...",
      "github_username": "...",
      "email": "peer@company.com",
      "relationship": "peer"
    }
  ],

  "github": {"orgs": ["your-org"]},
  "slack_search_mode": "public",
  "transcript_dir": null,
  "prep_output_dir": null,
  "_path_note": "Leave transcript_dir and prep_output_dir null to inherit from ~/.config/claude-skills/workspace.json (see _shared/workspace-config.md). Set them here only to override the workspace default for this skill.",

  "prep_defaults": {
    "fallback_window_days": 14,
    "open_commitment_threshold_days": 21,
    "include_kudos": true,
    "include_growth_topics_for_direct_reports": true,
    "include_calendar_lookup": true
  },

  "cached_at": "YYYY-MM-DD",
  "cache_source": "user_confirmed"
}
```

## Files in this skill

- `references/data-sources.md` — query patterns scoped to a specific person + `user.json` schema details
- `references/brief-structure.md` — section specs for the three templates (direct_report, manager, peer)
- `references/transcript-mining.md` — how to extract action items from Zoom transcripts and classify them via loose closure detection
- `scripts/search_github.py` — shared with other skills (PRs, commits, reviews)
- `scripts/render_brief.py` — JSON brief → markdown at `/tmp/1on1-prep-<person>-<date>.md`
- `config/user.example.json` — schema template (real `user.json` is gitignored)
