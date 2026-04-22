#!/usr/bin/env python3
"""
Smoke test for ai-exec-report. Exercises render_email.py (both HTML preview
and .eml draft), the shared search_github.py dry-run, and the Claude log
scanner — same coverage shape as the other skills in this repo.

Run from the skill root:
    python3 tests/smoke_test.py
"""

import email
from email.header import decode_header, make_header
from email.policy import default as default_policy
import json
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).parent
SKILL_ROOT = HERE.parent
FIX = HERE / "fixtures"
RENDER = SKILL_ROOT / "scripts" / "render_email.py"
SEARCH_GH = SKILL_ROOT / "scripts" / "search_github.py"
SCAN = SKILL_ROOT / "scripts" / "scan_claude_logs.py"


def run(cmd, check=True):
    r = subprocess.run(cmd, capture_output=True, check=False)
    if check and r.returncode != 0:
        print(f"FAIL: {' '.join(str(x) for x in cmd)}\nstderr: {r.stderr.decode()}",
              file=sys.stderr)
        sys.exit(1)
    return r


def assert_eq(actual, expected, label):
    if actual != expected:
        print(f"  FAIL {label}: expected {expected!r}, got {actual!r}", file=sys.stderr)
        sys.exit(1)
    print(f"  OK   {label}")


def assert_true(cond, label):
    if not cond:
        print(f"  FAIL {label}", file=sys.stderr)
        sys.exit(1)
    print(f"  OK   {label}")


# ----- renderer -----

def test_render_html_and_eml():
    print("[render_email balanced draft]")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        html_out = td / "preview.html"
        eml_out = td / "draft.eml"

        r = run(["python3", str(RENDER),
                 "--draft", str(FIX / "draft-balanced.json"),
                 "--to", "sam.boss@example.test",
                 "--cc", "peer@example.test",
                 "--from-name", "Alex Example",
                 "--from-email", "alex@example.test",
                 "--out-html", str(html_out),
                 "--out-eml", str(eml_out)])
        info = json.loads(r.stdout)
        assert_eq(info["to"], ["sam.boss@example.test"], "to recipient parsed")
        assert_eq(info["cc"], ["peer@example.test"], "cc recipient parsed")

        # HTML file checks
        html_content = html_out.read_text()
        assert_true("Platform AI Weekly" in html_content, "subject in HTML preview")
        assert_true("sam.boss@example.test" in html_content, "to address in preview")
        assert_true("peer@example.test" in html_content, "cc address in preview")
        assert_true("Taylor Example shipped" in html_content, "team win paragraph rendered")
        assert_true("On my end this week" in html_content, "personal paragraph rendered")
        assert_true("Preview only" in html_content, "preview banner present")

        # .eml file checks — parse back and verify structure
        msg = email.message_from_bytes(eml_out.read_bytes(), policy=default_policy)
        assert_eq(msg["To"], "sam.boss@example.test", ".eml To header")
        assert_eq(msg["Cc"], "peer@example.test", ".eml Cc header")
        # Subject contains em/en dashes which get RFC-2047-encoded in headers;
        # decode before comparing to the canonical string.
        subject_decoded = str(make_header(decode_header(msg["Subject"])))
        assert_eq(subject_decoded, "Platform AI Weekly \u2014 Jun 1\u20135, 2026", ".eml Subject header (decoded)")
        assert_eq(msg["X-Unsent"], "1", "X-Unsent draft marker")
        assert_true("alex@example.test" in msg["From"], ".eml From contains email")
        assert_true("Alex Example" in msg["From"], ".eml From contains name")
        assert_true(msg.is_multipart(), ".eml is multipart/alternative")

        parts = {part.get_content_type(): part for part in msg.walk()
                 if not part.is_multipart()}
        assert_true("text/plain" in parts, ".eml has plain text part")
        assert_true("text/html" in parts, ".eml has html part")
        plain = parts["text/plain"].get_content()
        assert_true("Sam," in plain, "greeting in plain text")
        assert_true("Taylor Example shipped" in plain, "team win in plain text")
        assert_true("Alex" in plain.splitlines()[-1], "signoff is last line")


def test_render_minimal_draft():
    print("[render_email minimal draft]")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        html_out = td / "preview.html"
        eml_out = td / "draft.eml"

        run(["python3", str(RENDER),
             "--draft", str(FIX / "draft-minimal.json"),
             "--to", "sam.boss@example.test",
             "--from-email", "alex@example.test",
             "--out-html", str(html_out),
             "--out-eml", str(eml_out)])

        html_content = html_out.read_text()
        # No CC configured — the Cc row must not appear.
        assert_true("Cc:" not in html_content, "no Cc row when cc list empty")
        # Personal section was empty — must be skipped.
        msg = email.message_from_bytes(eml_out.read_bytes(), policy=default_policy)
        plain = next(p for p in msg.walk()
                     if p.get_content_type() == "text/plain").get_content()
        assert_true("On my end" not in plain, "empty personal section skipped")
        # No-blockers line still present (it's a full sentence, not empty).
        assert_true("No material blockers" in plain, "no-blockers line still included")


def test_render_requires_to():
    print("[render_email requires --to]")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        r = run(["python3", str(RENDER),
                 "--draft", str(FIX / "draft-minimal.json"),
                 "--to", "",
                 "--from-email", "alex@example.test",
                 "--out-html", str(td / "x.html"),
                 "--out-eml", str(td / "x.eml")], check=False)
        assert_true(r.returncode != 0, "empty --to exits non-zero")


# ----- shared scripts -----

def test_github_dry_run():
    print("[search_github.py dry-run]")
    r = run(["python3", str(SEARCH_GH), "prs",
             "--config", str(FIX / "user-alex.json"),
             "--start", "2026-06-01", "--end", "2026-06-05",
             "--include-team",
             "--dry-run"], check=False)
    assert_eq(r.returncode, 0, "dry-run prs exits 0")
    # 1 user + 2 team members with handles = 3 gh calls.
    assert_eq(r.stderr.count(b"DRY-RUN"), 3, "team-mode fan-out runs 3 gh calls")


def test_claude_log_scan_empty():
    print("[scan_claude_logs nonexistent dir]")
    r = run(["python3", str(SCAN),
             "--start", "2026-06-01", "--end", "2026-06-05",
             "--claude-log-dir", "/tmp/definitely-does-not-exist-exec"])
    out = json.loads(r.stdout)
    assert_eq(out["aggregate"]["sessions_total"], 0, "zero sessions when dir missing")


def main():
    test_render_html_and_eml()
    test_render_minimal_draft()
    test_render_requires_to()
    test_github_dry_run()
    test_claude_log_scan_empty()
    print("\nAll smoke tests passed.")


if __name__ == "__main__":
    main()
