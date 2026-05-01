---
name: perf-review-draft
description: Draft a performance review write-up for one or more direct reports, drawing evidence from local 1:1 transcripts, Jira tickets, GitHub PRs/commits, and Slack. Produces a structured markdown draft per person with inline citations — no remote writes, no approval gate. Triggers include `perf-review-draft`, `perf review`, `draft perf review`, `performance review draft`, `write up <name>'s perf review`, `prep perf review for <name>`.
---

# Perf Review Draft

Generate a structured, evidence-backed performance review draft for one or more direct reports. Every claim is grounded in a real artifact — transcript line, Jira key, PR link, or Slack message — so the final reviewer (you) can verify before submitting.

**The signal hierarchy**: local 1:1 transcripts are the primary source because they capture commitments, growth conversations, and direct feedback that no tool tracks. Jira, GitHub, and Slack add quantitative weight and cross-team visibility.

**Output**: one markdown file per person, saved to `<workspace_dir>/perf-reviews/<YYYY>/<person-slug>-perf-draft-<date>.md`. Informational — you read, edit, and finalize the draft before submitting to whatever HR system your org uses. Nothing is written remotely.

## Config & cache locations

- **User config**: `${XDG_CONFIG_HOME:-$HOME/.config}/action-item-sync/user.json` (shared with action-item-sync — same team roster)
- **Workspace config**: `${XDG_CONFIG_HOME:-$HOME/.config}/claude-skills/workspace.json` — provides `transcript_dir`
- **Research cache**: `${XDG_CACHE_HOME:-$HOME/.cache}/perf-review-draft/<person-slug>/<review-period>/`

The skill reuses the action-item-sync user config for the team roster. On first run, if that config is absent, fall back to `${XDG_CONFIG_HOME:-$HOME/.config}/ai-weekly-update/user.json`, then fail-fast with a helpful message.

## Blast-radius table

| Action | Scope | When |
|---|---|---|
| Write `<workspace_dir>/perf-reviews/<YYYY>/<slug>-perf-draft-<date>.md` | Local | Phase 6 — path announced before writing |
| Write research cache under `${XDG_CACHE_HOME:-$HOME/.cache}/perf-review-draft/` | Local | Phase 4 |
| Read local transcript files in `transcript_dir` | Local reads | Phase 3 |
| Read Jira tickets via Atlassian MCP | Remote read | Phase 4 |
| Read GitHub PRs/commits via `gh` CLI | Remote read | Phase 4 |
| Read Slack via Slack MCP | Remote read | Phase 4 |
| Write to Jira, Confluence, Slack, or any remote system | **Never** | — |
| Assign a numeric performance rating | **Never — draft only; you decide the rating** | — |

## Prerequisites

- `${XDG_CONFIG_HOME:-$HOME/.config}/action-item-sync/user.json` (or `ai-weekly-update/user.json`) with `team.members[]`
- `${XDG_CONFIG_HOME:-$HOME/.config}/claude-skills/workspace.json` with `transcript_dir`
- Atlassian MCP (Jira) — for ticket data
- Slack MCP — for collaboration signals
- `gh` CLI authenticated with `repo` scope — for PR/commit data

If any are missing, the skill still runs and flags them in a **More signal available** note.

## Invocation

```
perf-review-draft <name>                    # one person, default review period
perf-review-draft <name> --period H1 2026   # explicit review period (H1/H2/Q1-Q4 + year)
perf-review-draft <name> --since 2026-01-01 --until 2026-06-30  # explicit dates
perf-review-draft --all                     # draft for all team.members[] in sequence
perf-review-draft --all --period H1 2026    # all, with explicit period
```

Name matching: fuzzy first-name match against `team.members[].display_name`. Multiple matches → ask. No match → fail with helpful message. Only `relationship: "direct_report"` members are valid targets — the skill is for your own team, not peers or managers.

**Period defaults** (when `--period` is omitted):
- If today is before July 1: H1 of the current year (Jan 1 – Jun 30)
- If today is July 1 or after: H2 of the current year (Jul 1 – Dec 31)
- Announce the inferred period and ask the user to confirm before researching.

## Workflow

### Phase 1 — Resolve person(s) and review period

1. Load config from `${XDG_CONFIG_HOME:-$HOME/.config}/action-item-sync/user.json`. Fall back to `ai-weekly-update/user.json`. If neither exists, fail with: "No team config found — run `action-item-sync init` or `init ai-weekly-update` first."
2. Load workspace config from `${XDG_CONFIG_HOME:-$HOME/.config}/claude-skills/workspace.json` to get `transcript_dir`.
3. Resolve name argument → `team.members` entry. For `--all`, queue every member with `relationship: "direct_report"`.
4. Determine review period dates (`start`, `end`). Parse `--period H1 2026` as Jan 1–Jun 30 2026; `H2 2026` as Jul 1–Dec 31; `Q1` = Jan–Mar, `Q2` = Apr–Jun, `Q3` = Jul–Sep, `Q4` = Oct–Dec. Announce: "Drafting review for **<name>** — period **H1 2026** (Jan 1–Jun 30 2026). Confirm or change?"

### Phase 2 — Mine local transcripts

Run for each target person:
```
scripts/mine_transcripts.py \
  --transcript-dir <transcript_dir> \
  --person "<display_name>" \
  --start <YYYY-MM-DD> --end <YYYY-MM-DD>
```

Returns JSON: list of matched meetings, each with full frontmatter + key content excerpts (action items, topics, and transcript lines containing growth/feedback keywords). See `references/data-sources.md` for keyword lists.

Announce: "Found N 1:1 transcripts for <name> in window (M team meetings). Mining for evidence."

### Phase 3 — Remote research

Run Jira, GitHub, and Slack searches in parallel for the target person. Full query patterns in `references/data-sources.md`. Cache results under `${XDG_CACHE_HOME:-$HOME/.cache}/perf-review-draft/<person-slug>/<review-period>/`.

Announce sources before starting: "Researching **<name>** across Jira, GitHub, Slack. Caching to `<cache-path>`."

**Jira** — tickets assigned to or commented on by the person in the period:
```jql
assignee = "<atlassian_account_id>"
AND updated >= "<start>" AND updated <= "<end>"
ORDER BY updated DESC
```
Also run comment-authored query. Categorize by status and type.

**GitHub** — PRs authored + PRs reviewed + commits:
```
scripts/search_github.py prs \
  --config <config_path> --author <github_username> \
  --start <start> --end <end> --state all

scripts/search_github.py commits \
  --config <config_path> --author <github_username> \
  --start <start> --end <end>
```

**Slack** — their messages + mentions of them (public mode unless config says otherwise):
```
from:<@slack_user_id> after:<start> before:<end>
```

### Phase 4 — Synthesize evidence

For each review dimension (defined in `references/review-dimensions.md`), collect supporting evidence from the aggregated sources:

1. **Delivery & execution** — tickets closed, PRs merged, commitments from 1:1s that got done
2. **Technical craft** — PR quality signals (review comments, revisions), complexity of work, `CLAUDE.md` / AI adoption
3. **Reliability & follow-through** — 1:1 action items completed vs. open, Jira tickets updated promptly, stated deadlines met
4. **Collaboration & communication** — cross-team PRs, Slack engagement, 1:1 consistency and openness
5. **Initiative & growth** — things they drove unprompted, self-directed learning (courses, AI experiments), feedback they gave peers
6. **Areas for development** — gaps observed in transcripts (recurring blockers, deferred items, avoidance patterns), framed constructively

For each dimension, produce:
- A **narrative paragraph** (3–5 sentences) synthesizing the evidence
- An **evidence list** (bullet citations) at the end of the section

Tone guidelines in `references/output-style.md`. Key rules: specific > general, evidence > assertions, developmental language for growth areas (not punitive), never invent.

If a dimension has no evidence (e.g. no GitHub data because `gh` isn't configured), omit it rather than pad with vague statements.

### Phase 5 — Check for open action items from Confluence

If `${XDG_CONFIG_HOME:-$HOME/.config}/action-item-sync/user.json` has a `confluence_page_id`, and `/tmp/action-item-sync-<page_id>.adf.json` is present (left from a recent action-item-sync run), parse it:
```
scripts/../../action-item-sync/scripts/manage_action_items.py parse \
  /tmp/action-item-sync-<page_id>.adf.json
```

Filter items where `owner == person.display_name` and `status == "Open"`. List these in the draft's **Open commitments** section — they're items from meeting discussions that haven't been closed yet, which may be relevant to the review.

If the ADF file isn't present, skip this step silently.

### Phase 6 — Write draft

Create output directory `<workspace_dir>/perf-reviews/<YYYY>/` if absent. Write draft to `<person-slug>-perf-draft-<YYYY-MM-DD>.md`.

Announce the path before writing.

File structure per `references/output-style.md`:
```markdown
---
person: <display_name>
review_period: H1 2026 (2026-01-01 to 2026-06-30)
date_drafted: YYYY-MM-DD
sources: [transcripts: N, jira_tickets: N, prs: N, commits: N]
---

# Performance Review Draft — <Name> — H1 2026

> **Manager note**: This is a working draft grounded in specific evidence. Ratings and final language are yours to complete. Every claim below has a citation — verify before submitting.

## Delivery & Execution

<narrative>

**Evidence**: ...

## Technical Craft

...

## Reliability & Follow-through

...

## Collaboration & Communication

...

## Initiative & Growth

...

## Areas for Development

...

## Open Commitments (as of <date>)

Items still marked Open on the team action items page:
- <item text> (added <date>)

## Evidence Index

Raw source summary used to compile this draft:
- **Transcripts**: <N> 1:1s, <M> team meetings — see `<transcript_dir>` for files
- **Jira**: <N> tickets closed, <M> in-progress, <K> commented
- **GitHub**: <N> PRs merged, <M> PRs reviewed, <K> commits
- **Slack**: searched public messages <start>–<end>
```

After writing, open the file: `open <path>`.

Report: "Draft saved to `<path>`. Open items, ratings, and final language are yours to complete."

### Phase 7 (--all mode only) — Continue to next person

If `--all` was specified and there are more team members queued, announce "Moving to <next person>…" and repeat Phases 1–6 for each. After all drafts are written, print a summary:

```
Drafts written:
  Brónach Falls  → <path>
  David Swan     → <path>
  Gavin Didrichsen → <path>
  Greg Hardy     → <path>
  Lukas Audzevicius → <path>
```

## Safety rules

- **Never rate.** The draft contains narrative evidence. You supply the final rating judgment. The skill must not say "exceeds expectations" or "meets expectations" in the narrative — that's your call after calibration.
- **No remote writes.** This is a local research + draft tool. Nothing is published.
- **Developmental, not punitive.** Growth areas are framed as "opportunity to develop X" or "continuing to build Y" — never as failures or character judgments.
- **Pronouns.** If a team member has `pronouns` set in config, use them. If absent, use their name only — never guess from name. See `_shared/pronoun-handling.md`.
- **No fabrication.** If there's no evidence for a dimension, omit the section. Thin data is a signal to gather more, not to fill with generalities.
