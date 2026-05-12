import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path
from unittest import mock


def load_githappens_module():
    root = Path(__file__).resolve().parents[1]
    config_dir = root / "configs"
    config_dir.mkdir(exist_ok=True)
    (config_dir / "config.ini").write_text(
        "[DEFAULT]\n"
        "base_url=https://gitlab.example\n"
        "group_id=42\n"
        "custom_template=Custom\n"
        "GITLAB_TOKEN=test-token\n"
        "squash_commits=true\n"
        "delete_branch_after_merge=true\n",
        encoding="utf-8",
    )
    (config_dir / "templates.json").write_text(
        '{"templates": [], "reviewers": []}',
        encoding="utf-8",
    )

    sys.modules["inquirer"] = types.SimpleNamespace(
        prompt=mock.Mock(),
        Text=lambda *args, **kwargs: ("Text", args, kwargs),
        List=lambda *args, **kwargs: ("List", args, kwargs),
        Checkbox=lambda *args, **kwargs: ("Checkbox", args, kwargs),
    )

    spec = importlib.util.spec_from_file_location("gitHappens_under_test", root / "gitHappens.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EmptyMilestonesTest(unittest.TestCase):
    def test_current_milestone_returns_none_when_no_active_milestone_exists(self):
        git_happens = load_githappens_module()
        result = mock.Mock()
        result.stdout = json.dumps([
            {"id": 1, "title": "Past", "start_date": "2024-01-01", "due_date": "2024-01-31"},
            {"id": 2, "title": "Future", "start_date": "2099-01-01", "due_date": "2099-01-31"},
        ]).encode()

        with mock.patch.object(git_happens.subprocess, "run", return_value=result):
            milestone = git_happens.list_milestones(current=True)

        self.assertIsNone(milestone)


if __name__ == "__main__":
    unittest.main()
