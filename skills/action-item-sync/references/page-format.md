# Page Format

The action items page uses a single ADF table with five columns. The script identifies this table by scanning for a header row containing both "Status" and "Action Item" cells.

## Table columns

| # | Header | Content |
|---|--------|---------|
| 1 | **Status** | ADF `status` inline node — color-coded lozenge |
| 2 | **Action Item** | Plain text description of the task |
| 3 | **Owner** | Display name of the person responsible |
| 4 | **Source Meeting** | Meeting type + participant + date, e.g. `1:1 with Brónach • Apr 30 2026` |
| 5 | **Date Added** | ISO date this item was added, e.g. `2026-05-01` |

## Status lozenge colors

| Status | ADF color |
|--------|-----------|
| Open | `yellow` |
| In Progress | `blue` |
| Done | `green` |
| Blocked | `red` |

New items added by the skill default to **Open** (yellow).

## First run vs. subsequent runs

- **First run** (page is empty): `build-update` creates the full table including the header row, then appends item rows.
- **Subsequent runs**: `build-update` locates the existing table by header signature, appends new rows at the bottom, and updates status cells for closed items.

## `_skillAdded` sentinel

Every node inserted by the skill carries `_skillAdded: true` in its `attrs`. The preview renderer highlights these yellow. `strip-sentinels` removes them before publishing.

## Source meeting format

`<meeting_type_name> with <other_participant> • <MMM D YYYY>`

For team meetings (grooming, planning) where no single "other participant" applies:
`<meeting_type_name> • <MMM D YYYY>`

Use the meeting date (not today's date) as the date in the source string.
