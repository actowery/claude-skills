# Management psychology

Framings for the "why help matters to them" and "business benefit" fields. The point is to give the model an honest vocabulary, not a greeting-card one. Generic affirmations are worse than nothing — they make the brief read as template filler and the manager stops trusting it.

**Governing rule**: don't invent emotion you can't see. Signals show actions (ticket went silent, comment got no reply); they don't show feelings. Frame in terms of **friction**, **expectation gaps**, **decisions being made by default**, and **what silence communicates** — not in terms of what anyone "feels."

## "Why help matters to them" — honest framings

### Removing invisible drag
> When an external team has gone silent, the cost falls on [name] to ping them again. That second/third ping is awkward for an IC — peer-level, no formal authority, easy to read as nagging. Pings from a manager route around that awkwardness; you spend social capital they don't have.

Use when: the stale item blocks a teammate on an external dependency.

### Closing an open loop
> [Name] asked a question X days ago and got no answer. They've likely moved on and the question is now forgotten from both sides. You closing the loop — either getting the answer or acknowledging the question was dropped — returns something they had written off.

Use when: an unanswered question from a teammate or external contact.

### Setting a floor for responsiveness
> A customer who's been waiting X days without acknowledgment is forming an opinion about how much we care. Even a holding reply ("We see this, engineering update by <date>") resets the clock. The value isn't in the content; it's in the signal that someone's reading.

Use when: customer/partner emails and escalation tickets.

### Removing the "is this still a thing?" overhead
> When work stalls without a decision, people spend real energy wondering whether to pick it back up, whether they're off the hook, whether it's secretly a fire. You calling the question — "yes keep going" or "no, drop it" — returns that cognitive space.

Use when: forgotten action items, stale proposals, stuck-in-draft work.

### Creating a low-pressure opening
> You don't know whether [name]'s quiet week is deep-focus, PTO, or stuck. A neutral "how's it going" 1:1 opener doesn't assume any of those — it just makes it easier for them to tell you if they want to.

Use when: gone-quiet signal. Use carefully — this one is the easiest to overdo.

### Peer-to-peer where peer-from-peer failed
> An IC-to-IC ask has been sitting two weeks. The same ask from you to the other team's manager often lands differently — not because of hierarchy, but because the signal is now "this is important enough to surface upward on our side." Managers are expected to ping managers; it's routine where the IC version would feel like escalation.

Use when: cross-team dependency stalled.

## "Business benefit" — honest framings

### Velocity recovery
> Unblocks [N days] of [name]'s work. Ballpark: each day of ticket-sitting is roughly a day of flow-state work that isn't happening downstream.

Use when: clearly blocking somebody's work path. Quantify if the math is honest; skip the number if it's speculative.

### Escalation-risk reduction
> Customer unreplied emails and stale escalation tickets are the leading indicator for "this becomes a bigger deal in two weeks." Cheap to cauterize now, expensive later.

Use when: customer-facing items.

### Adoption-cycle preservation
> When a rollout depends on a specific unblock (API key, access grant, dependency update), every day of silence is a day the rollout's momentum fades. Teams stop using the half-enabled thing; re-starting is more costly than continuing.

Use when: tooling/infra rollouts with a specific blocker.

### Attrition insurance
> The meta-pattern: people leave teams where friction compounds and nobody's clearing it. One unblock doesn't retain anyone, but the habit of unblocking does. Frame this as "insurance" — cheap premium, occasional large payout.

Use when: gone-quiet or invisible-drag patterns. Use sparingly — don't frame every check-in as "retention."

### Information surfacing
> Quiet teammates often hold context the rest of the team doesn't. The 1:1 isn't just care; it's also information gathering. Something they've noticed but didn't think was worth a Slack post might be worth the whole team knowing.

Use when: gone-quiet patterns where you specifically want to learn something, not just signal concern.

### Reputation-for-the-team dividend
> Responsiveness signals that your team takes external asks seriously. That compounds in the cross-team market — other teams prioritize asks from teams they trust respond. Missing @-mentions, over time, makes you the team others stop pinging.

Use when: buried @-mentions and cross-team threads.

## Anti-patterns — never write these

- **"They'll feel seen."** Platitude. Name the specific friction being removed instead.
- **"Boosts team morale."** Too vague to be actionable or verifiable.
- **"Shows you care."** Condescending to both the manager and the teammate.
- **"Prevents burnout."** Overclaim from single-signal data. You don't know.
- **"Builds trust."** True in aggregate, not per-item. Say what's happening in *this* item.
- **"Increases engagement."** Corporate-speak; non-specific.
- **Any phrase a manager would roll their eyes at when reading their own brief.** The test: would you, reading this about yourself, take the suggested action or cringe?

## A template for writing these fields cleanly

```
Why help matters to them:
> <One specific friction this action removes>, framed in terms of <what they'd be doing without help>.

Business benefit:
> <Concrete outcome>. <Optional: why this is cheap now and expensive later>.
```

Short. Honest. Specific.
