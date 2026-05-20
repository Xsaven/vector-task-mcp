"""
Live placeholder substitution on every task_update (v1.8.8)
============================================================

When the user edits ``task.md`` mid-development and pastes an unrendered
token like ``{task.id}`` or ``{date}`` into their notes, the next
``task_update`` call (regardless of which field is being updated) must
materialise it with the current value.

The substitution is regex-based (NOT ``str.format``) so unrelated
curly-brace content — JSON snippets, code samples, unknown placeholders
like ``{task.priority}`` — is preserved byte-for-byte.
"""

import re
from pathlib import Path
from unittest.mock import patch

import pytest

from src.task_folder import TaskFolderManager, _substitute_placeholders
from src.task_store import TaskStore


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def folder_root(tmp_path: Path) -> Path:
    folder = tmp_path / "tasks_root"
    folder.mkdir()
    return folder


@pytest.fixture
def working_dir(tmp_path: Path) -> Path:
    wd = tmp_path / "wd"
    wd.mkdir()
    return wd


@pytest.fixture
def mgr(folder_root: Path, working_dir: Path) -> TaskFolderManager:
    return TaskFolderManager(task_folder_root=folder_root, working_dir=working_dir)


@pytest.fixture
def store_with_folder(
    temp_db_path: Path, folder_root: Path, working_dir: Path, mock_embedding_model
) -> TaskStore:
    with patch("src.task_store.get_embedding_model", return_value=mock_embedding_model):
        store = TaskStore(
            db_path=temp_db_path,
            task_folder=folder_root,
            working_dir=working_dir,
        )
        store._ensure_db_initialized_sync()
        yield store


# =============================================================================
# _substitute_placeholders — pure function
# =============================================================================

class TestSubstitutePlaceholders:
    def test_substitutes_task_id(self):
        out = _substitute_placeholders("ID is {task.id}", "T", 42, "FEAT-1")
        assert out == "ID is 42"

    def test_substitutes_task_title(self):
        out = _substitute_placeholders("# {task.title}", "Hello", 1, "X-1")
        assert out == "# Hello"

    def test_substitutes_task_code(self):
        out = _substitute_placeholders("Code: {task.code}", "T", 1, "OLOM-460")
        assert out == "Code: OLOM-460"

    def test_substitutes_date(self):
        out = _substitute_placeholders("Date: {date}", "T", 1, "X-1")
        assert re.fullmatch(r"Date: \d{4}-\d{2}-\d{2}", out)

    def test_substitutes_datetime(self):
        out = _substitute_placeholders("DT: {datetime}", "T", 1, "X-1")
        assert re.match(r"DT: \d{4}-\d{2}-\d{2}T", out)

    def test_unknown_placeholder_untouched(self):
        # {task.priority} is NOT in the known set — left intact.
        out = _substitute_placeholders(
            "Priority: {task.priority}", "T", 1, "X-1"
        )
        assert "{task.priority}" in out

    def test_json_snippet_untouched(self):
        # User pasted a JSON example with curly braces — must survive.
        text = 'Example: {"foo": "bar", "n": 42}'
        out = _substitute_placeholders(text, "T", 1, "X-1")
        assert out == text

    def test_code_sample_untouched(self):
        text = "```python\ndef f(x): return {'k': x}\n```"
        out = _substitute_placeholders(text, "T", 1, "X-1")
        assert out == text

    def test_multiple_placeholders_in_one_text(self):
        out = _substitute_placeholders(
            "# {task.title}\nID: {task.id}\nCode: {task.code}",
            "Title", 99, "FEAT-99"
        )
        assert "# Title" in out
        assert "ID: 99" in out
        assert "Code: FEAT-99" in out

    def test_no_placeholders_returns_same(self):
        text = "plain text, nothing to substitute"
        out = _substitute_placeholders(text, "T", 1, "X-1")
        assert out == text


# =============================================================================
# refresh_placeholders — manager method
# =============================================================================

class TestRefreshPlaceholders:
    def test_refresh_writes_back_when_changed(
        self, mgr: TaskFolderManager, folder_root: Path
    ):
        mgr.create_folder("FEAT-1", "T", 42)
        # User edits task.md and pastes unrendered placeholders.
        (folder_root / "FEAT-1" / "task.md").write_text(
            "# Notes\nLink: task #{task.id} title={task.title}\n",
            encoding="utf-8",
        )

        changed = mgr.refresh_placeholders("FEAT-1", "T", 42)

        assert changed is True
        content = (folder_root / "FEAT-1" / "task.md").read_text(encoding="utf-8")
        assert "Link: task #42 title=T" in content

    def test_refresh_noop_when_no_placeholders(
        self, mgr: TaskFolderManager, folder_root: Path
    ):
        mgr.create_folder("FEAT-2", "T", 1)
        # Overwrite task.md with content that has no known placeholders.
        (folder_root / "FEAT-2" / "task.md").write_text(
            "# Final\nNo tokens here.\n", encoding="utf-8"
        )

        changed = mgr.refresh_placeholders("FEAT-2", "T", 1)

        assert changed is False  # unchanged

    def test_refresh_missing_folder_returns_false(
        self, mgr: TaskFolderManager
    ):
        assert mgr.refresh_placeholders("NONE-1", "T", 1) is False

    def test_refresh_missing_task_md_returns_false(
        self, mgr: TaskFolderManager, folder_root: Path
    ):
        (folder_root / "FEAT-3").mkdir()
        # No task.md
        assert mgr.refresh_placeholders("FEAT-3", "T", 1) is False

    def test_refresh_resolves_in_archive_position(
        self, mgr: TaskFolderManager, folder_root: Path
    ):
        # Folder might be at Archive when refresh runs (status=done).
        mgr.create_folder("FEAT-4", "T", 7)
        mgr.rename_on_done("FEAT-4")
        archive_md = folder_root / "Archive" / "FEAT-4" / "task.md"
        archive_md.write_text(
            "id={task.id} code={task.code}\n", encoding="utf-8"
        )

        changed = mgr.refresh_placeholders("FEAT-4", "T", 7)

        assert changed is True
        assert "id=7 code=FEAT-4" in archive_md.read_text(encoding="utf-8")


# =============================================================================
# Integration — task_update fires refresh on every call
# =============================================================================

class TestUpdateHookFiresRefresh:
    def test_status_update_resolves_pending_placeholders(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        result = store_with_folder.create_task(
            title="Live", content="x", tags=["feature"], code="LIVE-1"
        )
        # User edits task.md with placeholders.
        (folder_root / "LIVE-1" / "task.md").write_text(
            "Title: {task.title}\nID: {task.id}\nCode: {task.code}\n",
            encoding="utf-8",
        )

        # ANY update — even just a status change — should refresh.
        store_with_folder.update_task(
            task_id=result["task_id"], status="in_progress"
        )

        content = (folder_root / "LIVE-1" / "task.md").read_text(encoding="utf-8")
        assert "Title: Live" in content
        assert f"ID: {result['task_id']}" in content
        assert "Code: LIVE-1" in content

    def test_title_update_reflects_in_existing_placeholders(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        result = store_with_folder.create_task(
            title="Original", content="x", tags=["feature"], code="LIVE-2"
        )
        (folder_root / "LIVE-2" / "task.md").write_text(
            "Title: {task.title}\n", encoding="utf-8"
        )

        # First refresh after title change — should pick up NEW title.
        store_with_folder.update_task(
            task_id=result["task_id"], title="Renamed"
        )

        content = (folder_root / "LIVE-2" / "task.md").read_text(encoding="utf-8")
        assert "Title: Renamed" in content

    def test_refresh_preserves_user_notes(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        result = store_with_folder.create_task(
            title="T", content="x", tags=["feature"], code="LIVE-3"
        )
        # User adds notes WITH a placeholder AND JSON example.
        original = (
            "# Notes\n\n"
            "Working on task {task.id}.\n\n"
            "## Example response\n"
            '```json\n{"id": 42, "nested": {"flag": true}}\n```\n\n'
            "## TODO\n- step 1\n- step 2\n"
        )
        (folder_root / "LIVE-3" / "task.md").write_text(original, encoding="utf-8")

        store_with_folder.update_task(
            task_id=result["task_id"], status="in_progress"
        )

        content = (folder_root / "LIVE-3" / "task.md").read_text(encoding="utf-8")
        # Placeholder substituted.
        assert f"Working on task {result['task_id']}." in content
        # JSON snippet preserved byte-for-byte.
        assert '```json\n{"id": 42, "nested": {"flag": true}}\n```' in content
        # User TODO section preserved.
        assert "## TODO\n- step 1\n- step 2" in content

    def test_subtask_update_no_fs_effect(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        root = store_with_folder.create_task(
            title="Root", content="x", tags=["feature"], code="LIVE-4"
        )
        sub = store_with_folder.create_task(
            title="Sub", content="y", tags=["feature"],
            parent_id=root["task_id"], code="SUBLIVE-4"
        )
        # Edit ROOT's task.md (subtask has no folder).
        (folder_root / "LIVE-4" / "task.md").write_text(
            "ID: {task.id}\n", encoding="utf-8"
        )

        # Update subtask — must NOT refresh root's task.md (different task).
        store_with_folder.update_task(
            task_id=sub["task_id"], status="in_progress"
        )

        # Root's task.md still has the unresolved placeholder.
        content = (folder_root / "LIVE-4" / "task.md").read_text(encoding="utf-8")
        assert "ID: {task.id}" in content

    def test_unknown_placeholder_persists_across_refresh(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        result = store_with_folder.create_task(
            title="T", content="x", tags=["feature"], code="LIVE-5"
        )
        (folder_root / "LIVE-5" / "task.md").write_text(
            "ID: {task.id}\nPriority: {task.priority}\n", encoding="utf-8"
        )

        store_with_folder.update_task(
            task_id=result["task_id"], status="in_progress"
        )

        content = (folder_root / "LIVE-5" / "task.md").read_text(encoding="utf-8")
        # Known placeholder resolved.
        assert f"ID: {result['task_id']}" in content
        # Unknown placeholder left intact for future use.
        assert "{task.priority}" in content
