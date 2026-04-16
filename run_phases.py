#!/usr/bin/env python3
"""
run_phases.py — Execute tasks defined in .harness/phases.json and .harness/tasks.json.

This script reads the harness plan and prints each task that needs to be executed,
in the correct order (phase by phase, respecting dependencies).

It is designed to be called by Claude Code during Phase 4 of the harness skill.
Claude reads the output and implements each task.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

HARNESS_DIR = Path(".harness")
PHASES_FILE = HARNESS_DIR / "phases.json"
TASKS_FILE = HARNESS_DIR / "tasks.json"
LOG_FILE = HARNESS_DIR / "log.md"


def load_json(path: Path) -> dict:
    if not path.exists():
        print(f"Error: {path} not found. Run Phase 3 (Plan) first.", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


def save_json(path: Path, data: dict):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def append_log(message: str):
    with open(LOG_FILE, "a") as f:
        f.write(message + "\n")


def topological_sort(tasks: list[dict], task_ids: list[str]) -> list[dict]:
    """Sort tasks within a phase respecting depends_on."""
    task_map = {t["id"]: t for t in tasks}
    phase_tasks = [task_map[tid] for tid in task_ids if tid in task_map]

    sorted_tasks = []
    visited = set()

    def visit(task):
        if task["id"] in visited:
            return
        for dep_id in task.get("depends_on", []):
            if dep_id in task_map and dep_id not in visited:
                visit(task_map[dep_id])
        visited.add(task["id"])
        sorted_tasks.append(task)

    for t in phase_tasks:
        visit(t)

    return sorted_tasks


def main():
    phases_data = load_json(PHASES_FILE)
    tasks_data = load_json(TASKS_FILE)

    all_tasks = tasks_data["tasks"]
    task_index = {t["id"]: t for t in all_tasks}
    phases = phases_data["phases"]

    # Initialize log
    append_log(f"# Harness Execution Log")
    append_log(f"**Project**: {phases_data.get('project', 'Unknown')}")
    append_log(f"**Started**: {datetime.now().isoformat()}")
    append_log("")

    total_tasks = sum(len(p["task_ids"]) for p in phases)
    done_count = 0

    for phase in phases:
        phase_id = phase["id"]
        phase_name = phase["name"]

        print(f"\n{'='*60}")
        print(f"PHASE: {phase_name} ({phase_id})")
        print(f"Description: {phase['description']}")
        print(f"{'='*60}")
        append_log(f"## {phase_name}")
        append_log("")

        ordered_tasks = topological_sort(all_tasks, phase["task_ids"])

        for task in ordered_tasks:
            if task["status"] == "done":
                print(f"  [SKIP] {task['id']}: {task['title']} (already done)")
                done_count += 1
                continue

            print(f"\n--- TASK: {task['id']} ---")
            print(f"Title: {task['title']}")
            print(f"Description: {task['description']}")
            if task.get("files_to_create"):
                print(f"Files to create: {', '.join(task['files_to_create'])}")
            if task.get("files_to_modify"):
                print(f"Files to modify: {', '.join(task['files_to_modify'])}")
            if task.get("depends_on"):
                print(f"Depends on: {', '.join(task['depends_on'])}")
            print(f"Acceptance: {task['acceptance']}")
            print(f"---")

            # Mark as in-progress
            task_index[task["id"]]["status"] = "in_progress"
            save_json(TASKS_FILE, tasks_data)

            # The actual implementation is done by Claude after reading this output.
            # This script just orchestrates the order and status tracking.

            # Mark as done (Claude will call this script with --complete <task-id>)
            append_log(f"- [ ] **{task['id']}**: {task['title']}")

            done_count += 1

        append_log("")

    print(f"\n{'='*60}")
    print(f"All {total_tasks} tasks printed. Ready for implementation.")
    print(f"{'='*60}")

    append_log(f"**Completed**: {datetime.now().isoformat()}")


def complete_task(task_id: str):
    """Mark a task as done."""
    tasks_data = load_json(TASKS_FILE)
    for task in tasks_data["tasks"]:
        if task["id"] == task_id:
            task["status"] = "done"
            save_json(TASKS_FILE, tasks_data)
            print(f"Task {task_id} marked as done.")

            # Update log
            log_content = LOG_FILE.read_text()
            log_content = log_content.replace(
                f"- [ ] **{task_id}**:", f"- [x] **{task_id}**:"
            )
            LOG_FILE.write_text(log_content)
            return
    print(f"Task {task_id} not found.", file=sys.stderr)
    sys.exit(1)


def show_status():
    """Show current progress."""
    tasks_data = load_json(TASKS_FILE)
    phases_data = load_json(PHASES_FILE)

    total = len(tasks_data["tasks"])
    done = sum(1 for t in tasks_data["tasks"] if t["status"] == "done")
    in_progress = sum(1 for t in tasks_data["tasks"] if t["status"] == "in_progress")
    pending = total - done - in_progress

    print(f"Progress: {done}/{total} tasks done ({in_progress} in progress, {pending} pending)")
    print()

    for phase in phases_data["phases"]:
        phase_tasks = [t for t in tasks_data["tasks"] if t["id"] in phase["task_ids"]]
        phase_done = all(t["status"] == "done" for t in phase_tasks)
        icon = "v" if phase_done else ">"
        print(f"  [{icon}] {phase['name']}")
        for t in phase_tasks:
            status_icon = {"done": "v", "in_progress": ">", "pending": " "}[t["status"]]
            print(f"      [{status_icon}] {t['id']}: {t['title']}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--complete" and len(sys.argv) > 2:
            complete_task(sys.argv[2])
        elif cmd == "--status":
            show_status()
        else:
            print(f"Usage: {sys.argv[0]} [--complete <task-id> | --status]")
            sys.exit(1)
    else:
        main()
