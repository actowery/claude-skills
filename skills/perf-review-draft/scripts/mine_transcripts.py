#!/usr/bin/env python3
"""mine_transcripts.py

Search a local transcript directory for meetings where a given person
participated, within a date window. Returns structured JSON to stdout.

Usage
-----
python3 mine_transcripts.py \
    --transcript-dir /path/to/transcripts \
    --person "David Swan" \
    --start 2026-01-01 \
    --end 2026-06-30

Output: JSON object with matched meetings, action items, keyword excerpts,
and a summary count.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from datetime import date

# ── Keyword groups ────────────────────────────────────────────────────────────

KEYWORD_GROUPS = {
    "growth": [
        "learned", "learning", "course", "certification", "training",
        "improved", "growth", "development", "mentor",
        "took initiative", "drove", "proposed", "designed", "experiment",
    ],
    "delivery": [
        "shipped", "merged", "closed", "released", "deployed", "done",
        "finished", "completed", "resolved", "launched",
    ],
    "blocker": [
        "blocked", "waiting on", "stuck", "delayed", "still pending",
        "no update", "hasn't responded", "escalated", "can't proceed",
    ],
    "quality": [
        "clean", "elegant", "well-structured", "impressive", "nice work",
        "revisit", "rework", "needed changes", "too many revisions",
    ],
    "follow_up": [
        "action item", "ai:", "follow up", "follow-up", "homework",
        "next time", "i'll", "i will", "you'll", "can you",
    ],
}

CONTEXT_WINDOW = 120   # chars before/after keyword match to include as context


# ── YAML frontmatter parser ────────────────────────────────────────────────────

def _parse_frontmatter(text):
    """Parse simple YAML frontmatter from markdown. Returns (meta_dict, body_str)."""
    if not text.startswith("---"):
        return {}, text

    end = text.find("\n---", 3)
    if end == -1:
        return {}, text

    fm_text = text[3:end].strip()
    body    = text[end + 4:].lstrip("\n")

    meta = {}
    lines = fm_text.split("\n")
    current_key = None
    list_items  = []

    for line in lines:
        if line.startswith("  - "):
            # list item continuation
            if current_key and list_items is not None:
                list_items.append(line[4:].strip().strip('"'))
        elif ": " in line or line.endswith(":"):
            # flush previous list
            if current_key and list_items:
                meta[current_key] = list_items

            if ": " in line:
                k, v = line.split(": ", 1)
                k = k.strip()
                v = v.strip().strip('"')
                if v == "" or v == "[]":
                    current_key = k
                    list_items  = []
                else:
                    current_key = k
                    list_items  = None
                    meta[k]     = v
            else:
                current_key = line.rstrip(":").strip()
                list_items  = []
        elif line.startswith("- "):
            if current_key and list_items is not None:
                list_items.append(line[2:].strip().strip('"'))

    # flush last list
    if current_key and list_items:
        meta[current_key] = list_items

    return meta, body


def _parse_date(s):
    """Parse YYYY-MM-DD into a date object, or None."""
    try:
        return date.fromisoformat(str(s))
    except (ValueError, TypeError):
        return None


# ── Keyword excerpt extractor ─────────────────────────────────────────────────

def _extract_excerpts(body, person_name):
    """
    Scan body for keyword matches. For each match, also try to identify the
    speaker (Zoom transcripts have "Speaker Name\\nHH:MM:SS\\n<text>" blocks).
    Returns a list of {keyword, group, context, speaker} dicts.
    """
    excerpts   = []
    seen_spans = []   # prevent overlapping excerpts for same passage

    # Build speaker-line index: list of (char_offset, speaker_name)
    # Zoom transcripts look like: "First Last\n09:33:37\n<text>"
    speaker_pattern = re.compile(r'^([A-Z][a-zA-ZéÀ-ɏ\' -]+)\n\d{2}:\d{2}:\d{2}\n', re.MULTILINE)
    speaker_offsets = [(m.start(), m.group(1).strip()) for m in speaker_pattern.finditer(body)]

    def _speaker_at(offset):
        speaker = None
        for s_off, s_name in speaker_offsets:
            if s_off <= offset:
                speaker = s_name
            else:
                break
        return speaker

    for group, keywords in KEYWORD_GROUPS.items():
        for kw in keywords:
            for m in re.finditer(re.escape(kw), body, re.IGNORECASE):
                start = m.start()
                end   = m.end()

                # Skip if overlapping with an already-captured span
                if any(s <= start < e for s, e in seen_spans):
                    continue

                ctx_start = max(0, start - CONTEXT_WINDOW)
                ctx_end   = min(len(body), end + CONTEXT_WINDOW)
                context   = body[ctx_start:ctx_end].replace("\n", " ").strip()

                speaker   = _speaker_at(start)

                seen_spans.append((ctx_start, ctx_end))
                excerpts.append({
                    "keyword":   kw,
                    "group":     group,
                    "context":   context,
                    "speaker":   speaker,
                })

    return excerpts


# ── Action item parser ────────────────────────────────────────────────────────

def _parse_action_items(meta, person_name):
    """
    From frontmatter action_items list, return two lists:
      person_items  — items attributed to person (display_name prefix match)
      manager_items — items attributed to the manager (i.e. not person)
    """
    raw = meta.get("action_items") or []
    if isinstance(raw, str):
        raw = [raw]

    person_first = person_name.split()[0].lower()
    person_items  = []
    manager_items = []

    for item in raw:
        item_lower = item.lower()
        if item_lower.startswith(person_first + ":") or item_lower.startswith(person_name.lower() + ":"):
            person_items.append(item)
        else:
            manager_items.append(item)

    return person_items, manager_items


# ── Main scan ─────────────────────────────────────────────────────────────────

def scan(transcript_dir, person_name, start_date, end_date):
    td = Path(transcript_dir)
    if not td.exists():
        return {"error": f"transcript_dir not found: {transcript_dir}"}

    person_lower = person_name.lower()
    matched      = []

    for md_file in sorted(td.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        meta, body = _parse_frontmatter(text)

        # Date filter
        file_date = _parse_date(meta.get("date"))
        if file_date is None:
            continue
        if not (start_date <= file_date <= end_date):
            continue

        # Participant filter — match display_name (case-insensitive, full first name)
        participants = meta.get("participants") or []
        if isinstance(participants, str):
            participants = [participants]
        match = any(person_lower in p.lower() for p in participants)
        if not match:
            continue

        topics = meta.get("topics") or []
        if isinstance(topics, str):
            topics = [topics]

        person_ais, manager_ais = _parse_action_items(meta, person_name)
        excerpts                = _extract_excerpts(body, person_name)

        matched.append({
            "file":             md_file.name,
            "date":             str(file_date),
            "time":             meta.get("time", ""),
            "meeting_type":     meta.get("meeting_type", "other"),
            "participants":     participants,
            "topics":           topics,
            "action_items_person":  person_ais,
            "action_items_manager": manager_ais,
            "keyword_excerpts": excerpts,
        })

    # Summary
    one_on_ones   = sum(1 for m in matched if m["meeting_type"] == "1on1")
    team_meetings = sum(1 for m in matched if m["meeting_type"] != "1on1")
    total_ais     = sum(len(m["action_items_person"]) for m in matched)

    return {
        "person": person_name,
        "period": {"start": str(start_date), "end": str(end_date)},
        "meetings": matched,
        "summary": {
            "total_meetings":        len(matched),
            "one_on_ones":           one_on_ones,
            "team_meetings":         team_meetings,
            "action_items_for_person": total_ais,
        },
    }


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--transcript-dir", required=True, help="Directory containing .md transcript files")
    parser.add_argument("--person",         required=True, help="Display name to search for (e.g. 'David Swan')")
    parser.add_argument("--start",          required=True, help="Start date YYYY-MM-DD (inclusive)")
    parser.add_argument("--end",            required=True, help="End date YYYY-MM-DD (inclusive)")
    args = parser.parse_args()

    start = _parse_date(args.start)
    end   = _parse_date(args.end)
    if start is None or end is None:
        print(json.dumps({"error": "Invalid date format — use YYYY-MM-DD"}))
        sys.exit(1)

    result = scan(args.transcript_dir, args.person, start, end)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
