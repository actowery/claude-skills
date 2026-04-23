# Email style

This skill writes an email from an engineering manager to their manager, intended to be forwarded up to the next level. Every stylistic decision follows from who is reading it and why.

**Audience chain**: you → your manager → their manager (maybe further). By the time it's read two levels up, technical jargon and raw ticket keys become noise. Write so the second-level reader still understands.

**Purpose**: surface concrete AI-adoption wins from your team so leadership has cite-able proof that the investment is working. Secondary purpose: surface honest friction so the wins read as believable instead of performative.

## The core tension

Hype-but-honest. Miss either side and the email fails:

- **All hype, no honesty** → leadership gets skeptical over time; future wins land with less weight
- **All honesty, no hype** → leadership loses interest; team's effort goes unrecognized upward
- **Generic superlatives** ("great week", "strong momentum") → reads as filler; drop these

Concrete + attributed + a little human warmth is the target.

## Structure (matches Phase 4's draft shape)

### Subject
```
<Team> AI Weekly — <M–D M–D, YYYY>
```
Examples:
- `Platform AI Weekly — Apr 21–25, 2026`
- `DevX AI Weekly — May 5–9, 2026`

Stable, skimmable. If leadership pattern-matches on the subject line, you've made the weekly cadence scan-able.

### Greeting
`<Boss first name>,` — single line, no comma-space nonsense. Matches how managers actually write to each other.

### Opening sentence

One sentence. Sets the posture for the week. Pick the archetype that fits:

- **Strong week**: "The team had a strong week on `<theme>` — <brief numeric or named win>."
- **Mixed week**: "Mixed week for us — good momentum on `<X>`, but `<Y>` has become a real blocker we'll need help on."
- **Quiet week**: "Quiet week on shipments; heavy prep for `<Z>` landing next sprint."
- **Heads-down week**: "Heads-down on `<initiative>`; not much to ship yet, but `<what's visible>`."

Avoid: "Happy to report a productive week!" / "Just wanted to share the team's AI wins." These are throat-clearing, not posture.

### Team wins (the main body)

**One short paragraph per team member** with meaningful activity in the window. Lead with their first-name-last-name on first reference, first name thereafter.

Paragraph shape:
```
<Full name> <verb> <artifact/outcome in plain language>, <optional "and" clause>. <One follow-up sentence if needed for context or impact — skip if the first sentence stands alone>.
```

Good examples (fictional team, real shape):
> Brónach Falls shipped Claude integration into our `bolt-private` repo this week, laying the groundwork for AI-assisted code review across Platform. PR is up and a `CLAUDE.md` workflow is included so the pattern is repeatable for other repos.

> Gavin Didrichsen landed `CLAUDE.md` codebase guidance in `puppetlabs-firewall` (CAT-2614) — one of our most-touched modules now has structured context for Claude-assisted changes, cutting onboarding friction for new contributors.

> David Swan unblocked the `pdk-private` dependency bump pair (puppet_forge 6.1.0 and friends) that had been stuck on acceptance-test friction. Ships as CAT-2619; the cleanup opens room for the Debian 13 work.

Notes on what those examples do right:
- First sentence = what happened, in language a two-levels-up reader gets
- Optional second sentence = *why it matters*, not just mechanics
- Ticket / PR keys are present but not leading — they're citation, not subject
- No superlatives. The facts do the work.

Bad examples and why:
- "David did a great job on CAT-2619" — superlative, no content, readers don't know what CAT-2619 is
- "Gavin merged PR #1276 (CAT-2614)" — all mechanics, no impact framing
- "Brónach did amazing AI work!!" — breathless, unrooted, patronizing-sounding to a careful reader

**Skip members with no meaningful in-window activity.** Don't write filler like "Lukas continued participating in team channels" — silence is more honest and doesn't pad the email.

**Density target**: 2–4 sentences per teammate. Total team section: 5–10 sentences for a team of 5 (some will have more than one thing, some won't merit a paragraph).

### Blockers & concerns

One short paragraph, always present. If the week was genuinely smooth, say so in one line:

```
No material blockers this week; the pending items below are follow-throughs, not fires.
```

Otherwise:

```
Biggest open item is <specific blocker> — <who owns it> is <what they're doing>, and we may need <specific help> if <condition>.
```

Examples:
> The `ANTHROPIC_CODE_REVIEW_KEY` rollout to DevX repos is still in flight. IT's self-service access landed Tuesday, and Brónach is working through the rest of the repo list this week. No leadership ask yet; flagging so it's not a surprise if it slips a sprint.

> Biggest concern is the NatWest RHEL 7 PDK escalation (CAT-2598) — customer still waiting on fixture updates. David is the main driver; we'd welcome any cycles from the customer-success team if they can help shepherd.

The pattern: **what**, **who owns it**, **what help if any**. Don't over-explain technical detail; the reader trusts that you've judged it correctly.

**Never omit this section to make the email "feel better."** An email with zero friction reads as PR polish, not reporting.

### Personal work section

**Short.** One or two sentences max. This is the one section where brevity signals confidence.

Good:
> On my end this week, I shipped two reusable Claude Code skills the team now uses to automate our weekly reporting — small artifact, but it's paying itself back already in time saved.

Bad (too much):
> I've been heads-down on skill development. I shipped `weekly-confluence-update` (v0.3.0) and `ai-weekly-update` (v0.3.0), both of which are public on GitHub with CI and fixtures. I also started the exec report skill... [etc]

Cut everything after the first sentence unless a second sentence is genuinely needed for context. Your boss knows what you're doing day-to-day; they don't need your self-recap.

If you literally had no manager-scope individual shipping, say so honestly: "My week was mostly 1:1s, unblocking, and prep for X — no personal shipping."

### Closing

Brief, warm, useful:
```
Happy to dig into any of these in our 1:1 or before your upward review.
```

Variants:
- `Let me know if you want more detail on any of these before you roll it up.`
- `Happy to elaborate on anything that would be useful for <skip-level>'s context.`

### Sign-off

First name only. Single line.

## Tone calibration

The `boss_tone_preference` field in `user.json` modulates the dial:

- **`hype-friendly`** (rare): leadership wants energy. Slightly warmer opening sentences. Still concrete.
- **`balanced`** (default): the examples above.
- **`sober`** (common with senior leaders): drop all adverbs. No "really" / "genuinely" / "significant." Verbs carry the weight. Opening sentence is flat-factual.

Regardless of setting, **never fabricate to hit a tone**. If the week is genuinely quiet, "sober" is just what quiet looks like — don't dress it up for `hype-friendly`.

## Maturity framing — for exec audiences specifically

Upper-management readers care less about individual artifacts than about **where the team sits on the AI adoption curve**. Weave the S-level / phase vocabulary from [`ai-maturity-model.md`](ai-maturity-model.md) into the narrative so a skim gives them a trajectory read.

**How this differs from the Confluence row version.** The row version tags every paragraph inline with `(S1 Build infrastructure)`-style markers. The email version is **calibrated to feel natural, not mechanical** — you tag paragraphs but integrate the S-level into the prose, and close the body with a one-sentence trajectory line. Tags-in-parens look fine in Confluence; in a prose email to an exec, they read as template filler.

**Good example (balanced, in-prose):**
> Brónach integrated Claude into `bolt-private` with a `CLAUDE.md` and a workflow file, putting that repo on the **S1 Review infrastructure** step. Greg shipped `/install-agent` and extended `/provision-test-infra` to AWS — that's **S2 Deploy** territory, our team's first autonomous provisioning workflow. David closed a customer-facing PDK issue using Claude for fixture generation, which is an **S1 Build** pattern the team has genuinely internalized.
>
> Net: we're mostly at **S1 Build** across the stack with growing **S2 Deploy** through custom skills. Next milestone is the `ANTHROPIC_CODE_REVIEW_KEY` rollout completing, which tips Review from S1 to S2.

**Bad example (mechanical):**
> Brónach shipped CLAUDE.md integration (S1 Review). Greg shipped `/install-agent` (S2 Deploy). David closed ticket (S1 Build). Team at S1-S2.

The good version hands the reader a trajectory. The bad version reads as output from a reporting tool, which is exactly what you don't want leadership to see (even though it is, literally, output from a reporting tool).

**When to skip tags entirely.** If a paragraph is about a non-AI thing — a customer escalation, a blocker, an org update — don't shoehorn a tag in. The tags only work when they're accurate.

**Trajectory sentence at the end of the body.** If the week supports one, add a single sentence to the blockers/personal transition area framing where the team is and where it's heading. Make it concrete: name the specific transition. If it doesn't support a clean read (mixed week, sparse signal), skip it — the tags on individual paragraphs do enough work.

## Length target

400–700 words total. Leadership will scan it in under 90 seconds. Longer than that and the signal dilutes. Shorter than 300 and it reads like a thin status that didn't need an email.

## What NOT to include

- Emoji (even the tasteful ones — this is upward email, not team Slack)
- Bullet lists (paragraphs feel more like a human wrote them; bullets read like a report Claude generated)
- "Action items" / "Next week" sections — leadership doesn't want to do your planning; if there's a help ask, it's already in blockers
- Promotional language about the team ("world-class", "incredible", "leading the way")
- Apologies for length, tone, or self-deprecating asides
- Links to dashboards, wikis, or Confluence pages unless the boss asked for them specifically — force the content to stand alone
