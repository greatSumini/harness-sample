---
name: harness
description: Structured development harness that guides feature implementation through 5 phases — Clarify, Context Gather, Plan, Generate, Evaluate. Each phase runs as an independent sub-agent that produces artifacts for the next phase. Use this skill when starting a new feature, building a project from scratch, or implementing a complex requirement that benefits from structured planning before coding. Triggers on phrases like "build me X", "implement X", "new feature", "create an app that", or when the user explicitly invokes /harness.
disable-model-invocation: true
user-invocable: true
argument-hint: [feature description]
---

# Development Harness — Orchestrator

A structured 5-phase workflow where each phase is executed by an independent sub-agent. Artifacts flow between phases via `.harness/artifacts/`.

## Overview

```
Phase 1: Clarify      → Sub-Agent → artifacts/01-clarify.md
Phase 2: Context      → Sub-Agent → artifacts/02-context.md
Phase 3: Plan         → Sub-Agent → artifacts/03-plan.md + phases.json + tasks.json
Phase 4: Generate     → Sub-Agent (per phase) → artifacts/04-generate.md
Phase 5: Evaluate     → Sub-Agent → artifacts/05-evaluate.md
```

## Artifact Pipeline

Each sub-agent reads previous phase artifacts and produces its own. All artifacts live in `.harness/artifacts/`.

```
01-clarify.md ──→ 02-context.md ──→ 03-plan.md ──→ 04-generate.md ──→ 05-evaluate.md
                                     phases.json
                                     tasks.json
```

## How to use

The user provides a feature description as `$ARGUMENTS`. Execute each phase by spawning a sub-agent using the **Agent tool**. Get explicit user approval before advancing to the next phase.

---

## Orchestration Flow

### Step 0: Initialize

Create `.harness/artifacts/` directory if it doesn't exist:
```bash
mkdir -p .harness/artifacts
```

### Step 1: Clarify Phase

Spawn a sub-agent with the following:
- **description**: "Clarify phase - surface questions"
- **prompt**: Read the instructions from `.claude/skills/harness/phases/01-clarify.md` and include `$ARGUMENTS` as the `$FEATURE_DESCRIPTION`. Tell the agent to write its output to `.harness/artifacts/01-clarify.md`.

After the agent completes:
1. Read `.harness/artifacts/01-clarify.md` and present the questions to the user
2. Wait for the user's answers
3. **Update** `.harness/artifacts/01-clarify.md` — fill in the "User Decisions" section with the user's answers

**Gate**: Wait for explicit user approval before proceeding.

### Step 2: Context Gather Phase

Spawn a sub-agent with the following:
- **description**: "Context gather - scan codebase"
- **prompt**: Read the instructions from `.claude/skills/harness/phases/02-context.md`. The agent should read `.harness/artifacts/01-clarify.md` as input and write its output to `.harness/artifacts/02-context.md`.

After the agent completes:
1. Read `.harness/artifacts/02-context.md` and present the summary to the user

**Gate**: Wait for explicit user approval before proceeding.

### Step 3: Plan Phase

Spawn a sub-agent with the following:
- **description**: "Plan phase - create execution plan"
- **prompt**: Read the instructions from `.claude/skills/harness/phases/03-plan.md`. The agent should read `.harness/artifacts/01-clarify.md` and `.harness/artifacts/02-context.md` as input, then produce:
  - `.harness/phases.json`
  - `.harness/tasks.json`
  - `.harness/artifacts/03-plan.md`

After the agent completes:
1. Read `.harness/artifacts/03-plan.md` and present the plan summary table to the user
2. If the user requests changes, spawn the Plan agent again with the feedback

**Gate**: Wait for explicit user approval before proceeding.

### Step 4: Generate Phase

This phase runs **one sub-agent per execution phase** defined in `.harness/phases.json`.

For each phase in `phases.json` (in order):

1. Spawn a sub-agent with the following:
   - **description**: "Generate phase - {phase_name}"
   - **prompt**: Read the instructions from `.claude/skills/harness/phases/04-generate.md`. Set `$PHASE_ID` to the current phase ID (e.g., "phase-1"). The agent should read all previous artifacts and implement only the tasks in that phase. It should update `tasks.json` statuses and append to `.harness/artifacts/04-generate.md`.

2. After the agent completes, briefly report progress to the user:
   - Which tasks were completed
   - Current overall progress (e.g., "Phase 2/6 complete, 4/9 tasks done")

3. Initialize `.harness/artifacts/04-generate.md` with a header before the first generate sub-agent:
   ```markdown
   # Phase 4: Generate — Artifact
   ```

**Note**: Each generate sub-agent runs sequentially (phase by phase), but tasks within a phase that have no inter-dependencies can be implemented in parallel by the agent.

**Gate**: After ALL phases are generated, wait for user approval before proceeding to evaluation.

### Step 5: Evaluate Phase

Spawn a sub-agent with the following:
- **description**: "Evaluate phase - verify output"
- **prompt**: Read the instructions from `.claude/skills/harness/phases/05-evaluate.md`. The agent should read all artifacts, run available checks, verify acceptance criteria, fix errors, and write results to `.harness/artifacts/05-evaluate.md`.

After the agent completes:
1. Read `.harness/artifacts/05-evaluate.md` and present the results to the user
2. If there are remaining issues, report them clearly

---

## Error Handling

- If a sub-agent fails or reports a blocker, present the issue to the user and ask how to proceed
- If a sub-agent's artifact is missing or malformed, re-run the phase
- The user can always say "redo phase N" to re-run any specific phase

## State Management

All harness state lives in `.harness/` at the project root:

```
.harness/
├── artifacts/
│   ├── 01-clarify.md      # Phase 1 output: questions + user decisions
│   ├── 02-context.md      # Phase 2 output: codebase context
│   ├── 03-plan.md         # Phase 3 output: plan summary
│   ├── 04-generate.md     # Phase 4 output: generation log
│   └── 05-evaluate.md     # Phase 5 output: evaluation results
├── phases.json            # Phase definitions (from Phase 3)
├── tasks.json             # Task definitions with status (from Phase 3)
└── log.md                 # Legacy execution log (optional)
```

This directory can be safely deleted after the feature is complete, or kept for reference.
