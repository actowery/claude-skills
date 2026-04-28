# Brief structure

Three templates, one per `relationship` value. The template is chosen automatically from the matched person's config record. Sections are ordered to match how a manager actually walks into the meeting — opens by reviewing previous commitments, then current state, then forward-looking topics.

The honest count rule applies to every section: **omit a section entirely if it has no real content.** Empty sections kill trust. A short brief is a feature, not a failure.

---

## Template: `direct_report`

Use for `team.members[]` people. The brief answers: "what do I need to know about this person before our 1:1?"

### 1. Open from last 1:1
For each action item from the prior 1:1 transcript (extracted via `references/transcript-mining.md`):

- **Closed** items → drop entirely. Don't list them.
- **In flight** items → list with current status. Format: `<commitment> — <current state, with citation>`
- **Stale** items (no detectable activity) → flag as "worth following up on." Format: `<commitment> — no detectable movement since 1:1. Worth asking about.`

If there are no in-flight or stale items, omit this section. (Means everything from last time is closed — good news worth knowing.)

### 2. Recent shipped work
Bullet list of concrete shipped artifacts in the window:
- Closed Jira tickets (key + summary + closed date)
- Merged PRs (number + title + merged date)
- Direct commits if notable (e.g. CLAUDE.md additions, skill files)

Each bullet ends with a citation. Lead with the most impactful items. Cap at 5 — if there are more, say "and N more, see `<cache file>` for the full list."

### 3. In flight & potentially blocked
Tickets and PRs that are open but show signs of being stuck:
- Open PRs with no commits/comments past `pr_stale_days`
- In-progress Jira tickets with no recent updates
- Tickets where the target person asked a question and got no answer

Frame factually. Each item should suggest a specific question to ask in the 1:1.

### 4. Friction signals
Behavioral signals only — never fabricated emotion.

Surface:
- Slack messages with friction language (`blocked`, `still waiting`, `confused`, `bump`)
- Repeated comments on the same Jira ticket asking for the same thing
- Late-night / weekend Slack activity (only if pattern is unusual for them — needs baseline)

Format each as: `<observation> — <citation>. Worth asking how it's going.`

DO NOT write things like "they seem frustrated" or "they're getting demoralized." Those invent internal state. Stick to observable behavior.

### 5. Kudos worth giving
Toggleable via `prep_defaults.include_kudos`. Concrete wins worth specifically calling out in the meeting:
- A merged PR that was technically tricky
- A customer escalation they resolved
- A teaching/mentoring moment with a teammate
- Strong Slack writeup or design doc

Keep to 1–3 items. The point is "remember to actually say something nice about <specific thing>" — not a participation trophy list.

### 6. Growth & development topics
Only included if `prep_defaults.include_growth_topics_for_direct_reports: true` AND there's actual signal — never fabricated.

Sources of signal:
- Stretch work they took on (consider asking about their experience)
- Cross-team meetings they attended (consider asking what they learned)
- Topics they've expressed interest in (Slack/transcript) — ask if they want to go deeper
- Skill gaps that surfaced this period — frame as "have you thought about X" not "you need to learn Y"

Cap at 2 items. If no signal, OMIT this section. Forced growth topics are worse than none.

---

## Template: `manager`

Use for the `manager` field — the user's own boss. Fundamentally different from direct report briefs: this is **what the user needs to communicate upward and ask for**, not "what to know about the manager."

### 1. Open from last 1:1
Two sub-buckets:
- **You committed to** — things the user said they'd do; classified by closure detection
- **They committed to you** — things the manager said they'd come back on; flag if no movement

Loose closure detection — see `references/transcript-mining.md`. Stale items here are especially important; the manager forgot, the user needs to remind them tactfully.

### 2. Status headlines
3–5 terse bullets the manager would actually want to hear. Lead with shipped work. Use upper-management framing — outcomes, not tool names. Each bullet 1 line.

Example:
- "CAT-2598 NatWest escalation resolved this week — David shipped Apr 23"
- "Firewall module CI pipeline overhaul in progress — Eric piloting, expected end-of-month"

NOT:
- "We made 47 commits this week"
- "The team used Claude Code 200 times"

### 3. Blockers needing escalation
Things only the manager can unblock:
- Cross-team dependencies that need their lateral pressure
- Headcount / budget / tooling asks
- Leadership messaging the team needs them to deliver
- Decisions blocked at their level or above

Each item: state the block, name the owner who's blocking, name the ask.

### 4. Decisions needing their input
Things the user is holding pending the manager's call. Frame as a decision, not a discussion topic. State the options and the user's recommendation.

### 5. Questions for them
Things the user has been waiting on:
- Items the manager said they'd come back to (cross-reference Slack/email)
- Open requests for guidance
- Strategic context the user needs

### 6. Cross-team asks affecting your team
Anything coming from the manager's world (other teams, leadership, exec) that's landing on the user's team. Things to:
- Acknowledge ("we got the request, here's our plan")
- Push back on ("this conflicts with X — needs realignment")
- Get clarity on ("scope is unclear")

---

## Template: `peer`

Use for `peers[]` people. Lighter than direct-report briefs. No growth topics, no upward asks. Collaboration-focused.

### 1. Open from last 1:1
Same closure detection logic, but framed as collaboration items:
- Joint deliverables in progress
- Mutual asks left hanging
- Decisions you were going to align on

### 2. Recent collaboration
Things the user and peer have worked on together in the window:
- Shared Jira projects with both names on tickets
- PRs reviewed across teams
- Joint meetings (from Zoom search where both attended a non-1:1 meeting)

### 3. Alignment topics
Things where the two teams should be in sync but currently aren't:
- Conflicting roadmap items
- Tooling / process choices that affect both teams
- Customer issues spanning both teams

Frame as "worth getting on the same page about" — not as escalations.

### 4. Mutual asks
Things either party is waiting on the other for. Two sub-buckets:
- **You asked them** — flag if past `open_commitment_threshold_days`
- **They asked you** — own these. Don't show up to a 1:1 with someone waiting on you for two weeks.

---

## Closure detection (loose)

For every action item from the prior 1:1, check if ANY downstream activity exists in any source that plausibly relates to the topic. Loose match counts:
- Jira ticket with similar wording in summary or description
- Slack thread mentioning the topic
- PR with related title
- Email thread on the topic
- Transcript of a later meeting where the topic was discussed

If any match: classify as **Closed** (clear evidence of resolution) or **In flight** (activity but not done).

Only items with **zero** detectable activity get classified as **Stale**. These are the high-signal items — they're what the user actually needs to bring up again.

The loose-match approach is intentional. False negatives (calling something stale that's actually closed) are worse than false positives (calling something closed when it's still open) for this skill — false negatives waste meeting time on already-handled items, false positives are caught when the user reads the brief.

## Citation format

Every concrete claim needs a citation. Inline format:
```
- Closed CAT-2598 NatWest TAM ([Jira](https://...)) — shipped Apr 23
- Firewall PR no movement since Apr 19 ([PR #234](https://github.com/...))
- He flagged "blocked on Walmart contract" twice in #devx-puppet ([Slack 04-22 09:14](https://...))
```

For transcript references, use line range:
```
- Said he'd own the firewall homework ([transcript 2026-04-21 0930, lines 142-148])
```

## Pronouns

Use the person's `pronouns` field from their config record when referring to them in the brief. If the field is absent or empty, **use the person's name and avoid gendered pronouns entirely.** Don't guess pronouns from a name — names are not a reliable signal of gender. A brief that says "Barr — he committed to..." or "Barr committed to..." is fine; one that assumes "she" because the name reads feminine to the writer is a real failure mode this skill must avoid.

When in doubt, default to the person's name. It's marginally more verbose and entirely safe.

## What NOT to put in any brief

- Speculative emotion ("they seem demoralized")
- Comparisons to other team members ("unlike Bronach, David...")
- Sensitive personal info from transcripts (illness, family) — even if it came up in casual chat
- Anything about pay, performance ratings, or HR matters — those go in private notes, not skill output
- Items from outside the window (unless explicitly cross-referenced for closure detection)
