import copy
import importlib.util
import json
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("validate_way_direction.py")
SPEC = importlib.util.spec_from_file_location("validate_way_direction", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def active_block():
    directions = [{"id": f"direction-{i}", "title": f"Direction {i}"} for i in range(1, 7)]
    task = {
        "id": "task-1",
        "title": "First task",
        "linked_direction_ids": ["direction-1"],
        "why_helpful": "Moves the selected direction",
        "next_action": "Take one observable step",
        "done_criteria": "Observable result exists",
        "status": "PROPOSED",
        "hypothesis": None,
    }
    tasks = [
        dict(task, id=f"task-{i}", linked_direction_ids=["direction-1" if i <= 3 else "direction-2"])
        for i in range(1, 7)
    ]
    return {
        "phase": "ACTIVE",
        "offered_directions": directions,
        "selected_direction_ids": ["direction-1", "direction-2"],
        "background_tasks": tasks,
        "main_task_ids": ["task-1", "task-4", "task-5"],
        "open_main_slots": 0,
    }


class WayDirectionValidatorTests(unittest.TestCase):
    def test_template_not_started_is_valid(self):
        template = json.loads(
            (MODULE_PATH.parent.parent / "releases" / "alpha-007" / "templates" / "STATE_SAVE.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(MODULE.validate_way_direction(template), [])

    def test_valid_active_structure(self):
        self.assertEqual(MODULE.validate_way_direction({"way_direction": active_block()}), [])

    def test_active_allows_shorter_offered_list_but_requires_two_three(self):
        block = active_block()
        block["offered_directions"].pop()
        block["selected_direction_ids"].pop()
        block["background_tasks"].pop()
        block["main_task_ids"].pop()
        block["open_main_slots"] = 0
        errors = MODULE.validate_way_direction({"way_direction": block})
        self.assertFalse(any("offered directions" in error for error in errors))
        self.assertTrue(any("exactly 2" in error for error in errors))
        self.assertTrue(any("exactly 6" in error for error in errors))
        self.assertTrue(any("plus open main slots" in error for error in errors))

    def test_offered_phase_accepts_one_to_five_honest_directions(self):
        block = active_block()
        block["phase"] = "OFFERED"
        block["offered_directions"] = block["offered_directions"][:4]
        block["selected_direction_ids"] = []
        block["background_tasks"] = []
        block["main_task_ids"] = []
        block["open_main_slots"] = 3
        self.assertEqual(MODULE.validate_way_direction({"way_direction": block}), [])

    def test_offered_phase_rejects_empty_list(self):
        block = {"phase": "OFFERED", "offered_directions": [], "selected_direction_ids": [], "background_tasks": [], "main_task_ids": [], "open_main_slots": 3}
        errors = MODULE.validate_way_direction({"way_direction": block})
        self.assertTrue(any("1 to 6" in error for error in errors))

    def test_task_must_link_to_selected_direction(self):
        block = active_block()
        block["background_tasks"][0]["linked_direction_ids"] = ["direction-6"]
        errors = MODULE.validate_way_direction({"way_direction": block})
        self.assertTrue(any("unselected directions" in error for error in errors))

    def test_hypothesis_must_be_explicit(self):
        block = active_block()
        block["background_tasks"][0]["hypothesis"] = {"status": "FACT", "text": "avoidance"}
        errors = MODULE.validate_way_direction({"way_direction": block})
        self.assertTrue(any("must equal HYPOTHESIS" in error for error in errors))

    def test_each_direction_owns_three_background_tasks(self):
        block = active_block()
        block["background_tasks"][2]["linked_direction_ids"] = ["direction-2"]
        errors = MODULE.validate_way_direction({"way_direction": block})
        self.assertTrue(any("own exactly 3" in error for error in errors))

    def test_main_three_cover_both_directions(self):
        block = active_block()
        block["main_task_ids"] = ["task-1", "task-2", "task-3"]
        errors = MODULE.validate_way_direction({"way_direction": block})
        self.assertTrue(any("at least one" in error for error in errors))

    def test_done_slot_may_remain_open_without_autoactivation(self):
        block = active_block()
        block["main_task_ids"] = ["task-4", "task-5"]
        block["open_main_slots"] = 1
        self.assertEqual(MODULE.validate_way_direction({"way_direction": block}), [])


if __name__ == "__main__":
    unittest.main()
