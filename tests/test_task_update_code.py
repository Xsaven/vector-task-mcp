"""
task_update accepts ``code`` (v1.8.1)
======================================

Renaming the ``code`` field of an existing task. The DB layer enforces
uniqueness via the partial UNIQUE index added in #209; the FS layer renames
the on-disk folder at whichever lifecycle position it currently occupies
(``{code}/``, ``{code}-on-review/``, or ``Archive/{code}/``).

Tests cover:
- rename code in active state → folder renamed at root
- rename code in -on-review state → folder renamed at -on-review position
- rename code in Archive/ state → folder renamed inside Archive
- collision with an existing code → friendly IntegrityError response
- invalid code format → SecurityError surfaced
- subtask code change → DB-only, no folder side-effect
- feature off → DB-only update, no manager calls
- legacy NULL → set: creates a fresh folder for the new code
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
# Active state rename
# =============================================================================

class TestActiveRename:
    def test_rename_in_active_state(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        result = store_with_folder.create_task(
            title="A", content="x", tags=["feature"]
        )
        old_code = result["code"]
        assert (folder_root / old_code).is_dir()

        update_result = store_with_folder.update_task(
            task_id=result["task_id"], code="OLOM-100"
        )
        assert update_result["success"] is True
        assert update_result["task"]["code"] == "OLOM-100"
        # Folder renamed at root level.
        assert (folder_root / "OLOM-100").is_dir()
        assert (folder_root / "OLOM-100" / "task.md").is_file()
        assert not (folder_root / old_code).exists()

    def test_rename_preserves_folder_contents(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        result = store_with_folder.create_task(
            title="B", content="x", tags=["feature"]
        )
        old_code = result["code"]
        # Add side-files; they MUST survive the rename.
        (folder_root / old_code / "notes.md").write_text("hello", encoding="utf-8")
        (folder_root / old_code / "subdir").mkdir()
        (folder_root / old_code / "subdir" / "deep.md").write_text("d", encoding="utf-8")

        store_with_folder.update_task(task_id=result["task_id"], code="JIRA-99")

        assert (folder_root / "JIRA-99" / "notes.md").read_text(encoding="utf-8") == "hello"
        assert (folder_root / "JIRA-99" / "subdir" / "deep.md").read_text(encoding="utf-8") == "d"


# =============================================================================
# -on-review state rename
# =============================================================================

class TestOnReviewRename:
    def test_rename_in_on_review_state(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        result = store_with_folder.create_task(
            title="C", content="x", tags=["feature"]
        )
        old_code = result["code"]
        store_with_folder.update_task(task_id=result["task_id"], status="in_progress")
        store_with_folder.update_task(task_id=result["task_id"], status="completed")
        assert (folder_root / f"{old_code}-on-review").is_dir()

        store_with_folder.update_task(task_id=result["task_id"], code="OLOM-200")

        assert (folder_root / "OLOM-200-on-review").is_dir()
        assert not (folder_root / f"{old_code}-on-review").exists()


# =============================================================================
# Archive state rename
# =============================================================================

class TestArchiveRename:
    def test_rename_in_archive_state(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        result = store_with_folder.create_task(
            title="D", content="x", tags=["feature"]
        )
        old_code = result["code"]
        for s in ("in_progress", "completed", "tested", "validated", "done"):
            store_with_folder.update_task(task_id=result["task_id"], status=s)
        assert (folder_root / "Archive" / old_code).is_dir()

        store_with_folder.update_task(task_id=result["task_id"], code="OLOM-300")

        assert (folder_root / "Archive" / "OLOM-300").is_dir()
        assert (folder_root / "Archive" / "OLOM-300" / "task.md").is_file()
        assert not (folder_root / "Archive" / old_code).exists()


# =============================================================================
# Validation / error paths
# =============================================================================

class TestValidation:
    def test_collision_returns_friendly_error(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        a = store_with_folder.create_task(
            title="A", content="x", tags=["feature"], code="OLOM-1"
        )
        b = store_with_folder.create_task(
            title="B", content="y", tags=["feature"], code="OLOM-2"
        )

        # Try to rename B onto A's code → UNIQUE violation.
        result = store_with_folder.update_task(task_id=b["task_id"], code="OLOM-1")
        assert result["success"] is False
        assert "code" in result["message"].lower()
        # Folders untouched.
        assert (folder_root / "OLOM-1").is_dir()
        assert (folder_root / "OLOM-2").is_dir()

    def test_invalid_format_raises_security_error(
        self, store_with_folder: TaskStore
    ):
        result = store_with_folder.create_task(
            title="A", content="x", tags=["feature"]
        )
        from src.security import SecurityError
        with pytest.raises(SecurityError):
            store_with_folder.update_task(task_id=result["task_id"], code="lower-1")

    def test_path_traversal_format_rejected(
        self, store_with_folder: TaskStore
    ):
        result = store_with_folder.create_task(
            title="A", content="x", tags=["feature"]
        )
        from src.security import SecurityError
        with pytest.raises(SecurityError):
            store_with_folder.update_task(task_id=result["task_id"], code="..")


# =============================================================================
# Subtask code change → DB-only
# =============================================================================

class TestSubtaskCodeChange:
    def test_subtask_code_change_no_folder_op(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        root = store_with_folder.create_task(
            title="R", content="x", tags=["feature"]
        )
        child = store_with_folder.create_task(
            title="C", content="y", tags=["feature"], parent_id=root["task_id"]
        )
        old_child_code = child["code"]
        # Verify no folder for child up front.
        assert not (folder_root / old_child_code).exists()

        new_code = "FEAT-999"
        result = store_with_folder.update_task(
            task_id=child["task_id"], code=new_code
        )
        assert result["success"] is True
        assert result["task"]["code"] == new_code
        # No folder created or renamed at any of the 3 positions for the child.
        assert not (folder_root / new_code).exists()
        assert not (folder_root / f"{new_code}-on-review").exists()
        assert not (folder_root / "Archive" / new_code).exists()


# =============================================================================
# Feature off — DB-only path
# =============================================================================

class TestFeatureOff:
    def test_code_change_db_only_when_feature_off(
        self, task_store
    ):
        # task_store fixture has no --task-folder → folder_mgr=None.
        result = task_store.create_task(
            title="A", content="x", tags=["feature"]
        )
        update_result = task_store.update_task(
            task_id=result["task_id"], code="MIGR-7"
        )
        assert update_result["success"] is True
        assert update_result["task"]["code"] == "MIGR-7"


# =============================================================================
# Legacy NULL → set
# =============================================================================

class TestLegacyNullToSet:
    def test_setting_code_creates_folder(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        # Insert a legacy root task with NULL code directly to bypass auto-gen.
        # Migration runs in the fixture above and would normally backfill, but
        # we deliberately delete the code afterward to simulate a row created
        # AFTER migration (e.g. a future bug or manual SQL edit).
        import sqlite3
        db_path = store_with_folder.db_path
        conn = sqlite3.connect(str(db_path))
        try:
            cursor = conn.execute(
                "INSERT INTO tasks (parent_id, status, title, content, "
                "content_hash, created_at, code) "
                "VALUES (?, ?, ?, ?, ?, ?, NULL)",
                (None, "pending", "Legacy", "old",
                 "legacy_t226_setcode", "2020-01-01T00:00:00"),
            )
            legacy_id = cursor.lastrowid
            conn.commit()
        finally:
            conn.close()

        # Now set a code on the legacy row.
        result = store_with_folder.update_task(
            task_id=legacy_id, code="LEGACY-1"
        )
        assert result["success"] is True
        assert result["task"]["code"] == "LEGACY-1"
        # Fresh folder created for the new code.
        assert (folder_root / "LEGACY-1").is_dir()
        assert (folder_root / "LEGACY-1" / "task.md").is_file()


# =============================================================================
# Migration backfill: NULL-code root tasks get codes on init
# =============================================================================

class TestMigrationBackfill:
    def test_backfill_populates_root_codes(
        self, temp_db_path: Path, folder_root: Path, working_dir: Path,
        mock_embedding_model
    ):
        # Pre-populate DB with a legacy NULL-code root row BEFORE first init,
        # then init the store and verify backfill ran.
        with patch("src.task_store.get_embedding_model", return_value=mock_embedding_model):
            seed = TaskStore(
                db_path=temp_db_path,
                task_folder=folder_root,
                working_dir=working_dir,
            )
            seed._ensure_db_initialized_sync()  # creates schema only

        import sqlite3
        conn = sqlite3.connect(str(temp_db_path))
        try:
            conn.execute(
                "INSERT INTO tasks (parent_id, status, title, content, tags, "
                "content_hash, created_at, code) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, NULL)",
                (None, "pending", "Legacy root A", "x", '["feature"]',
                 "legacy_t226_root_a", "2020-01-01T00:00:00"),
            )
            conn.execute(
                "INSERT INTO tasks (parent_id, status, title, content, tags, "
                "content_hash, created_at, code) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, NULL)",
                (None, "pending", "Legacy root B", "y", '["bugfix"]',
                 "legacy_t226_root_b", "2020-01-01T00:00:00"),
            )
            conn.commit()
        finally:
            conn.close()

        # Re-create the store; backfill should run on init.
        with patch("src.task_store.get_embedding_model", return_value=mock_embedding_model):
            store2 = TaskStore(
                db_path=temp_db_path,
                task_folder=folder_root,
                working_dir=working_dir,
            )
            # Force a fresh init pass.
            store2._db_initialized = False
            store2._ensure_db_initialized_sync()

        # Both rows now have codes.
        conn = sqlite3.connect(str(temp_db_path))
        try:
            rows = conn.execute(
                "SELECT title, code FROM tasks "
                "WHERE parent_id IS NULL AND title LIKE 'Legacy root%'"
            ).fetchall()
            codes = {title: code for title, code in rows}
        finally:
            conn.close()

        assert codes["Legacy root A"] is not None
        assert codes["Legacy root B"] is not None
        # Prefix follows the type tag.
        assert codes["Legacy root A"].startswith("FEAT-")
        assert codes["Legacy root B"].startswith("FIX-")

    def test_subtasks_kept_null(
        self, temp_db_path: Path, folder_root: Path, working_dir: Path,
        mock_embedding_model
    ):
        # Subtasks with NULL code MUST NOT be backfilled — the contract is
        # root-only. Subtasks tolerate NULL code by design.
        with patch("src.task_store.get_embedding_model", return_value=mock_embedding_model):
            seed = TaskStore(
                db_path=temp_db_path,
                task_folder=folder_root,
                working_dir=working_dir,
            )
            seed._ensure_db_initialized_sync()

        import sqlite3
        conn = sqlite3.connect(str(temp_db_path))
        try:
            cursor = conn.execute(
                "INSERT INTO tasks (parent_id, status, title, content, "
                "content_hash, created_at, code) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (None, "pending", "Root", "r",
                 "legacy_t226_subtask_root", "2020-01-01T00:00:00", "FEAT-999"),
            )
            root_id = cursor.lastrowid
            conn.execute(
                "INSERT INTO tasks (parent_id, status, title, content, "
                "content_hash, created_at, code) "
                "VALUES (?, ?, ?, ?, ?, ?, NULL)",
                (root_id, "pending", "Subtask", "s",
                 "legacy_t226_subtask_child", "2020-01-01T00:00:00"),
            )
            conn.commit()
        finally:
            conn.close()

        with patch("src.task_store.get_embedding_model", return_value=mock_embedding_model):
            store2 = TaskStore(
                db_path=temp_db_path,
                task_folder=folder_root,
                working_dir=working_dir,
            )
            store2._db_initialized = False
            store2._ensure_db_initialized_sync()

        conn = sqlite3.connect(str(temp_db_path))
        try:
            sub_code = conn.execute(
                "SELECT code FROM tasks WHERE title = 'Subtask'"
            ).fetchone()[0]
        finally:
            conn.close()
        assert sub_code is None  # subtask still NULL — backfill doesn't touch
