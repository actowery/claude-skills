# Page parsing

AI-report pages are shaped differently from team-level weekly reports. A parser for this skill must handle:

- **Multiple tables on one page.** Typically two: one for individual contributors ("Champion Weekly Report") and one for managers ("Manager Weekly Report"). Each is preceded by a level-2 heading; the heading text is the table's identity.
- **Plain-text name matching.** Each person's row carries their name in the first cell as a raw `text` node — no `mention`, no `account_id`. The parser matches on the user's display name (case-insensitive, whitespace-trimmed).
- **Group divider rows.** Labels like `Puppet`, `Delphix` appear in the first cell with a `strong` mark and empty paragraphs in every other cell. Must be skipped — they look like person rows structurally.
- **Header-driven column discovery.** The first row of each table is the header; its cells name the columns (`Wins this week`, `Blockers`, etc.). Never hard-code column names — read them at runtime.
- **Empty-cell shape preservation.** A blank cell's paragraph is encoded as `{type: paragraph, attrs: {localId: "..."}}` with **no** `content` key (not `content: []`). Match this when leaving cells untouched.

## Relevant node shapes

### Person row (filled)
```json
{
  "type": "tableRow",
  "attrs": {"localId": "..."},
  "content": [
    {"type": "tableCell", "attrs": {...},
     "content": [{"type": "paragraph", "content": [{"text": "Adrian Towery", "type": "text"}]}]},
    {"type": "tableCell", "attrs": {...},
     "content": [{"type": "paragraph", "content": [{"text": "Wins prose here...", "type": "text"}]}]},
    {"type": "tableCell", "attrs": {...},
     "content": [{"type": "paragraph", "content": [{"text": "Blockers prose...", "type": "text"}]}]}
  ]
}
```

### Group divider row (skip)
```json
{
  "type": "tableRow",
  "content": [
    {"type": "tableCell",
     "content": [{"type": "paragraph",
                  "content": [{"text": "Puppet", "type": "text", "marks": [{"type": "strong"}]}]}]},
    {"type": "tableCell", "content": [{"type": "paragraph", "attrs": {"localId": "..."}}]},
    {"type": "tableCell", "content": [{"type": "paragraph", "attrs": {"localId": "..."}}]}
  ]
}
```
Distinguisher: the first cell's first text run has a `strong` mark.

### Inline `code` marks
Skill names, slash commands, filenames like `CLAUDE.md`, `/provision-test-infra aws`. Encoded as a text run with a `code` mark:
```json
{"type": "text", "text": "/provision-test-infra aws", "marks": [{"type": "code"}]}
```
Convention: in draft content, wrap such spans with single backticks; the patch builder converts them to marked runs.

## Section-mapping algorithm (`parse_page.py rows`)

1. Walk `doc.content` linearly. Track the most recent `heading` (any level); any `table` encountered attaches to that heading as its title.
2. For each table: take its first `tableRow` as the header row. Build `{column_index → column_name}` from the header cells' text.
3. For each subsequent `tableRow`:
   - Skip if the first cell's first text run has a `strong` mark (group divider).
   - Compute the first cell's concatenated text (case-insensitive, trimmed).
   - If it equals the user's display name, record this row as a match.
4. Emit per-match details: enclosing table heading, row path, column map, and per-cell information (path, current content preview, whether it's the attr-only empty shape).

## Patch building (`parse_page.py build-patch`)

Input drafts are keyed by `"<Table Heading>|<Column Name>"`, values are `{paragraphs: [...]}`. The builder:

1. Finds the named table by heading text (case-insensitive).
2. Finds the column index by matching column name against the table's header row.
3. Finds the user's row in that table (per the same name-matching rules).
4. Replaces that cell's `content` with new paragraphs — never touches the name cell, never touches cells not in the drafts, never modifies row or table structure.
5. Tags every inserted node with `_skillAdded: true` for preview highlighting; the `strip-sentinels` subcommand removes these before publishing.

Skipped drafts (missing heading, unknown column, row not found) are reported on stderr so Claude can surface them in the preview.

## Common pitfalls

- **Display-name drift** (e.g. `Adrian Towery` vs `Adrian R. Towery`). If zero rows match, surface the issue rather than guessing. User config can carry `display_name_overrides` for this.
- **Table-heading drift** across weeks (`Champion Weekly Report` vs `Champions Weekly Report`). Use case-insensitive match and warn on miss.
- **Column-name drift** (`Blockers` vs `Blockers / concerns`). Column matching is case-insensitive and exact — no fuzzy match. If your template varies, add column aliases to user config.
- **Non-paragraph content in cells** (rare): bullet lists, nested panels. This skill treats cells as paragraph-holders; if the template demands richer content, extend `_paragraph_from_backtick` to produce a list or preserve existing structure.

## Date extraction

Extracted from the page title only. Common patterns handled by `parse_page.py dates`:

- `AI Weekly Report for 14 Apr - 18 Apr 2026`
- `Weekly Report 2026-04-14 to 2026-04-18`
- `Week of 2026-04-14`

Unparseable title → non-zero exit. The skill must then ask the user.
