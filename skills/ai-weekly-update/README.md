# ai-weekly-update

A Claude Code skill that fills the current user's **individual row** on a shared Confluence AI-usage weekly-report page (Champion or Manager tables). It researches the reporting window across Jira, Slack (public + private), Outlook, GitHub (PRs / commits / CLAUDE.md touches), and local Claude Code session logs, drafts dense AI-focused content into the user's columns, shows a local HTML preview, and only publishes after explicit approval.

Companion to [weekly-confluence-update](https://github.com/actowery/weekly-confluence-update) (team-level). This one is per-individual and matches the user by plain-text name in the row's first cell — no `@mention` required on the page.

## Prerequisites

| Tool | Used for | Required? |
|---|---|---|
| Atlassian MCP (Confluence + Jira) | Fetch/update the page; AI-label Jira search | Yes |
| Slack MCP | Search public + (optionally) private for AI discussion | Yes |
| Outlook / M365 MCP | Search email for AI / Claude threads | Recommended |
| `gh` CLI | Your PRs + commits + CLAUDE.md touches in configured orgs | Recommended |
| Read access to `~/.claude/projects/` | Scan local session logs for AI activity signal | Optional, on by default |

Private Slack search is **off by default**. Enable via `slack_search_mode: "public_and_private"` in your user config, or decline per-run with `public only`.

## Quick start

```bash
git clone --branch v0.1.0 https://github.com/<you>/ai-weekly-update.git \
  ~/.claude/skills/ai-weekly-update
```

**First run — configure:**
```
init ai-weekly-update
```
Claude asks for your Slack mode, GitHub orgs, AI keywords, and whether to scan Claude Code logs. Writes `${XDG_CONFIG_HOME:-$HOME/.config}/ai-weekly-update/user.json` — outside the skill install dir so plugin upgrades don't wipe your config.

**Each week:**
```
fill my AI weekly: <confluence-url>
```

Claude:
1. Fetches the page and finds your row (matches by display name)
2. Parses column headers ("Wins this week", "Blockers", etc.)
3. Parses the date range from the page title
4. Runs parallel research across five sources
5. Drafts dense, AI-focused paragraphs into your columns
6. Opens a local HTML preview with your additions highlighted yellow
7. Waits for `approve` / `edit <column>: <change>` / `cancel`

Nothing writes to Confluence until you explicitly approve.

## What's in the box

```
ai-weekly-update/
├── SKILL.md                   # Workflow + safety rules — start here
├── README.md                  # This file
├── LICENSE                    # MIT
├── references/
│   ├── page-parsing.md        # Table / row / column map, name matching
│   ├── data-sources.md        # 5 sources + user.json schema
│   └── output-style.md        # Golden reference + density targets per column
├── scripts/
│   ├── parse_page.py          # ADF parser, row matcher, dates, patch builder
│   ├── render_preview.py      # Standalone HTML with diff highlighting
│   ├── search_github.py       # PRs + commits with AI keyword filters
│   └── scan_claude_logs.py    # Local Claude Code session scanner
├── config/
│   └── user.example.json      # Schema template
├── tests/
│   ├── fixtures/              # Sanitized sample pages + user config
│   ├── make_fixtures.py
│   └── smoke_test.py
└── .github/workflows/smoke.yml
```

## Running the smoke test

```bash
python3 tests/smoke_test.py
```

Exercises the parser, patch builder, sentinel strip, HTML renderer, and the Claude-log scanner against sanitized fixtures. No network, no auth, no external tools required. Also regenerates fixtures and fails if they drift from `make_fixtures.py`.

## Different template?

If your AI-report Confluence template uses different table headings or different column names, tell the skill once via `init ai-weekly-update` — the parser is header-driven and doesn't hard-code column names.

## Safety rules the skill follows

- **Row-scoped** — only edits cells in rows where the first-cell plain text matches your display name (case-insensitive).
- **Never touches group dividers** — rows where the first cell is bold (`Puppet`, `Delphix`) are skipped.
- **Never fabricates** — every sentence traces to a real Jira ticket, Slack message, email, PR, commit, or session log entry.
- **Private Slack is opt-in** — off by default; enable per-config, override per-run.
- **Approval-gated** — no Confluence write without explicit `approve`.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| "Zero rows matched your name" | Your row might be under a different name on the page (middle initial? nickname?) — set `display_name_overrides` in user config |
| Columns not found | Page template uses non-standard headers — pass `--column-map` or override via `user.json` |
| Claude log scan empty | Windows before Claude Code was installed, or session files live outside `~/.claude/projects/` — configurable via `claude_log_dir` |
| GitHub returns empty | `gh auth status` → confirm repo scope; check `github.orgs` in user config |
