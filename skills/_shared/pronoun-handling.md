# Pronoun handling — universal rule for all skills

When a skill produces output that refers to a person by pronoun (briefs, summaries, emails, status updates, weekly reports), pronouns MUST come from the person's `pronouns` field in `user.json`. **Never guess pronouns from a name.** Names do not reliably indicate gender.

## The rule

For every person referenced in skill output:

1. **If `pronouns` is set** in their config record (`he/him`, `she/her`, `they/them`, etc.), use those pronouns throughout the output.
2. **If `pronouns` is absent or empty**, refer to the person by name only. Do not use any gendered pronouns. The output may be marginally more repetitive but is entirely safe.

## Where the field lives

For all four skills (`ai-weekly-update`, `ai-exec-report`, `weekly-confluence-update`, `how-can-i-help`, `1on1-prep`), the `pronouns` field is optional on every person record:

- `team.members[].pronouns` — direct reports / team members
- `manager.pronouns` — upward target (1on1-prep only)
- `peers[].pronouns` — peer collaborators (1on1-prep only)
- The user's own `pronouns` (top-level) — applies in any output that references the user in third person

## Init flow

Init phases (Phase 0) should ask for pronouns when capturing each person, but treat the field as optional. A user who declines or doesn't know is fine — the rule above handles missing values safely.

## Failure mode this prevents

Guessing pronouns from a name (e.g. assuming "Barr" or "Sam" or "Jordan" reads as one gender) produces incorrect output that's embarrassing in a manager-facing brief and damaging in an upward-facing email or external Confluence page. This rule eliminates the entire failure class by removing the temptation to guess.

## Examples

**Good** (pronouns set):
> Barr — he committed to reaching out to Amit Karsale.

**Good** (pronouns missing):
> Barr committed to reaching out to Amit Karsale.

**BAD** (guessing from name):
> Barr — she committed to reaching out to Amit Karsale.

**BAD** (using "they" as a guess instead of just the name):
> Barr — they committed to reaching out to Amit Karsale.

(The third example is bad because "they" should only appear when explicitly listed in the person's pronouns field, not as a hedging fallback. Use the name when you don't know.)
