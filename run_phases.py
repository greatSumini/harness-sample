#!/usr/bin/env python3
"""
run_phases.py — Utility for the harness artifact-based pipeline.

Provides commands to:
- Show status of all phases and tasks
- Mark tasks as complete
- Validate artifact pipeline integrity
- Initialize the artifact directory
"""

import json
import sys
from pathlib import Path

HARNESS_DIR = Path(".harness")
ARTIFACTS_DIR = HARNESS_DIR / "artifacts"
PHASES_FILE = HARNESS_DIR / "phases.json"
TASKS_FILE = HARNESS_DIR / "tasks.json"

ARTIFACT_FILES = {
    "clarify": ARTIFACTS_DIR / "01-clarify.md",
    "context": ARTIFACTS_DIR / "02-context.md",
    "plan": ARTIFACTS_DIR / "03-plan.md",
    "generate": ARTIFACTS_DIR / "04-generate.md",
    "evaluate": ARTIFACTS_DIR / "05-evaluate.md",
}


def load_json(path: Path) -> dict:
    if not path.exists():
        print(f"Error: {path} not found. Run Phase 3 (Plan) first.", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


def save_json(path: Path, data: dict):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def init():
    """Initialize the harness artifact directory."""
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Initialized {ARTIFACTS_DIR}/")


def show_status():
    """Show current progress of all phases and artifacts."""
    print("=" * 60)
    print("HARNESS STATUS")
    print("=" * 60)

    # Check artifact pipeline
    print("\n## Artifact Pipeline\n")
    for _, path in ARTIFACT_FILES.items():
        exists = path.exists()
        size = path.stat().st_size if exists else 0
        icon = "v" if exists else " "
        print(f"  [{icon}] {path.name} ({size} bytes)" if exists else f"  [{icon}] {path.name}")

    # Check task progress
    if TASKS_FILE.exists() and PHASES_FILE.exists():
        tasks_data = load_json(TASKS_FILE)
        phases_data = load_json(PHASES_FILE)

        total = len(tasks_data["tasks"])
        done = sum(1 for t in tasks_data["tasks"] if t["status"] == "done")
        in_progress = sum(1 for t in tasks_data["tasks"] if t["status"] == "in_progress")
        pending = total - done - in_progress

        print(f"\n## Task Progress: {done}/{total} done ({in_progress} in progress, {pending} pending)\n")

        for phase in phases_data["phases"]:
            phase_tasks = [t for t in tasks_data["tasks"] if t["id"] in phase["task_ids"]]
            phase_done = all(t["status"] == "done" for t in phase_tasks)
            icon = "v" if phase_done else ">"
            print(f"  [{icon}] {phase['name']}")
            for t in phase_tasks:
                status_icon = {"done": "v", "in_progress": ">", "pending": " "}[t["status"]]
                print(f"      [{status_icon}] {t['id']}: {t['title']}")
    else:
        print("\n## Tasks: Not yet planned (run Phase 3)")


def complete_task(task_id: str):
    """Mark a task as done."""
    tasks_data = load_json(TASKS_FILE)
    for task in tasks_data["tasks"]:
        if task["id"] == task_id:
            task["status"] = "done"
            save_json(TASKS_FILE, tasks_data)
            print(f"Task {task_id} marked as done.")
            return
    print(f"Task {task_id} not found.", file=sys.stderr)
    sys.exit(1)


def validate():
    """Validate artifact pipeline integrity."""
    errors = []

    # Check artifact ordering
    for _, path in ARTIFACT_FILES.items():
        if not path.exists():
            break  # artifacts should exist in order; stop at first missing

    # Check plan consistency
    if PHASES_FILE.exists() and TASKS_FILE.exists():
        phases_data = load_json(PHASES_FILE)
        tasks_data = load_json(TASKS_FILE)
        task_ids = {t["id"] for t in tasks_data["tasks"]}

        for phase in phases_data["phases"]:
            for tid in phase["task_ids"]:
                if tid not in task_ids:
                    errors.append(f"Phase {phase['id']} references unknown task {tid}")

        for task in tasks_data["tasks"]:
            for dep in task.get("depends_on", []):
                if dep not in task_ids:
                    errors.append(f"Task {task['id']} depends on unknown task {dep}")

    if errors:
        print("Validation FAILED:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("Validation passed.")


def list_tasks(phase_id: str = None):
    """List tasks, optionally filtered by phase."""
    tasks_data = load_json(TASKS_FILE)
    phases_data = load_json(PHASES_FILE)

    if phase_id:
        phase = next((p for p in phases_data["phases"] if p["id"] == phase_id), None)
        if not phase:
            print(f"Phase {phase_id} not found.", file=sys.stderr)
            sys.exit(1)
        task_ids = set(phase["task_ids"])
        tasks = [t for t in tasks_data["tasks"] if t["id"] in task_ids]
    else:
        tasks = tasks_data["tasks"]

    for t in tasks:
        print(json.dumps(t, indent=2, ensure_ascii=False))
        print("---")


def usage():
    print(f"""Usage: {sys.argv[0]} <command> [args]

Commands:
  init                    Initialize artifact directory
  status                  Show pipeline and task progress
  complete <task-id>      Mark a task as done
  validate                Check artifact pipeline integrity
  tasks [phase-id]        List tasks (optionally for a specific phase)
""")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "init":
        init()
    elif cmd == "status":
        show_status()
    elif cmd == "complete" and len(sys.argv) > 2:
        complete_task(sys.argv[2])
    elif cmd == "validate":
        validate()
    elif cmd == "tasks":
        phase_id = sys.argv[2] if len(sys.argv) > 2 else None
        list_tasks(phase_id)
    else:
        usage()
        sys.exit(1)
