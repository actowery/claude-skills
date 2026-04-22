#!/usr/bin/env python3
"""
Render an exec AI-weekly draft as (1) a browser-previewable HTML file and
(2) a `.eml` draft file that opens in the user's default mail client with
To/Subject/Body pre-filled.

The skill never sends mail — it hands files to the user for them to send
themselves from Outlook / Mail.app / etc.

Input draft JSON shape (paragraphs are plain strings, one per paragraph):
    {
      "subject": "Platform AI Weekly — Apr 21–25, 2026",
      "greeting": "Sam",
      "opening": "The team had a strong week on X — ...",
      "team_wins": [
        "Brónach Falls shipped ...",
        "Gavin Didrichsen landed ..."
      ],
      "blockers": "No material blockers this week; ...",
      "personal": "On my end this week, I ...",
      "closing": "Happy to dig into any of these in our 1:1.",
      "signoff": "Alex"
    }

Usage:
    render_email.py \
        --draft drafts.json \
        --to sam.boss@company.com \
        [--cc alice@company.com,bob@company.com] \
        --from-name "Alex Example" --from-email alex.example@company.com \
        --out-html /tmp/ai-exec-report-2026-04-25.html \
        --out-eml  /tmp/ai-exec-report-2026-04-25.eml

The .eml file is RFC 5322 multipart/alternative with plain text + HTML.
Double-clicking it on macOS opens Mail.app (or Outlook if it's the
default mail handler) with all fields pre-filled as an editable draft.
"""

import argparse
import html
import json
import sys
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import format_datetime, formataddr
from pathlib import Path


# ---------- body assembly ----------

def join_paragraphs(paragraphs):
    """Plain-text body: blank line between paragraphs, no extra formatting."""
    return "\n\n".join(p.strip() for p in paragraphs if p and p.strip())


def html_paragraphs(paragraphs):
    """HTML body: one <p> per non-empty paragraph, escaped."""
    return "\n".join(
        f"<p>{html.escape(p.strip())}</p>"
        for p in paragraphs if p and p.strip()
    )


def assemble_body(draft):
    """Compose the full ordered list of paragraphs from the draft dict.
    Greeting is its own paragraph; team_wins expands to many; blockers, personal,
    closing, and signoff each become one paragraph (signoff is often short)."""
    paras = []
    greeting = draft.get("greeting")
    if greeting:
        paras.append(f"{greeting},")

    opening = draft.get("opening")
    if opening:
        paras.append(opening)

    team_wins = draft.get("team_wins") or []
    for p in team_wins:
        paras.append(p)

    blockers = draft.get("blockers")
    if blockers:
        paras.append(blockers)

    personal = draft.get("personal")
    if personal:
        paras.append(personal)

    closing = draft.get("closing")
    if closing:
        paras.append(closing)

    signoff = draft.get("signoff")
    if signoff:
        paras.append(signoff)

    return paras


# ---------- HTML preview ----------

HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>{title}</title>
<style>
  :root {{ color-scheme: light; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    max-width: 820px; margin: 2em auto; padding: 0 1.5em;
    color: #172b4d; background: #fff; line-height: 1.55; }}
  .banner {{ background: #fffae6; border: 1px solid #ffc400; padding: 0.75em 1em;
    border-radius: 4px; margin-bottom: 1.5em; font-size: 0.95em; }}
  .banner strong {{ color: #974f0c; }}
  .envelope {{ border: 1px solid #dfe1e6; border-radius: 6px; padding: 0; overflow: hidden;
    background: #fff; }}
  .headers {{ background: #f4f5f7; padding: 0.8em 1.2em; border-bottom: 1px solid #dfe1e6;
    font-size: 0.9em; color: #5e6c84; }}
  .headers .row {{ margin: 0.15em 0; }}
  .headers .label {{ display: inline-block; width: 5em; color: #6b778c; }}
  .headers .value {{ color: #172b4d; }}
  .subject {{ font-weight: 600; font-size: 1.05em; color: #172b4d; margin-top: 0.4em; }}
  .body {{ padding: 1.3em 1.4em; font-size: 1em; }}
  .body p {{ margin: 0 0 1em 0; }}
  .body p:last-child {{ margin-bottom: 0; }}
  .next-steps {{ margin-top: 2em; padding: 1em 1.2em; background: #f4f5f7;
    border-radius: 4px; font-size: 0.92em; color: #42526e; }}
  .next-steps code {{ background: #fff; padding: 1px 5px; border-radius: 3px;
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.88em; }}
</style>
</head>
<body>
<div class="banner">
  <strong>Preview only.</strong> This skill does not send mail. Review the draft below.
  A matching <code>.eml</code> file has been written to <code>{eml_path}</code> — double-click
  that file to open the draft in your default mail client (Outlook or Mail.app) with To,
  Subject, and Body pre-filled. You send it from there.
</div>

<div class="envelope">
  <div class="headers">
    <div class="row"><span class="label">From:</span> <span class="value">{from_display}</span></div>
    <div class="row"><span class="label">To:</span> <span class="value">{to_display}</span></div>
    {cc_row}
    <div class="subject">{subject_html}</div>
  </div>
  <div class="body">
    {body_html}
  </div>
</div>

<div class="next-steps">
  <strong>Next:</strong> Reply <code>approve</code> to keep these files in <code>/tmp/</code>,
  <code>edit &lt;section&gt;: &lt;change&gt;</code> to rewrite a section, or
  <code>cancel</code> to delete both files.
</div>
</body>
</html>
"""


def render_html(draft, from_name, from_email, to, cc, eml_path):
    paras = assemble_body(draft)
    body_html = html_paragraphs(paras)

    from_display = html.escape(f"{from_name} <{from_email}>" if from_name else from_email)
    to_display = html.escape(", ".join(to))
    subject = draft.get("subject") or "(no subject)"

    cc_row = ""
    if cc:
        cc_display = html.escape(", ".join(cc))
        cc_row = f'<div class="row"><span class="label">Cc:</span> <span class="value">{cc_display}</span></div>'

    return HTML_TEMPLATE.format(
        title=html.escape(subject),
        eml_path=html.escape(str(eml_path)),
        from_display=from_display,
        to_display=to_display,
        cc_row=cc_row,
        subject_html=html.escape(subject),
        body_html=body_html,
    )


# ---------- .eml file ----------

def render_eml(draft, from_name, from_email, to, cc):
    """Produce a multipart/alternative EmailMessage ready to write to disk.
    Opens as a draft in macOS Mail.app and Outlook when double-clicked."""
    msg = EmailMessage()
    msg["Subject"] = draft.get("subject") or "(no subject)"
    msg["From"] = formataddr((from_name, from_email)) if from_name else from_email
    msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg["Date"] = format_datetime(datetime.now(timezone.utc))

    # Mail clients only need X-Unsent: 1 to recognize this as a draft.
    # Outlook specifically keys on this.
    msg["X-Unsent"] = "1"

    paras = assemble_body(draft)
    plain_body = join_paragraphs(paras)
    html_body = f"""<!doctype html>
<html><body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size: 14px; line-height: 1.5; color: #172b4d;">
{html_paragraphs(paras)}
</body></html>"""

    msg.set_content(plain_body)
    msg.add_alternative(html_body, subtype="html")
    return msg


# ---------- CLI ----------

def split_csv(s):
    if not s:
        return []
    return [x.strip() for x in s.split(",") if x.strip()]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--draft", required=True, help="Path to draft JSON")
    p.add_argument("--to", required=True, help="Comma-separated TO addresses")
    p.add_argument("--cc", default="", help="Comma-separated CC addresses (optional)")
    p.add_argument("--from-name", default="")
    p.add_argument("--from-email", required=True)
    p.add_argument("--out-html", required=True)
    p.add_argument("--out-eml", required=True)
    args = p.parse_args()

    draft = json.loads(Path(args.draft).read_text())
    to = split_csv(args.to)
    cc = split_csv(args.cc)

    if not to:
        print("error: --to is required and must contain at least one address", file=sys.stderr)
        sys.exit(2)

    # Write .eml first so the HTML preview can reference its path accurately.
    eml_path = Path(args.out_eml)
    msg = render_eml(draft, args.from_name, args.from_email, to, cc)
    eml_path.write_bytes(bytes(msg))

    html_path = Path(args.out_html)
    html_path.write_text(render_html(draft, args.from_name, args.from_email, to, cc, eml_path))

    print(json.dumps({
        "html": str(html_path),
        "eml": str(eml_path),
        "to": to,
        "cc": cc,
        "subject": draft.get("subject", ""),
    }))


if __name__ == "__main__":
    main()
