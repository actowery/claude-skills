---
name: ai-exec-report
description: Drafts a weekly AI-adoption email update from an engineering manager to their manager, intended to be forwarded up to the next level of leadership. Researches the team's AI activity across Jira, Slack (public + optional private), Outlook, GitHub (PRs + commits + CLAUDE.md touches), and the manager's local Claude Code session logs, then drafts an email in upper-management language that uplifts the team's wins, mentions the manager's own work secondarily, and is honest about blockers and concerns. Renders a local HTML preview PLUS a .eml draft file that opens in the user's default mail client (Outlook, Mail.app) with To/Subject/Body pre-filled — the skill never sends mail directly. Use this skill whenever the user asks to draft a weekly AI update for their boss / manager / skip-level, an "AI usage email for leadership," a hype email about team AI work, or similar phrases — even when they don't explicitly say "skill" or "draft." Distinct from `ai-weekly-update` (which fills a Confluence row) and `weekly-confluence-update` (which is general team status): this skill's output is an EMAIL, is team-uplift focused, and is for upward communication.
---

# AI Exec Report

Drafts a weekly team-AI-adoption email from a manager to their manager. The recipient is expected to forward the content (or re-summarize it) to their own leadership, so the draft reads for that audience, not peers.

**Tone posture**: hype-but-honest. The goal is to uplift the team's AI-adoption work in concrete, non-promotional language. Include difficulties, blockers, and concerns — those give the wins credibility. The manager's own work is mentioned but kept secondary; the point is to surface what the team is doing.

**Delivery**: the skill never sends email directly. It renders an HTML preview and writes a `.eml` file to `/tmp/`. Double-clicking the `.eml` opens it in the user's default mail client as a draft with To/Subject/Body pre-filled. User reviews in-app and clicks Send themselves.

## Config & cache locations

- **User config**: `${XDG_CONFIG_HOME:-$HOME/.config}/ai-exec-report/user.json`
- **Research cache**: `${XDG_CACHE_HOME:-$HOME/.cache}/ai-exec-report/<YYYY-MM-DD>/`

Paths live outside the skill install dir so plugin upgrades can't wipe your boss's email or the cached team roster.

## Blast-radius table

| Action | Scope | When |
|---|---|---|
| Write `${XDG_CONFIG_HOME:-$HOME/.config}/ai-exec-report/user.json` | Local write | Phase 0 init — path announced first |
| Write `/tmp/ai-exec-report-<date>.html` (preview) + `.eml` (draft file) | Local write | Phase 6 |
| Write research cache under `${XDG_CACHE_HOME:-$HOME/.cache}/ai-exec-report/` | Local write | Phase 4 |
| Run `open <path>` to launch browser for preview | Local | Phase 6 |
| Read Jira / Slack / Outlook / GitHub / local Claude Code logs | Remote reads only | Phase 4 |
| **Send an email** | **Never — handled by the user clicking Send in their mail client** | — |
| Auto-CC anyone, skip-levels, or distribution lists beyond what the user configured | **Never** | — |

## Prerequisites

- Atlassian MCP (Jira for signal)
- Slack MCP (for team discussion signal)
- Outlook / M365 MCP (for research, not for sending)
- Zoom MCP (for meeting transcripts and summaries via AI Companion)
- `gh` CLI authenticated with `repo` scope
- Read access to `~/.claude/projects/` for local session scan
- A default mail client on the OS that handles `.eml` files (macOS Mail.app, Outlook, etc.)

If any are missing, the skill still runs. After delivering the preview, follow `_shared/missing-sources.md` to append a **More signal available** note for any source that couldn't run or had no config.

## Workflow

### Phase 0 — Init / edit user config

Trigger: `init ai-exec-report`, "set up the exec report," similar intent.

**Side effects:** read-only MCP calls; writes `${XDG_CONFIG_HOME:-$HOME/.config}/ai-exec-report/user.json` locally.

1. Call `atlassianUserInfo` to capture the user's name + email.
2. Ask for the boss's name + email (required — the skill cannot draft without a recipient).
3. Offer to import the team roster from an existing `$XDG_CONFIG_HOME/ai-weekly-update/user.json` if one is present. Show the member list and ask to confirm.
4. Ask for any additional CC recipients — default none. Common case: leave empty and let the boss forward up.
5. Ask for AI keywords + Jira AI labels — offer defaults: `["Claude", "Anthropic", "CLAUDE.md", "AI", "agent", "skill"]` and `["AI", "Claude", "Devx"]`.
6. Slack mode: `public` or `public_and_private` — default `public`.
7. Ask whether to scan local Claude Code logs — default yes.
8. Announce the XDG path, then write `user.json`. Create parent dirs.

Do not invent values. Boss's email is the only truly required field.

### Phase 1 — Load config and determine window

**Side effects:** read-only (`atlassianUserInfo`, `getAccessibleAtlassianResources` if needed); no writes.

1. Load `user.json` from XDG path. If absent, route to Phase 0.
2. Confirm the user's display name and email haven't drifted from the cache.
3. Determine the reporting window. Default: Monday → Friday of the current week. If today is Saturday/Sunday, default to the week that just ended. User can override with explicit dates.

### Phase 2 — Research the team's AI activity

**Side effects:** read-only external searches (Jira, Slack, Outlook, GitHub, local Claude logs). Writes research cache under `${XDG_CACHE_HOME:-$HOME/.cache}/ai-exec-report/<YYYY-MM-DD>/`.

Announce sources up front. Example:
> Researching <window>. Sources: Jira (AI labels + team assignees), Slack (public + private per config), Outlook (AI keywords, your inbox only), GitHub (team PRs + commits in orgs: <orgs>), Zoom (meeting transcripts + summaries via AI Companion), Claude Code logs (your local only). Reply `public only` to downgrade Slack this run.

Fire queries in parallel. Same patterns as `ai-weekly-update` — see `references/data-sources.md` for specifics. Key differences:

- **Team fan-out by default** — this skill is always in manager-with-team mode (it's for managers reporting on their team). If no team is configured in `user.json`, ask the user to init first.
- **Include Champions** — unlike `ai-weekly-update`, this skill does NOT apply the self-reporting-champion rule. The email is a standalone artifact that does not conflict with anyone's Champion row; the team's wins should appear in full regardless of where else they're surfaced.
- **Outlook is broader** — search the user's inbox for threads matching any team member's name OR any AI keyword, not just the user's own mail. Still personal mailbox only; no delegated access.

### Phase 3 — Synthesize per-member briefs

**Side effects:** none — pure reasoning.

For each team member with any signal in the window, produce a short brief capturing:
- 1–3 concrete things they did (PR title / Jira summary / Slack thread subject), with links
- One-sentence impact framing in upper-mgmt language (no jargon; lead with outcome)
- Honest assessment: is this "shipped", "in flight", "blocked"?

For the user themselves, produce a briefer brief: 1–2 items max.

See `references/email-style.md` for the full tone + density guide. Do NOT write the email yet — produce the briefs as structured notes.

### Phase 4 — Draft the email

**Side effects:** none — pure reasoning.

Structure (the renderer in Phase 5 lays this out):
1. **Subject** — `<Team> AI Weekly — <M–D M–D, YYYY>` (plain, skimmable)
2. **Greeting** — `<Boss first name>,`
3. **Opening sentence** — one-sentence posture on the week ("The team had a strong week on X" / "Mixed week — lots of momentum on X, a real blocker on Y" / "Quiet week on shipments; heavy prep for Z next week")
4. **Team wins section** — one paragraph per team member with meaningful activity, led by their name. Uplift, don't inflate. Concrete artifacts. First-name-last-name on first reference, first name thereafter.
5. **Blockers & concerns section** — one short paragraph. Honest. Name owners. Propose help asks if any.
6. **Personal work section** — one or two sentences on what the user drove this week, not more. Do not hide, do not puff up.
7. **Closing** — brief offer to discuss in 1:1 or before the boss's upward review.
8. **Sign-off** — user's first name.

Every factual claim in the email must cite a Jira key, PR number, or a clear attribution (name + action verb + artifact).

**Maturity tagging.** Upper-management audiences use maturity framing to understand trajectory, not just ticket count. Weave S-level + phase into the narrative per `references/ai-maturity-model.md`, without making it mechanical. See `references/email-style.md` for the calibration — the goal is that a reader skimming the email comes away with a mental picture of *where* the team is on the curve, not just *what* they shipped. Do this at paragraph level (per teammate or per team-level beat), never per sentence, and finish the body with a one-sentence trajectory read if one is fair ("Team is mostly at S1 Build with increasing S2 Deploy via custom skills").

### Phase 5 — Render preview + draft file

**Side effects:** writes `/tmp/ai-exec-report-<YYYY-MM-DD>.html` (preview) and `/tmp/ai-exec-report-<YYYY-MM-DD>.eml` (mail-client-openable draft). On macOS, also drives Outlook via AppleScript to open a real editable draft window.

```
scripts/render_email.py \
    --draft <path to JSON produced in Phase 4> \
    --to <boss-email> --cc <comma-separated> \
    --from-name "<user display name>" --from-email "<user email>" \
    --out-html /tmp/ai-exec-report-<date>.html \
    --out-eml /tmp/ai-exec-report-<date>.eml \
    --push-to-outlook     # macOS + Outlook users — see note below
```

Open the HTML preview with `open <path>`.

**Outlook for Mac caveat.** Double-clicking a `.eml` file in Outlook for Mac opens it as a **read-only viewer**, ignoring the `X-Unsent: 1` header that marks it as a draft. There is no Send button in that viewer. The `--push-to-outlook` flag drives Outlook's AppleScript API directly to create a real draft window (with Send button) in the user's running Outlook instance. The `.eml` and HTML files are still written as a paper-trail backup but are not the primary delivery path. Always pass `--push-to-outlook` when the user's default mail client is Outlook for Mac. Apple Mail users can omit it (Mail.app handles the `.eml` draft correctly).

Tell the user:
> Draft opened in Outlook with Send button. Preview at `<html path>` for reference.
>
> Reply `approve` — the draft stays open in Outlook; you click Send when ready.
> Reply `edit <section>: <change>` to rewrite that section (I'll close the current draft and open a revised one).
> Reply `cancel` to discard the Outlook draft and delete the local files.

**Missing-sources check.** After delivering the above prompt, follow `_shared/missing-sources.md`: check which of the seven sources (Zoom, Jira, Slack public, Slack private, Outlook, GitHub, Claude Code logs) were skipped or errored during Phase 2. If any were, append the **More signal available** note at the end of your message — after the approve/edit/cancel options, never before.

### Phase 6 — Finalize on approval

**Side effects:** on approval, the files stay in `/tmp/` for the user to open. On cancel, delete both.

The skill never sends mail. The "publish" step is whatever the user does next in their mail client. This is an explicit design choice — upward-comm email is high-stakes and belongs to the human.

On any response other than unambiguous approval (`approve`, `looks good`, `ship it`), treat as edit/cancel and re-prompt.

## Safety rules

- **Never send mail** — the skill's only output is files on local disk.
- **Never CC someone the user didn't configure**. Never add the boss's boss to TO or CC; the whole point is that the boss forwards.
- **Team scope only** — do not attribute wins to people outside the user's `team.members[]`.
- **No fabrication** — every named artifact must trace to a real Jira/PR/commit/Slack/email/log entry. If research is thin, reflect that in the email rather than invent.
- **Honesty requirement** — the email MUST include at least one blocker/concern/nuance line, even when the week was genuinely good. If there's truly nothing, say so explicitly ("No material blockers this week"). Excessive positivity without any grounding reads as unreliable signal to leadership.
- **Respect the boss's preferences** — if the user has configured `boss_tone_preference` in `user.json` (`hype-friendly` / `balanced` / `sober`), calibrate accordingly. Default is `balanced`.
- **Pronouns** — when referring to a teammate by pronoun in the email, use the value from their `pronouns` config field. If absent, use the person's name only. Never guess pronouns from a name. See `_shared/pronoun-handling.md`. This is especially important here because the email goes upward — wrong pronouns in an exec-facing artifact are expensive to fix.

## Files in this skill

- `references/email-style.md` — tone rules, per-section density targets, good/bad examples
- `references/data-sources.md` — query patterns shared with `ai-weekly-update`, plus exec-specific framing notes
- `scripts/search_github.py` — team PR + commit search with AI filter
- `scripts/scan_claude_logs.py` — local Claude Code session scan
- `scripts/render_email.py` — HTML preview + `.eml` draft writer
- `config/user.example.json` — schema template (real `user.json` is gitignored)
