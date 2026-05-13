"""
Integration: task_update folder rename/archive on status transitions (task #214)
=================================================================================

Tests TaskStore.update_task hooks that call TaskFolderManager rename/archive
methods on root-task status transitions:
- * → completed         → rename_on_completed (folder → {code}-on-review)
- * → done              → rename_on_done (folder → Archive/{code})
- completed → in_progress (revert) → revert_on_completed
- any other transition  → no-op

Resilience contract: an FS failure during a folder operation must NOT block
the DB status update — the row is already committed before the hook runs.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

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
def store_with_folder(
    temp_db_path: Path, folder_root: Path, working_dir: Path, mock_embedding_model
) -> TaskStore:
    """TaskStore with --task-folder enabled (folder_mgr instantiated)."""
    with patch("src.task_store.get_embedding_model", return_value=mock_embedding_model):
        store = TaskStore(
            db_path=temp_db_path,
            task_folder=folder_root,
            working_dir=working_dir,
        )
        store._ensure_db_initialized_sync()
        yield store


def _walk_to(store: TaskStore, task_id: int, target: str) -> None:
    """Drive a task through the lifecycle to reach `target` status."""
    sequence = ["in_progress", "completed", "tested", "validated"]
    for s in sequence:
        store.update_task(task_id=task_id, status=s)
        if s == target:
            return


# =============================================================================
# Transition matrix — feature ON
# =============================================================================

class TestUpdateTransitionsFeatureOn:
    def test_pending_to_in_progress_no_folder_change(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        result = store_with_folder.create_task(
            title="A", content="x", tags=["feature"]
        )
        code = result["code"]
        assert (folder_root / code).is_dir()

        store_with_folder.update_task(task_id=result["task_id"], status="in_progress")
        # Folder name unchanged.
        assert (folder_root / code).is_dir()
        assert not (folder_root / f"{code}-on-review").exists()

    def test_in_progress_to_completed_renames_to_on_review(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        result = store_with_folder.create_task(
            title="B", content="x", tags=["feature"]
        )
        code = result["code"]
        # Add side-content so folder is NOT empty-template-only — the
        # post-1.8.6 rule would otherwise DELETE an empty folder at the
        # completed transition instead of renaming.
        (folder_root / code / "notes.md").write_text("note", encoding="utf-8")

        store_with_folder.update_task(task_id=result["task_id"], status="in_progress")
        store_with_folder.update_task(task_id=result["task_id"], status="completed")

        assert not (folder_root / code).exists()
        assert (folder_root / f"{code}-on-review").is_dir()

    def test_completed_to_done_archives(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        result = store_with_folder.create_task(
            title="C", content="x", tags=["feature"]
        )
        code = result["code"]
        # Marker file keeps the folder out of the empty-delete fast-path.
        (folder_root / code / "notes.md").write_text("note", encoding="utf-8")
        _walk_to(store_with_folder, result["task_id"], "completed")
        # Source: {code}-on-review (after rename_on_completed).
        assert (folder_root / f"{code}-on-review").is_dir()

        store_with_folder.update_task(task_id=result["task_id"], status="done")

        archive = folder_root / "Archive" / code
        assert archive.is_dir()
        assert (archive / "task.md").is_file()
        # Old -on-review folder gone after move; no leftover {code}/ container.
        assert not (folder_root / f"{code}-on-review").exists()
        assert not (folder_root / code).exists()

    def test_tested_to_done_archives(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        result = store_with_folder.create_task(
            title="D", content="x", tags=["feature"]
        )
        code = result["code"]
        (folder_root / code / "notes.md").write_text("note", encoding="utf-8")
        _walk_to(store_with_folder, result["task_id"], "tested")
        store_with_folder.update_task(task_id=result["task_id"], status="done")
        assert (folder_root / "Archive" / code).is_dir()

    def test_validated_to_done_archives(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        result = store_with_folder.create_task(
            title="E", content="x", tags=["feature"]
        )
        code = result["code"]
        (folder_root / code / "notes.md").write_text("note", encoding="utf-8")
        _walk_to(store_with_folder, result["task_id"], "validated")
        store_with_folder.update_task(task_id=result["task_id"], status="done")
        assert (folder_root / "Archive" / code).is_dir()

    def test_completed_to_in_progress_reverts(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        result = store_with_folder.create_task(
            title="F", content="x", tags=["feature"]
        )
        code = result["code"]
        (folder_root / code / "notes.md").write_text("note", encoding="utf-8")
        _walk_to(store_with_folder, result["task_id"], "completed")
        assert (folder_root / f"{code}-on-review").is_dir()

        store_with_folder.update_task(task_id=result["task_id"], status="in_progress")

        assert (folder_root / code).is_dir()
        assert not (folder_root / f"{code}-on-review").exists()

    def test_completed_to_tested_no_rename(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        # Once at -on-review, going further to tested/validated must NOT rename.
        result = store_with_folder.create_task(
            title="G", content="x", tags=["feature"]
        )
        code = result["code"]
        (folder_root / code / "notes.md").write_text("note", encoding="utf-8")
        _walk_to(store_with_folder, result["task_id"], "completed")

        store_with_folder.update_task(task_id=result["task_id"], status="tested")

        # Still in -on-review state.
        assert (folder_root / f"{code}-on-review").is_dir()
        assert not (folder_root / code).exists()

    def test_completed_to_validated_no_rename(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        result = store_with_folder.create_task(
            title="H", content="x", tags=["feature"]
        )
        code = result["code"]
        (folder_root / code / "notes.md").write_text("note", encoding="utf-8")
        _walk_to(store_with_folder, result["task_id"], "completed")

        store_with_folder.update_task(task_id=result["task_id"], status="tested")
        store_with_folder.update_task(task_id=result["task_id"], status="validated")

        # Still in -on-review state.
        assert (folder_root / f"{code}-on-review").is_dir()
        assert not (folder_root / code).exists()


# =============================================================================
# Predicates that suppress the hook
# =============================================================================

class TestPredicateSuppression:
    def test_subtask_transitions_no_folder_ops(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        # Root + child. Walk child through completed → done; the child's code
        # MUST NOT produce folder side-effects (parent_id != None predicate).
        root = store_with_folder.create_task(
            title="Root", content="x", tags=["feature"]
        )
        child = store_with_folder.create_task(
            title="Child",
            content="y",
            tags=["feature"],
            parent_id=root["task_id"],
        )
        child_code = child["code"]
        # No folder for child — only root has one.
        assert not (folder_root / child_code).exists()

        # Walk child to done. None of these should produce a folder for the child.
        _walk_to(store_with_folder, child["task_id"], "validated")
        store_with_folder.update_task(task_id=child["task_id"], status="done")

        # Child must not appear at any of the three layout positions.
        assert not (folder_root / child_code).exists()
        assert not (folder_root / f"{child_code}-on-review").exists()
        assert not (folder_root / "Archive" / child_code).exists()

    def test_feature_off_no_fs_calls(
        self, task_store, monkeypatch
    ):
        # task_store fixture builds TaskStore WITHOUT task_folder → folder_mgr=None.
        # Even without monkeypatching, no hook runs. Sanity-check via attribute.
        assert task_store.folder_mgr is None
        result = task_store.create_task(
            title="Off", content="x", tags=["feature"]
        )
        # Walk through completed and done. No exception, no AttributeError.
        for s in ("in_progress", "completed", "tested", "validated", "done"):
            task_store.update_task(task_id=result["task_id"], status=s)
        # Still no folder_mgr.
        assert task_store.folder_mgr is None

    def test_legacy_task_without_code_skipped(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        # Insert a legacy row directly (NULL code) — emulate pre-#209 data.
        conn = store_with_folder._get_connection()
        try:
            cursor = conn.execute(
                'INSERT INTO tasks (parent_id, status, title, content, '
                'content_hash, created_at, code) '
                'VALUES (?, ?, ?, ?, ?, ?, NULL)',
                (None, "in_progress", "Legacy", "old", "legacy_t214",
                 "2020-01-01T00:00:00"),
            )
            legacy_id = cursor.lastrowid
            # Backfill task_vectors row to satisfy update_task's later regen path
            # if it triggers (it does not for a status-only update, but be safe).
            conn.commit()
        finally:
            conn.close()

        # Walk legacy through completed → done. No folder ops should fire.
        store_with_folder.update_task(task_id=legacy_id, status="completed")
        store_with_folder.update_task(task_id=legacy_id, status="done")

        # Folder root must contain NO entry — no code, no folder.
        # (The store also has no folder for this task because no code exists.)
        assert not any(folder_root.iterdir())


# =============================================================================
# Resilience — FS failure does not break status update
# =============================================================================

class TestResilienceFsFailure:
    def test_rename_failure_does_not_block_status_update(
        self, store_with_folder: TaskStore, monkeypatch
    ):
        from src.task_folder import TaskFolderManager

        def boom(self, *args, **kwargs):
            raise OSError("simulated rename failure")

        result = store_with_folder.create_task(
            title="Crash", content="x", tags=["feature"]
        )
        tid = result["task_id"]
        store_with_folder.update_task(task_id=tid, status="in_progress")

        monkeypatch.setattr(TaskFolderManager, "rename_on_completed", boom)

        # Status MUST still flip to completed despite the FS exception.
        update_result = store_with_folder.update_task(task_id=tid, status="completed")
        assert update_result["success"] is True
        task = store_with_folder.get_task_by_id(tid)
        assert task.status == "completed"

    def test_archive_failure_does_not_block_done_transition(
        self, store_with_folder: TaskStore, monkeypatch
    ):
        from src.task_folder import TaskFolderManager

        def boom(self, *args, **kwargs):
            raise OSError("simulated archive failure")

        result = store_with_folder.create_task(
            title="ArchiveCrash", content="x", tags=["feature"]
        )
        tid = result["task_id"]
        _walk_to(store_with_folder, tid, "completed")

        monkeypatch.setattr(TaskFolderManager, "rename_on_done", boom)

        update_result = store_with_folder.update_task(task_id=tid, status="done")
        assert update_result["success"] is True
        task = store_with_folder.get_task_by_id(tid)
        assert task.status == "done"