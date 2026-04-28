#!/usr/bin/env python3
"""
Render a 1:1 prep brief from a structured JSON document to a markdown file.
Output directory is resolved from user.json's `prep_output_dir` field
(default: ~/Projects/Mgmt Assistant/1on1-preps), falling back to /tmp/.
The skill's model produces the JSON during Phase 4; this script lays it out
consistently so the same brief format comes out every run.

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
    render_brief.py --input brief.json [--out PATH] [--user-config PATH]

    If --out is omitted, the output path is derived from `prep_output_dir` in
    user.json (or ~/Projects/Mgmt\ Assistant/1on1-preps as the hardcoded
    fallback) using the person slug + date from the brief JSON.
"""

import argparse
import json
import os
import sys
from pathlib import Path


DEFAULT_PREP_OUTPUT_DIR = "~/Projects/Mgmt Assistant/1on1-preps"
DEFAULT_USER_CONFIG = "~/.config/1on1-prep/user.json"


def resolve_output_dir(user_config_path: str) -> Path:
    """Read prep_output_dir from user.json, falling back to default."""
    cfg_path = Path(user_config_path).expanduser()
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text())
            output_dir = cfg.get("prep_output_dir")
            if output_dir:
                return Path(output_dir).expanduser()
        except Exception:
            pass
    return Path(DEFAULT_PREP_OUTPUT_DIR).expanduser()


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
    p.add_argument("--out", default=None, help="Path to write the markdown brief (derived from prep_output_dir if omitted)")
    p.add_argument("--user-config", default=DEFAULT_USER_CONFIG, help="Path to user.json")
    args = p.parse_args()

    data = json.loads(Path(args.input).read_text())

    if args.out:
        out_path = Path(args.out)
    else:
        person = data.get("person") or {}
        slug = person.get("slug") or person.get("display_name", "unknown").lower().replace(" ", "-")
        window = data.get("meeting_window") or {}
        date = window.get("this_1on1") or "unknown-date"
        out_dir = resolve_output_dir(args.user_config)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"1on1-prep-{slug}-{date}.md"

    md = render(data)
    out_path.write_text(md)
    print(json.dumps({
        "out": str(out_path),
        "sections": len([s for s in data.get("sections") or [] if s.get("include", True)]),
        "person": (data.get("person") or {}).get("display_name"),
    }))


if __name__ == "__main__":
    main()
