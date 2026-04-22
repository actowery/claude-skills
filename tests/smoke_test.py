#!/usr/bin/env python3
"""
Smoke test for ai-weekly-update. Exercises every subcommand against sanitized
fixtures. No network, no auth.

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
PARSE = SKILL_ROOT / "scripts" / "parse_page.py"
RENDER = SKILL_ROOT / "scripts" / "render_preview.py"
SEARCH_GH = SKILL_ROOT / "scripts" / "search_github.py"
SCAN = SKILL_ROOT / "scripts" / "scan_claude_logs.py"

DISPLAY_NAME = "Alex Example"


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


# ----- rows command -----

def test_rows_on_empty():
    print("[rows on empty-ai-weekly.json]")
    r = run(["python3", str(PARSE), "rows",
             str(FIX / "empty-ai-weekly.json"),
             "--display-name", DISPLAY_NAME])
    out = json.loads(r.stdout)
    assert_eq(len(out["matches"]), 2, "two matches (Champion + Manager)")
    headings = sorted(m["table_heading"] for m in out["matches"])
    assert_eq(headings, ["Champion Weekly Report", "Manager Weekly Report"],
              "table headings captured correctly")

    # Column map: Champion table should have 5 columns.
    champ = next(m for m in out["matches"] if m["table_heading"] == "Champion Weekly Report")
    assert_eq(len(champ["columns"]), 5, "champion table has 5 columns")
    assert_true("Wins this week" in champ["columns"], "wins column discovered")

    # Manager table: 3 columns.
    mgr = next(m for m in out["matches"] if m["table_heading"] == "Manager Weekly Report")
    assert_eq(len(mgr["columns"]), 3, "manager table has 3 columns")
    assert_true("Blockers / concerns" in mgr["columns"], "blockers column discovered")


def test_rows_skips_dividers_and_others():
    print("[rows skips dividers and other-name rows]")
    r = run(["python3", str(PARSE), "rows",
             str(FIX / "empty-ai-weekly.json"),
             "--display-name", "Not Alex Person"])
    out = json.loads(r.stdout)
    assert_eq(out["matches"], [], "non-matching display name returns zero rows")

    # Sanity: "Jordan Sample" IS in the fixture (another person) and should match only their row.
    r = run(["python3", str(PARSE), "rows",
             str(FIX / "empty-ai-weekly.json"),
             "--display-name", "Jordan Sample"])
    out = json.loads(r.stdout)
    assert_eq(len(out["matches"]), 1, "Jordan matches exactly one row (Champion only)")


def test_rows_case_insensitive():
    print("[rows is case-insensitive]")
    r = run(["python3", str(PARSE), "rows",
             str(FIX / "empty-ai-weekly.json"),
             "--display-name", "alex example"])
    out = json.loads(r.stdout)
    assert_eq(len(out["matches"]), 2, "lowercase name still matches both rows")


# ----- dates -----

def test_dates():
    print("[dates]")
    r = run(["python3", str(PARSE), "dates",
             "--title", "AI Weekly Report for 01 Jun - 05 Jun 2026"])
    out = json.loads(r.stdout)
    assert_eq(out, {"start": "2026-06-01", "end": "2026-06-05"}, "date range parsed")

    r = run(["python3", str(PARSE), "dates", "--title", "No date here"], check=False)
    assert_true(r.returncode != 0, "unparseable title → non-zero exit")


# ----- build-patch -----

def test_build_patch_fills_targeted_cells():
    print("[build-patch fills Alex's cells, preserves others]")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        drafts = {
            "Manager Weekly Report|Wins this week": {
                "paragraphs": ["Shipped `/demo-skill` and Team at 80% adoption (per log scan)."]
            },
            "Manager Weekly Report|Blockers / concerns": {
                "paragraphs": ["Budget approval for API keys pending."]
            },
            "Champion Weekly Report|Wins this week": {
                "paragraphs": ["Merged first `CLAUDE.md` across 4 repos."]
            },
        }
        drafts_path = td / "drafts.json"
        drafts_path.write_text(json.dumps(drafts))

        r = run(["python3", str(PARSE), "build-patch",
                 str(FIX / "empty-ai-weekly.json"),
                 "--drafts", str(drafts_path),
                 "--display-name", DISPLAY_NAME])
        mod = json.loads(r.stdout)

        # Text we wrote should appear somewhere in the output.
        flat = json.dumps(mod)
        assert_true("/demo-skill" in flat, "slash command text present")
        assert_true("Budget approval" in flat, "blockers text present")
        assert_true("CLAUDE.md" in flat, "champion wins text present")

        # Code marks applied to backtick-wrapped spans.
        assert_true('"type": "code"' in flat, "code marks applied")

        # Sentinels present on added nodes.
        assert_true('"_skillAdded": true' in flat, "sentinels tagged")

        # Jordan Sample's text still present (wasn't in drafts).
        assert_true("widget foo" in flat, "other-user content preserved")


def test_build_patch_skips_missing_keys():
    print("[build-patch warns on unknown heading/column]")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        drafts = {"Unknown Table|Some Column": {"paragraphs": ["noop"]}}
        drafts_path = td / "drafts.json"
        drafts_path.write_text(json.dumps(drafts))
        r = run(["python3", str(PARSE), "build-patch",
                 str(FIX / "empty-ai-weekly.json"),
                 "--drafts", str(drafts_path),
                 "--display-name", DISPLAY_NAME])
        # stdout is still valid ADF; stderr carries the skip.
        mod = json.loads(r.stdout)
        assert_true("title" in mod, "output is still a valid ADF doc")
        assert_true(b"skipped" in r.stderr, "skip reported on stderr")


# ----- strip-sentinels -----

def test_strip_sentinels():
    print("[strip-sentinels]")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        drafts = {"Manager Weekly Report|Wins this week": {"paragraphs": ["Test."]}}
        drafts_path = td / "drafts.json"
        drafts_path.write_text(json.dumps(drafts))
        r = run(["python3", str(PARSE), "build-patch",
                 str(FIX / "empty-ai-weekly.json"),
                 "--drafts", str(drafts_path),
                 "--display-name", DISPLAY_NAME])
        mod_path = td / "mod.json"
        mod_path.write_text(r.stdout.decode())

        r2 = run(["python3", str(PARSE), "strip-sentinels", str(mod_path)])
        stripped = json.loads(r2.stdout)
        flat = json.dumps(stripped)
        assert_true('"_skillAdded"' not in flat, "all sentinels removed")
        assert_true("Test." in flat, "content survives strip")


# ----- preview renderer -----

def test_render_preview():
    print("[render_preview]")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        drafts = {"Manager Weekly Report|Wins this week": {"paragraphs": ["Preview test."]}}
        drafts_path = td / "drafts.json"
        drafts_path.write_text(json.dumps(drafts))
        r = run(["python3", str(PARSE), "build-patch",
                 str(FIX / "empty-ai-weekly.json"),
                 "--drafts", str(drafts_path),
                 "--display-name", DISPLAY_NAME])
        mod_path = td / "mod.json"
        mod_path.write_text(r.stdout.decode())

        out = td / "preview.html"
        run(["python3", str(RENDER), str(mod_path),
             "--title", "AI Weekly Preview Test",
             "--out", str(out)])
        html = out.read_text()
        assert_true("skill-added" in html, "preview has yellow-highlight class")
        assert_true("Preview test." in html, "preview includes added text")
        assert_true("<table" in html, "preview renders tables")


# ----- github dry-run -----

def test_github_dry_run():
    print("[search_github.py dry-run, no team]")
    r = run(["python3", str(SEARCH_GH), "prs",
             "--config", str(FIX / "user-alex.json"),
             "--start", "2026-06-01", "--end", "2026-06-05",
             "--dry-run"], check=False)
    assert_eq(r.returncode, 0, "dry-run prs exits 0")
    assert_true(b"DRY-RUN" in r.stderr, "dry-run prints gh command")
    # Personal-only mode: exactly one gh invocation.
    assert_eq(r.stderr.count(b"DRY-RUN"), 1, "personal mode → 1 gh call")

    r2 = run(["python3", str(SEARCH_GH), "commits",
              "--config", str(FIX / "user-alex.json"),
              "--start", "2026-06-01", "--end", "2026-06-05",
              "--dry-run"], check=False)
    assert_eq(r2.returncode, 0, "dry-run commits exits 0")
    assert_true(b"DRY-RUN" in r2.stderr, "dry-run commits prints gh command")


def test_github_dry_run_with_team():
    print("[search_github.py dry-run, --include-team]")
    # Manager fixture has the user + 2 members-with-handles + 1 member-without.
    # We expect 3 gh calls (user + 2 resolved handles), and a warn about the
    # unresolved member.
    r = run(["python3", str(SEARCH_GH), "prs",
             "--config", str(FIX / "user-alex-manager.json"),
             "--start", "2026-06-01", "--end", "2026-06-05",
             "--include-team",
             "--dry-run"], check=False)
    assert_eq(r.returncode, 0, "team-mode dry-run exits 0")
    assert_eq(r.stderr.count(b"DRY-RUN"), 3, "team-mode → 3 gh calls (user + 2 handles)")
    assert_true(b"Unresolved Member" in r.stderr, "warns about member missing handle")

    # Without --include-team on the manager fixture: back to 1 call.
    r2 = run(["python3", str(SEARCH_GH), "prs",
              "--config", str(FIX / "user-alex-manager.json"),
              "--start", "2026-06-01", "--end", "2026-06-05",
              "--dry-run"], check=False)
    assert_eq(r2.stderr.count(b"DRY-RUN"), 1,
              "manager fixture without --include-team stays personal-only")


# ----- claude log scanner -----

def test_claude_log_scan_empty():
    print("[scan_claude_logs on nonexistent dir]")
    r = run(["python3", str(SCAN),
             "--start", "2026-06-01", "--end", "2026-06-05",
             "--claude-log-dir", "/tmp/definitely-does-not-exist-wcu"])
    out = json.loads(r.stdout)
    assert_eq(out["aggregate"]["sessions_total"], 0, "zero sessions when dir missing")


def test_claude_log_scan_synth():
    print("[scan_claude_logs on synthetic data]")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        proj = td / "project-a"
        proj.mkdir()
        # Fake session log: one Skill invocation + a Bash call.
        events = [
            {"type": "user", "timestamp": "2026-06-02T10:00:00Z",
             "sessionId": "s1", "cwd": "/Users/test/work/project-a"},
            {"type": "assistant", "timestamp": "2026-06-02T10:00:02Z",
             "sessionId": "s1",
             "message": {"content": [
                 {"type": "tool_use", "name": "Skill", "input": {"skill": "test-skill"}},
                 {"type": "tool_use", "name": "Bash", "input": {}},
             ]}},
            # Outside window — must be skipped.
            {"type": "assistant", "timestamp": "2025-01-01T10:00:00Z",
             "sessionId": "s1",
             "message": {"content": [{"type": "tool_use", "name": "Bash"}]}},
        ]
        (proj / "s1.jsonl").write_text("\n".join(json.dumps(e) for e in events))

        r = run(["python3", str(SCAN),
                 "--start", "2026-06-01", "--end", "2026-06-05",
                 "--claude-log-dir", str(td)])
        out = json.loads(r.stdout)
        assert_eq(out["aggregate"]["sessions_total"], 1, "one session in window")
        assert_true("test-skill" in out["aggregate"]["skills_invoked_total"],
                    "skill invocation captured")
        assert_eq(out["aggregate"]["tool_counts_total"].get("Bash"), 1,
                  "Bash count excludes out-of-window event")


def main():
    test_rows_on_empty()
    test_rows_skips_dividers_and_others()
    test_rows_case_insensitive()
    test_dates()
    test_build_patch_fills_targeted_cells()
    test_build_patch_skips_missing_keys()
    test_strip_sentinels()
    test_render_preview()
    test_github_dry_run()
    test_github_dry_run_with_team()
    test_claude_log_scan_empty()
    test_claude_log_scan_synth()
    print("\nAll smoke tests passed.")


if __name__ == "__main__":
    main()
