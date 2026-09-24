#!/usr/bin/env python3
"""Validate the WAY / DIRECTION · ПУТЬ / ЗАДАЧИ block in a P1AY SAVE."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PHASES = {"NOT_STARTED", "OFFERED", "SELECTED", "ACTIVE"}
TASK_STATUSES = {
    "PROPOSED", "ACTIVE", "WAITING", "IN_REVIEW", "DONE",
    "PAUSED", "BLOCKED", "CANCELLED",
}


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_way_direction(save: dict[str, Any]) -> list[str]:
    if not isinstance(save,dict):
        return ["SAVE must be an object"]
    candidate=save.get("way_direction")
    if isinstance(candidate,dict):
        if not isinstance(candidate.get("phase"),str):
            return ["way_direction.phase must be a string"]
        for key in ("selected_direction_ids","main_task_ids"):
            values=candidate.get(key,[])
            if isinstance(values,list) and any(not _nonempty(v) for v in values):
                return [f"way_direction.{key} must contain non-empty string IDs"]
        for key in ("offered_directions","background_tasks"):
            values=candidate.get(key,[])
            if isinstance(values,list):
                for item in values:
                    if isinstance(item,dict):
                        if not _nonempty(item.get("id")):
                            return [f"way_direction.{key} item ID must be a non-empty string"]
                        if key=="background_tasks":
                            if not isinstance(item.get("status"),str):
                                return ["task status must be a string"]
                            links=item.get("linked_direction_ids")
                            if not isinstance(links,list) or len(links)!=1 or not _nonempty(links[0]):
                                return ["each background task must have exactly one string direction ID"]
        if "open_main_slots" in candidate and type(candidate["open_main_slots"]) is not int:
            return ["open_main_slots must be an integer, not a boolean or other type"]
    errors: list[str] = []
    block = save.get("way_direction")
    if not isinstance(block, dict):
        return ["way_direction must be an object"]

    phase = block.get("phase")
    if phase not in PHASES:
        errors.append(f"way_direction.phase must be one of {sorted(PHASES)}")
        return errors

    offered = block.get("offered_directions", [])
    selected = block.get("selected_direction_ids", [])
    tasks = block.get("background_tasks", [])
    main_task_ids = block.get("main_task_ids", [])
    open_main_slots = block.get("open_main_slots", 3 if phase != "ACTIVE" else 0)
    if not isinstance(offered, list):
        errors.append("way_direction.offered_directions must be an array")
        offered = []
    if not isinstance(selected, list):
        errors.append("way_direction.selected_direction_ids must be an array")
        selected = []
    if not isinstance(tasks, list):
        errors.append("way_direction.background_tasks must be an array")
        tasks = []
    if not isinstance(main_task_ids, list):
        errors.append("way_direction.main_task_ids must be an array")
        main_task_ids = []

    direction_ids: list[str] = []
    for index, direction in enumerate(offered):
        path = f"way_direction.offered_directions[{index}]"
        if not isinstance(direction, dict):
            errors.append(f"{path} must be an object")
            continue
        direction_id = direction.get("id")
        if not _nonempty(direction_id):
            errors.append(f"{path}.id must be a non-empty string")
        else:
            direction_ids.append(direction_id)
        if not _nonempty(direction.get("title")):
            errors.append(f"{path}.title must be a non-empty string")

    if len(direction_ids) != len(set(direction_ids)):
        errors.append("offered direction ids must be unique")
    if len(selected) != len(set(selected)):
        errors.append("selected direction ids must be unique")
    unknown_selected = [item for item in selected if item not in set(direction_ids)]
    if unknown_selected:
        errors.append(f"selected directions are not offered: {unknown_selected}")

    if phase in {"OFFERED", "SELECTED", "ACTIVE"} and not 1 <= len(offered) <= 6:
        errors.append(f"phase {phase} requires 1 to 6 honestly supported offered directions")
    if phase in {"SELECTED", "ACTIVE"} and len(selected) != 2:
        errors.append(f"phase {phase} requires exactly 2 selected directions")
    if phase == "ACTIVE" and len(tasks) != 6:
        errors.append("phase ACTIVE requires exactly 6 background tasks")
    if phase == "ACTIVE" and (not isinstance(open_main_slots, int) or not 0 <= open_main_slots <= 3):
        errors.append("phase ACTIVE requires open_main_slots from 0 to 3")
    if phase == "ACTIVE" and isinstance(open_main_slots, int) and len(main_task_ids) + open_main_slots != 3:
        errors.append("main task ids plus open main slots must equal 3")
    if phase != "ACTIVE" and (tasks or main_task_ids):
        errors.append("background tasks and main task ids must stay empty until phase ACTIVE")

    task_ids: list[str] = []
    for index, task in enumerate(tasks):
        path = f"way_direction.background_tasks[{index}]"
        if not isinstance(task, dict):
            errors.append(f"{path} must be an object")
            continue
        task_id = task.get("id")
        if not _nonempty(task_id):
            errors.append(f"{path}.id must be a non-empty string")
        else:
            task_ids.append(task_id)
        links = task.get("linked_direction_ids")
        if not isinstance(links, list) or not links:
            errors.append(f"{path}.linked_direction_ids must be a non-empty array")
        else:
            invalid_links = [item for item in links if item not in set(selected)]
            if invalid_links:
                errors.append(f"{path} links to unselected directions: {invalid_links}")
        for field in ("title", "why_helpful", "next_action", "done_criteria"):
            if not _nonempty(task.get(field)):
                errors.append(f"{path}.{field} must be a non-empty string")
        if task.get("status") not in TASK_STATUSES:
            errors.append(f"{path}.status must be one of {sorted(TASK_STATUSES)}")
        hypothesis = task.get("hypothesis")
        if hypothesis is not None:
            if not isinstance(hypothesis, dict):
                errors.append(f"{path}.hypothesis must be an object or null")
            elif hypothesis.get("status") != "HYPOTHESIS":
                errors.append(f"{path}.hypothesis.status must equal HYPOTHESIS")

    if len(task_ids) != len(set(task_ids)):
        errors.append("task ids must be unique")
    if len(main_task_ids) != len(set(main_task_ids)):
        errors.append("main task ids must be unique")
    unknown_main = [item for item in main_task_ids if item not in set(task_ids)]
    if unknown_main:
        errors.append(f"main task ids are not background tasks: {unknown_main}")
    if phase == "ACTIVE":
        ownership = {direction_id: 0 for direction_id in selected}
        main_ownership = {direction_id: 0 for direction_id in selected}
        by_id = {task.get("id"): task for task in tasks if isinstance(task, dict)}
        for task in tasks:
            if isinstance(task, dict):
                links = task.get("linked_direction_ids", [])
                if isinstance(links, list) and len(links) == 1 and links[0] in ownership:
                    ownership[links[0]] += 1
        if any(count != 3 for count in ownership.values()):
            errors.append("each selected direction must own exactly 3 background tasks")
        for task_id in main_task_ids:
            task = by_id.get(task_id, {})
            if task.get("status") in {"DONE", "WAITING", "IN_REVIEW", "CANCELLED"}:
                errors.append("completed, waiting, review or cancelled tasks cannot occupy a main slot")
            links = task.get("linked_direction_ids", []) if isinstance(task, dict) else []
            if isinstance(links, list) and len(links) == 1 and links[0] in main_ownership:
                main_ownership[links[0]] += 1
        if open_main_slots == 0 and any(count < 1 for count in main_ownership.values()):
            errors.append("main tasks must include at least one task from each selected direction")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("save", type=Path, help="Path to a JSON SAVE")
    args = parser.parse_args()
    try:
        payload = json.loads(args.save.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    errors = validate_way_direction(payload)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("PASS: WAY / DIRECTION structure is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
