# ai-exec-report

A Claude Code skill that drafts a weekly **email** from an engineering manager to their manager — summarizing the team's AI-adoption work in upper-management language, with an explicit honest-blockers section so the wins don't read as performative. The skill **does not send mail**. It renders an HTML preview and writes a `.eml` draft file that opens in your default mail client (Outlook, Mail.app) with To/Subject/Body pre-filled; you send it from there.

Companion to the `ai-weekly-update` skill. Different audience, different artifact:

| Skill | Audience | Artifact |
|---|---|---|
| `ai-weekly-update` | You + skip-level leadership reading the shared Confluence page | Row update on a shared AI-usage Confluence page |
| **`ai-exec-report`** | **Your manager, forwarding upward** | **An email draft (HTML preview + `.eml` file)** |

## Prerequisites

| Tool | Used for | Required? |
|---|---|---|
| Atlassian MCP | Jira AI-tagged ticket search | Yes |
| Slack MCP | Team AI-discussion signal | Recommended |
| Outlook / M365 MCP | Research only — the skill never sends mail | Recommended |
| `gh` CLI | Team PRs + commits in configured orgs | Recommended |
| Read access to `~/.claude/projects/` | Local Claude Code session scan | Optional, on by default |
| A default mail client that opens `.eml` files | Sending (macOS Mail.app, Outlook, etc.) | Yes, for the send step |

## Quick start

Installed via the consolidated repo — see the top-level [README](../../README.md#installing-all-of-them) for symlink setup.

**First run — configure:**
```
init ai-exec-report
```
Claude asks for your boss's name + email, optional CC list, team roster (offered as an import from `ai-weekly-update`'s config if present), Slack mode, AI keywords, and whether to scan local Claude Code logs. Writes to `${XDG_CONFIG_HOME:-$HOME/.config}/ai-exec-report/user.json`.

**Each week:**
```
draft my AI exec report
```
or similar phrasing. Claude:
1. Loads your config
2. Determines the reporting window (defaults to Mon–Fri of the current week)
3. Researches in parallel across Jira / Slack / Outlook / GitHub / Claude logs
4. Synthesizes per-member briefs, drafts the email
5. Renders an HTML preview + writes a `.eml` draft file
6. Waits for `approve` / `edit <section>: <change>` / `cancel`

On approve: both files stay in `/tmp/` for you to open. Double-click the `.eml` to open the draft in your default mail client, review once more, and click Send.

## Tone posture

The email is **hype-but-honest**:
- Team wins in full, concrete, cite-able form
- Honest blockers and concerns — non-negotiable, even when the week was genuinely smooth
- Your own work mentioned briefly, never the headline
- No emoji, no bullet lists, no superlatives, no throat-clearing

Full guide in [`references/email-style.md`](references/email-style.md).

## Files in this skill

```
ai-exec-report/
├── SKILL.md                # Workflow + safety rules
├── README.md               # This file
├── references/
│   ├── email-style.md      # Tone, density, good/bad examples
│   └── data-sources.md     # Query patterns + user.json schema
├── scripts/
│   ├── search_github.py    # Team PRs + commits with --ai-filter
│   ├── scan_claude_logs.py # Local session scanner
│   └── render_email.py     # HTML preview + .eml draft file
├── config/
│   └── user.example.json   # Schema template (real user.json is gitignored)
└── tests/
    ├── fixtures/
    ├── make_fixtures.py
    └── smoke_test.py
```

## Running the smoke test

```bash
python3 tests/smoke_test.py
```

22 assertions across the renderer (HTML + `.eml` parsing), the shared GitHub script (dry-run fan-out), and the Claude log scanner. No network, no mail-sending, no fixtures needed at runtime.

## Safety

- **Skill does not send mail.** The only "publish" step is you clicking Send in your own mail client. If the skill ever appears about to send mail on its own, stop it — that's a bug.
- **No auto-CC** beyond what's configured in `user.json`. Never adds the boss's boss, skip-levels, or distribution lists on its own.
- **Team-scope attribution only.** Wins attributed to people outside the configured `team.members[]` are a bug.
- **No fabrication.** Every named artifact must trace to a real Jira ticket, PR, commit, or Slack/email entry. If research is thin, the email says so rather than filling with generic language.
- **Honesty requirement.** The blockers section is always present. "No material blockers" is a valid entry — silence is not.
