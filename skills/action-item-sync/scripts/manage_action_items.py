#!/usr/bin/env python3
"""manage_action_items.py

Manages the action items table on a Confluence ADF page.

Subcommands
-----------
parse <adf-file>
    Print existing action items as a JSON array to stdout.

build-update <adf-file> --new-items <items.json> [--close-items <close.json>]
    Output modified ADF JSON (with _skillAdded sentinels) to stdout.
    Creates the table from scratch if none exists; otherwise appends rows.

strip-sentinels <adf-file>
    Output ADF with all _skillAdded attrs removed. Use before publishing.

render-preview <adf-file> --title <str> --out <html-path>
    Write a standalone HTML preview. New/changed rows highlighted yellow.
"""

import argparse
import json
import sys
import uuid
from pathlib import Path


# ── Constants ────────────────────────────────────────────────────────────────

TABLE_HEADERS = ["Status", "Action Item", "Owner", "Source Meeting", "Date Added"]
TABLE_IDENTIFIER = {"Status", "Action Item"}   # must be present to identify the table

STATUS_COLORS = {
    "Open":        "yellow",
    "In Progress": "blue",
    "Done":        "green",
    "Blocked":     "red",
}
HTML_STATUS_COLORS = {
    "yellow": "#d6a800",
    "blue":   "#0052cc",
    "green":  "#5aac44",
    "red":    "#d04437",
    "neutral":"#97a0af",
}


# ── ADF helpers ──────────────────────────────────────────────────────────────

def _lid():
    return uuid.uuid4().hex[:12]


def _status_node(text, color):
    return {
        "type": "status",
        "attrs": {"text": text, "color": color, "style": "bold", "localId": _lid()},
    }


def _text_node(text, bold=False):
    node = {"type": "text", "text": text}
    if bold:
        node["marks"] = [{"type": "strong"}]
    return node


def _paragraph(content_nodes, local_id=None):
    p = {"type": "paragraph", "attrs": {"localId": local_id or _lid()}}
    if content_nodes:
        p["content"] = content_nodes
    return p


def _cell(paragraphs, *, header=False, skill_added=False):
    cell = {
        "type": "tableHeader" if header else "tableCell",
        "attrs": {"colspan": 1, "rowspan": 1, "localId": _lid()},
        "content": paragraphs,
    }
    if skill_added:
        cell["attrs"]["_skillAdded"] = True
    return cell


def _row(cells, *, skill_added=False):
    row = {
        "type": "tableRow",
        "attrs": {"localId": _lid()},
        "content": cells,
    }
    if skill_added:
        row["attrs"]["_skillAdded"] = True
    return row


def _header_row():
    return _row([
        _cell([_paragraph([_text_node(h, bold=True)])], header=True)
        for h in TABLE_HEADERS
    ])


def _item_row(item, *, skill_added=False):
    status = item.get("status", "Open")
    color  = STATUS_COLORS.get(status, "yellow")
    cells  = [
        _cell([_paragraph([_status_node(status, color)])],          skill_added=skill_added),
        _cell([_paragraph([_text_node(item.get("text",  ""))])],    skill_added=skill_added),
        _cell([_paragraph([_text_node(item.get("owner", ""))])],    skill_added=skill_added),
        _cell([_paragraph([_text_node(item.get("source", ""))])],   skill_added=skill_added),
        _cell([_paragraph([_text_node(item.get("date_added", ""))])], skill_added=skill_added),
    ]
    return _row(cells, skill_added=skill_added)


def _make_table(rows):
    return {
        "type": "table",
        "attrs": {"layout": "default", "width": 760, "localId": _lid()},
        "content": rows,
    }


# ── ADF traversal ────────────────────────────────────────────────────────────

def _cell_text(cell):
    """Concatenate all text and status-label strings from a table cell."""
    parts = []

    def walk(node):
        if not isinstance(node, dict):
            return
        t = node.get("type")
        if t == "text":
            parts.append(node.get("text", ""))
        elif t == "status":
            parts.append(node.get("attrs", {}).get("text", ""))
        for child in node.get("content", []):
            walk(child)

    walk(cell)
    return " ".join(parts).strip()


def _load_doc(path):
    """Load ADF from file, unwrapping {title, body} wrapper if present."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return raw.get("body", raw)


def _find_table(doc):
    """Return (table_node, index_in_doc_content) or (None, None)."""
    for i, node in enumerate(doc.get("content", [])):
        if node.get("type") != "table":
            continue
        rows = node.get("content", [])
        if not rows:
            continue
        header_texts = {_cell_text(c) for c in rows[0].get("content", [])}
        if TABLE_IDENTIFIER.issubset(header_texts):
            return node, i
    return None, None


# ── Subcommand: parse ────────────────────────────────────────────────────────

def cmd_parse(args):
    doc   = _load_doc(args.adf_file)
    table, _ = _find_table(doc)
    items = []
    if table:
        for row in table["content"][1:]:   # skip header
            cells = row.get("content", [])
            if len(cells) < 5:
                continue
            items.append({
                "status":     _cell_text(cells[0]),
                "text":       _cell_text(cells[1]),
                "owner":      _cell_text(cells[2]),
                "source":     _cell_text(cells[3]),
                "date_added": _cell_text(cells[4]),
            })
    print(json.dumps(items, indent=2, ensure_ascii=False))


# ── Subcommand: build-update ─────────────────────────────────────────────────

def cmd_build_update(args):
    import copy
    doc = copy.deepcopy(_load_doc(args.adf_file))

    new_items   = json.loads(Path(args.new_items).read_text(encoding="utf-8"))   if args.new_items   else []
    close_texts = set(json.loads(Path(args.close_items).read_text(encoding="utf-8"))) if args.close_items else set()

    for item in new_items:
        item.setdefault("status", "Open")

    table, _ = _find_table(doc)

    if table is None:
        # First run — build table from scratch
        all_rows = [_header_row()] + [_item_row(item, skill_added=True) for item in new_items]
        doc["content"].append(_make_table(all_rows))
    else:
        # Close matching items
        for row in table["content"][1:]:
            cells = row.get("content", [])
            if len(cells) < 2:
                continue
            if _cell_text(cells[1]) in close_texts:
                cells[0]["content"] = [_paragraph([_status_node("Done", "green")])]
                cells[0]["attrs"]["_skillAdded"] = True
                row["attrs"]["_skillAdded"]      = True

        # Append new rows
        for item in new_items:
            table["content"].append(_item_row(item, skill_added=True))

    print(json.dumps(doc, ensure_ascii=False))


# ── Subcommand: strip-sentinels ───────────────────────────────────────────────

def cmd_strip_sentinels(args):
    import copy
    doc = copy.deepcopy(_load_doc(args.adf_file))

    def walk(node):
        if isinstance(node, dict):
            node.get("attrs", {}).pop("_skillAdded", None)
            for child in node.get("content", []):
                walk(child)

    walk(doc)
    print(json.dumps(doc, ensure_ascii=False))


# ── Subcommand: render-preview ────────────────────────────────────────────────

def _cell_html(cell):
    parts = []

    def walk(node):
        if not isinstance(node, dict):
            return
        t = node.get("type")
        if t == "text":
            import html as html_mod
            parts.append(html_mod.escape(node.get("text", "")))
        elif t == "status":
            text  = node.get("attrs", {}).get("text", "")
            color = HTML_STATUS_COLORS.get(node.get("attrs", {}).get("color", "neutral"), "#97a0af")
            parts.append(
                f'<span style="background:{color};color:#fff;padding:2px 7px;'
                f'border-radius:3px;font-size:11px;font-weight:bold">{text}</span>'
            )
        else:
            for child in node.get("content", []):
                walk(child)

    walk(cell)
    return "".join(parts)


def cmd_render_preview(args):
    doc   = _load_doc(args.adf_file)
    table, _ = _find_table(doc)

    if not table:
        table_html = "<p><em>No action items table found — will be created on publish.</em></p>"
    else:
        rows_html = []
        for r_idx, row in enumerate(table["content"]):
            added = row.get("attrs", {}).get("_skillAdded", False)
            if r_idx == 0:
                row_style = 'style="background:#f0f0f0;font-weight:bold"'
            elif added:
                row_style = 'style="background:#fffbcc"'
            else:
                row_style = ""
            tag = "th" if r_idx == 0 else "td"
            cells_html = "".join(
                f'<{tag} style="padding:6px 10px;border:1px solid #ccc">{_cell_html(c)}</{tag}>'
                for c in row.get("content", [])
            )
            rows_html.append(f"<tr {row_style}>{cells_html}</tr>")
        table_html = (
            '<table style="border-collapse:collapse;width:100%;font-size:13px">'
            + "".join(rows_html)
            + "</table>"
        )

    html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>Preview: {args.title}</title>
<style>
  body {{ margin: 2em; font-family: -apple-system, Helvetica, sans-serif; color: #333 }}
  h1   {{ font-size: 1.1em; margin-bottom: 0.3em }}
  .legend {{ font-size: 11px; color: #888; margin-bottom: 1em }}
</style>
</head><body>
<h1>Preview: {args.title}</h1>
<p class="legend">🟡 Yellow rows = new additions by this run</p>
{table_html}
</body></html>"""

    Path(args.out).write_text(html, encoding="utf-8")
    print(f"Preview written to {args.out}", file=sys.stderr)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("parse", help="Print existing items as JSON")
    p.add_argument("adf_file")
    p.set_defaults(func=cmd_parse)

    p = sub.add_parser("build-update", help="Build modified ADF with new rows/closures")
    p.add_argument("adf_file")
    p.add_argument("--new-items",   dest="new_items",   help="JSON file of items to add")
    p.add_argument("--close-items", dest="close_items", help="JSON file of item texts to mark Done")
    p.set_defaults(func=cmd_build_update)

    p = sub.add_parser("strip-sentinels", help="Remove _skillAdded attrs before publishing")
    p.add_argument("adf_file")
    p.set_defaults(func=cmd_strip_sentinels)

    p = sub.add_parser("render-preview", help="Write HTML preview")
    p.add_argument("adf_file")
    p.add_argument("--title", required=True)
    p.add_argument("--out",   required=True)
    p.set_defaults(func=cmd_render_preview)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
