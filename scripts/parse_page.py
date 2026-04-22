#!/usr/bin/env python3
"""
ADF parser for per-individual AI Weekly Report pages.

Different from a team weekly-report parser: here each person is one tableRow,
identified by plain-text name in the first cell (no @mention, no account_id).
Columns are discovered by reading the table's header row at runtime.

Subcommands:
  rows <adf_file> --display-name <name>
      Emit JSON listing every tableRow whose first-cell text matches
      the user's display name (case-insensitive, trimmed) AND whose first
      cell text is NOT strong-marked (filters out group dividers).

  dates --title <page_title> | --adf <adf_file>
      Extract {start, end} ISO date range from the page title.

  build-patch <adf_file> --drafts <drafts_file> --display-name <name>
      Apply drafts keyed by "<Table Heading>|<Column Name>" onto the user's
      matched row(s). Replaces cell content; leaves other cells untouched.
      Backtick-wrapped spans in draft paragraphs render as inline code marks.
      Emits the modified ADF to stdout.

  strip-sentinels <adf_file>
      Remove `_skillAdded` sentinel attrs before publishing.

The drafts file shape:
  {
    "Manager Weekly Report|Wins this week": {
      "paragraphs": ["Some prose with `/slash cmd` and more prose."]
    },
    "Manager Weekly Report|Blockers / concerns": {
      "paragraphs": ["Single blocker sentence."]
    }
  }
"""

import argparse
import copy
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path


SENTINEL_KEY = "_skillAdded"


# ---------- generic ADF utilities ----------

def load_adf(path):
    text = Path(path).read_text()
    data = json.loads(text)
    if isinstance(data, dict) and data.get("type") == "doc":
        return data
    if isinstance(data, dict) and isinstance(data.get("body"), dict) and data["body"].get("type") == "doc":
        body = data["body"]
        if "title" in data and "title" not in body:
            body["title"] = data["title"]
        return body
    return data


def text_of(node):
    """Concatenate all descendant text, preserving spacing; hardBreaks become spaces."""
    if not isinstance(node, dict):
        return ""
    if node.get("type") == "text":
        return node.get("text", "")
    if node.get("type") == "hardBreak":
        return " "
    parts = []
    for child in node.get("content", []) or []:
        parts.append(text_of(child))
    return "".join(parts)


def is_first_text_strong(cell_node):
    """True if the cell's first non-whitespace text run has a strong mark.
    Used to distinguish group-divider rows from person rows."""
    if not isinstance(cell_node, dict):
        return False
    for para in cell_node.get("content", []) or []:
        if para.get("type") != "paragraph":
            continue
        for child in para.get("content", []) or []:
            if child.get("type") != "text":
                continue
            if not (child.get("text") or "").strip():
                continue
            marks = child.get("marks") or []
            return any(m.get("type") == "strong" for m in marks)
    return False


def walk(node, path="", out=None):
    """Yield (path, node) for every dict node. Paths index by (type, ordinal-within-parent)."""
    if out is None:
        out = []
    out.append((path, node))
    content = node.get("content") if isinstance(node, dict) else None
    if isinstance(content, list):
        counter = {}
        for child in content:
            if not isinstance(child, dict):
                continue
            t = child.get("type", "node")
            i = counter.get(t, 0)
            counter[t] = i + 1
            child_path = f"{path}/{t}[{i}]" if path else f"{t}[{i}]"
            walk(child, child_path, out)
    return out


def locate(adf, path):
    """Return (parent_list, idx_in_parent, node) for the node at path, or (None,None,None)."""
    if not path:
        return None, None, adf
    parts = path.split("/")
    cur = adf
    parent_list = None
    idx = None
    for part in parts:
        m = re.match(r"([A-Za-z]+)\[(\d+)\]", part)
        if not m:
            return None, None, None
        t, i = m.group(1), int(m.group(2))
        content = cur.get("content") or []
        matches = [c for c in content if isinstance(c, dict) and c.get("type") == t]
        if i >= len(matches):
            return None, None, None
        target = matches[i]
        abs_idx = content.index(target)
        parent_list = content
        idx = abs_idx
        cur = target
    return parent_list, idx, cur


# ---------- table + row discovery ----------

def find_tables(adf):
    """Walk the top-level doc.content sequence in order; attach each table to the
    most recent preceding heading (any level). Returns list of
    {heading, heading_level, table_path, table_node}."""
    out = []
    last_heading_text = None
    last_heading_level = None
    top = adf.get("content") or []
    for i, node in enumerate(top):
        if not isinstance(node, dict):
            continue
        t = node.get("type")
        if t == "heading":
            last_heading_text = text_of(node).strip()
            last_heading_level = (node.get("attrs") or {}).get("level")
        elif t == "table":
            out.append({
                "heading": last_heading_text or "",
                "heading_level": last_heading_level,
                "table_path": f"table[{sum(1 for j in range(i) if isinstance(top[j], dict) and top[j].get('type') == 'table')}]",
                "table_node": node,
            })
    return out


def column_map(table_node):
    """Read the table's first row as the header row; return list of column names."""
    rows = [c for c in (table_node.get("content") or []) if c.get("type") == "tableRow"]
    if not rows:
        return []
    header = rows[0]
    out = []
    for cell in (header.get("content") or []):
        if cell.get("type") not in ("tableHeader", "tableCell"):
            continue
        out.append(text_of(cell).strip())
    return out


def iter_person_rows(table_node):
    """Yield (row_index, row_node) for rows below the header, skipping strong-marked first-cell rows."""
    rows = [c for c in (table_node.get("content") or []) if c.get("type") == "tableRow"]
    for i, row in enumerate(rows):
        if i == 0:
            continue  # header
        cells = [c for c in (row.get("content") or []) if c.get("type") in ("tableHeader", "tableCell")]
        if not cells:
            continue
        if is_first_text_strong(cells[0]):
            continue  # group divider
        yield i, row, cells


def row_matches_name(cells, display_name):
    if not cells:
        return False
    text = text_of(cells[0]).strip().casefold()
    target = display_name.strip().casefold()
    return text == target


# ---------- subcommand: rows ----------

def cmd_rows(args):
    adf = load_adf(args.adf_file)
    tables = find_tables(adf)
    result_matches = []

    for t_idx, tbl in enumerate(tables):
        cols = column_map(tbl["table_node"])
        for row_idx, row, cells in iter_person_rows(tbl["table_node"]):
            if not row_matches_name(cells, args.display_name):
                continue
            # Build per-cell info.
            cell_info = []
            for ci, cell in enumerate(cells):
                cell_info.append({
                    "column_index": ci,
                    "column_name": cols[ci] if ci < len(cols) else f"(col {ci})",
                    "cell_path": f"{tbl['table_path']}/tableRow[{row_idx}]/{cell.get('type')}[0]"
                                 if ci == 0 and cell.get("type") == "tableHeader"
                                 else f"{tbl['table_path']}/tableRow[{row_idx}]/tableCell[{_cell_typed_index(cells, ci, 'tableCell')}]"
                                 if cell.get("type") == "tableCell"
                                 else f"{tbl['table_path']}/tableRow[{row_idx}]/tableHeader[{_cell_typed_index(cells, ci, 'tableHeader')}]",
                    "cell_type": cell.get("type"),
                    "current_text_preview": text_of(cell).strip()[:140],
                    "is_empty": _is_empty_cell(cell),
                })
            result_matches.append({
                "table_heading": tbl["heading"],
                "table_path": tbl["table_path"],
                "row_path": f"{tbl['table_path']}/tableRow[{row_idx}]",
                "row_index": row_idx,
                "columns": cols,
                "cells": cell_info,
            })

    out = {
        "page_title": adf.get("title", ""),
        "display_name": args.display_name,
        "matches": result_matches,
    }
    print(json.dumps(out, indent=2))


def _cell_typed_index(cells, ci, wanted_type):
    """For a given row's flattened cell list and a column index, compute the
    within-type ordinal of the cell at ci (so path indexing matches our walker)."""
    count = 0
    for i, c in enumerate(cells):
        if c.get("type") != wanted_type:
            continue
        if i == ci:
            return count
        count += 1
    return 0


def _is_empty_cell(cell):
    """Match the attr-only-paragraph shape used for empty cells."""
    content = cell.get("content") or []
    if len(content) != 1:
        return False
    para = content[0]
    if para.get("type") != "paragraph":
        return False
    # Empty paragraphs may have attrs but no content key, or an empty content list.
    return not (para.get("content") or [])


# ---------- subcommand: dates ----------

MONTHS = {m.lower(): i for i, m in enumerate(
    ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
)}
MONTHS.update({m.lower(): i for i, m in enumerate(
    ["", "January", "February", "March", "April", "May", "June",
     "July", "August", "September", "October", "November", "December"]
)})


def parse_dates_from_text(text):
    if not text:
        return None
    m = re.search(
        r"(\d{1,2})\s+([A-Za-z]+)\s*[\-\u2013]\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})",
        text,
    )
    if m:
        d1, mo1, d2, mo2, yr = m.groups()
        mo1i, mo2i = MONTHS.get(mo1.lower()), MONTHS.get(mo2.lower())
        if mo1i and mo2i:
            return (
                date(int(yr), mo1i, int(d1)).isoformat(),
                date(int(yr), mo2i, int(d2)).isoformat(),
            )
    m = re.search(r"(\d{4}-\d{2}-\d{2})\s*(?:to|[\-\u2013])\s*(\d{4}-\d{2}-\d{2})", text)
    if m:
        return m.group(1), m.group(2)
    m = re.search(r"week of\s+(\d{4}-\d{2}-\d{2})", text, re.IGNORECASE)
    if m:
        from datetime import timedelta
        start = datetime.fromisoformat(m.group(1)).date()
        return start.isoformat(), (start + timedelta(days=4)).isoformat()
    return None


def cmd_dates(args):
    text = args.title
    if args.adf:
        adf = load_adf(args.adf)
        text = text or adf.get("title") or ""
    parsed = parse_dates_from_text(text or "")
    if not parsed:
        print(f"Could not parse date range from: {text!r}", file=sys.stderr)
        sys.exit(2)
    print(json.dumps({"start": parsed[0], "end": parsed[1]}))


# ---------- subcommand: build-patch ----------

def _paragraph_from_backtick(text_with_ticks, mark_added=True):
    """Convert `backtick` runs in a plain string to a paragraph with code-marked
    text nodes. Every node gets the _skillAdded sentinel so the preview can
    highlight it and the publish phase can strip them."""
    parts = re.split(r"(`[^`]+`)", text_with_ticks)
    runs = []
    for part in parts:
        if not part:
            continue
        if part.startswith("`") and part.endswith("`") and len(part) >= 2:
            inner = part[1:-1]
            runs.append({"type": "text", "text": inner, "marks": [{"type": "code"}]})
        else:
            runs.append({"type": "text", "text": part})
    para = {"type": "paragraph", "content": runs}
    if mark_added:
        para.setdefault("attrs", {})[SENTINEL_KEY] = True
    return para


def cmd_build_patch(args):
    adf = load_adf(args.adf_file)
    drafts = json.loads(Path(args.drafts).read_text())
    out = copy.deepcopy(adf)

    tables = find_tables(out)

    # Resolve each drafts key ("<Heading>|<Column>") to a (table, column_index).
    applied = []
    skipped = []

    for key, payload in drafts.items():
        if "|" not in key:
            skipped.append({"key": key, "reason": "key must be '<Heading>|<Column>'"})
            continue
        heading, column = [s.strip() for s in key.split("|", 1)]
        tbl = next((t for t in tables
                    if t["heading"].strip().casefold() == heading.casefold()), None)
        if not tbl:
            skipped.append({"key": key, "reason": f"no table with heading {heading!r}"})
            continue
        cols = column_map(tbl["table_node"])
        col_idx = next((i for i, c in enumerate(cols)
                        if c.strip().casefold() == column.casefold()), None)
        if col_idx is None:
            skipped.append({"key": key, "reason": f"no column {column!r} in table {heading!r}"})
            continue

        # Find the user's row in this table.
        row_node = None
        for row_idx, row, cells in iter_person_rows(tbl["table_node"]):
            if row_matches_name(cells, args.display_name):
                row_node = row
                target_cells = cells
                break
        if row_node is None:
            skipped.append({"key": key, "reason": f"no row for {args.display_name!r} in {heading!r}"})
            continue
        if col_idx >= len(target_cells):
            skipped.append({"key": key, "reason": f"col_idx {col_idx} out of range"})
            continue
        target_cell = target_cells[col_idx]

        paragraphs = payload.get("paragraphs") or []
        new_content = [_paragraph_from_backtick(p) for p in paragraphs] if paragraphs else []
        target_cell["content"] = new_content if new_content else [
            {"type": "paragraph", "attrs": (target_cell.get("content") or [{}])[0].get("attrs") or {}}
        ]
        applied.append({"key": key, "paragraphs_written": len(new_content)})

    if skipped:
        print(json.dumps({"skipped": skipped, "applied": applied}), file=sys.stderr)
    print(json.dumps(out))


# ---------- subcommand: strip-sentinels ----------

def cmd_strip_sentinels(args):
    adf = load_adf(args.adf_file)

    def scrub(n):
        if not isinstance(n, dict):
            return
        attrs = n.get("attrs")
        if isinstance(attrs, dict) and SENTINEL_KEY in attrs:
            del attrs[SENTINEL_KEY]
            if not attrs:
                del n["attrs"]
        for ch in n.get("content", []) or []:
            scrub(ch)

    scrub(adf)
    print(json.dumps(adf))


# ---------- main ----------

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("rows")
    pr.add_argument("adf_file")
    pr.add_argument("--display-name", required=True)
    pr.set_defaults(func=cmd_rows)

    pd = sub.add_parser("dates")
    pd.add_argument("--title", default=None)
    pd.add_argument("--adf", default=None)
    pd.set_defaults(func=cmd_dates)

    pb = sub.add_parser("build-patch")
    pb.add_argument("adf_file")
    pb.add_argument("--drafts", required=True)
    pb.add_argument("--display-name", required=True)
    pb.set_defaults(func=cmd_build_patch)

    ps = sub.add_parser("strip-sentinels")
    ps.add_argument("adf_file")
    ps.set_defaults(func=cmd_strip_sentinels)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
