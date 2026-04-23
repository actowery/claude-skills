# how-can-i-help

A Claude Code skill that scans your Jira / Slack / Outlook / GitHub footprint for **items that have fallen through the cracks** — stale conversations, read-but-not-replied emails, buried @-mentions, forgotten action items — and returns a short, honest brief (up to 3 items) with the psychology of why helping matters, the business benefit, and a specific low-effort management action you can take.

**Not** a triage queue. **Not** a dashboard. **Not** the things your team's already actively raising to you. The point is to find what you don't already know about — where conversation stopped mid-flight and nobody's chasing it.

## When to run it

- Start of a week — what fell through last week's cracks
- After a high-meeting / low-focus day — what got missed
- Before a team offsite — what you want cleared before you're off the grid
- Whenever you catch yourself thinking "I feel like I'm forgetting something"

## Prerequisites

| Tool | Used for | Required? |
|---|---|---|
| Atlassian MCP | Jira silence/staleness queries | Yes |
| Slack MCP | Unanswered threads and buried @-mentions | Recommended |
| Outlook / M365 MCP | Read-but-not-replied inbound | Recommended |
| `gh` CLI | Stale-PR detection | Recommended |

Private Slack search is opt-in per user config — off by default.

## Quick start

Installed via the consolidated repo — see the top-level [README](../../README.md#installing-all-of-them).

**First run — configure:**
```
init how-can-i-help
```
Bootstraps from your `ai-weekly-update` config if it's present (team roster is the key overlap). Saves to `${XDG_CONFIG_HOME:-$HOME/.config}/how-can-i-help/user.json`.

**Each run:**
```
how can I help today?
```
(or any phrasing that describes the intent — "what fell through the cracks this week", "what have I missed", etc.)

The skill:
1. Loads your config and determines a scan window (default: past 14 days)
2. Scans all configured sources in parallel for stale/silent/forgotten items
3. Scores candidates, picks up to 3
4. Produces a markdown brief in chat + mirrors it to `/tmp/how-can-i-help-<date>.md`
5. Done — no drafting, no publish, no approval gate

## Output shape

Each item in the brief has four fields:

- **Description** — what it is, who's involved, when it went silent (with citations to the artifact)
- **Why help matters to them** — the psychology of what your help removes (friction, expectation gaps, social-capital load)
- **Business benefit** — the org-level outcome (velocity, customer retention, adoption acceleration, attrition insurance)
- **Suggested action** — one specific low-effort thing you can do, ideally ≤5 minutes

See [`references/management-psychology.md`](references/management-psychology.md) for the honest framings used in the "why" and "benefit" fields — explicitly designed to avoid greeting-card platitudes.

## Safety

- **Read-only.** The skill never writes to Jira, Slack, email, or GitHub.
- **Honest count.** Up to 3 items — but if fewer than 3 actually meet the bar, the brief is shorter. Empty "quiet week" outputs are valid and useful.
- **No fabricated emotion.** The skill frames around observable friction, not invented feelings.
- **No surveillance creep.** The "gone quiet" signal exists but is used sparingly and always with a low-pressure framing. The skill won't suggest actions that read as monitoring team members' activity patterns.

## Files

```
how-can-i-help/
├── SKILL.md                              # Workflow + safety rules
├── README.md                             # This file
├── references/
│   ├── pain-point-catalog.md             # Crack types with example signals and action patterns
│   ├── management-psychology.md          # Honest framings; anti-patterns to avoid
│   └── data-sources.md                   # Per-source query patterns + user.json schema
├── scripts/
│   ├── search_github.py                  # Stale-PR detection (shared with other skills)
│   ├── scan_claude_logs.py               # Gone-quiet sanity check via local session history
│   └── render_brief.py                   # Candidates JSON → markdown brief
├── config/
│   └── user.example.json                 # Schema template (real user.json is gitignored)
└── tests/
    ├── fixtures/
    ├── make_fixtures.py
    └── smoke_test.py
```

## Running the smoke test

```
python3 tests/smoke_test.py
```

Covers the renderer (3-item, 1-item, empty cases), confirms the honest-count path doesn't fabricate filler, and checks the shared scripts' dry-run behavior. No network.
