# Transcript mining — extracting action items from prior 1:1s

The killer feature of this skill is mining the previous 1:1's transcript for things that were committed to, then cross-checking against current state to filter out what's already done. This file is the playbook.

## Sources

The prior 1:1 transcript can come from two places:

1. **Zoom MCP** — `get_meeting_assets` returns `my_notes.transcript.transcript_items[]` with speaker labels and timestamps, plus `meeting_summary.next_steps` (when AI Companion was running and produced a summary)
2. **Local transcript files** — `~/Projects/Mgmt-Assistant/transcripts/<YYYY-MM-DD>_*.md` with YAML frontmatter (`action_items: ["owner: task"]` field is pre-extracted)

If both exist for the same meeting, prefer the Zoom source — it's more detailed and includes the AI-extracted next steps. Fall back to local frontmatter `action_items` if Zoom is unavailable.

## Extracting action items from Zoom transcripts

### Path 1: AI Companion summary (preferred when present)

`meeting_summary.next_steps` is already structured. Each entry typically looks like:
```
{
  "step": "David to complete Wednesday open PR review homework on firewall module",
  "owner": "David Swan"
}
```

Trust this as the starting point. It's not perfect — Companion sometimes invents steps that weren't really committed to, or misses casual asides that were real commitments — but it's a strong baseline.

### Path 2: Direct transcript scanning

If `meeting_summary.next_steps` is missing or thin, scan `transcript_items[]` for commitment language:

**First-person commitments (target person to do something):**
- "I'll" / "I will" / "I'm going to" / "I can"
- "I'll take care of" / "I'll handle" / "I'll own"
- "Let me" / "I'll get on it"

**Second-person commitments (user asked target to do something, target acknowledged):**
- "Can you..." followed by acknowledgment
- "...by next week / by Friday / before our next 1:1"
- "I'd like you to..." / "Would you mind..."

**User commitments (user to do something):**
- Same patterns but speaker is the user
- These go into the "you committed to" bucket for the manager template, or are noted in direct-report briefs as "things you owe them"

**Skip:**
- Hypotheticals ("I might want to") — not commitments
- Past tense ("I did...") — already done
- Generic agreement ("yeah okay") without a concrete object
- Pleasantries ("I'll see you later")

### Output format

For each extracted action item, capture:
```json
{
  "id": "ai-1",
  "owner": "David Swan" | "Adrian Towery",
  "task": "Complete Wednesday open PR review homework on firewall module",
  "transcript_anchor": {
    "uuid": "AF9CC9CA-0CAD-495F-9E0D-33F9439277C7",
    "start": "00:13:42.000",
    "end": "00:14:05.000",
    "quote": "exact text from transcript"
  },
  "extraction_source": "summary" | "transcript_scan",
  "confidence": "high" | "medium" | "low"
}
```

Confidence:
- **high** — direct, unambiguous commitment with a concrete object ("I'll close CAT-2598 by Friday")
- **medium** — clear language but vague timing or scope ("I'll look into the firewall thing")
- **low** — implied or weakly committed ("yeah, sounds good" after a vague ask)

Only include high and medium in the brief by default. Low-confidence items can be surfaced if the user explicitly asks to see them.

## Extracting from local frontmatter

If the file has:
```yaml
action_items:
  - "David: complete firewall PR review homework"
  - "Adrian: push back on NatWest extra meeting"
```

Parse each as `<owner>: <task>`. Owner before colon, task after. Confidence defaults to high (already pre-extracted by the user or a prior skill run).

## Closure detection (loose)

For each extracted action item, search across all sources for plausibly-related activity:

### Search strategies per source

**Jira:**
- Tickets where summary or description matches keywords from the task ("firewall", "PR review", "CAT-2598" if explicitly mentioned)
- Tickets the owner commented on after the 1:1 date
- Status changes on already-existing tickets that match the task

**Slack:**
- Messages from the owner after 1:1 date mentioning task keywords
- Messages the owner replied to that mentioned the task

**GitHub:**
- PRs by the owner with titles matching task keywords, created/merged after 1:1
- Reviews by the owner on PRs matching keywords

**Outlook:**
- Emails from/to the owner after 1:1 mentioning task keywords

**Other Zoom meetings:**
- `meeting_summary.next_steps` from later meetings that reference the task or topic
- Transcript mentions of the task in later meetings

### Classification rules

| Activity found | Classification |
|---|---|
| Direct evidence of completion (Jira closed, PR merged, "done" message) | **Closed** |
| Activity related to the task but not finished | **In flight** |
| No activity at all matching the task or its keywords | **Stale** |

Loose matching is intentional. False negatives (calling something stale that's closed) hurt more than false positives. When in doubt, classify as **In flight** rather than **Stale** — better to ask "how's this going" than to wrongly flag a closed item as forgotten.

### Brief impact by classification

- **Closed** — drop from the brief entirely
- **In flight** — include with a one-line current status from the matching evidence
- **Stale** — include with "no detectable activity since 1:1" framing

## Edge cases

### Recurring 1:1 with no prior transcript

If the previous 1:1 has no Zoom transcript (AI Companion wasn't running, no local file exists), skip Phase 4 Section 1 entirely. Note in the brief: "No prior 1:1 transcript available — starting fresh." Don't fabricate items.

### Multiple prior 1:1s in window

If two or more 1:1s happened in the window (rare, but possible if 1:1s are very frequent), pull action items from each in order. Newer commitments override older ones if they cover the same task. Most-recent 1:1 is the primary source.

### Action item the user owns

If the prior 1:1's transcript shows the user (Adrian) committing to something, that goes in:
- **Direct report brief**: a "things you owe them" subsection inside Section 1
- **Manager brief**: the "you committed to" bucket
- **Peer brief**: the mutual-asks section, "you asked them" → "they asked you" reversed

Don't drop user-owned commitments. They're often the highest-signal items because the manager forgot to follow up on them, and the report is waiting.

### Casual chat noise

The first few minutes and last few minutes of a 1:1 are often pleasantries. Skip:
- Greetings, weather, weekend plans, family chat
- Bonus / tax / pay grumbling unless it leads to a concrete commitment
- Unrelated tangents (the underwater scooter conversation in DevX Standup is the canonical example)

Casual chat that builds rapport is not action-item material. The skill doesn't need to surface it.

### Action items mentioned but explicitly walked back

Sometimes someone says "I'll do X" and then later in the same meeting says "actually, on second thought, let's not do that." Detect these by looking for negation language ("actually", "let's not", "scratch that") later in the transcript referencing the same topic. If detected, drop the original action item entirely.

## Citation in the brief

Every action item carried into the brief needs a transcript citation:
```
- Said he'd take the firewall homework on Wednesday ([transcript 2026-04-21 09:30, lines 142-148])
```

If the transcript came from Zoom, use the meeting UUID + start time. If from local file, use the file path + line range. Never paraphrase a commitment without anchoring to its source.
