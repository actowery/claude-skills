---
name: ai-weekly-update
description: Fill in the current user's row on a shared Confluence AI-usage weekly report (Champion Weekly Report or Manager Weekly Report tables — one row per person, with columns like "Wins this week", "Blockers", "What didn't work", "What mentees should try next"). Researches the window across Jira, Slack (public + private), Outlook, GitHub (PRs + commits + CLAUDE.md touches), and local Claude Code session logs to build a dense AI-focused draft, renders a local HTML preview, and publishes only after explicit approval. If the user is a manager with a team configured, also researches each team member's AI activity (Jira tickets, GitHub PRs/commits, Slack messages) and weaves team wins into the Wins paragraph alongside the user's own contributions. Use this skill whenever the user asks to fill their AI weekly, AI Champion report, AI Manager report, Puppet AI weekly, Delphix AI weekly, or pastes a Confluence URL titled "AI Weekly Report" — even if they don't explicitly say "skill" or "draft." Distinct from team-level weekly reports (see `weekly-confluence-update`): this one is per-individual row, matches the user by plain-text NAME in the row's first cell, and focuses on AI adoption / Claude usage rather than general sprint work.
---

# AI Weekly Update

This skill fills the current user's individual row on a shared AI-usage weekly-report page. The page typically has two tables — **Champion Weekly Report** (for individual contributors, 5 columns) and **Manager Weekly Report** (for managers, 3 columns). The user appears as a plain-text name in exactly one row across the two tables; the skill writes only into that row's non-name cells.

Designed for people reporting on their own (and their team's) AI / Claude adoption — skills shipped, integrations landed, adoption signals, blockers.

## Config & cache locations

Paths used throughout this skill (override via env vars if needed):

- **User config**: `${XDG_CONFIG_HOME:-$HOME/.config}/ai-weekly-update/user.json`
- **Research cache**: `${XDG_CACHE_HOME:-$HOME/.cache}/ai-weekly-update/<pageId>/<YYYY-MM-DD>/`

These paths are user-writable and persist across plugin upgrades. The skill must never write to its own install directory — that location gets wiped on upgrade.

**Legacy locations** (dev/standalone use): the old `${XDG_CONFIG_HOME:-$HOME/.config}/ai-weekly-update/user.json` relative to the skill directory is still read as a fallback if the XDG location is absent. New configs write to XDG.

## What this skill does and does not do (blast radius at a glance)

| Action | Scope | When |
|---|---|---|
| Call `updateConfluencePage` (publish to live page) | Remote write | Phase 8, ONLY after explicit `approve` |
| Write `${XDG_CONFIG_HOME:-$HOME/.config}/ai-weekly-update/user.json` | Local write | Phase 0 init — path announced first |
| Write `/tmp/ai-weekly-preview-*.html`, `modified.json`, drafts JSON, research cache under `${XDG_CACHE_HOME:-$HOME/.cache}/ai-weekly-update/` | Local writes | Phases 4, 6, 7 |
| Read page / Jira / Slack / email / GitHub / local Claude session logs | Remote reads only | Phases 1, 4 |
| Read team members' Jira / Slack / GitHub activity | Remote reads only | Phase 4, ONLY if `team.members` is set in `${XDG_CONFIG_HOME:-$HOME/.config}/ai-weekly-update/user.json` |
| Run `open <path>` to launch browser | Local | Phase 7 |
| Send messages, comment on tickets, post to Slack/email | **Never** | — |
| Touch rows belonging to other people or divider rows (`Puppet`, `Delphix`) | **Never** | — |
| Change table structure, add rows, reorder columns | **Never** | — |

If you see the skill about to do anything outside this table, stop it. That's a bug.

## Invocation

```
<confluence-page-url>
```
e.g. `https://<your-tenant>.atlassian.net/wiki/.../pages/3007840369/...`

No team parameter — this skill is per-individual. If the invocation is `init ai-weekly-update` (or anything clearly asking to set up or change the user's config), jump to Phase 0.

## Prerequisites

- Atlassian MCP (Confluence + Jira)
- Slack MCP
- Outlook / M365 MCP
- `gh` CLI (authenticated with `repo` scope)
- Read access to `~/.claude/projects/` on the local machine

If any are missing, the skill still runs; it reports which sources it couldn't reach.

## Workflow

### Phase 0 — Init / edit the user's config (only if asked)

Trigger: user says `init ai-weekly-update`, "set up my AI weekly config", or similar.

**Side effects:** read-only MCP calls (`atlassianUserInfo`, `slack_search_users`, `lookupJiraAccountId`); writes `${XDG_CONFIG_HOME:-$HOME/.config}/ai-weekly-update/user.json` locally after user confirmation.

1. Call `atlassianUserInfo` once. Capture `name`, `email`, `account_id`.
2. Resolve the user's Slack user ID via `slack_search_users`, confirming on email match.
3. Resolve the user's GitHub handle — try `gh api "search/users?q=<email>"` first; if no match or ambiguous, ask.
4. Ask the user once (one batched question, all optional):
   ```
   Slack search mode?                      (public / public+private)
   GitHub orgs to scope PR+commit searches? (e.g. your-org)
   AI-focused Jira labels/keywords?         (optional, defaults shown)
   Scan local Claude Code session logs?     (yes / no — default yes)
   Are you a manager with a team?           (yes / no)
   ```
5. If manager-yes:
   - Check `${XDG_CONFIG_HOME:-$HOME/.config}/weekly-confluence-update/teams/*.json` — if any exist, offer to import one: "Found DevX roster at `$XDG_CONFIG_HOME/weekly-confluence-update/teams/devx.json`. Use this for AI weekly team research too? (yes / name a different team / no — gather inline)"
   - Otherwise ask for team member names; resolve each to Atlassian+Slack+GitHub IDs the same way the team-level skill does (parallel `lookupJiraAccountId` + `slack_search_users` + `gh api orgs/<org>/teams/<slug>/members` if the team has a GitHub team name).
   - Store under `team.members` in `user.json`. Each member needs at minimum `display_name`; add whichever IDs we could resolve.
6. Save `${XDG_CONFIG_HOME:-$HOME/.config}/ai-weekly-update/user.json` following the schema in `references/data-sources.md`. Announce the path before writing.

Do not invent values. Empty answers are acceptable. If `team` is absent or empty, the skill runs in personal-only mode.

### Phase 1 — Identify the user and the page

**Side effects:** read-only Atlassian calls.

1. Load `${XDG_CONFIG_HOME:-$HOME/.config}/ai-weekly-update/user.json` if present; otherwise run Phase 0 first.
2. Call `atlassianUserInfo` to confirm display name hasn't changed.
3. Resolve `cloudId` from the page URL hostname; fetch the page in ADF.
4. If ADF is large (common), the MCP will save it to a file — pass that path to the parser.

### Phase 2 — Map tables and find the user's row

**Side effects:** local script only.

Run:
```
scripts/parse_page.py rows <adf-file> --display-name "<full name>"
```

Returns JSON listing every `tableRow` whose first-cell plain text (case-insensitive, trimmed) matches the user's display name AND whose first cell text is **not** strong-marked (which distinguishes person rows from group dividers). For each match, the output includes:
- the enclosing table's path + heading text (from the preceding level-2 heading)
- the row's path
- a column map built from the table's header row: `{column_index → column_name}`
- per-cell path + current content summary for every non-name cell

If zero matches: tell the user and stop — don't guess. If the user's name has changed or they're in a table under a different heading, confirm before proceeding.

**If `team.members[]` is configured**, also run `rows` once per team member's display_name to build a **self-reporting set**: team members who have their own row elsewhere on the page (typically in the Champion Weekly Report) are filling in their own glory and should NOT be attributed in the user's Wins paragraph. Record their display_names as `self_reporting_champions`; Phase 5 drafting will skip them. See the "Self-reporting rule" note in `references/output-style.md` for why this matters.

Present the row(s) and column names to the user briefly so they can confirm the mapping. Example:
```
Found your row in "Manager Weekly Report":
  Manager          = Adrian Towery
  Wins this week   → <empty, will draft>
  Blockers / concerns → <empty, will draft>
Self-reporting champions on this page (will be excluded from team attribution): Greg Hardy
```

### Phase 3 — Determine date range

**Side effects:** local script only.

Extract from the page title (e.g. `AI Weekly Report for 14 Apr - 18 Apr 2026`) via `scripts/parse_page.py dates`. If unparseable, ask — don't guess.

### Phase 4 — Research the week (AI-focused)

**Side effects:** read-only across all sources. Writes `${XDG_CACHE_HOME:-$HOME/.cache}/ai-weekly-update/<pageId>/<YYYY-MM-DD>/` locally.

**Announce sources up front, explicitly calling out team fan-out if present:**
> Researching <window>. Sources: Jira (AI labels/keywords, you + team members <names if any>), Slack (**public + private** per config, you + team), Outlook (AI keywords, your inbox only), GitHub (PRs + commits in orgs: <orgs>, you + team), Claude Code logs (your local `~/.claude/projects/` only). Reply `public only` to downgrade Slack this run. Reply `no team` to run personal-only this run.

Run these in parallel; cache results under `${XDG_CACHE_HOME:-$HOME/.cache}/ai-weekly-update/<pageId>/<YYYY-MM-DD>/`.

**Team-mode note:** if `${XDG_CONFIG_HOME:-$HOME/.config}/ai-weekly-update/user.json` has `team.members[]`, every remote query EXCEPT Outlook and Claude-Code-logs fans out to include team members. Outlook searches only the user's own mailbox (no delegated access). Claude Code logs are local to the user. Tag every result with the `display_name` of the member it came from.

**Jira.** AI/Claude tickets assigned to you OR any team member:
```
assignee in (currentUser(), <team_account_ids>)
AND (labels in (<jira_ai_labels>) OR text ~ "Claude" OR text ~ "Anthropic" OR text ~ "CLAUDE.md")
AND updated >= "<start>" AND updated <= "<end>"
```
If `team.members` is empty, drop the IN-list and use `assignee = currentUser()`. Also run a variant with `reporter in (...) OR watcher in (...)` to catch AI-adjacent tickets the team is shepherding rather than directly assigned.

**Slack.** Three searches (tool selected by `slack_search_mode`):
- You + team AI-related messages: `(from:<@you> OR from:<@member_1> OR from:<@member_2> ...) (Claude OR Anthropic OR "AI" OR skill OR CLAUDE.md OR agent) after:<start> before:<end>`
- Team channels AI discussions: `(Claude OR Anthropic OR CLAUDE.md OR "AI adoption" OR agent OR /provision OR skill) in:<team_channel> after:<start> before:<end>`
- Direct AI discussion threads you participated in (if private search is on).

**Outlook.** `DevX OR Claude OR Anthropic OR "CLAUDE.md" OR "AI agent" OR "AI adoption"` with date window.

**GitHub.** Run `scripts/search_github.py` twice — once for PRs, once for commits. Add `--include-team` to fan out to every `team.members[].github_username` in addition to the user's handle. Results are annotated with each author's `display_name`.

```
scripts/search_github.py prs --config ${XDG_CONFIG_HOME:-$HOME/.config}/ai-weekly-update/user.json \
  --start <YYYY-MM-DD> --end <YYYY-MM-DD> \
  --state all --ai-filter --include-team

scripts/search_github.py commits --config ${XDG_CONFIG_HOME:-$HOME/.config}/ai-weekly-update/user.json \
  --start <YYYY-MM-DD> --end <YYYY-MM-DD> \
  --ai-filter --include-team
```

Run a second PR pass WITHOUT `--ai-filter` so you don't miss PRs whose titles don't match your keyword list but are substantively about AI integration (e.g. commits adding a `CLAUDE.md` file where the PR title is "docs/onboarding"). Use judgment when drafting.

**Claude Code logs.** Run:
```
scripts/scan_claude_logs.py --start <YYYY-MM-DD> --end <YYYY-MM-DD>
```

Returns a summary of your local Claude Code sessions in the window: projects touched, session count per day, tool invocations (especially `Skill` tool calls showing which skills you used), and rough activity duration. Unique signal for this skill — nothing else captures day-to-day AI tool usage.

### Phase 5 — Draft

**Side effects:** none — pure reasoning.

For each column the user owns (per Phase 2's map), synthesize content in the style defined in `references/output-style.md`. Summary:

- **One paragraph per cell.** 1–3 dense sentences for "Wins", 1 for "Blockers", 1–2 for "What didn't work" / "What mentees should try next".
- **AI-focused** — lead with skills shipped, CLAUDE.md integrations, adoption stories, concrete Claude-usage numbers if the log scan surfaced them.
- **Inline `code` marks** for slash commands, skill names, file paths (backtick-wrap in the draft text and the parser will apply marks).
- **Every claim traces to a source.** Jira key, Slack link, PR number, log entry. No invention.

**Manager-with-team mode** — Wins paragraph weaves personal + team activity naturally. Structure (see `references/output-style.md` for a full example):
1. **Lead with team-level posture** — "Team continued heavy Claude adoption this week…" or similar framing if the log scan / activity is broad.
2. **Name specific team members for specific wins** — "Brónach closed <X> in `bolt-private`; David refactored <Y>; Gavin unblocked <Z>." Use display names as they appear on the page (first name acceptable when unambiguous).
3. **Add personal wins** — skills you shipped, adoption events you drove, cross-BU conversations you led.
4. **Cite keys / URLs inline** — keep the source trail intact even when naming multiple people in one sentence.

Do NOT claim credit ambiguously. If a team member shipped something, say so explicitly. The goal is to surface the team's AI adoption to leadership, not to compress it into first-person.

**Self-reporting rule** — if a team member appears in the `self_reporting_champions` set built in Phase 2 (they have their own row on this page, usually in the Champion Weekly Report), **skip them entirely** in the manager's Wins paragraph. They get to tell their own story in their own row. Attributing their wins in the manager row duplicates content and steals their glory. Acceptable exceptions: mentioning a team member in a collaboration context where you're the driver ("led API-key escalation with Brónach and IT"), where the attribution is yours, not theirs.

### Phase 6 — Build the modified ADF

**Side effects:** writes drafts JSON and modified ADF JSON locally (paths announced first). No network.

Write a drafts file keyed by table heading + column name:
```json
{
  "Manager Weekly Report|Wins this week": {
    "paragraphs": [
      "Shipped `/provision-test-infra aws` as a reusable Claude Code skill. Team onboarded 2 new DevX members to Claude; adoption at 80% daily-active in the window. Initial draft of Forge AI guidance merged (`docs/ai-guidance.md`)."
    ]
  },
  "Manager Weekly Report|Blockers / concerns": {
    "paragraphs": [
      "Team Anthropic API key still pending IT approval — blocking Claude integration in `puppet-agent-mono` and `pdk-ai` repos."
    ]
  }
}
```

Backtick-wrapped text in `paragraphs` gets converted to `code`-marked runs. Run:
```
scripts/parse_page.py build-patch <original-adf-file> --drafts <drafts.json> --display-name "<full name>" > modified.json
```

The builder preserves cell `localId`s, leaves the name cell untouched, leaves untargeted cells unchanged, and tags every inserted node with `_skillAdded: true` for preview highlighting.

### Phase 7 — Render preview

**Side effects:** writes `/tmp/ai-weekly-preview-<pageId>.html` and launches browser.

```
scripts/render_preview.py <modified-adf.json> --title "<page title>" --out /tmp/ai-weekly-preview-<pageId>.html
```

Tell the user: preview path + `approve` / `edit <column>: <change>` / `cancel`.

### Phase 8 — Publish on approval

**Side effects — the only phase that writes to Confluence:**
- Strips `_skillAdded` sentinels: `scripts/parse_page.py strip-sentinels modified.json > publish.json`
- Calls `updateConfluencePage` with the stripped body, version bumped.
- Deletes local `${XDG_CACHE_HOME:-$HOME/.cache}/ai-weekly-update/<pageId>/` on success.

Rules:
- Never publish on implicit cues ("thanks", "ok"). Require unambiguous approval.
- On `edit <column>: <change>`, re-draft only that column, rebuild patch, re-render, re-ask.
- On `cancel`, delete preview + modified + drafts, stop.

## Safety rules

- **Row scope** — only write into cells of rows whose first-cell text (not strong-marked) matches the user's display name.
- **Column scope** — only write into cells whose column header matches one explicitly targeted in the drafts file.
- **Preserve empty-cell shape** — blank cells in the source ADF are encoded as `{type: paragraph, attrs: {localId: ...}}` with no `content` key; match that shape when leaving cells unchanged.
- **No fabrication** — every sentence traces to a real artifact. If a research source is thin, report that in the preview rather than invent filler.
- **Private Slack opt-in** — only when `slack_search_mode: "public_and_private"` in config AND the user hasn't downgraded this run.

## Files in this skill

- `references/page-parsing.md` — table/row/column structure, name matching, column-map building
- `references/data-sources.md` — Jira / Slack / Outlook / GitHub / Claude-log query patterns + `user.json` schema
- `references/output-style.md` — golden reference, per-column density targets, `code`-mark convention
- `scripts/parse_page.py` — ADF walker, row matcher, dates extractor, patch builder, sentinel stripper
- `scripts/render_preview.py` — standalone HTML preview with diff highlighting
- `scripts/search_github.py` — PRs + commits, with CLAUDE.md and AI keyword filters
- `scripts/scan_claude_logs.py` — local Claude Code session scanner
- `config/user.example.json` — schema template (the real `user.json` is gitignored)
