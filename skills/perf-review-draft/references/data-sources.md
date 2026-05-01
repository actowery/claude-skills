# Data Sources — Performance Review Draft

## Config loading order

1. `${XDG_CONFIG_HOME:-$HOME/.config}/action-item-sync/user.json` — preferred (same team roster)
2. `${XDG_CONFIG_HOME:-$HOME/.config}/ai-weekly-update/user.json` — fallback
3. Fail with: "No team config found — run `action-item-sync init` first."

Workspace config (for `transcript_dir`): `${XDG_CONFIG_HOME:-$HOME/.config}/claude-skills/workspace.json`.

---

## Local transcripts (primary source)

Uses `scripts/mine_transcripts.py`. Greps the local `transcript_dir` for files where the person appears in `participants` and the `date` falls within the review period.

### mine_transcripts.py output

```json
{
  "person": "David Swan",
  "period": {"start": "2026-01-01", "end": "2026-06-30"},
  "meetings": [
    {
      "file": "2026-04-28_0930_david-adrian-1on1.md",
      "date": "2026-04-28",
      "meeting_type": "1on1",
      "topics": ["ADP April check-in", "NatWest PDK RHEL 7 support", "AI maturity"],
      "action_items": [
        "David: complete ADP April check-in by ~May 8",
        "David: continue puppetlabs-firewall Claude implementation (CAT-2614)"
      ],
      "keyword_excerpts": [
        {"keyword": "blocked", "context": "I'm blocked on the RHEL 7 test matrix because...", "speaker": "David Swan"},
        {"keyword": "merged", "context": "The firewall refactor got merged yesterday", "speaker": "David Swan"}
      ]
    }
  ],
  "summary": {
    "total_meetings": 6,
    "one_on_ones": 5,
    "team_meetings": 1,
    "action_items_total": 18,
    "action_items_by_person": 12
  }
}
```

### Keyword groups used for excerpt extraction

`mine_transcripts.py` scans transcript bodies for these groups:

```python
GROWTH_KEYWORDS = [
    "learned", "learning", "course", "certification", "training",
    "improved", "growth", "development", "mentor",
    "took initiative", "drove", "proposed", "designed"
]

DELIVERY_KEYWORDS = [
    "shipped", "merged", "closed", "released", "deployed", "done",
    "finished", "completed", "resolved"
]

BLOCKER_KEYWORDS = [
    "blocked", "waiting on", "stuck", "delayed", "still pending",
    "no update", "hasn't responded", "escalated"
]

QUALITY_KEYWORDS = [
    "clean", "elegant", "well-structured", "impressive", "nice work",
    "revisit", "rework", "needed changes", "too many revisions", "messy"
]

FOLLOW_UP_KEYWORDS = [
    "action item", "ai:", "follow up", "follow-up", "homework",
    "next time", "i'll", "i will", "you'll", "can you"
]
```

Action items in frontmatter are already structured — extract both `person-attributed` items ("`David: ...`") and `me-attributed` items ("`Adrian: ...`") separately.

---

## Jira

### Assigned tickets in period

```jql
assignee = "<atlassian_account_id>"
AND updated >= "<start>"
AND updated <= "<end>"
ORDER BY updated DESC
```

Categorize returned tickets:
| Jira status | Review bucket |
|---|---|
| Done / Closed / Resolved | Delivery & Execution (shipped) |
| In Progress, recently updated | Delivery (active) |
| In Progress, stale (no update >14 days) | Reliability signal |
| To Do / Backlog | Skip |

Keep key + summary + status + resolution date.

### Tickets they commented on

```jql
issueFunction in commented("by <atlassian_account_id> after <start>")
```

If `issueFunction` is unavailable (depends on plugin):
```jql
project in (<team_jira_projects>) AND updated >= "<start>"
```
Then read recent comments and filter manually.

Comment activity signals:
- Technical depth in comments → Technical Craft
- Flagging blockers in comments → Reliability (proactive)
- Questions / requests for clarification → normal — only notable if excessive

### Tickets they opened (reporter)

```jql
reporter = "<atlassian_account_id>"
AND created >= "<start>"
AND created <= "<end>"
```

Tickets they opened = Initiative signal. Cross-reference with the types: bug reports = reliability, improvement/tech-debt = initiative, feature = initiative.

---

## GitHub

Use `scripts/search_github.py` from the `1on1-prep` skill (symlink or copy). The script lives at:
`../1on1-prep/scripts/search_github.py`

Call with `--author <github_username>` to target a specific person.

### PRs authored
```bash
python3 ../1on1-prep/scripts/search_github.py prs \
  --config <config_path> \
  --author <github_username> \
  --start <YYYY-MM-DD> --end <YYYY-MM-DD> \
  --state all
```

For each PR:
- Merged → Delivery & Execution (cite repo + title)
- Open → note, may be active or stale
- Closed (not merged) → note if there's a pattern of abandoned PRs (rare but possible signal)
- PR contains `CLAUDE.md` changes or title contains "Claude", "AI", "skill" → Technical Craft (AI adoption)

### Commits (not in PRs)
```bash
python3 ../1on1-prep/scripts/search_github.py commits \
  --config <config_path> \
  --author <github_username> \
  --start <YYYY-MM-DD> --end <YYYY-MM-DD>
```

Useful for:
- `CLAUDE.md` additions or modifications (AI adoption signal)
- Direct-to-main changes (signals trust + autonomy or bypassing review — context matters)
- Doc updates, test additions (Technical Craft signal)

### PRs they reviewed
```bash
gh search prs \
  --reviewed-by <github_username> \
  --created ">= <start>" \
  --json url,title,createdAt,mergedAt,state \
  --limit 50
```

Review activity signals Collaboration. If they reviewed zero PRs in a long period, that's a Collaboration gap worth noting.

---

## Slack

Tool selected by config `slack_search_mode`. Announce mode before querying.

### Their messages
```
from:<@slack_user_id> after:<start> before:<end>
```

Scan for:
- Announcements of shipped work: "just merged X", "shipped Y to prod" → Delivery
- Asking for help or flagging blockers → Reliability (proactive) or Collaboration
- Thanking / appreciating teammates → Collaboration
- Sharing knowledge / articles / discoveries → Initiative

### Mentions of them
```
to:<@slack_user_id> after:<start> before:<end>
```

Check for pattern of unanswered mentions — collect instances older than 5 business days with no reply. If more than 2–3 in period, that's a Reliability/Collaboration signal.

### Positive signals from others
Search for their display name or @-mention alongside positive words:
```
"<display_name>" (thanks OR "great work" OR "nice job" OR "awesome" OR "helped") after:<start> before:<end>
```

Peer appreciation captured in Slack is Initiative / Collaboration evidence (someone thought to publicly acknowledge them).

---

## Parallelization

All remote sources (Jira, GitHub, Slack) are independent. Fire all queries in one batched message. Cache raw JSON under:
`${XDG_CACHE_HOME:-$HOME/.cache}/perf-review-draft/<person-slug>/<review-period>/`

Cache files:
- `jira-assigned.json`
- `jira-comments.json`
- `jira-reporter.json`
- `github-prs.json`
- `github-commits.json`
- `github-reviews.json`
- `slack-from.json`
- `slack-mentions.json`
- `transcript-mine.json` (output of mine_transcripts.py)

Re-running for the same person + period reuses cache. Force refresh with `--no-cache`.

---

## Cross-referencing transcripts with Jira

This is the highest-value synthesis step. For each action item extracted from transcripts:

1. Extract the item text (e.g., "David: complete puppetlabs-firewall Claude implementation (CAT-2614)")
2. If a Jira key appears in the text, look it up directly
3. If no key, search for tickets with similar text assigned to the person
4. Report: committed in transcript on `<date>`, closed in Jira on `<date>` (or: still open as of review period end)

This cross-reference is the core evidence for the **Reliability & Follow-through** dimension — it's the difference between "said they'd do it" and "actually did it."
