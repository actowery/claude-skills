# Output style

These pages are read fast. Managers and execs skim them to gauge AI adoption and surface blockers. Match the terse, concrete, citation-anchored style — one paragraph per cell, density over volume.

## Shape per cell

Each column is **one paragraph**, 1–3 sentences. No bullet lists, no bold leads, no emoji (unless the rest of the page uses them consistently). Every claim traces to a real artifact — a Jira key, PR number, Slack link, commit SHA, or Claude log entry.

Inline `code` marks for:
- Slash commands (`/provision-test-infra aws`)
- Skill names (`ai-weekly-update`, `weekly-confluence-update`)
- File paths (`CLAUDE.md`, `docs/ai-guidance.md`)
- Repo names when technical (`puppet-agent-mono`, `pdk-ai`)
- Command names (`gh search prs`)

Draft text: wrap these with single backticks; the patch builder converts to code-marked text runs.

## Golden reference

A real manager's filled row (Manager Weekly Report, one-week window), showing the density target:

**Wins this week** — 
> Team fully engaged with Claude across PDK, Bolt, VSCode and AI tooling. CLAUDE.md files added to PDK repos. `/provision-test-infra aws` skill shipped. Shared Claude engagement report showing strong adoption (Mar 23–Apr 10); usage split between high-velocity code completion and conversational styles. Brainstorm with Modules team on Forge AI use scheduled for next week.

**Blockers / concerns** —
> Team Anthropic API key pending IT approval — blocking Claude integration into GitHub repos.

Notes:
- Wins is ~3 sentences with 4–5 concrete facts (skills shipped, files added, adoption numbers, upcoming events). Roughly 60 words.
- Blockers is 1 sentence, naming a specific thing and what it's blocking. Under 20 words.
- Em-dash (`—`) and en-dash (`–`) used for flow; hyphens (`-`) only inside compound words or keys.
- Inline `code` mark on the skill-command span only; repo and filename strings like `CLAUDE.md` are plain text here.

## Manager-with-team variant

When `team.members[]` is set, Wins becomes a weave of team + personal activity. Structure:

1. **Team-level framing sentence** (if the log scan / activity is broad) — "Team continued heavy Claude adoption this week across PDK, Bolt, and CI repos."
2. **Named specific wins** — use first names if unambiguous, full names if not. Cite keys/URLs inline.
3. **Your own wins last**, as an equal peer — don't hide them, don't inflate them.

**Manager-variant golden reference** (fictional):
> Team shipped multiple Claude integrations this week: Alex merged `CLAUDE.md` into three service repos and unblocked the `ANTHROPIC_CODE_REVIEW_KEY` rollout (ITHELP-999); Jordan refactored CI provision in `platform-ci` to use the organizational forge token (PLAT-1234); Sam closed a customer escalation (CAT-888) with PDK + Claude assist. I shipped the `ai-weekly-update` skill v0.2.0, added team-fan-out so this very page gets drafted with team context, and hosted the cross-BU AI sync Wednesday.

Four named people, four specific artifacts, one personal paragraph, ~75 words. The reader walks away with concrete evidence of team-wide AI adoption — not just the manager's activity.

**Anti-patterns — do not emit these:**
- `The team had a great week with AI.` — zero attribution, zero specifics.
- `Everyone on the team shipped CLAUDE.md.` — overclaim; not literally true unless it is.
- `Alex, Jordan, Sam, Brónach, David all did AI work.` — listing names without specifics is worse than not naming anyone.
- **Any win attributed to a team member who has their own row on the same page** — they're self-reporting as a Champion, and the manager row should leave their attribution to them. Covering their work here duplicates content and reads as stolen glory.

If a team member had no meaningful AI activity in the window per the research, don't list them — absence is fine. Don't fabricate generic "continued participating in AI channels" filler.

**Self-reporting rule in action.** If Greg has his own Champion row on this week's page, do not write "Greg shipped X" in the manager row — even if the research surfaced a real, cite-able Greg win. The exception is collaboration context where you were the driver: "led API-key escalation with Brónach and IT" is fine because the attribution is yours; "Brónach closed the escalation" would duplicate her own row.

## Density targets by column

| Column | Target |
|---|---|
| `Wins this week` | 3 sentences, 4–5 concrete facts, ~60 words |
| `What didn't work` | 1–2 sentences, specific thing + why |
| `Blockers / concerns` / `Blockers` | 1 sentence, what's blocked + root cause/owner |
| `What mentees should try next` | 1–2 sentences, concrete action + source |

## Good vs bad bullets

**Good:**
- `Shipped `/provision-test-infra aws` skill and onboarded 2 new teammates to Claude (adoption 80% daily-active, per scan of ~/.claude/projects).`
- `Team Anthropic API key still pending IT approval — blocks CI integration in `puppet-agent-mono` and `pdk-ai`.`

**Bad (too vague):**
- `Team engaged with Claude.` — nothing concrete; no numbers or artifacts.
- `Several skills shipped.` — which ones? cite them.

**Bad (no attribution):**
- `Lots of AI adoption this week.` — prove it with a scan or a PR count.

**Bad (non-AI noise):**
- `Closed 5 Jira tickets.` — this is an AI report. Only mention tickets that involve AI/Claude work.

## Content scoping rules

- **Stay on-topic.** This page is about AI adoption and Claude usage. Team sprint work goes on the generic weekly report, not here.
- **Cite adoption evidence when you have it.** If the Claude log scan gives you session counts, use them. If GitHub shows CLAUDE.md commits, name them.
- **Don't overclaim.** "Strong adoption" is fine if you have a scan backing it. "Industry-leading" is not.
- **Customer names** only if already public on the page or in an escalation you're summarizing. Never introduce new customer names unilaterally.
- **Code marks stay sparse** — they're for things the reader would literally type or grep for. Don't code-mark regular nouns ("the `team` onboarded").

## Tone

- Factual, not promotional.
- Past tense for wins (shipped / merged / landed). Present for in-flight (working on / pending).
- No hedging words ("I think", "probably"). If unsure, leave it out.
- 1st-person singular/plural as appropriate — "I shipped", "the team onboarded". Match the tone of the pre-existing content on the page.

## What NOT to write

- Emojis unless already used consistently in the column
- Bold leads inside paragraphs (the only bold on the page is the group dividers)
- Tables, nested lists, blockquotes, panels — these break the single-paragraph-per-cell convention
- Links as markdown — let the ADF `link` mark handle it (rare in practice; Jira keys and repo names as plain text are the norm)
