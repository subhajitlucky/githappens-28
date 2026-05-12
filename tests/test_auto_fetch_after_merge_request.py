import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest import mock


def load_githappens_module(auto_fetch_after_merge_request):
    root = Path(__file__).resolve().parents[1]
    config_dir = root / "configs"
    config_dir.mkdir(exist_ok=True)
    (config_dir / "config.ini").write_text(
        "[DEFAULT]\n"
        "base_url=https://gitlab.example\n"
        "group_id=1\n"
        "custom_template=Custom\n"
        "GITLAB_TOKEN=test-token\n"
        "squash_commits=true\n"
        "delete_branch_after_merge=true\n"
        f"auto_fetch_after_merge_request={str(auto_fetch_after_merge_request).lower()}\n",
        encoding="utf-8",
    )
    (config_dir / "templates.json").write_text(
        '{"templates": [], "reviewers": []}',
        encoding="utf-8",
    )

    inquirer_stub = types.SimpleNamespace(
        prompt=mock.Mock(return_value={"estimated_time": ""}),
        Text=lambda *args, **kwargs: ("Text", args, kwargs),
        List=lambda *args, **kwargs: ("List", args, kwargs),
        Checkbox=lambda *args, **kwargs: ("Checkbox", args, kwargs),
    )
    sys.modules["inquirer"] = inquirer_stub

    spec = importlib.util.spec_from_file_location("gitHappens_under_test", root / "gitHappens.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AutoFetchAfterMergeRequestTest(unittest.TestCase):
    def test_fetches_origin_after_merge_request_when_setting_is_enabled(self):
        git_happens = load_githappens_module(auto_fetch_after_merge_request=True)
        created_issue = {"iid": 12, "title": "Fix broken thing"}
        created_branch = {"name": "12-fix-broken-thing"}
        created_merge_request = {
            "iid": 34,
            "title": "Fix broken thing",
            "source_branch": "12-fix-broken-thing",
        }

        with mock.patch.object(git_happens, "createIssue", return_value=created_issue), \
             mock.patch.object(git_happens, "create_branch", return_value=created_branch), \
             mock.patch.object(git_happens, "create_merge_request", return_value=created_merge_request), \
             mock.patch.object(git_happens.subprocess, "check_call") as check_call:
            result = git_happens.startIssueCreation(
                99,
                "Fix broken thing",
                False,
                False,
                False,
                {"labels": ["Bug"]},
                False,
            )

        self.assertEqual(result, created_issue)
        check_call.assert_called_once_with(["git", "fetch", "origin"])


if __name__ == "__main__":
    unittest.main()
