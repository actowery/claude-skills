# Review Dimensions — What to Look For

Six dimensions cover the core areas of a software engineer's performance review. Each maps to specific evidence signals. If evidence is thin for a dimension, omit that section entirely — do not pad.

---

## 1. Delivery & Execution

**What this covers**: shipped work, tickets closed, features/fixes delivered on time, release contributions.

**Evidence signals to collect:**
- Jira tickets with `status in (Done, Closed, Resolved)` in the period — note key/summary/resolution
- GitHub PRs merged in the period — title, repo, any notable size or complexity
- 1:1 transcript topics where deliveries were discussed and confirmed done
- Action items from previous meetings that have been closed (appear in "Done" status on action items page)
- Explicit statements in transcripts: "I shipped X", "we closed that", "merged yesterday"

**Watch for**: items committed to in Q1 that appear in multiple 1:1s still not done by end of period — those belong in Areas for Development or Reliability, not here.

**Anti-signals (do not count):** tickets still in progress at end of period, PRs still open, items discussed but not actioned.

---

## 2. Technical Craft

**What this covers**: quality of code and engineering work, technical judgment, learning and depth.

**Evidence signals to collect:**
- PR review comments from others (visible in PR details if available) — many revision cycles on same PR may signal quality issues; quick approvals with positive comments signal quality work
- Complexity of work: large/complex PRs, cross-service changes, refactors, new tooling
- `CLAUDE.md` additions or AI integration PRs — signals active engagement with new tooling and a willingness to invest in the team's AI posture
- Transcript conversations about technical decisions: "we talked through the architecture", "they designed the approach themselves"
- Explicit praise or concerns about technical output from transcripts: "really clean implementation", "we had to revisit the approach three times"
- GitHub commits to documentation, tests, tooling (not just feature code) — signals investment beyond the minimum

**Watch for**: evidence of growth trajectory — did their technical work in the second half of the period differ from the first half? Note improvement arcs explicitly.

---

## 3. Reliability & Follow-through

**What this covers**: do commitments made in 1:1s get completed? Are deadlines self-managed? Is in-flight work proactively communicated?

**Evidence signals to collect:**
- 1:1 transcript action items from early in the period → check if they appear as closed Jira tickets, merged PRs, or completed in later transcripts
- Recurring "still in progress" items across multiple 1:1s on the same topic = reliability signal (negative) — note the gap between commitment and completion
- Jira tickets with long idle periods followed by sudden activity — may indicate procrastination or blocking
- Instances in transcripts where the person proactively flagged blockers before being asked: "I wanted to flag that I'm stuck on X" — positive reliability signal
- Unanswered Slack mentions older than a week (if Slack data available): pattern of slow or absent responses to async asks

**How to frame issues**: "Several items carried across multiple 1:1s suggest an opportunity to strengthen follow-through on time-sensitive commitments" — not "failed to complete X."

---

## 4. Collaboration & Communication

**What this covers**: working with peers and other teams, visibility and communication in async channels, 1:1 engagement.

**Evidence signals to collect:**
- Cross-team PRs (repos outside the team's primary repos) or PRs reviewed for teammates
- Slack messages in team channels — are they contributing to discussions or mainly silent?
- Transcript quality: do they come to 1:1s prepared? Do they raise topics or only respond to your questions? Meaningful engagement in planning/grooming transcripts
- GitHub PR reviews performed — are they reviewing others' work proactively?
- Mentions of collaboration in transcripts: "I synced with X about this", "we're pair-programming on it", "I drafted a doc for the team"
- Cross-team meetings in transcript directory (non-1:1 meetings they appear in) — signals visibility and involvement beyond the immediate team

**Watch for**: contributors who are deeply engaged in private channels/DMs but invisible in public team channels — that may be a growth area (visibility, not participation).

---

## 5. Initiative & Growth

**What this covers**: self-directed learning, things they drove without being asked, professional development, mentoring others.

**Evidence signals to collect:**
- Transcript mentions of courses taken, certifications, self-study: "I watched a talk on X", "I'm working through a course on Y"
- PRs opened for improvements they identified without a Jira ticket prompting it
- New skills or tools adopted and brought to the team: AI adoption stories, CLAUDE.md contributions, tooling experiments
- Tickets opened by them (reporter = this person) — signals proactive problem-finding
- Topics in 1:1s they raised themselves (rather than items you put on the agenda): distinguishable because you asked a question and they went beyond it, or they opened with it
- Peer feedback signals in Slack: "thanks for your help", "@person this is really useful" directed at them
- Any evidence of mentoring or knowledge-sharing: running a demo, writing a doc, helping a teammate in a public thread

**Watch for**: people who only execute what they're handed vs. those who generate their own work. The latter is a strong growth indicator for senior engineer / tech lead paths.

---

## 6. Areas for Development

**What this covers**: specific, actionable growth opportunities — not character judgments.

**Construction rules:**
- Always frame as "opportunity to develop X" or "continuing to strengthen Y"
- Each area should map to at least one concrete evidence signal — no invented gaps
- Each area should have a plausible next step or direction ("could build on X by doing Y")
- Maximum 3 development areas — more than that overwhelms the review and signals the manager hasn't prioritized

**Common patterns to look for:**
- Items that recurred across multiple 1:1s without closure (Reliability dimension cross-link)
- Technical areas where complexity was avoided or escalated to you rather than addressed independently
- Communication patterns: over-communicating in 1:1 but invisible in async/Slack; or the reverse (active in Slack, avoidant in 1:1 direct conversations)
- Estimation and scoping: tickets consistently taking longer than expected, or scope creep on PRs — signals a planning/decomposition growth area
- Proactivity gap: strong executor but low initiative — if evidence shows they primarily respond rather than initiate, frame the next level clearly

**What NOT to include here:**
- Personality observations ("they seem disengaged") without specific behavioral evidence
- Things that happened before the review period
- Issues already acknowledged and actively improving — those belong in "Initiative & Growth" as a growth arc
- Single-incident events that may have had external causes — a pattern needs at least 2–3 data points across the period

---

## Open Commitments (bonus section)

Not a formal review dimension, but valuable context: items from the action-item-sync page still marked Open for this person at the time of the review. These may be:
- Legitimately in progress and fine
- Forgotten and worth a quick conversation
- Evidence for the Reliability section if many are stale

List them with their date added. Do not editorialize — just surface them. The manager decides what to do.
