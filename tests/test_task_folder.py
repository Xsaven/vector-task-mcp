"""
TaskFolderManager Tests
=======================

Tests for src/task_folder.py — pure FS lifecycle for root-task folders.
Resilience contract: every public method must log + return False/None on
failure rather than raise to its caller.
"""

import os
import sys
from pathlib import Path

import pytest

from src.task_folder import TaskFolderManager, TASK_MD_TEMPLATE


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def root(tmp_path: Path) -> Path:
    folder = tmp_path / "task_folders"
    folder.mkdir()
    return folder


@pytest.fixture
def working_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def mgr(root: Path, working_dir: Path) -> TaskFolderManager:
    """Manager whose root lives INSIDE working_dir → relative paths in list_files."""
    return TaskFolderManager(task_folder_root=root, working_dir=working_dir)


# =============================================================================
# create_folder
# =============================================================================

class TestCreateFolder:
    def test_creates_new_folder_and_task_md(self, mgr: TaskFolderManager, root: Path):
        ok = mgr.create_folder("FEAT-1", "My Feature", 42)
        assert ok is True
        folder = root / "FEAT-1"
        assert folder.is_dir()
        task_md = folder / "task.md"
        assert task_md.is_file()
        content = task_md.read_text(encoding="utf-8")
        assert "# My Feature" in content
        assert "## Vector ID" in content
        assert "42" in content
        assert content == TASK_MD_TEMPLATE.format(title="My Feature", task_id=42)

    def test_idempotent_existing_folder_with_vector_id(
        self, mgr: TaskFolderManager, root: Path
    ):
        # Pre-create folder with a complete task.md (incl. Vector ID)
        folder = root / "FEAT-2"
        folder.mkdir()
        existing = "# Custom\n\n## Vector ID\n99\n\n## Notes\nKeep me\n"
        (folder / "task.md").write_text(existing, encoding="utf-8")

        ok = mgr.create_folder("FEAT-2", "Custom", 99)

        assert ok is True
        # File should be untouched (Vector ID was already present)
        assert (folder / "task.md").read_text(encoding="utf-8") == existing

    def test_appends_vector_id_when_missing(
        self, mgr: TaskFolderManager, root: Path
    ):
        folder = root / "FEAT-3"
        folder.mkdir()
        existing = "# Custom\n\n## Notes\nNo vector id yet\n"
        (folder / "task.md").write_text(existing, encoding="utf-8")

        ok = mgr.create_folder("FEAT-3", "Custom", 7)

        assert ok is True
        new_content = (folder / "task.md").read_text(encoding="utf-8")
        assert "## Vector ID\n7" in new_content
        # Original content preserved
        assert "## Notes\nNo vector id yet" in new_content

    def test_failure_returns_false_no_raise(
        self, mgr: TaskFolderManager, root: Path, monkeypatch
    ):
        # Force mkdir to raise — manager must catch and return False
        def boom(self, *args, **kwargs):
            raise OSError("simulated mkdir failure")
        monkeypatch.setattr(Path, "mkdir", boom)

        ok = mgr.create_folder("FEAT-X", "title", 1)
        assert ok is False  # no exception escapes


# =============================================================================
# ensure_vector_id
# =============================================================================

class TestEnsureVectorId:
    def test_appends_when_missing(self, mgr: TaskFolderManager, root: Path):
        folder = root / "FEAT-4"
        folder.mkdir()
        (folder / "task.md").write_text("# Title\n\n## Notes\nx\n", encoding="utf-8")

        mgr.ensure_vector_id("FEAT-4", 11)

        content = (folder / "task.md").read_text(encoding="utf-8")
        assert content.endswith("## Vector ID\n11\n")
        assert "## Notes\nx" in content

    def test_no_op_when_present(self, mgr: TaskFolderManager, root: Path):
        folder = root / "FEAT-5"
        folder.mkdir()
        original = "# T\n\n## Vector ID\n5\n\n## Notes\nKeep\n"
        (folder / "task.md").write_text(original, encoding="utf-8")

        mgr.ensure_vector_id("FEAT-5", 999)  # different id, must NOT overwrite

        assert (folder / "task.md").read_text(encoding="utf-8") == original

    def test_no_op_when_file_missing(self, mgr: TaskFolderManager):
        # Folder doesn't exist either — must not raise
        mgr.ensure_vector_id("FEAT-NOPE", 1)


# =============================================================================
# rename_on_completed / revert_on_completed
# =============================================================================

class TestRenameLifecycle:
    def test_rename_on_completed(self, mgr: TaskFolderManager, root: Path):
        mgr.create_folder("FEAT-6", "T", 1)
        ok = mgr.rename_on_completed("FEAT-6")
        assert ok is True
        assert not (root / "FEAT-6").exists()
        assert (root / "FEAT-6-on-review").is_dir()
        assert (root / "FEAT-6-on-review" / "task.md").is_file()

    def test_rename_on_completed_idempotent(
        self, mgr: TaskFolderManager, root: Path
    ):
        mgr.create_folder("FEAT-7", "T", 1)
        assert mgr.rename_on_completed("FEAT-7") is True
        # Second call: source missing, target exists — treated as success
        assert mgr.rename_on_completed("FEAT-7") is True

    def test_rename_on_completed_missing_source(
        self, mgr: TaskFolderManager
    ):
        assert mgr.rename_on_completed("FEAT-MISSING") is False

    def test_revert_on_completed(self, mgr: TaskFolderManager, root: Path):
        mgr.create_folder("FEAT-8", "T", 1)
        mgr.rename_on_completed("FEAT-8")
        ok = mgr.revert_on_completed("FEAT-8")
        assert ok is True
        assert (root / "FEAT-8").is_dir()
        assert not (root / "FEAT-8-on-review").exists()

    def test_revert_on_completed_idempotent(
        self, mgr: TaskFolderManager, root: Path
    ):
        mgr.create_folder("FEAT-9", "T", 1)
        # Already at original name (no -on-review); idempotent success
        assert mgr.revert_on_completed("FEAT-9") is True

    def test_revert_on_completed_missing_source(
        self, mgr: TaskFolderManager
    ):
        assert mgr.revert_on_completed("FEAT-MISSING") is False


# =============================================================================
# rename_on_done
# =============================================================================

class TestRenameOnDone:
    def test_done_after_completed(self, mgr: TaskFolderManager, root: Path):
        mgr.create_folder("FEAT-10", "T", 1)
        # Add an extra file so we can verify contents survive the move
        (root / "FEAT-10" / "notes.md").write_text("hello", encoding="utf-8")
        mgr.rename_on_completed("FEAT-10")

        ok = mgr.rename_on_done("FEAT-10")

        assert ok is True
        archive = root / "FEAT-10" / "Archive" / "FEAT-10-done"
        assert archive.is_dir()
        assert (archive / "task.md").is_file()
        assert (archive / "notes.md").read_text(encoding="utf-8") == "hello"
        # Old -on-review folder is gone
        assert not (root / "FEAT-10-on-review").exists()

    def test_done_jump_from_original(self, mgr: TaskFolderManager, root: Path):
        # Jump-to-done without going through -on-review first
        mgr.create_folder("FEAT-11", "T", 1)
        (root / "FEAT-11" / "notes.md").write_text("x", encoding="utf-8")

        ok = mgr.rename_on_done("FEAT-11")

        assert ok is True
        archive = root / "FEAT-11" / "Archive" / "FEAT-11-done"
        assert archive.is_dir()
        assert (archive / "task.md").is_file()
        assert (archive / "notes.md").read_text(encoding="utf-8") == "x"
        # No leftover temp directory
        assert not (root / "FEAT-11-pending-archive").exists()

    def test_done_missing_source(self, mgr: TaskFolderManager):
        assert mgr.rename_on_done("FEAT-MISSING") is False

    def test_done_target_already_exists(
        self, mgr: TaskFolderManager, root: Path
    ):
        # Simulate an interrupted previous run: the -on-review source still
        # exists AND the final target was already created.
        on_review = root / "FEAT-12-on-review"
        on_review.mkdir()
        (on_review / "task.md").write_text("source", encoding="utf-8")

        # Pre-populate the destination — manager must abort safely
        (root / "FEAT-12" / "Archive" / "FEAT-12-done").mkdir(parents=True)

        assert mgr.rename_on_done("FEAT-12") is False
        # Source folder must remain intact (no destructive partial move)
        assert (on_review / "task.md").is_file()


# =============================================================================
# list_files
# =============================================================================

class TestListFiles:
    def test_recursive_listing(self, mgr: TaskFolderManager, root: Path):
        mgr.create_folder("FEAT-13", "T", 1)
        (root / "FEAT-13" / "notes.md").write_text("a", encoding="utf-8")
        sub = root / "FEAT-13" / "sub"
        sub.mkdir()
        (sub / "deep.md").write_text("b", encoding="utf-8")

        files = mgr.list_files("FEAT-13")

        assert files is not None
        names = [Path(f["path"]).name for f in files]
        assert sorted(names) == ["deep.md", "notes.md", "task.md"]

    def test_relative_paths_when_inside_working_dir(
        self, mgr: TaskFolderManager
    ):
        mgr.create_folder("FEAT-14", "T", 1)
        files = mgr.list_files("FEAT-14")
        assert files
        # working_dir is the parent of root → all entries should be relative
        assert all(f["relative"] is True for f in files)
        for f in files:
            assert not Path(f["path"]).is_absolute()

    def test_absolute_paths_when_outside_working_dir(
        self, tmp_path: Path
    ):
        # Place the root OUTSIDE working_dir
        outside_root = tmp_path / "outside_root"
        outside_root.mkdir()
        working_dir = tmp_path / "wd"
        working_dir.mkdir()

        m = TaskFolderManager(task_folder_root=outside_root, working_dir=working_dir)
        m.create_folder("FEAT-15", "T", 1)

        files = m.list_files("FEAT-15")

        assert files
        assert all(f["relative"] is False for f in files)
        for f in files:
            assert Path(f["path"]).is_absolute()

    def test_empty_when_folder_missing(self, mgr: TaskFolderManager):
        assert mgr.list_files("FEAT-NOPE") == []

    def test_resolves_on_review_folder(
        self, mgr: TaskFolderManager, root: Path
    ):
        mgr.create_folder("FEAT-16", "T", 1)
        mgr.rename_on_completed("FEAT-16")
        files = mgr.list_files("FEAT-16")
        assert files
        # Resolved through the -on-review fallback
        assert any(Path(f["path"]).name == "task.md" for f in files)

    def test_returns_none_on_unexpected_failure(
        self, mgr: TaskFolderManager, monkeypatch
    ):
        def boom(self, *args, **kwargs):
            raise OSError("simulated rglob failure")
        monkeypatch.setattr(Path, "rglob", boom)

        # Folder must exist so we get past _resolve_existing_folder
        mgr.create_folder("FEAT-17", "T", 1)
        result = mgr.list_files("FEAT-17")
        assert result is None  # never raises


# =============================================================================
# Resilience — read-only filesystem simulation
# =============================================================================

@pytest.mark.skipif(
    sys.platform.startswith("win"), reason="POSIX-only chmod semantics"
)
class TestResilience:
    def test_create_folder_on_read_only_root(self, tmp_path: Path):
        ro_root = tmp_path / "ro_root"
        ro_root.mkdir()
        os.chmod(ro_root, 0o500)  # read+execute, no write
        try:
            wd = tmp_path / "wd"
            wd.mkdir()
            m = TaskFolderManager(task_folder_root=ro_root, working_dir=wd)
            ok = m.create_folder("FEAT-RO", "T", 1)
            assert ok is False  # logged + handled, never raised
        finally:
            os.chmod(ro_root, 0o700)  # restore so pytest can clean up

    def test_rename_on_completed_when_target_locked(
        self, mgr: TaskFolderManager, root: Path
    ):
        # Pre-create both source and target — manager treats target-existing as
        # idempotent success only when source is gone; here source exists, so
        # the rename is a no-op, but the contract still says "do not raise".
        mgr.create_folder("FEAT-COL", "T", 1)
        (root / "FEAT-COL-on-review").mkdir()
        # On many filesystems Path.rename onto an existing dir raises; the
        # manager must catch it.
        result = mgr.rename_on_completed("FEAT-COL")
        # Either idempotent True (target exists) or False (rename failed) —
        # both acceptable, what matters is "no exception".
        assert result in (True, False)