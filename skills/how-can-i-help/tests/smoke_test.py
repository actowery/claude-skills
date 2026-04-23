#!/usr/bin/env python3
"""
Smoke test for how-can-i-help.

Exercises render_brief.py (3-item, 1-item, empty cases), the shared
search_github.py dry-run (team fan-out), and the Claude log scanner on
a nonexistent directory.

Run from the skill root:
    python3 tests/smoke_test.py
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).parent
SKILL_ROOT = HERE.parent
FIX = HERE / "fixtures"
RENDER = SKILL_ROOT / "scripts" / "render_brief.py"
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


def test_render_three_items():
    print("[render_brief three-item brief]")
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "brief.md"
        r = run(["python3", str(RENDER),
                 "--input", str(FIX / "brief-three-items.json"),
                 "--out", str(out),
                 "--today", "2026-06-15"])
        info = json.loads(r.stdout)
        assert_eq(info["items"], 3, "3 items rendered")
        md = out.read_text()
        assert_true("# How Can I Help — 2026-06-15" in md, "header with date")
        assert_true("Scan window: **2026-06-01 to 2026-06-15**" in md, "scan window shown")
        assert_true("## 1. Customer escalation PLAT-888" in md, "item 1 titled")
        assert_true("## 2. Buried @-mention" in md, "item 2 titled")
        assert_true("## 3. PR #456" in md, "item 3 titled")
        assert_true("**Why help matters to them:**" in md, "why-help field present")
        assert_true("**Business benefit:**" in md, "business benefit field present")
        assert_true("**Suggested action:**" in md, "suggested action field present")
        assert_true("[PLAT-888](https://example.test/browse/PLAT-888)" in md,
                    "citation rendered as link")


def test_render_one_item_with_notes():
    print("[render_brief one-item brief with notes]")
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "brief.md"
        r = run(["python3", str(RENDER),
                 "--input", str(FIX / "brief-one-item.json"),
                 "--out", str(out),
                 "--today", "2026-06-22"])
        info = json.loads(r.stdout)
        assert_eq(info["items"], 1, "1 item rendered (honest-count case)")
        md = out.read_text()
        assert_true("> Quiet window" in md, "notes rendered as blockquote")
        assert_true("## 1. Stale cross-team dependency" in md, "single item titled")
        assert_true("## 2." not in md, "no fabricated second item")


def test_render_empty():
    print("[render_brief empty brief — quiet week]")
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "brief.md"
        r = run(["python3", str(RENDER),
                 "--input", str(FIX / "brief-empty.json"),
                 "--out", str(out),
                 "--today", "2026-06-29"])
        info = json.loads(r.stdout)
        assert_eq(info["items"], 0, "0 items rendered")
        md = out.read_text()
        assert_true("No items met the bar" in md, "empty-state message present")
        assert_true("quiet week" not in md.lower() or "good signal" in md,
                    "no platitudes in empty message")
        assert_true("## 1." not in md, "no fabricated item in empty brief")


def test_github_dry_run_with_team():
    print("[search_github.py dry-run --include-team]")
    r = run(["python3", str(SEARCH_GH), "prs",
             "--config", str(FIX / "user-alex.json"),
             "--start", "2026-06-01", "--end", "2026-06-15",
             "--state", "open",
             "--include-team",
             "--dry-run"], check=False)
    assert_eq(r.returncode, 0, "dry-run prs exits 0")
    # 1 user + 2 team members with handles = 3 gh calls
    assert_eq(r.stderr.count(b"DRY-RUN"), 3, "team-mode runs 3 gh calls")


def test_claude_log_scan_missing_dir():
    print("[scan_claude_logs nonexistent dir]")
    r = run(["python3", str(SCAN),
             "--start", "2026-06-01", "--end", "2026-06-15",
             "--claude-log-dir", "/tmp/definitely-does-not-exist-hcih"])
    out = json.loads(r.stdout)
    assert_eq(out["aggregate"]["sessions_total"], 0, "zero sessions when dir missing")


def main():
    test_render_three_items()
    test_render_one_item_with_notes()
    test_render_empty()
    test_github_dry_run_with_team()
    test_claude_log_scan_missing_dir()
    print("\nAll smoke tests passed.")


if __name__ == "__main__":
    main()
