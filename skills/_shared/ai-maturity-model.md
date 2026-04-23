# AI Maturity Model — classification reference

When a reporting skill mentions AI-related work — something involving Claude, an AI agent, an AI-assisted workflow, a `CLAUDE.md` landing, a new skill shipping — tag the work with its **S-level and phase** using this reference. This gives leadership an immediate read on where a given artifact sits on the adoption curve, which is more useful to them than the artifact itself.

The model is a common-vocabulary tool, not a compliance exercise. Tag once per topic or paragraph, not per sentence.

## Levels

| Level | Name | Definition |
|---|---|---|
| **S0** | Baseline | Existing engineering practice; no AI involved |
| **S1** | Assistant | AI augments human work — human drives, AI suggests / completes / explains |
| **S2** | Autonomous | AI executes tasks autonomously under human-defined constraints, with self-verification |
| **S3** | Orchestrated | Multiple agents coordinate on a workflow; architecture-as-agent-topology |
| S4 | Aspirational | Self-improving systems; not shipping today |

**Promotion depends on gates, not ambition.** To move S1 → S2 you need test infrastructure solid enough for agents to self-verify and requirements machine-verifiable enough for an agent to validate against. To move S2 → S3 you need every inner phase (Build / Test / Review) AND every outer phase (Requirements / Design / Deploy / Operate) at S2 — plus architecture that supports independent agent units.

## Phases

Work doesn't have a single S-level — it has an S-level **per phase**. A team can be S2 in Build, S1 in Test, S0 in Operate all at once. The phases:

| Phase | S1 | S2 | S3 |
|---|---|---|---|
| **Requirements** | AI drafts PRDs/specs from templates | Acceptance criteria machine-verifiable | Formal contracts with defined interfaces |
| **Design** | AI suggests patterns, drafts ADRs | AI generates component designs; human defines constraints | Architecture = agent topology & orchestration |
| **Build** | Code completion, generation, explanation | Agents implement whole features end-to-end | Multiple specialized agents on same feature |
| **Test** | AI-generated tests and edge cases | Self-verifying loop: agent writes tests → code → verifies | Cross-agent integration tests, contract tests |
| **Review** | AI pre-review (lint, bugs, security) | Outcome-based review: does it pass tests and meet criteria? | System-level quality dashboards across agents |
| **Deploy** | AI assists with deploy scripts and debugging | Automated CI/CD handling agent volume | Multi-component orchestration, canary / blue-green |
| **Operate** | AI assists debugging, log analysis, incident diagnosis | Automated anomaly detection, AI performs diagnosis | Cross-system feedback loops; prod data informs priorities |

## How to classify a piece of work

Walk through these in order. Stop at the first clear match.

1. **What's the artifact?**
   - A `CLAUDE.md` file landed in a repo → **S1 Build infrastructure** (enables AI assistance for that codebase)
   - A Claude Code skill, slash command, or agent shipped → **S2** in whatever phase it covers (`/install-pe` = S2 Deploy; `/ai-exec-report` = S2 Operate; an agent reviewer = S2 Review)
   - A PR where a human wrote the code with Claude help → **S1 Build** (assistant, not autonomous)
   - A CI hook that enforces Claude-generated standards (e.g., CLAUDE.md-mirrored lint rules) → **S2 Review** (outcome-based, autonomous)
   - A process where multiple agents coordinate (e.g., Claude plans → Claude writes → Claude tests → Claude reviews) → **S3** in the affected phases

2. **Does the AI drive or assist?**
   - Human initiates and supervises every step → S1
   - Human defines the goal + constraints, agent executes and self-verifies → S2
   - Agents hand work to each other within defined contracts → S3

3. **Where in the workflow does the AI intervene?** Use the Phase column from the table above. Same artifact can touch multiple phases — pick the dominant one for tagging.

## Classification examples

Concrete examples drawn from typical platform-team work. Use these as calibration:

- **"CLAUDE.md added to the firewall module"** → **S1 Build infrastructure**. It enables S1 assistance for anyone working in that module; it is not itself autonomous work.
- **"Team ran 200+ Claude Code sessions this week"** → **S1 Build** (dominant) + some **S1 Operate** (debugging assists). High-volume S1 use, not S2.
- **"Shipped `/provision-test-infra aws` skill that provisions an AWS instance and adds it to the inventory"** → **S2 Deploy**. The skill executes the provisioning task autonomously; human defines what to provision, agent does the work and writes back the verified result.
- **"Added a pre-commit hook that enforces rules from CLAUDE.md"** → **S2 Review**. Outcome-based autonomous check. Moves the team's Review phase from S1 to S2.
- **"Built a Claude Code skill that drafts weekly reports from Jira / Slack / GitHub signal"** → **S2 Operate**. Agent performs diagnosis (what happened this week) and produces the artifact; human reviews and sends.
- **"CI pipeline automatically triggers Claude to re-run acceptance tests when a PR is labeled `test-me`"** → Sitting between S2 Deploy and S2 Test; call it **S2 Test** since the self-verification is the point.
- **"Anthropic API key deployed across team repos, enabling Claude code review on every PR"** → **S1 Review infrastructure** (prerequisite, not yet autonomous). Once the review is outcome-based and merge-blocking, that's the S2 Review transition.
- **"Three agents coordinating on a Bolt plan — one plans, one writes, one tests"** → **S3 Build** (agent topology in Build phase).

## Tagging format for output

**Inline parenthetical** at the end of the sentence or paragraph where the artifact is named:

> Brónach shipped `CLAUDE.md` into `bolt-private` this week with a matching workflow file, making AI-assisted review the default for one of our security-sensitive repos (**S1 Review infrastructure**).

> Greg opened a WIP PR extending the `/provision-test-infra` skill to AWS and adding a new `/install-agent` skill (**S2 Deploy**) — moves a chunk of PE test provisioning into autonomous territory.

One tag per topic paragraph. Don't tag every sentence — reads as boilerplate.

**When reporting aggregate activity** (e.g., session counts), tag the dominant level:

> The team ran 164 Claude Code sessions Mon–Tue across seven projects — steady **S1 Build** usage with occasional **S2 Operate** escapes into skill-execution workflows.

**When the work is a transition itself** (landing a prerequisite that promotes a phase), name the transition explicitly:

> The `ANTHROPIC_CODE_REVIEW_KEY` rollout completes the prerequisite for automated, merge-blocking Claude code review — the **S1 → S2 Review** transition for the team.

## When NOT to tag

- **Artifacts that have no AI angle** — a regular bug fix, a dependency bump, a routine ticket. Don't shoehorn a tag in to make something look AI-ish.
- **Pure tooling maintenance** — CI cleanup, repo hygiene, non-AI refactors. Even if a Claude session was used to author the change, the artifact isn't itself an AI adoption artifact.
- **Speculative future work** — tag what has shipped or is visibly in progress; don't tag aspirations.

The tags only help if they're accurate. Overtagging devalues them fast.

## Communication guidance by audience

- **Team weekly (internal)**: tag team blocks; helps the team self-assess trajectory.
- **Individual AI report row (Champion/Manager tables)**: tag each win; readers include skip-level leadership who uses these to assess adoption maturity.
- **Exec email (upward to your manager and their chain)**: tag paragraph-level, not sentence-level; leadership wants to see the *mix* of S-levels the team is operating at, not a nested breakdown. End sections with a one-sentence trajectory read if one is fair: "Team is mostly S1 Build, experimenting with S2 Deploy via the custom skills."
- **Crack-finder (how-can-i-help)**: the skill isn't AI-reporting per se, but if a surfaced item is AI-adjacent (a stuck CLAUDE.md rollout, a languishing agent-enablement PR), the phase/S-level context helps frame urgency — that's a prerequisite for a phase transition, not just a stale PR.

## Source

Organization-specific reference model; each org will have its own canonical source. Update the examples in this file to match the org's language.
