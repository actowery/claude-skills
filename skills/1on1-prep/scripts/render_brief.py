#!/usr/bin/env python3
"""
Render a 1:1 prep brief from a structured JSON document to a markdown file
saved under /tmp/. The skill's model produces the JSON during Phase 4; this
script lays it out consistently so the same brief format comes out every run.

Input JSON shape:
  {
    "person": {
      "display_name": "David Swan",
      "relationship": "direct_report",
      "slug": "david-swan"
    },
    "meeting_window": {
      "previous_1on1": "2026-04-21",
      "this_1on1": "2026-04-28",
      "research_window": "2026-04-22 to 2026-04-28"
    },
    "template": "direct_report" | "manager" | "peer",
    "sections": [
      {
        "id": "open-from-last",
        "title": "Open from last 1:1",
        "body_markdown": "...",   # already-formatted markdown
        "include": true            # honest count rule — false means omit
      }
    ],
    "missing_sources": [             # optional; appended at the end if present
      "Outlook: not authenticated"
    ]
  }

Sections with include=false are dropped. If all sections are dropped, an
empty-brief message is rendered noting that the scan turned up nothing.

Usage:
    render_brief.py --input brief.json --out /tmp/1on1-prep-david-swan-2026-04-28.md
"""

import argparse
import json
import sys
from pathlib import Path


HEADER = """# 1:1 Prep — {display_name}

**Relationship:** {relationship_label}
**Previous 1:1:** {previous_1on1}
**This 1:1:** {this_1on1}
**Research window:** {research_window}
"""


EMPTY_BODY = """No material signal in the research window. Either it's been a quiet stretch or the previous 1:1 closed everything cleanly. A short or empty brief is valid — walk into the meeting fresh and ask how things are going.
"""


RELATIONSHIP_LABELS = {
    "direct_report": "Direct report",
    "manager": "Your manager (upward)",
    "peer": "Peer / cross-team",
}


def render_section(section):
    title = section.get("title", "(untitled)")
    body = (section.get("body_markdown") or "").rstrip()
    if not body:
        return ""
    return f"## {title}\n\n{body}\n"


def render_missing_sources(missing):
    if not missing:
        return ""
    lines = ["", "---", "", "**More signal available**", ""]
    for m in missing:
        lines.append(f"- {m}")
    return "\n".join(lines) + "\n"


def render(data):
    person = data.get("person") or {}
    window = data.get("meeting_window") or {}
    template = data.get("template", "direct_report")
    sections = data.get("sections") or []
    missing = data.get("missing_sources") or []

    header = HEADER.format(
        display_name=person.get("display_name", "(unknown)"),
        relationship_label=RELATIONSHIP_LABELS.get(template, template),
        previous_1on1=window.get("previous_1on1") or "(none found)",
        this_1on1=window.get("this_1on1") or "(unspecified)",
        research_window=window.get("research_window") or "(unspecified)",
    )

    rendered_sections = [
        render_section(s)
        for s in sections
        if s.get("include", True) and (s.get("body_markdown") or "").strip()
    ]
    rendered_sections = [r for r in rendered_sections if r]

    if not rendered_sections:
        body = EMPTY_BODY
    else:
        body = "\n".join(rendered_sections)

    parts = [header, "", body, render_missing_sources(missing)]
    return "\n".join(p for p in parts if p).rstrip() + "\n"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="Path to brief JSON")
    p.add_argument("--out", required=True, help="Path to write the markdown brief")
    args = p.parse_args()

    data = json.loads(Path(args.input).read_text())
    md = render(data)
    Path(args.out).write_text(md)
    print(json.dumps({
        "out": args.out,
        "sections": len([s for s in data.get("sections") or [] if s.get("include", True)]),
        "person": (data.get("person") or {}).get("display_name"),
    }))


if __name__ == "__main__":
    main()
