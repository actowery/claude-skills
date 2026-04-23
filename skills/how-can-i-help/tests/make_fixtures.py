#!/usr/bin/env python3
"""
Build sanitized fixtures for the how-can-i-help smoke test.

Emits:
  fixtures/brief-three-items.json  — full 3-item brief
  fixtures/brief-one-item.json     — honest-count short brief (1 real item)
  fixtures/brief-empty.json        — zero-item "quiet week" case
  fixtures/user-alex.json          — test user config with team

All fictional; no real names, emails, orgs, or ticket keys.
"""

import json
from pathlib import Path


HERE = Path(__file__).parent
FIX = HERE / "fixtures"


def brief_three():
    return {
        "scan_window": "2026-06-01 to 2026-06-15",
        "generated_at": "2026-06-15T09:30:00",
        "items": [
            {
                "rank": 1,
                "title": "Customer escalation PLAT-888 — silent on our side for 9 days",
                "category": "customer-escalation",
                "description": (
                    "PLAT-888 is a customer-tagged escalation that last had a customer comment "
                    "on Jun 6 asking for a status update on the gateway timeout issue. Taylor "
                    "(assignee) hasn't responded in-ticket since Jun 4. Ticket is still Open, "
                    "customer is still waiting."
                ),
                "why_help_matters": (
                    "Taylor almost certainly isn't avoiding the customer — they've likely "
                    "deprioritized in favor of sprint work and no one's told them the customer "
                    "is getting restless. Your nudge surfaces that signal without it having to "
                    "come from the customer or the TAM."
                ),
                "business_benefit": (
                    "A 9-day silence gap on a customer escalation is the leading indicator for "
                    "churn-risk conversations at renewal. One acknowledgment message buys two "
                    "weeks of goodwill for the cost of 30 seconds."
                ),
                "suggested_action": (
                    "Ping Taylor: 'Customer pinged PLAT-888 on Jun 6 — worth a one-liner even "
                    "if the fix isn't ready?'"
                ),
                "citations": [
                    {"label": "PLAT-888", "url": "https://example.test/browse/PLAT-888"}
                ],
            },
            {
                "rank": 2,
                "title": "Buried @-mention in #cross-platform from Jun 4",
                "category": "buried-mention",
                "description": (
                    "On Jun 4, the SRE team @-mentioned @platform-team in #cross-platform-cicd "
                    "asking our preference on a runtime upgrade timing. No reply in-thread since. "
                    "It's been 11 days; they're probably making the decision without us."
                ),
                "why_help_matters": (
                    "Your team didn't intentionally ignore this — it buried in a busy channel. "
                    "An unacknowledged cross-team ask compounds: next time SRE has a decision "
                    "to make, they may not bother asking us at all."
                ),
                "business_benefit": (
                    "Responsiveness to cross-team asks is how your team stays in the decision "
                    "loop on shared infrastructure. Missing this consistently gets you designed "
                    "around, not with."
                ),
                "suggested_action": (
                    "Reply in-thread: 'Catching up — Taylor will review the upgrade timing this "
                    "week.' Then forward to Taylor with the specific ask."
                ),
                "citations": [
                    {"label": "#cross-platform-cicd thread",
                     "url": "https://example.slack.com/archives/C000/p11111"}
                ],
            },
            {
                "rank": 3,
                "title": "PR #456 on gateway-api — 12 days waiting on review",
                "category": "stale-pr",
                "description": (
                    "Taylor opened PR #456 on gateway-api 12 days ago. Jordan was assigned as "
                    "reviewer and hasn't commented or approved. Taylor has stopped pushing "
                    "commits — likely context-switched to other work."
                ),
                "why_help_matters": (
                    "Taylor has quietly given up on getting this landed. Jordan probably doesn't "
                    "know they're blocking. Neither will surface it without an external nudge."
                ),
                "business_benefit": (
                    "The gateway-api improvement was scoped for the Jun sprint. Every week it "
                    "sits is a week the next dependent task can't start."
                ),
                "suggested_action": (
                    "Ping Jordan: 'Taylor's PR #456 has been waiting 12 days — 15 min this week "
                    "or should I reassign?'"
                ),
                "citations": [
                    {"label": "PR #456",
                     "url": "https://github.com/example/gateway-api/pull/456"}
                ],
            },
        ],
    }


def brief_one():
    return {
        "scan_window": "2026-06-08 to 2026-06-22",
        "generated_at": "2026-06-22T09:30:00",
        "notes": "Quiet window — only one item met the bar. Good signal that the team's channels are clearing things in real time.",
        "items": [
            {
                "rank": 1,
                "title": "Stale cross-team dependency on DEP-555",
                "category": "cross-team-dependency",
                "description": (
                    "Two of our tickets reference DEP-555 (owned by the API Platform team). "
                    "DEP-555 hasn't been updated in 18 days. Our tickets are sitting in a Blocked state."
                ),
                "why_help_matters": (
                    "An IC-to-IC ping has been tried twice. The next ping from Taylor would be a "
                    "third in a row, which is awkward for them. Manager-to-manager escalates the "
                    "signal without escalating the relationship."
                ),
                "business_benefit": (
                    "Unblocking DEP-555 unblocks two downstream tickets on our side. Faster "
                    "resolution also keeps the API Platform team's silence from becoming a "
                    "habitual pattern."
                ),
                "suggested_action": (
                    "Manager-to-manager ping to the API Platform lead: 'Two of ours are blocked "
                    "on DEP-555 — realistic ETA or can we help pick it up?'"
                ),
                "citations": [
                    {"label": "DEP-555", "url": "https://example.test/browse/DEP-555"}
                ],
            }
        ],
    }


def brief_empty():
    return {
        "scan_window": "2026-06-15 to 2026-06-29",
        "generated_at": "2026-06-29T09:30:00",
        "items": [],
    }


def user_config():
    return {
        "display_name": "Alex Example",
        "email": "alex@example.test",
        "atlassian_account_id": "test-alex-001",
        "slack_user_id": "U_ALEX_TEST",
        "github_username": "alex-example",
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
        "staleness_thresholds": {
            "slack_thread_silent_days": 7,
            "email_unreplied_days": 5,
            "jira_comment_unanswered_days": 14,
            "jira_assignee_silent_days": 21,
            "pr_stale_days": 7,
            "cross_team_mention_unacked_days": 5,
        },
        "scan_window_days": 14,
        "customer_escalation_labels": ["Escalation", "Support"],
        "cached_at": "2026-06-15",
        "cache_source": "test_fixture",
    }


def main():
    FIX.mkdir(parents=True, exist_ok=True)
    (FIX / "brief-three-items.json").write_text(json.dumps(brief_three(), indent=2))
    (FIX / "brief-one-item.json").write_text(json.dumps(brief_one(), indent=2))
    (FIX / "brief-empty.json").write_text(json.dumps(brief_empty(), indent=2))
    (FIX / "user-alex.json").write_text(json.dumps(user_config(), indent=2))
    print(f"Wrote fixtures to {FIX}")


if __name__ == "__main__":
    main()
