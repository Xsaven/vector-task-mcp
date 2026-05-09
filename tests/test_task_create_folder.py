"""
Integration: task_create folder + task.md generation (task #213)
=================================================================

Tests TaskStore.create_task and create_tasks_bulk hooks that wire
TaskFolderManager into the create path. Folder creation is opt-in
(self.folder_mgr is set only when --task-folder is configured) and
applies to ROOT tasks only (parent_id is None).

Resilience contract: a filesystem failure during folder creation must
NOT block the DB INSERT — the task must still be created.
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
        # Ensure DB is initialized synchronously for direct create_task calls.
        store._ensure_db_initialized_sync()
        yield store


# =============================================================================
# create_task (single)
# =============================================================================

class TestCreateTaskFolderHook:
    def test_root_task_creates_folder_and_task_md(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        result = store_with_folder.create_task(
            title="Root Feature", content="Body", tags=["feature"]
        )
        assert result["success"] is True
        code = result["code"]
        assert code.startswith("FEAT-")

        folder = folder_root / code
        assert folder.is_dir()

        task_md = folder / "task.md"
        assert task_md.is_file()
        content = task_md.read_text(encoding="utf-8")
        assert "# Root Feature" in content
        assert "## Vector ID" in content
        assert str(result["task_id"]) in content

    def test_subtask_does_not_create_folder(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        root = store_with_folder.create_task(
            title="Root", content="x", tags=["feature"]
        )
        sub = store_with_folder.create_task(
            title="Sub", content="y", tags=["feature"], parent_id=root["task_id"]
        )
        assert sub["success"] is True
        # Only the root code folder exists; the subtask must NOT have one.
        sub_folder = folder_root / sub["code"]
        assert not sub_folder.exists()

    def test_feature_off_no_folder_created(
        self, task_store, tmp_path: Path
    ):
        # task_store fixture builds TaskStore WITHOUT task_folder → folder_mgr = None
        assert task_store.folder_mgr is None
        result = task_store.create_task(
            title="Off", content="x", tags=["feature"]
        )
        assert result["success"] is True
        # No folder root exists at all in this fixture, but more importantly
        # the manager is disabled — creation path is silent no-op.
        # (Listing a folder is impossible without root, so just assert disabled.)

    def test_fs_failure_does_not_block_db_insert(
        self, store_with_folder: TaskStore, monkeypatch
    ):
        # Force TaskFolderManager.create_folder to raise — DB INSERT must still
        # succeed and the task must be returned.
        from src.task_folder import TaskFolderManager

        def boom(self, *args, **kwargs):
            raise OSError("simulated FS failure")

        monkeypatch.setattr(TaskFolderManager, "create_folder", boom)

        result = store_with_folder.create_task(
            title="FS-Crash", content="x", tags=["feature"]
        )
        assert result["success"] is True
        assert result["task_id"] is not None
        # DB row exists.
        retrieved = store_with_folder.get_task_by_id(result["task_id"])
        assert retrieved is not None
        assert retrieved.title == "FS-Crash"

    def test_custom_code_passed_through_to_folder_name(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        result = store_with_folder.create_task(
            title="Jira", content="x", tags=["feature"], code="OLOM-460"
        )
        assert result["code"] == "OLOM-460"
        assert (folder_root / "OLOM-460").is_dir()

    def test_auto_gen_code_creates_named_folder(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        result = store_with_folder.create_task(
            title="Auto", content="x", tags=["bugfix"]
        )
        assert result["code"] == "FIX-1"
        assert (folder_root / "FIX-1").is_dir()


# =============================================================================
# create_tasks_bulk
# =============================================================================

class TestCreateTasksBulkFolderHook:
    def test_bulk_root_plus_subtask_only_root_gets_folder(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        # Two-step: bulk-create a root first to obtain its id, then bulk-create
        # a child referencing it. Bulk INSERTs cannot resolve forward references
        # within one batch, so this is the realistic usage shape.
        root_batch = store_with_folder.create_tasks_bulk([
            {"title": "RootA", "content": "a", "tags": ["feature"]},
        ])
        root_id = root_batch["created_task_ids"][0]

        result = store_with_folder.create_tasks_bulk([
            {"title": "RootB", "content": "b", "tags": ["bugfix"]},
            {"title": "Child", "content": "c", "tags": ["feature"],
             "parent_id": root_id},
        ])
        assert result["success"] is True
        ids = result["created_task_ids"]
        tasks = [store_with_folder.get_task_by_id(tid) for tid in ids]

        # RootB is parent_id=None → folder created
        rootB = next(t for t in tasks if t.title == "RootB")
        assert (folder_root / rootB.code).is_dir()

        # Child has parent_id → no folder
        child = next(t for t in tasks if t.title == "Child")
        assert not (folder_root / child.code).exists()

    def test_bulk_fs_failure_does_not_block_other_tasks(
        self, store_with_folder: TaskStore, folder_root: Path, monkeypatch
    ):
        from src.task_folder import TaskFolderManager

        # Make ONE specific code raise; others succeed.
        original = TaskFolderManager.create_folder

        def selective(self, code, title, task_id):
            if code == "FIX-1":
                raise OSError("simulated")
            return original(self, code, title, task_id)

        monkeypatch.setattr(TaskFolderManager, "create_folder", selective)

        result = store_with_folder.create_tasks_bulk([
            {"title": "Boom", "content": "a", "tags": ["bugfix"]},   # → FIX-1, fails
            {"title": "OK", "content": "b", "tags": ["feature"]},    # → FEAT-1, ok
        ])
        # Both DB rows created.
        assert result["success"] is True
        assert len(result["created_task_ids"]) == 2

        # FEAT-1 folder exists (the "OK" task), FIX-1 does not (raised).
        assert (folder_root / "FEAT-1").is_dir()
        assert not (folder_root / "FIX-1").exists()