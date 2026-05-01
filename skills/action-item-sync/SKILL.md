---
name: action-item-sync
description: Scans recent meeting transcripts (1:1s, sprint grooming, sprint planning) for action items, diffs them against a Confluence page, and appends new items + marks completed ones. Run weekly or after a batch of meetings. Triggers include `action-item-sync`, `sync action items`, `action items`, `update my action items`.
---

# Action Item Sync

Scan recent Zoom meeting transcripts for action items, cross-reference against the configured Confluence tracking page, and publish additions/closures after preview.

**The workflow in one sentence**: search Zoom transcripts → extract action items with owners → diff against existing open items on the page → preview → publish.

## Config & cache locations

- **User config**: `${XDG_CONFIG_HOME:-$HOME/.config}/action-item-sync/user.json`
- **Research cache**: `${XDG_CACHE_HOME:-$HOME/.cache}/action-item-sync/<YYYY-MM-DD>/`

Legacy fallback: `config/user.json` relative to this skill directory.

## Blast-radius table

| Action | Scope | When |
|---|---|---|
| Call `updateConfluencePage` | Remote write | Phase 7, ONLY after explicit `approve` |
| Write `${XDG_CONFIG_HOME:-$HOME/.config}/action-item-sync/user.json` | Local write | Phase 0 init |
| Write `/tmp/action-item-sync-preview-<date>.html`, `new-items.json`, `close-items.json`, modified ADF | Local writes | Phases 5, 6 |
| Read Confluence page (ADF) | Remote read | Phase 1 |
| Read Zoom meeting transcripts | Remote read | Phase 3 |
| Mark complete, edit, or delete existing items not confirmed as Done in transcripts | **Never** | — |
| Touch any page other than the configured `confluence_page_id` | **Never** | — |

## Prerequisites

- Atlassian MCP (Confluence)
- Zoom MCP (`search_meetings`, `get_meeting_assets`)

## Invocation

```
action-item-sync                      # run for window since last_run_date (or lookback_days)
action-item-sync --since YYYY-MM-DD   # explicit start date
action-item-sync init                 # Phase 0 — set up or edit config
```

## Workflow

### Phase 0 — Init (only if asked)

Trigger: user says `init action-item-sync` or "set up action item sync" or similar.

1. Load any existing config. If present, show current values.
2. Ask once (all optional except page URL):
   ```
   Confluence action items page URL?  (required)
   Meeting types to scan?             (default: 1:1 / Sprint Grooming / Sprint Planning)
   Lookback window (days)?            (default: 7 — used when no last_run_date)
   ```
3. Offer to bootstrap team members from an existing skill config:
   - Check `${XDG_CONFIG_HOME:-$HOME/.config}/ai-weekly-update/user.json` → use `team.members[]` if present
   - Or `${XDG_CONFIG_HOME:-$HOME/.config}/1on1-prep/user.json` → same
   - If neither exists, ask for team member names inline and resolve via `lookupJiraAccountId`
4. Extract `confluence_page_id` from the URL (numeric ID after `/pages/`).
5. Announce path, write `${XDG_CONFIG_HOME:-$HOME/.config}/action-item-sync/user.json`.

### Phase 1 — Load config and fetch page

1. Load config from `${XDG_CONFIG_HOME:-$HOME/.config}/action-item-sync/user.json`.
2. Fetch the Confluence page using `getConfluencePage` with `contentFormat: "adf"`.
   - If the MCP saves the result to a file (large pages), read that file.
   - Save raw ADF to `/tmp/action-item-sync-<page_id>.adf.json` wrapped as `{"title": "<page title>", "body": <adf-doc>}`.
3. Run: `scripts/manage_action_items.py parse /tmp/action-item-sync-<page_id>.adf.json`
   - Outputs JSON array of existing items: `[{status, text, owner, source, date_added}]`
   - If the page has no action items table yet, the array is empty — first-run mode.
4. Report to user: "Found N existing items (M open, K done)."

### Phase 2 — Determine date range

- **Start**: `last_run_date` from config if set; otherwise `today - lookback_days`.
- **End**: today.
- Announce: "Scanning meetings from YYYY-MM-DD to YYYY-MM-DD."

If `--since` was passed at invocation, use that date as start.

### Phase 3 — Fetch meeting transcripts

Use `search_meetings` with the date range and `include_zoom_my_notes: true`. For each meeting returned:

1. Check if the meeting title matches any configured `meeting_types[].title_keywords` (case-insensitive substring match).
2. If matched, call `get_meeting_assets(meeting_uuid)` to retrieve the transcript (`my_notes.transcript.transcript_items[]`).
3. Cache results under `${XDG_CACHE_HOME:-$HOME/.cache}/action-item-sync/<YYYY-MM-DD>/` — filename `<meeting_uuid>.json`.

If a meeting title does not match any configured type, skip it. If `search_meetings` returns nothing, report "No matching meetings found in window" and stop gracefully (don't error).

Announce each matched meeting: `"Found transcript: 1:1 with Brónach — Apr 30"`.

### Phase 4 — Extract action items

For each transcript, reason carefully over the full content. Follow `references/output-style.md` for extraction rules. Summary:

- Look for **explicit** action items: "I'll do X", "can you X by [date]?", "action item:", "AI:", "let's make sure X", commitments to do something.
- Look for **implied** action items: clear task assignments with a named or implied owner.
- **Skip**: general discussion, observations without ownership, things already described as done in the same meeting.

For each item found, produce:
```json
{
  "text": "Follow up with IT on API key request",
  "owner": "Adrian Towery",
  "source": "1:1 with Brónach • Apr 30 2026",
  "date_added": "YYYY-MM-DD",
  "status": "Open"
}
```

**Owner resolution**: map first names to `team.members[].display_name`. If the speaker says "I'll do it" and you know which side of the 1:1 they are on, assign accordingly. If genuinely ambiguous, use `"TBD"`.

**Completion detection**: if the transcript references a previously completed item ("that PR got merged", "I sent that email"), note the item text for potential closure — add to a `candidates_to_close` list. Do not auto-close; surface for confirmation in Phase 5.

### Phase 5 — Diff

1. For each extracted new item, check if a semantically equivalent item already exists in the open items from Phase 1. Use fuzzy matching — if the text is >70% similar to an existing open item, treat it as a duplicate and skip.
2. Separate `candidates_to_close` into items that clearly match an existing open item (text similarity) vs. uncertain matches.
3. Report:
   - `N new items to add`
   - `K items mentioned as done — confirm closure?` (list them for the user to confirm or skip)

Write new items to `/tmp/action-item-sync-new-items.json` and (if any confirmed closures) `/tmp/action-item-sync-close-items.json`.

If the user confirms which closures to apply, proceed. If they say "skip closures," only add new items.

### Phase 6 — Build modified ADF and render preview

Run:
```
scripts/manage_action_items.py build-update /tmp/action-item-sync-<page_id>.adf.json \
  --new-items /tmp/action-item-sync-new-items.json \
  [--close-items /tmp/action-item-sync-close-items.json] \
  > /tmp/action-item-sync-modified.json
```

Then render preview:
```
scripts/manage_action_items.py render-preview /tmp/action-item-sync-modified.json \
  --title "Team Action Items" \
  --out /tmp/action-item-sync-preview-<date>.html
```

Open with `open /tmp/action-item-sync-preview-<date>.html`.

Tell the user: "Preview opened. Yellow rows are new additions. Reply `approve`, `edit <item text>: <change>`, `skip closures`, or `cancel`."

### Phase 7 — Publish on approval

**Only after unambiguous `approve`.**

1. Strip sentinels:
   ```
   scripts/manage_action_items.py strip-sentinels /tmp/action-item-sync-modified.json \
     > /tmp/action-item-sync-publish.json
   ```
2. Call `updateConfluencePage`:
   - `cloudId`: from config or derive from page URL hostname
   - `pageId`: `confluence_page_id` from config
   - `contentFormat`: `"adf"`
   - `title`: `"Team Action Items"` (or existing title)
   - `body`: contents of `/tmp/action-item-sync-publish.json`
   - `versionMessage`: `"action-item-sync: +N items, K closed — <date>"`
3. Update `last_run_date` to today in `${XDG_CONFIG_HOME:-$HOME/.config}/action-item-sync/user.json`.
4. Clean up `/tmp/action-item-sync-*.json` on success.
5. Report: "Published. N items added, K closed. Next run will scan from <today>."

On `edit <item>: <change>`, re-draft that item, rebuild, re-render, re-ask.  
On `cancel`, delete local temp files and stop.

## Safety rules

- **Never close items that weren't explicitly confirmed** in Phase 5. When in doubt, add to new items rather than close existing ones.
- **Never touch other pages**. The only `updateConfluencePage` call is for `confluence_page_id`.
- **Never publish without unambiguous `approve`**.
- **Deduplicate conservatively**: if you're unsure whether an extracted item is a duplicate of an existing open item, add it anyway — better a near-duplicate than a missed item.
