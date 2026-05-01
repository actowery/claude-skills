# Data Sources

## Zoom meeting search

Use `search_meetings` with the following parameters:
```
date_from: <start_date>   # YYYY-MM-DD
date_to:   <end_date>     # YYYY-MM-DD
include_zoom_my_notes: true
```

Filter the results client-side by checking each meeting's title against `meeting_types[].title_keywords` (case-insensitive substring match). Do not try to filter in the search query itself — the Zoom API does not support title filtering.

## Transcript retrieval

For each matched meeting, call `get_meeting_assets(meeting_uuid)`.

**Always use `meeting_uuid` (not `meeting_number`) when calling `get_meeting_assets`.**

The transcript lives at:
```
response.my_notes.transcript.transcript_items[]
```

Each item has at minimum `{ speaker, text, timestamp }`. Some meetings may return an empty transcript (recording not processed, no audio, etc.) — skip these silently.

Do NOT use `get_file_content` for transcripts — it returns empty content even when a recording exists. This is a known false flag.

## Caching

Save each transcript response to `${XDG_CACHE_HOME:-$HOME/.cache}/action-item-sync/<YYYY-MM-DD>/<meeting_uuid>.json`. On re-run for the same date window, skip `get_meeting_assets` calls for already-cached meeting UUIDs.

## Meeting type matching examples

Given `title_keywords: ["1:1", "1on1", "1-on-1", "one on one"]`:
- `"1:1 with Brónach"` → match (contains "1:1")
- `"Weekly 1:1 - Adrian / Gavin"` → match
- `"Team standup"` → no match

Given `title_keywords: ["grooming", "backlog refinement", "refinement"]`:
- `"Sprint Grooming 2026-05-01"` → match
- `"Backlog Refinement"` → match

Given `title_keywords: ["sprint planning", "planning"]`:
- `"Sprint 24 Planning"` → match
- `"Sprint Planning — DevX"` → match
- Note: "planning" is broad; if false positives occur, tighten to `"sprint planning"` only.

## No Jira / Slack / Outlook needed

This skill is intentionally transcript-only. It does not query Jira, Slack, or Outlook. The signal source is exclusively Zoom meeting transcripts — keeping the blast radius small and the results fast.
