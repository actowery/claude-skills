# Output Style — Performance Review Draft

## The reader

You. The manager. This draft is your working document — not a polished artifact ready to copy-paste into an HR system. It should be dense with evidence and honest about what's missing, so you can edit intelligently before submitting.

## Tone register

- **Specific over general**: "Merged 4 PRs in the firewall module, including a refactor that reduced cyclomatic complexity by ~30%" beats "Contributed meaningfully to the firewall module."
- **Evidence over assertion**: every positive claim has a citation. Every growth area has a behavioral observation, not a character label.
- **Developmental, not punitive**: growth areas are phrased as next steps, not indictments. "Continuing to develop ownership of time-sensitive commitments" not "missed deadlines."
- **Manager-internal register**: this is your working language. It can be frank. It isn't the sanitized version for HR calibration review — that's what you'll produce after editing this draft.

## Section structure

Each dimension section follows this template:

```markdown
## <Dimension Name>

<Narrative paragraph(s): 3–5 sentences synthesizing evidence into a coherent picture.
 One concrete example minimum. Note any arc or trajectory (early period vs. late period).>

**Evidence:**
- <Source: specific artifact> — <what it shows>
- ...
```

The narrative paragraph comes first, not the evidence list. Reviewers read the narrative; the evidence list is verification.

## Narrative density targets

| Section | Target length |
|---|---|
| Delivery & Execution | 4–6 sentences — this is the most evidence-rich section |
| Technical Craft | 3–5 sentences |
| Reliability & Follow-through | 3–4 sentences |
| Collaboration & Communication | 3–4 sentences |
| Initiative & Growth | 3–5 sentences (shorter if thin evidence) |
| Areas for Development | 2–3 bullets, each 2–3 sentences |

Don't write to fill. A 3-sentence section with strong evidence is better than a 6-sentence section padded with hedges.

## Evidence citation format

```
- Jira DEVX-123 (closed 2026-03-14): puppetlabs-firewall refactor — shipped on time
- GitHub PR #88 merged 2026-04-22 (puppet-agent-mono): "Add CLAUDE.md onboarding guide"
- 1:1 transcript 2026-04-28: "David mentioned completing the self-leadership course today"
- 1:1 transcript 2026-03-10, action item: "Resolve NatWest RHEL 7 blocker by end of sprint" → closed in Jira 2026-03-28
- Slack #devx 2026-04-15: reviewed Greg's PR and provided detailed inline feedback
```

Format: `<source type> <identifier> (<date or range>): <what it shows>`

## Growth area format

Each growth area uses this structure:

```markdown
- **<Specific growth area name>**: <1-sentence description of the observed gap, grounded in evidence.>
  <1–2 sentences on the specific opportunity or direction.>
  *Evidence*: <brief citation>
```

Example:
```markdown
- **Proactive communication on blocked work**: Several 1:1s included discussion of blockers that had been sitting idle for 1–2 weeks before being raised. Building a habit of flagging blockers within 24–48 hours, even informally in #devx, would reduce the gap between stuck and unstuck.
  *Evidence*: Jira DEVX-99 (9 days between last commit and blocker mention in 2026-03-17 1:1); Jira DEVX-112 (similar pattern, 2026-04-14 1:1).
```

## Ratings

**Do not include a rating in the draft.** The narrative provides the evidence the manager needs to make the rating call after calibration. Adding a rating in the draft creates anchoring bias.

Leave a placeholder at the top of the file:
```markdown
> **Rating** (to be completed by manager after calibration): _______________
```

## The manager note block

Always include this verbatim at the top of the draft, after the YAML frontmatter:

```markdown
> **Manager note**: This is a working draft grounded in specific evidence. Every claim below has a citation — verify before submitting. Ratings, final language, and any sections you want to strengthen or remove are yours to complete. Sections with thin evidence are noted inline.
```

## Open commitments section

List open action items (from action-item-sync page) with no editorializing:

```markdown
## Open Commitments (as of YYYY-MM-DD)

The following items are still marked Open on the team action items page — may be in progress, forgotten, or context for the review.

| Item | Date Added | Source Meeting |
|---|---|---|
| Review firewall PR and provide approve-or-comment | 2026-04-30 | 1:1 with David • Apr 28 2026 |
```

If there are no open items, omit this section.

## Evidence index (footer)

Always end with a brief raw count to help the reader calibrate completeness:

```markdown
---
## Evidence Index

Sources used to compile this draft:

- **1:1 transcripts**: 6 meetings (Jan–Jun 2026) — `<transcript_dir>`
- **Team meetings**: 4 transcripts (standup, planning, grooming, retro)
- **Jira**: 14 tickets closed, 2 in-progress, 8 commented on
- **GitHub**: 9 PRs merged, 5 PRs reviewed, 21 commits — orgs: puppetlabs
- **Slack**: public messages searched Apr 24–May 1 (full period: public mode)

Missing / not searched:
- Slack private channels (mode is "public" — see config to enable)
```

The "Missing / not searched" subsection uses the same format as `_shared/missing-sources.md` but is embedded inline in the file rather than appended to a chat message.
