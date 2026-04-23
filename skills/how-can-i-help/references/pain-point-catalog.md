# Pain-point catalog

Categorized list of "cracks" this skill looks for, with example signals and the kinds of management actions that fit each. Use this as the menu when scanning — if a candidate doesn't map to one of these categories, it's probably not a management-action item.

**Common thread across all categories**: conversation happened, then went silent. The signal isn't activity; it's *interrupted* activity.

---

## 1. Ticket/thread with unanswered question

**Signal:** Jira comment or Slack thread where a teammate asked a specific question of an external person/team, got no response in ≥14 days (Jira) or ≥7 days (Slack).

**Example pattern:**
> Alex commented on PLAT-1234 on day -18 asking the security team whether the new secret-rotation policy applies to CI hooks. No reply since. Ticket is now sitting at Accepted with Alex blocked on the answer.

**Why it's a crack**: Alex almost certainly doesn't want to send a third ping to security. They probably moved on to other work and forgot. Security forgot too.

**Manager action pattern**: Ping the security team's manager/lead directly. One sentence: "Saw this question has been open two weeks — who's the right owner?"

**Do NOT**: answer the technical question yourself (engineering). Do NOT re-ping from the teammate's account (that's their job if they want to).

---

## 2. Customer escalation with one-sided conversation

**Signal:** Jira ticket with `Escalation`, `TAM`, `Support`, or customer-name labels, where the most recent comment is from the customer or a customer-facing role (TAM/SE/CSM), and the team hasn't responded in ≥5 days.

**Example pattern:**
> PROJ-888 has a customer comment from 9 days ago asking for a status update. No reply from the team. Ticket is still Open.

**Why it's a crack**: Customers reading silence as "nobody cares" is the #1 driver of escalation anger. Internally, the ticket assignee may be prioritizing work they think matters more; no one has told them the customer is waiting.

**Manager action pattern**: Nudge the assignee with context — "Customer pinged 9 days ago, worth sending even a one-liner?" OR send a short interim yourself — "We saw your note; engineering update coming by <date>." Buying a week of goodwill with one message.

---

## 3. Buried @-mention

**Signal:** Slack @-mention of you or your team in a channel (especially cross-team channels) that was never acknowledged, ≥5 days ago.

**Example pattern:**
> On day -11, someone from the DevOps team @-mentioned @devx-team in #cross-platform-cicd asking whether we had a preference on a runtime upgrade. No reply in-thread since.

**Why it's a crack**: The asker now assumes we don't care or don't have a preference — both of which are bad defaults. The team probably just buried the notification in a busy day.

**Manager action pattern**: Reply in-thread yourself with a one-line ack ("Catching up on this — <name> on my team will take a look this week") OR forward to a specific teammate with an ask.

---

## 4. Read-but-not-replied customer/external email

**Signal:** In your Outlook inbox, email from an external sender (customer, partner, another org), marked read, no reply sent in the same thread, >5 days old. The email had a specific ask or question.

**Example pattern:**
> 8-day-old email from `<external partner>` asking about our position on a shared tooling decision. Marked read day-of, no reply.

**Why it's a crack**: You read it, intended to reply, got interrupted. Unlike ticketed work, there's no board surfacing it. It lives or dies in your inbox.

**Manager action pattern**: Either reply now with a short answer, OR reply saying "Will come back with a full answer by <date>" to set an expectation. Even the latter is 30 seconds and buys credibility.

---

## 5. PR sitting in draft or waiting on review

**Signal:** Team-member PR open >7 days, no activity (no new commits, no review comments). Especially if a specific reviewer was assigned but hasn't reviewed.

**Example pattern:**
> PR #456 by Taylor has been open 12 days. One reviewer requested, no comments or approval. Taylor's stopped pushing commits — likely waiting.

**Why it's a crack**: Taylor is quietly context-switching away because they think the PR is stuck. The reviewer didn't notice they were blocking. Neither will surface this unless you do.

**Manager action pattern**: Ping the assigned reviewer ("Hey, Taylor's waiting on you — 15 mins of your time this week?"). If the reviewer is overloaded, reassign to someone else.

**Do NOT**: review the PR yourself. That's engineering leading by example, not management unblocking.

---

## 6. Gone-quiet teammate

**Signal:** A team member who normally has steady Jira / PR / Slack activity has had notably quieter signal in the past 1–2 weeks. Specifically: no tickets resolved, no PR activity, fewer than usual Slack posts.

**Example pattern:**
> Alex usually ships 2–3 PRs a week and is active in team channels. Past 10 days: 0 PRs, sparse channel presence, no closed tickets.

**Why it's a crack**: Silence has many explanations — PTO, deep-focus work, heads-down on something hairy, illness, or they're stuck and too tired to ask. The last two are the cracks. You don't know until you ask.

**Manager action pattern**: A genuinely low-pressure 1:1 check-in. Not "why are you quiet," but "I noticed you've been heads-down, anything worth flagging?" Opens a door without pushing them through it.

**Do NOT**: assume the worst. Don't phrase it as concern about performance unless you actually have that concern (in which case this isn't a crack, it's a real management task and this skill is the wrong surface for it).

---

## 7. Stale cross-team dependency

**Signal:** A Jira ticket or Slack thread where your team is waiting on another team's deliverable, and the last update from that team was ≥14 days ago.

**Example pattern:**
> Three of our tickets reference DEP-555 (owned by the API platform team). DEP-555 hasn't been updated in 18 days. Our tickets are sitting in a "blocked" state.

**Why it's a crack**: The API team's manager may not realize their silence is blocking three people on another team. And your teammates probably think "no point pinging again, we've pinged twice."

**Manager action pattern**: Manager-to-manager ping. "Three of my team's tickets are blocked on DEP-555 — can we get a realistic ETA or a handoff?" One message, peer-level, concrete.

---

## 8. Old action-item from sync / meeting notes

**Signal (harder to detect automatically)**: Confluence page or meeting-notes email where an action item was assigned, never followed up, and the owner has had no subsequent mention of it in the past 2+ weeks.

**Example pattern:**
> 3-weeks-ago sync notes: "Alex to write up the Q3 tooling proposal by end of month." No mention of the proposal in any source since.

**Why it's a crack**: Action items without external deadlines are the first thing to fall off. Alex may have forgotten or decided it wasn't worth the time; either way, nobody's closed the loop.

**Manager action pattern**: Ask directly: "Is the tooling proposal still a thing we want? Want me to find cycles for it, or should we officially drop it?" Forcing a decision either way.

**Note**: this is harder for the skill to detect automatically without scanning Confluence pages or meeting notes. In v0.1, flag these only when they surface from another source (e.g., someone mentions it in Slack).

---

## Not pain points (skip these)

- **Active fires** — anything touched in the past 72 hours. The user already knows.
- **Routine notifications** — auto-generated Jira updates, bot messages, CI failures. The skill isn't a triage queue.
- **Things requiring engineering work** — if the management action is "write the fix yourself," that's not a fit. Skill is management-lever only.
- **Peer-manager territory** — if the action belongs to someone else's lane (e.g., an HR issue, a different manager's direct report's work), skip. Management etiquette matters; the skill should respect it.
- **Things the user likely doesn't want surfaced automatically** — anything that could read as surveillance of their reports' activity patterns. The gone-quiet signal is already borderline; use it lightly and with a low-pressure framing.
