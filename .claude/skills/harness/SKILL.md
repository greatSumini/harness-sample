---
name: harness
description: Structured development harness that guides feature implementation through 5 phases — Clarify, Context Gather, Plan, Generate, Evaluate. Use this skill when starting a new feature, building a project from scratch, or implementing a complex requirement that benefits from structured planning before coding. Triggers on phrases like "build me X", "implement X", "new feature", "create an app that", or when the user explicitly invokes /harness.
disable-model-invocation: true
user-invocable: true
argument-hint: [feature description]
---

# Development Harness

A structured 5-phase workflow for implementing features from idea to working code.

## Overview

```
Phase 1: Clarify      → Surface questions before writing code
Phase 2: Context      → Understand the existing codebase
Phase 3: Plan         → Create tasks.json and phases.json
Phase 4: Generate     → Execute tasks phase by phase
Phase 5: Evaluate     → Verify the output works
```

## How to use

The user provides a feature description as `$ARGUMENTS`. Walk through each phase sequentially, getting explicit user approval before advancing to the next phase.

---

## Phase 1: Clarify

Before touching any code, surface discussion points the user should consider. Generate 5-10 questions organized into these categories:

### Categories
- **Feasibility**: Can this be built with the proposed stack? Are there technical blockers?
- **UX/Design**: How should users interact with this? What screens/flows are needed?
- **Data Model**: What entities, relationships, and storage are needed?
- **Scope**: What's in v1 vs. later? What can be cut?
- **Dependencies**: External APIs, libraries, services needed?

### Format
Present questions as a numbered list grouped by category. Example:

```
### Feasibility
1. Are we targeting web only, or also mobile?
2. Do we need real-time updates or is polling acceptable?

### Data Model
3. Should users have roles (admin/member) from day one?
4. Is soft-delete required for any entities?
```

After presenting questions, wait for the user's answers. Incorporate their decisions into the plan.

**Transition**: When the user has answered (or said "skip"), move to Phase 2.

---

## Phase 2: Context Gather

Scan the existing codebase to understand what already exists.

### If the codebase is empty or brand new
Say: "This is a fresh project — skipping context gathering." and move directly to Phase 3.

### If there is existing code
1. Read the project structure (directories, key files)
2. Identify the tech stack (package.json, requirements.txt, go.mod, etc.)
3. Find existing patterns: routing, state management, API layer, DB schema
4. Note any existing tests, CI config, or build setup
5. Summarize findings to the user in under 200 words

Save a brief context summary to `.harness/context.md` for reference in later phases.

**Transition**: Present the summary, then move to Phase 3.

---

## Phase 3: Plan

Create a structured execution plan as two JSON files inside `.harness/`.

### 1. Create `.harness/phases.json`

Phases are ordered groups of work that must be completed sequentially. Each phase has a name, description, and list of task IDs.

```json
{
  "project": "Feature name from user input",
  "created_at": "ISO timestamp",
  "phases": [
    {
      "id": "phase-1",
      "name": "Data Layer",
      "description": "Set up database schema and models",
      "task_ids": ["task-1", "task-2"]
    },
    {
      "id": "phase-2",
      "name": "API Layer",
      "description": "Build REST endpoints",
      "task_ids": ["task-3", "task-4"]
    }
  ]
}
```

### 2. Create `.harness/tasks.json`

Each task is a discrete, implementable unit of work.

```json
{
  "tasks": [
    {
      "id": "task-1",
      "phase_id": "phase-1",
      "title": "Create User table migration",
      "description": "Detailed description of what to implement",
      "files_to_create": ["src/db/migrations/001_users.sql"],
      "files_to_modify": [],
      "depends_on": [],
      "status": "pending",
      "acceptance": "Table exists with columns: id, email, name, created_at"
    }
  ]
}
```

### Rules for planning
- Tasks should be small enough to implement in one shot (1-3 files each)
- Dependencies between tasks must be explicit via `depends_on`
- All tasks within a phase can run in parallel unless they have inter-dependencies
- Each task must have a clear `acceptance` criterion
- File paths in `files_to_create` / `files_to_modify` must be concrete

**Transition**: Show the user the phase/task breakdown as a readable summary table. Wait for approval or edits before proceeding to Phase 4.

---

## Phase 4: Generate

Execute tasks using `run_phases.py`. This is the code generation phase.

### Execution flow

1. Read `.harness/phases.json` and `.harness/tasks.json`
2. For each phase in order:
   a. For each task in the phase (respecting `depends_on`):
      - Read the task definition
      - Implement the task: create/modify the specified files
      - Update `status` in tasks.json to `"done"`
      - Log what was done to `.harness/log.md`
   b. After all tasks in a phase are done, update phase status
3. After all phases complete, write a summary to `.harness/log.md`

### Implementation rules
- Follow existing code patterns found in Phase 2 (if any)
- Use the decisions made in Phase 1 to guide implementation choices
- Each task should result in working, self-contained code
- Do not leave placeholder/TODO comments — implement fully
- After each phase, briefly report progress to the user

### Running the script

If `run_phases.py` exists at the project root, execute it:
```bash
python run_phases.py
```

If it doesn't exist, execute tasks inline by following the phases/tasks JSON manually — read each task, implement it, mark it done.

**Transition**: When all tasks are done, move to Phase 5.

---

## Phase 5: Evaluate

Verify that the generated code is correct. This phase is optional but recommended.

### Available checks (run whichever apply)

| Check | When to run | Command |
|-------|-------------|---------|
| TypeScript typecheck | If tsconfig.json exists | `npx tsc --noEmit` |
| ESLint | If .eslintrc* exists | `npx eslint .` |
| Python type check | If pyproject.toml with mypy | `mypy .` |
| Python lint | If ruff/flake8 configured | `ruff check .` |
| Build | If build script exists | `npm run build` or equivalent |
| Tests | If test files were created | `npm test` / `pytest` / etc. |

### Process
1. Detect which checks are available based on project config files
2. Run each applicable check
3. If errors are found, fix them immediately
4. Report results to the user

### If no checks are configured
Tell the user: "No linting/type-checking/build tools are configured. Consider adding: [suggestions based on stack]."

---

## State Management

All harness state lives in `.harness/` at the project root:

```
.harness/
├── context.md       # Codebase context from Phase 2
├── phases.json      # Phase definitions
├── tasks.json       # Task definitions with status
└── log.md           # Execution log
```

This directory can be safely deleted after the feature is complete, or kept for reference.
