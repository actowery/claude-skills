#!/usr/bin/env python3
"""
Render a `how-can-i-help` brief from a JSON candidates file to a markdown
document saved under /tmp/. The skill's model produces the structured JSON
during Phase 4; this script just lays it out in a consistent, copy-friendly
shape so the same brief format comes out every run.

Input JSON shape:
  {
    "scan_window": "2026-04-09 to 2026-04-23",
    "generated_at": "2026-04-23T14:30:00",
    "items": [
      {
        "rank": 1,
        "title": "...",
        "category": "customer-escalation" | "buried-mention" | ...,
        "description": "2-4 sentence paragraph with citation(s)",
        "why_help_matters": "1-2 sentences",
        "business_benefit": "1-2 sentences",
        "suggested_action": "single sentence",
        "citations": [
          {"label": "PLAT-1234", "url": "https://..."}
        ]
      }
    ],
    "notes": "optional — e.g. 'quiet week, only 1 item met the bar'"
  }

Usage:
    render_brief.py --input items.json --out /tmp/how-can-i-help-2026-04-23.md
"""

import argparse
import json
import sys
from pathlib import Path


HEADER = """# How Can I Help — {date}

Scan window: **{scan_window}**

{notes_block}
"""


ITEM_TEMPLATE = """## {rank}. {title}

**Category:** {category}

{description}

**Why help matters to them:** {why_help_matters}

**Business benefit:** {business_benefit}

**Suggested action:** {suggested_action}

{citations_block}
"""


EMPTY_TEMPLATE = """# How Can I Help — {date}

Scan window: **{scan_window}**

No items met the bar this run. Everything in the scan window was either fresh (you already know) or not actionable by a management lever. That's a good signal — the team's channels are working.

_Run again later in the week if you want a second pass._
"""


def render_citations(citations):
    if not citations:
        return ""
    lines = ["**Citations:**"]
    for c in citations:
        label = c.get("label", "(untitled)")
        url = c.get("url", "")
        if url:
            lines.append(f"- [{label}]({url})")
        else:
            lines.append(f"- {label}")
    return "\n".join(lines)


def render_notes(notes):
    if not notes:
        return ""
    return f"> {notes}\n"


def render(data, today):
    scan_window = data.get("scan_window", "(unspecified)")
    items = data.get("items") or []
    notes = data.get("notes", "")

    if not items:
        return EMPTY_TEMPLATE.format(date=today, scan_window=scan_window)

    parts = [HEADER.format(
        date=today,
        scan_window=scan_window,
        notes_block=render_notes(notes),
    )]

    for it in items:
        parts.append(ITEM_TEMPLATE.format(
            rank=it.get("rank", "?"),
            title=it.get("title", "(untitled)"),
            category=it.get("category", "(uncategorized)"),
            description=it.get("description", "").strip(),
            why_help_matters=it.get("why_help_matters", "").strip(),
            business_benefit=it.get("business_benefit", "").strip(),
            suggested_action=it.get("suggested_action", "").strip(),
            citations_block=render_citations(it.get("citations") or []),
        ))

    return "\n".join(parts).rstrip() + "\n"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="Path to candidates JSON")
    p.add_argument("--out", required=True, help="Path to write the markdown brief")
    p.add_argument("--today", default=None, help="Override today's date for the header (YYYY-MM-DD)")
    args = p.parse_args()

    data = json.loads(Path(args.input).read_text())

    today = args.today
    if not today:
        from datetime import date
        today = date.today().isoformat()

    md = render(data, today)
    Path(args.out).write_text(md)
    print(json.dumps({"out": args.out, "items": len(data.get("items") or [])}))


if __name__ == "__main__":
    main()
