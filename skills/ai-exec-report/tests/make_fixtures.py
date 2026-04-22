#!/usr/bin/env python3
"""
Build sanitized fixtures for the ai-exec-report smoke test.

Emits:
  fixtures/draft-balanced.json  — complete draft with all sections populated
  fixtures/draft-minimal.json   — minimal draft (opening + single win + signoff)
  fixtures/user-alex.json       — test user config

All fictional; no real names, emails, or ticket keys.
"""

import json
from pathlib import Path


HERE = Path(__file__).parent
FIX = HERE / "fixtures"


def draft_balanced():
    return {
        "subject": "Platform AI Weekly — Jun 1–5, 2026",
        "greeting": "Sam",
        "opening": "Mixed week for us — strong Claude integration progress from Taylor and a release landed from Jordan, but a dependency blocker on the Observability side that's worth flagging.",
        "team_wins": [
            "Taylor Example shipped Claude integration into our gateway repo this week, adding a CLAUDE.md and a review workflow so the pattern is repeatable. First PR using the new flow is already in review (PLAT-1234).",
            "Jordan Sample landed the rate-limiter v2 cutover (OBS-456) ahead of the cross-team freeze — the canary completed clean and full production rollout is queued for Monday.",
        ],
        "blockers": "Biggest open item is the Observability dependency bump — Taylor is unblocked after IT granted the Anthropic developer-group access Tuesday, but we're waiting on a response from the platform-ci team on CI-789 that's gating Jordan's next step. No leadership ask yet; flagging so it's not a surprise if it slips a sprint.",
        "personal": "On my end this week, I shipped two reusable skills the team now uses to automate our weekly reporting — small artifact, but paying itself back already.",
        "closing": "Happy to dig into any of these in our 1:1 or before your upward review.",
        "signoff": "Alex",
    }


def draft_minimal():
    return {
        "subject": "Platform AI Weekly — Jun 8–12, 2026",
        "greeting": "Sam",
        "opening": "Quiet week on shipments; most of the team was heads-down on prep for the cross-team review.",
        "team_wins": [
            "Taylor Example continued the gateway migration work — nothing merged this week, but the refactor PR is ready for review Monday.",
        ],
        "blockers": "No material blockers this week; pending items are follow-throughs from last week.",
        "personal": "",
        "closing": "Let me know if you want more detail before your review.",
        "signoff": "Alex",
    }


def user_config():
    return {
        "display_name": "Alex Example",
        "email": "alex@example.test",
        "atlassian_account_id": "test-alex-001",
        "slack_user_id": "U_ALEX_TEST",
        "github_username": "alex-example",
        "boss_display_name": "Sam Boss",
        "boss_first_name": "Sam",
        "boss_email": "sam.boss@example.test",
        "boss_tone_preference": "balanced",
        "cc_list": [],
        "team": {
            "name": "Platform",
            "members": [
                {"display_name": "Taylor Example", "atlassian_account_id": "test-taylor-002",
                 "slack_user_id": "U_TAYLOR_TEST", "github_username": "taylor-example",
                 "email": "taylor@example.test"},
                {"display_name": "Jordan Sample", "atlassian_account_id": "test-jordan-003",
                 "slack_user_id": "U_JORDAN_TEST", "github_username": "jordan-sample",
                 "email": "jordan@example.test"},
            ],
        },
        "slack_search_mode": "public",
        "github": {"orgs": ["test-org"]},
        "ai_keywords": ["Claude", "Anthropic", "CLAUDE.md", "AI"],
        "jira_ai_labels": ["AI"],
        "scan_claude_logs": True,
        "claude_log_dir": "~/.claude/projects",
        "cached_at": "2026-06-01",
        "cache_source": "test_fixture",
    }


def main():
    FIX.mkdir(parents=True, exist_ok=True)
    (FIX / "draft-balanced.json").write_text(json.dumps(draft_balanced(), indent=2))
    (FIX / "draft-minimal.json").write_text(json.dumps(draft_minimal(), indent=2))
    (FIX / "user-alex.json").write_text(json.dumps(user_config(), indent=2))
    print(f"Wrote fixtures to {FIX}")


if __name__ == "__main__":
    main()
