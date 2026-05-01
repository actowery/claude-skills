# Output Style — Action Item Extraction

## What counts as an action item

**Include:**
- Explicit commitments: "I'll send that over", "I'll follow up", "can you look into X?"
- Named task assignments: "Gavin is going to cut that release", "let's have Brónach pick that up"
- Decisions that require a concrete follow-through step: "we agreed to move forward — someone needs to open the ticket"
- Meeting-end summaries: items recapped as "so our action items are..."
- Items prefixed with "AI:", "Action:", "TODO:", "Follow-up:"

**Exclude:**
- Pure discussion or observations with no owner
- Things explicitly described as already done *within the same meeting*
- Vague intentions without a task: "we should probably look at that someday"
- Recurring standing items that are always true (not a discrete action)

## Writing the item text

- Imperative verb, specific: "Send API key request to IT", not "API key"
- Include enough context to understand without reading the transcript
- 5–15 words is the target range
- Do not include the owner's name in the text (that's the Owner column)

## Owner resolution

1. Named person: "Gavin said he'd do it" → `display_name` from `team.members[]`
2. "I" or implied manager: assign to `display_name` from config (the skill user)
3. "You" in a 1:1 context: assign to the other participant (the direct report)
4. Unnamed or unclear: `TBD`

For first-name-only references, match against `team.members[].display_name` (first word match, case-insensitive).

## Source meeting format

```
<meeting type> with <other participant> • <Month D YYYY>
```
Examples:
- `1:1 with Brónach Falls • Apr 30 2026`
- `Sprint Grooming • May 1 2026`
- `1:1 with Gavin Porter • Apr 29 2026`

Use the meeting's own date (from the Zoom meeting record), not today's date.

## Completion detection

An item is a **candidate to close** when the transcript contains language like:
- "I finished X", "that's done", "X got merged", "we shipped that", "closed that ticket"
- A reference to a specific previous item being resolved

Match candidate completions against existing open items by text similarity. Surface as a list in Phase 5; don't auto-close without user confirmation.

## Deduplication

Two items are duplicates if they describe the same task for the same owner. Use semantic similarity, not exact string match. When in doubt, keep both — a near-duplicate is less harmful than a missed item.
