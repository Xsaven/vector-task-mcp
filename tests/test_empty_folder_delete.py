"""
Empty-template folder deletion (v1.8.6)
=======================================

When a task transitions to a non-active aggregate position (on-review or
archive) AND its on-disk folder contains only the unmodified rendered
template (1 file, ``task.md`` matches the rendered template byte-for-byte
after :meth:`str.strip`), delete the folder outright instead of renaming
to ``{code}-on-review/`` or ``Archive/{code}/``.

Rationale: pointless to maintain a "review" or "archive" shell for a task
whose folder holds zero work product.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from src.task_folder import TaskFolderManager
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


def _walk_to(store: TaskStore, task_id: int, target: str) -> None:
    sequence = ["in_progress", "completed", "tested", "validated"]
    for s in sequence:
        store.update_task(task_id=task_id, status=s)
        if s == target:
            return


# =============================================================================
# delete_if_empty_template — unit-level (TaskFolderManager only)
# =============================================================================

class TestDeleteIfEmptyTemplateUnit:
    def test_deletes_pristine_template_only_folder(
        self, mgr: TaskFolderManager, folder_root: Path
    ):
        mgr.create_folder("FEAT-1", "My Task", 42)
        assert (folder_root / "FEAT-1").is_dir()

        ok = mgr.delete_if_empty_template("FEAT-1", "My Task", 42)

        assert ok is True
        assert not (folder_root / "FEAT-1").exists()

    def test_keeps_folder_with_modified_task_md(
        self, mgr: TaskFolderManager, folder_root: Path
    ):
        mgr.create_folder("FEAT-2", "My Task", 42)
        # User edits task.md
        (folder_root / "FEAT-2" / "task.md").write_text(
            "# Hand-written\n\nProgress notes here.\n", encoding="utf-8"
        )

        ok = mgr.delete_if_empty_template("FEAT-2", "My Task", 42)
        assert ok is False
        assert (folder_root / "FEAT-2").is_dir()

    def test_keeps_folder_with_extra_files(
        self, mgr: TaskFolderManager, folder_root: Path
    ):
        mgr.create_folder("FEAT-3", "My Task", 42)
        (folder_root / "FEAT-3" / "notes.md").write_text("note", encoding="utf-8")

        ok = mgr.delete_if_empty_template("FEAT-3", "My Task", 42)
        assert ok is False
        assert (folder_root / "FEAT-3").is_dir()

    def test_keeps_folder_with_nested_files(
        self, mgr: TaskFolderManager, folder_root: Path
    ):
        mgr.create_folder("FEAT-4", "My Task", 42)
        sub = folder_root / "FEAT-4" / "screenshots"
        sub.mkdir()
        (sub / "img.png").write_text("img", encoding="utf-8")

        ok = mgr.delete_if_empty_template("FEAT-4", "My Task", 42)
        assert ok is False
        assert (folder_root / "FEAT-4").is_dir()

    def test_returns_false_when_no_folder(
        self, mgr: TaskFolderManager
    ):
        ok = mgr.delete_if_empty_template("MISSING-1", "T", 1)
        assert ok is False

    def test_trim_tolerant_match(
        self, mgr: TaskFolderManager, folder_root: Path
    ):
        # If task.md has stray whitespace at start/end, strip-comparison
        # still matches.
        mgr.create_folder("FEAT-5", "T", 5)
        current = (folder_root / "FEAT-5" / "task.md").read_text(encoding="utf-8")
        (folder_root / "FEAT-5" / "task.md").write_text(
            "\n\n  " + current + "\n\n ", encoding="utf-8"
        )

        ok = mgr.delete_if_empty_template("FEAT-5", "T", 5)
        assert ok is True
        assert not (folder_root / "FEAT-5").exists()

    def test_deletes_on_review_position(
        self, mgr: TaskFolderManager, folder_root: Path
    ):
        # Folder might be at -on-review when delete_if_empty is called from
        # the archive transition path.
        mgr.create_folder("FEAT-6", "T", 6)
        mgr.rename_on_completed("FEAT-6")
        assert (folder_root / "FEAT-6-on-review").is_dir()

        ok = mgr.delete_if_empty_template("FEAT-6", "T", 6)
        assert ok is True
        assert not (folder_root / "FEAT-6-on-review").exists()

    def test_deletes_archive_position(
        self, mgr: TaskFolderManager, folder_root: Path
    ):
        mgr.create_folder("FEAT-7", "T", 7)
        mgr.rename_on_done("FEAT-7")
        assert (folder_root / "Archive" / "FEAT-7").is_dir()

        ok = mgr.delete_if_empty_template("FEAT-7", "T", 7)
        assert ok is True
        assert not (folder_root / "Archive" / "FEAT-7").exists()

    def test_custom_template_pristine_deletes(
        self, mgr: TaskFolderManager, folder_root: Path
    ):
        # Custom template — pristine task.md still matches re-render.
        (folder_root / "task-template.md").write_text(
            "# {task.title}\nCode: {task.code}\nID: {task.id}\n",
            encoding="utf-8",
        )
        mgr.create_folder("CUST-1", "Custom", 100)
        assert (folder_root / "CUST-1").is_dir()

        ok = mgr.delete_if_empty_template("CUST-1", "Custom", 100)
        assert ok is True
        assert not (folder_root / "CUST-1").exists()


# =============================================================================
# Integration — task lifecycle drives the deletion
# =============================================================================

class TestLifecycleEmptyDelete:
    def test_pending_to_completed_deletes_empty_folder(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        result = store_with_folder.create_task(
            title="A", content="x", tags=["feature"]
        )
        code = result["code"]
        assert (folder_root / code).is_dir()

        store_with_folder.update_task(task_id=result["task_id"], status="in_progress")
        store_with_folder.update_task(task_id=result["task_id"], status="completed")

        # Folder is gone — no -on-review shell created.
        assert not (folder_root / code).exists()
        assert not (folder_root / f"{code}-on-review").exists()

    def test_pending_to_completed_with_user_content_keeps_folder(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        result = store_with_folder.create_task(
            title="B", content="x", tags=["feature"]
        )
        code = result["code"]
        # User adds work product.
        (folder_root / code / "report.md").write_text("findings", encoding="utf-8")

        store_with_folder.update_task(task_id=result["task_id"], status="in_progress")
        store_with_folder.update_task(task_id=result["task_id"], status="completed")

        # Folder renamed to -on-review (user content preserved).
        assert (folder_root / f"{code}-on-review").is_dir()
        assert (folder_root / f"{code}-on-review" / "report.md").is_file()

    def test_walk_to_done_deletes_empty_folder(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        result = store_with_folder.create_task(
            title="C", content="x", tags=["feature"]
        )
        code = result["code"]
        for s in ("in_progress", "completed", "tested", "validated", "done"):
            store_with_folder.update_task(task_id=result["task_id"], status=s)

        # Folder deleted at completed transition; no Archive shell.
        assert not (folder_root / code).exists()
        assert not (folder_root / "Archive" / code).exists()

    def test_walk_to_done_with_content_archives(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        result = store_with_folder.create_task(
            title="D", content="x", tags=["feature"]
        )
        code = result["code"]
        (folder_root / code / "notes.md").write_text("notes", encoding="utf-8")

        for s in ("in_progress", "completed", "tested", "validated", "done"):
            store_with_folder.update_task(task_id=result["task_id"], status=s)

        # Folder content survived all the way to Archive.
        assert (folder_root / "Archive" / code / "notes.md").is_file()

    def test_shared_code_one_pristine_one_with_content_keeps(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        # Two tasks share code; one's content is in the folder (we don't
        # know "whose" content it is, but it's not pristine for either).
        # Aggregate flip to on-review must NOT delete.
        a = store_with_folder.create_task(
            title="A", content="x", tags=["feature"], code="DUO-9"
        )
        (folder_root / "DUO-9" / "shared.md").write_text("shared", encoding="utf-8")
        b = store_with_folder.create_task(
            title="B", content="y", tags=["feature"], code="DUO-9"
        )
        # Walk both to completed → aggregate flips to on-review.
        for tid in (a["task_id"], b["task_id"]):
            store_with_folder.update_task(task_id=tid, status="in_progress")
            store_with_folder.update_task(task_id=tid, status="completed")

        assert (folder_root / "DUO-9-on-review").is_dir()
        assert (folder_root / "DUO-9-on-review" / "shared.md").is_file()