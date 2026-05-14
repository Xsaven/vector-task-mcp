"""
``init_folder`` flag on task_update (v1.8.7)
============================================

A boolean flag that re-creates the on-disk folder for a ROOT task at the
lifecycle position matching its CURRENT status. Used to recover folders
that were deleted via the empty-template fast-path (1.8.6) or never
created (e.g. ``--task-folder`` enabled after task creation).

Position mapping (single-task case; aggregate sync can move further):
- pending / in_progress / draft → ``{code}/``
- completed / tested / validated → ``{code}-on-review/``
- done → ``Archive/{code}/``
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from src.task_store import TaskStore


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
    with patch("src.task_store.get_embedding_model", return_value=mock_embedding_model):
        store = TaskStore(
            db_path=temp_db_path,
            task_folder=folder_root,
            working_dir=working_dir,
        )
        store._ensure_db_initialized_sync()
        yield store


# =============================================================================
# Recovery scenarios — folder previously deleted / never existed
# =============================================================================

class TestInitFolderRecovery:
    def test_init_after_empty_template_delete_pending(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        # Task created → walked to completed → folder DELETED (1.8.6).
        result = store_with_folder.create_task(
            title="Recover me", content="x", tags=["feature"]
        )
        tid = result["task_id"]
        code = result["code"]
        store_with_folder.update_task(task_id=tid, status="in_progress")
        store_with_folder.update_task(task_id=tid, status="completed")
        # Folder gone (empty-template fast-path).
        assert not (folder_root / code).exists()
        assert not (folder_root / f"{code}-on-review").exists()

        # User wants the folder back. Revert to in_progress + init.
        store_with_folder.update_task(
            task_id=tid, status="in_progress", init_folder=True
        )
        # Folder back at active position.
        assert (folder_root / code).is_dir()
        assert (folder_root / code / "task.md").is_file()

    def test_init_on_already_existing_folder_is_no_op(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        result = store_with_folder.create_task(
            title="Existing", content="x", tags=["feature"]
        )
        tid = result["task_id"]
        code = result["code"]
        # Add side-content so we can detect any rewrite of task.md.
        (folder_root / code / "user.md").write_text("user", encoding="utf-8")

        # init_folder=True while folder is at correct position → adopts.
        store_with_folder.update_task(task_id=tid, init_folder=True)

        # Side-file preserved; folder untouched.
        assert (folder_root / code / "user.md").read_text(encoding="utf-8") == "user"
        assert (folder_root / code).is_dir()


# =============================================================================
# Position by status
# =============================================================================

class TestInitFolderPositionByStatus:
    def test_pending_creates_at_active(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        result = store_with_folder.create_task(
            title="Pending init", content="x", tags=["feature"], code="INIT-1"
        )
        # Delete folder externally to simulate "never created".
        import shutil
        shutil.rmtree(folder_root / "INIT-1")

        store_with_folder.update_task(task_id=result["task_id"], init_folder=True)
        assert (folder_root / "INIT-1").is_dir()

    def test_init_with_completed_status_lands_on_review(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        # Create + walk to completed + delete (would happen with empty).
        result = store_with_folder.create_task(
            title="On-review init", content="x", tags=["feature"], code="INIT-2"
        )
        tid = result["task_id"]
        store_with_folder.update_task(task_id=tid, status="in_progress")
        store_with_folder.update_task(task_id=tid, status="completed")
        # Empty folder deleted at completed.
        assert not (folder_root / "INIT-2-on-review").exists()

        # Init while status is completed → on-review.
        store_with_folder.update_task(task_id=tid, init_folder=True)
        assert (folder_root / "INIT-2-on-review").is_dir()

    def test_init_with_done_status_lands_in_archive(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        result = store_with_folder.create_task(
            title="Archive init", content="x", tags=["feature"], code="INIT-3"
        )
        tid = result["task_id"]
        for s in ("in_progress", "completed", "tested", "validated", "done"):
            store_with_folder.update_task(task_id=tid, status=s)
        # Empty folder deleted.
        assert not (folder_root / "Archive" / "INIT-3").exists()

        # Init while status is done → Archive/INIT-3.
        store_with_folder.update_task(task_id=tid, init_folder=True)
        assert (folder_root / "Archive" / "INIT-3").is_dir()
        assert not (folder_root / "INIT-3").exists()
        assert not (folder_root / "INIT-3-on-review").exists()

    def test_init_combined_with_status_change(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        # init_folder + status=completed in ONE call → folder lands at
        # -on-review (the FINAL status's position).
        result = store_with_folder.create_task(
            title="Combo", content="x", tags=["feature"], code="INIT-4"
        )
        tid = result["task_id"]
        # Delete the folder so init has work to do.
        import shutil
        shutil.rmtree(folder_root / "INIT-4")

        store_with_folder.update_task(
            task_id=tid, status="in_progress", init_folder=True
        )
        # status change pending → in_progress + init_folder requested.
        assert (folder_root / "INIT-4").is_dir()


# =============================================================================
# Predicate suppression
# =============================================================================

class TestInitFolderPredicates:
    def test_init_subtask_no_fs_effect(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        root = store_with_folder.create_task(
            title="Root", content="x", tags=["feature"], code="ROOT-1"
        )
        sub = store_with_folder.create_task(
            title="Sub", content="y", tags=["feature"],
            parent_id=root["task_id"], code="SUB-1"
        )
        # No folder for SUB-1 (subtasks don't have folders).
        assert not (folder_root / "SUB-1").exists()

        store_with_folder.update_task(task_id=sub["task_id"], init_folder=True)
        # Still no folder.
        assert not (folder_root / "SUB-1").exists()
        assert not (folder_root / "SUB-1-on-review").exists()
        assert not (folder_root / "Archive" / "SUB-1").exists()

    def test_init_feature_off_no_fs_effect(
        self, task_store
    ):
        # task_store fixture has no --task-folder → folder_mgr=None.
        result = task_store.create_task(
            title="No folder feature", content="x", tags=["feature"]
        )
        # Must NOT crash.
        update_result = task_store.update_task(
            task_id=result["task_id"], init_folder=True
        )
        assert update_result["success"] is True

    def test_init_without_code_no_fs_effect(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        # Insert a legacy NULL-code row directly to bypass auto-gen.
        import sqlite3
        db_path = store_with_folder.db_path
        conn = sqlite3.connect(str(db_path))
        try:
            cursor = conn.execute(
                "INSERT INTO tasks (parent_id, status, title, content, "
                "content_hash, created_at, code) "
                "VALUES (?, ?, ?, ?, ?, ?, NULL)",
                (None, "pending", "Legacy", "old",
                 "legacy_init_folder_test", "2020-01-01T00:00:00"),
            )
            legacy_id = cursor.lastrowid
            conn.commit()
        finally:
            conn.close()

        # init_folder on a NULL-code task → no-op (no code to anchor folder).
        result = store_with_folder.update_task(
            task_id=legacy_id, init_folder=True
        )
        assert result["success"] is True


# =============================================================================
# Aggregate interaction — init respects shared-code rules
# =============================================================================

class TestInitFolderAggregate:
    def test_init_respects_aggregate_when_sibling_active(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        # Two tasks share code; one is pending, one walks to done.
        a = store_with_folder.create_task(
            title="A", content="x", tags=["feature"], code="GROUP-1"
        )
        # Add content so A's folder survives (not the empty-delete path).
        (folder_root / "GROUP-1" / "shared.md").write_text("s", encoding="utf-8")
        b = store_with_folder.create_task(
            title="B", content="y", tags=["feature"], code="GROUP-1"
        )

        # Walk A to done (B still pending → folder stays at active).
        for s in ("in_progress", "completed", "tested", "validated", "done"):
            store_with_folder.update_task(task_id=a["task_id"], status=s)
        # Aggregate keeps folder at active because B is pending.
        assert (folder_root / "GROUP-1").is_dir()

        # init_folder on A (status=done) → would suggest Archive position,
        # but aggregate sync reasserts active because B is still pending.
        store_with_folder.update_task(task_id=a["task_id"], init_folder=True)
        assert (folder_root / "GROUP-1").is_dir()
        assert not (folder_root / "Archive" / "GROUP-1").exists()
