---
name: zoom-transcript-sync
description: Scans Zoom My Notes (dictation captured via Zoom AI Companion) for a configurable date window, compares against transcripts already saved locally, and saves any new ones as structured markdown files with YAML frontmatter. Writes nothing to Zoom — purely a one-way pull into a local transcript directory. Use this skill whenever the user asks to sync, scan, fetch, or pull Zoom transcripts, meeting notes, or dictation — even without the explicit skill name. Triggers include "sync zoom notes", "scan my zoom transcripts", "fetch zoom dictation", "pull meeting notes from zoom", "did I miss any zoom notes".
---

# Zoom Transcript Sync

Pull Zoom AI Companion dictation (My Notes) for a date window, deduplicate against what's already saved locally, and write new transcripts as structured markdown files.

**Output**: one `.md` file per new meeting with dictation, written to `transcript_dir`. Summary of what was found and what was skipped printed inline. No remote writes, no approval gate.

## Critical rules — read before touching any Zoom MCP calls

These encode hard-won experience with unreliable Zoom API fields:

1. **Never use `has_transcript: false` to skip a meeting.** This field is a false flag — many meetings with `has_transcript: false` have dictation in `my_notes.transcript`. Call `get_meeting_assets` regardless.
2. **Never use `has_transcript_permission: false` to skip a meeting.** Same issue — unreliable for My Notes dictation.
3. **Never use `get_file_content` for dictation.** It returns empty content even when a My Notes file exists. Dictation is only accessible via `get_meeting_assets`.
4. **The only reliable skip signal**: `get_meeting_assets` response where `has_my_notes: false`.
5. **`schedule_expired` entries use numeric IDs** — `get_meeting_assets` on a numeric ID returns the **latest** history occurrence of that recurring meeting, not a specific past occurrence. After fetching, verify the returned meeting's date falls within the scan window before saving.
6. **Large responses auto-save to temp files**: when `get_meeting_assets` returns more than ~100KB, results are saved to `~/.claude/projects/.../tool-results/<tool-call-id>.txt`. Extract transcript text with: `jq -r '.my_notes.transcript.transcript_items[].text' <tempfile>`

## Config & cache locations

- **Workspace config** (shared): `${XDG_CONFIG_HOME:-$HOME/.config}/claude-skills/workspace.json` — provides `transcript_dir`
- **Skill config**: `${XDG_CONFIG_HOME:-$HOME/.config}/zoom-transcript-sync/user.json`
- **Research cache**: none — meetings are fetched fresh each run

See `_shared/workspace-config.md` for the workspace config schema and resolution order.

## Blast-radius table

| Action | Scope | When |
|---|---|---|
| Write `${XDG_CONFIG_HOME:-$HOME/.config}/claude-skills/workspace.json` | Local | Phase 0 init only — path announced first |
| Write `${XDG_CONFIG_HOME:-$HOME/.config}/zoom-transcript-sync/user.json` | Local | Phase 0 init only — path announced first |
| Write `<transcript_dir>/YYYY-MM-DD_HHMM_<slug>.md` | Local | Phase 6 — listed before writing |
| Read Zoom My Notes via `search_meetings` + `get_meeting_assets` | Remote reads only | Phases 3–4 |
| Write anything to Zoom | **Never** | — |

## Prerequisites

- Zoom MCP with `search_meetings` and `get_meeting_assets` tools
- `jq` CLI (for large-response extraction from temp files)

If Zoom MCP is missing, fail fast with a clear message — this skill cannot run without it.

## Invocation

```
zoom-transcript-sync               # scan default window (scan_window_days from config)
zoom-transcript-sync since <date>  # explicit start date (e.g. "since 2026-04-14")
zoom-transcript-sync <date> to <date>   # explicit window
zoom-transcript-sync --dry-run     # show what would be saved without writing files
```

## Transcript file format

All transcript files use this structure. Optimize frontmatter for grep-based lookup — participant names must be full names as they appear in the transcript.

```markdown
---
date: YYYY-MM-DD
time: "HH:MM"
participants:
  - Full Name
  - Full Name
meeting_type: ""   # 1on1 | team | stakeholder | other
topics:
  - keyword topic
action_items:
  - "Owner Name: task description"
source: zoom-ai
---

Speaker Name: line of dictation text.
Speaker Name: continuation.
```

**`meeting_type` inference rules:**
- `1on1`: exactly 2 distinct speakers
- `team`: 3–8 distinct speakers, internal meeting feel
- `stakeholder`: external company names in topics or participant names
- `other`: anything else, or when inference is unclear

**Filename format**: `YYYY-MM-DD_HHMM_<meeting-topic-slug>.md`
- Date and time from the meeting's actual start time (not today's date)
- Slug: lowercase, spaces to hyphens, strip special characters, max 50 chars
- Example: `2026-04-28_1430_barr-adrian-1on1.md`

## Workflow

### Phase 0 — Init / bootstrap config (only on first run or when `init zoom-transcript-sync` is invoked)

**Side effects:** writes workspace config and/or skill config.

1. **Workspace config**: load `${XDG_CONFIG_HOME:-$HOME/.config}/claude-skills/workspace.json` if it exists. If absent, offer to create it:
   - Ask for `transcript_dir` (the directory where transcript markdown files are saved). Default: current working directory.
   - Ask for `workspace_dir` if the user wants to derive other paths from a single root (optional).
   - Announce the XDG path, write `claude-skills/workspace.json`. Create parent dirs.

2. **Skill config**: load `${XDG_CONFIG_HOME:-$HOME/.config}/zoom-transcript-sync/user.json` if it exists. If absent, collect:
   - `email` — user's email address (used to verify Zoom identity if needed)
   - `scan_window_days` — how many days back to scan (default: 14)
   - Announce the XDG path, write `zoom-transcript-sync/user.json`. Create parent dirs.

### Phase 1 — Load config and resolve paths

**Side effects:** none.

1. Load workspace config. Resolve `transcript_dir`:
   - Use `transcript_dir` from workspace config if set.
   - Else derive: `<workspace_dir>/transcripts` if `workspace_dir` is set.
   - Else: current working directory.
2. Load skill config. Resolve scan window:
   - If invocation includes explicit dates, use those.
   - Else if `last_successful_scan` is set in skill config, use that date → today.
   - Else: today minus `scan_window_days` → today.
3. Announce:
   > Transcript directory: `<transcript_dir>`
   > Scan window: `<start_date>` → `<end_date>`

   Pause for a moment (one breath). If the transcript_dir doesn't exist, warn the user and ask whether to create it or abort. Do not silently create it.

### Phase 2 — Inventory existing transcripts

**Side effects:** read-only filesystem.

1. Scan `<transcript_dir>/*.md` for all existing transcript files.
2. Extract date and time from each filename (`YYYY-MM-DD_HHMM_*.md` pattern).
3. Build an index: list of `{date, time_approx}` tuples already saved.
4. Count files in the scan window vs. total (for the final report).

### Phase 3 — Search Zoom

**Side effects:** read-only Zoom MCP calls.

#### Step 3a — `search_meetings`

Call `search_meetings` with:
- `from`: scan window start date (UTC)
- `to`: scan window end date (UTC)
- `include_zoom_my_notes: true`

Collect all results regardless of:
- `meeting_category` (`history`, `schedule_expired`, or any other value)
- `has_transcript` field value — **do not filter on this**
- `has_transcript_permission` field value — **do not filter on this**

#### Step 3b — `search_zoom` with `doc_view: "notes"` (catches ad hoc meetings)

`search_meetings` only indexes scheduled meetings. Instant/PMI meetings (e.g. "Adrian Towery's Zoom Meeting") never appear there. To catch them, also call `search_zoom` with:

```json
{
  "search_entities": [{"entity_type": "zoom_doc", "filters": {"doc_view": "notes", "from": "<window_start_UTC>", "to": "<window_end_UTC>"}}],
  "page_size": 50
}
```

The `from`/`to` filter on `modify_time`, not start time — set `to` to end of today UTC to avoid missing notes from meetings that completed just before the sync.

For each doc returned:
- Extract `file_id`, `title`, and `create_time` (≈ meeting start time).
- Check whether the `create_time` falls within the scan window. If not, skip.
- Check whether a meeting with this title and time already appears in the Step 3a results. If it does, skip (prefer the `meeting_uuid` path).
- Otherwise → mark as **doc-only** entry and carry it into Phase 4.

Log: "Found X meetings via search_meetings, Y additional doc-only entries via search_zoom."

### Phase 4 — Fetch meeting assets

**Side effects:** read-only Zoom MCP calls.

There are two entry types from Phase 3 — handle each differently.

#### Scheduled meetings (from Step 3a)

Call `get_meeting_assets` for every meeting:
- Prefer `meeting_uuid` over `meeting_number` when a UUID is available (targets the specific occurrence).
- For `schedule_expired` entries that only have a numeric `meeting_number`: call with the numeric ID, but after receiving the response, **check the returned meeting date** — if it falls outside the scan window, skip it (log: "returned occurrence out of window — skipping").

After each call:
- If `has_my_notes: false` → log "no dictation" and skip. This is the only reliable skip signal.
- If `transcript_items` is null or empty despite `has_my_notes: true` → log "has_my_notes but no items — skipping" and skip.
- Otherwise → queue for deduplication in Phase 5, tagged as **raw transcript**.

**Large response handling**: if the tool result contains a file path instead of inline JSON (the response will include a path like `~/.claude/projects/.../tool-results/<id>.txt`), read that file and extract transcript items with:
```bash
jq -r '.my_notes.transcript.transcript_items[].text' <tempfile>
```

#### Doc-only entries (from Step 3b)

These are ad hoc / instant PMI meetings with no meeting UUID accessible via `search_meetings`. Use `get_file_content` with the `file_id` from the `search_zoom` result:

```
get_file_content(fileId: "<file_id>") → file_name, file_content (Markdown)
```

- If the response is empty or an error → log "doc-only: no content retrievable — skipping" and skip.
- Otherwise → queue for deduplication in Phase 5, tagged as **AI summary only** (no raw transcript items).
- Use `create_time` from the `search_zoom` result as the meeting start time for deduplication and filename.

Process meetings one at a time in this phase — do not fire all calls in parallel, as large responses are more manageable sequentially.

### Phase 5 — Deduplicate

**Side effects:** none.

For each meeting queued in Phase 4:

1. Extract the meeting's start date and time from `my_notes.transcript` metadata or meeting info.
2. Check the existing transcript index (Phase 2):
   - Match if any existing file has the **same date** (YYYY-MM-DD) **and** a start time within ±10 minutes.
   - If matched → log "already saved: `<existing filename>`" and skip.
3. If no match found → mark as new, proceed to Phase 6.

When in doubt (ambiguous match), prefer writing a new file over silently skipping. Duplicates can be manually deleted; silent skips can't be detected.

### Phase 6 — Write new transcripts

**Side effects:** writes `.md` files to `transcript_dir`. Announce the list of files to be written before writing any.

For each new meeting:

1. **Extract participants**: collect unique speaker names from `transcript_items[].speaker`. If speaker names are not present in items (or this is an AI-summary-only entry), fall back to names mentioned in the summary content or meeting metadata.
2. **Infer meeting type**: count distinct speakers → `1on1` (2 speakers), `team` (3–8), `other` (>8 or unclear).
3. **Extract topics** (3–6 keywords): skim the transcript or summary for recurring themes, product/project names, and key discussion areas.
4. **Extract action items**: scan for explicit commitments — phrases like "I'll", "you'll", "action:", "follow up", "by [date]", "will send", "need to". Format as `"Owner Name: task"`.
5. **Generate filename**: `YYYY-MM-DD_HHMM_<topic-slug>.md` using the meeting's actual date/time.
6. **Write file**:
   - **Raw transcript**: YAML frontmatter block, then the full raw transcript — one line per `transcript_items[].text`, prefixed with speaker name if available: `Speaker Name: text`. Do not truncate or summarize.
   - **AI summary only**: YAML frontmatter block with an added `note: "AI summary only — instant/PMI meeting, raw transcript unavailable"` field, then the full `file_content` from `get_file_content` verbatim.

### Phase 7 — Report

Print a summary after all writes complete:

```
Zoom transcript sync complete.

Window: <start> → <end>
Meetings scanned: X (Y scheduled via search_meetings + Z ad hoc via search_zoom)
  New transcripts saved: A
    Raw transcripts: B
    AI summary only (ad hoc/PMI): C
  Already existed: D
  No dictation: E
  Out of window: F (schedule_expired, returned occurrence outside scan range)

New files:
  transcripts/2026-04-28_1430_barr-adrian-1on1.md
  transcripts/2026-04-29_1000_devx-standup.md
  transcripts/2026-04-30_1132_devx-eric-pr-automation.md  [AI summary only]

Already saved (skipped):
  transcripts/2026-04-20_1200_weekly-champions-sync.md
```

If no new transcripts were found: confirm this clearly — "All meetings in the window already have transcripts saved locally, or had no Zoom dictation."

After printing the report, write today's date to `last_successful_scan` in `~/.config/zoom-transcript-sync/user.json`. This is the date future runs will use as their start boundary when no explicit dates are given.

## Safety rules

- **Read-only remote.** Never write to Zoom.
- **Announce before writing.** List the files to be created and their paths before writing any of them. Never silently write files.
- **Verify scan window for `schedule_expired`.** A numeric meeting ID always returns the latest history occurrence, which may predate the scan window. Always check the returned date before saving.
- **Never truncate transcripts.** Write the full raw dictation.
- **No fabrication.** Participants, topics, and action items must come from the transcript text — never invented or inferred from context outside the transcript.
- **Dry-run mode.** When invoked with `--dry-run`, print exactly what would be written (paths, frontmatter) without writing any files.

## Config schema

### Workspace config (`~/.config/claude-skills/workspace.json`)

See `_shared/workspace-config.md` for the full schema. Relevant field for this skill:

```json
{
  "transcript_dir": "/absolute/path/to/transcripts"
}
```

### Skill config (`~/.config/zoom-transcript-sync/user.json`)

```json
{
  "email": "you@company.com",
  "scan_window_days": 14,
  "last_successful_scan": "YYYY-MM-DD",
  "cached_at": "YYYY-MM-DD",
  "cache_source": "user_confirmed"
}
```

`last_successful_scan` is written automatically after each successful run. On the next run, it replaces `scan_window_days` as the default start boundary. Delete it to force a full `scan_window_days` lookback.

## Files in this skill

- `config/user.example.json` — skill config template (real config is gitignored)
