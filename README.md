# claude-skills

A collection of Claude Code skills I build and maintain. One repo, one CI pipeline, one issue tracker, one release cadence — easier to share and less operational overhead than a repo per skill.

## Skills

| Skill | What it does |
|---|---|
| [`weekly-confluence-update`](skills/weekly-confluence-update/) | Drafts a team's section on a shared Confluence team weekly-report page. Handles @mention-based assignment, team block detection, append-only safety. 4 signal sources: Jira, Slack (public + optional private), Outlook, GitHub PRs. |
| [`ai-weekly-update`](skills/ai-weekly-update/) | Drafts an individual row on a shared AI-usage weekly report (Champion/Manager tables). Matches by plain-text name. 5 signal sources including local Claude Code session scanning. Manager-mode weaves team wins alongside personal wins; self-reporting rule skips teammates with their own row. |
| [`ai-exec-report`](skills/ai-exec-report/) | Drafts a weekly upward-communication **email** from a manager to their manager, reporting the team's AI adoption in upper-mgmt language. Hype-but-honest tone with a non-negotiable blockers section. Skill never sends mail — renders an HTML preview + `.eml` draft file that opens in your default mail client with To/Subject/Body pre-filled. |
| [`how-can-i-help`](skills/how-can-i-help/) | Crack-finder. Scans Jira / Slack / Outlook / GitHub for stale, silent, forgotten items — the stuff that fell through the cracks because nobody's actively chasing it. Returns a short honest brief (up to 3) with description, psychology of why help matters, business benefit, and a specific low-effort management action. Read-only; informational; no approval gate. |

Each skill has its own `README.md`, `SKILL.md`, and `tests/`. Start with the subdirectory `README.md`.

## Installing one skill

Clone the repo and symlink only the skill(s) you want into your Claude Code skills directory:

```bash
git clone https://github.com/<user>/claude-skills.git ~/src/claude-skills
ln -s ~/src/claude-skills/skills/weekly-confluence-update ~/.claude/skills/weekly-confluence-update
ln -s ~/src/claude-skills/skills/ai-weekly-update       ~/.claude/skills/ai-weekly-update
```

Using a symlink (vs a copy) means `git pull` in the clone immediately updates every installed skill — no separate upgrade step per skill.

## Installing all of them

```bash
git clone https://github.com/<user>/claude-skills.git ~/src/claude-skills
for d in ~/src/claude-skills/skills/*/; do
  ln -sf "$d" ~/.claude/skills/$(basename "$d")
done
```

## Contributing a new skill

1. Create `skills/<new-skill-name>/` with at least `SKILL.md` + `tests/smoke_test.py`
2. The matrix CI picks it up automatically if `tests/make_fixtures.py` and `tests/smoke_test.py` exist (see `.github/workflows/smoke.yml`)
3. Update the top-level `README.md` skills table
4. Open a PR

## Running tests

Each skill is self-contained and can be tested from its own directory:

```bash
cd skills/<name>
python3 tests/smoke_test.py
```

CI runs every skill's smoke test via a matrix strategy, so adding a new skill costs zero workflow changes as long as it follows the convention.

## Config & cache philosophy

Skills write user state to `${XDG_CONFIG_HOME:-$HOME/.config}/<skill-name>/` and research caches to `${XDG_CACHE_HOME:-$HOME/.cache}/<skill-name>/` — never to the skill install directory. This keeps user state safe across upgrades and out of git.

## License

MIT — see [LICENSE](LICENSE).
