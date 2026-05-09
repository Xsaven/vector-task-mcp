"""
CLI --task-folder + validate_task_folder + TaskStore wiring (task #211)
=======================================================================

Tests for:
- src/security.py validate_task_folder helper
- src/task_store.py TaskStore constructor accepting task_folder/working_dir
- main.py get_task_folder CLI parser
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from src.security import validate_task_folder, SecurityError


# =============================================================================
# validate_task_folder
# =============================================================================

class TestValidateTaskFolder:
    def test_none_returns_none(self):
        assert validate_task_folder(None) is None

    def test_valid_path_creates_and_resolves(self, tmp_path: Path):
        target = tmp_path / "tasks" / "root"
        # Folder does not exist yet — helper must create it.
        assert not target.exists()
        result = validate_task_folder(str(target))
        assert result == target.resolve()
        assert target.is_dir()

    def test_existing_path_idempotent(self, tmp_path: Path):
        target = tmp_path / "existing"
        target.mkdir()
        result = validate_task_folder(target)
        assert result == target.resolve()
        assert target.is_dir()

    def test_relative_path_resolved_to_absolute(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = validate_task_folder("./relative_tasks")
        assert result is not None
        assert result.is_absolute()
        assert result == (tmp_path / "relative_tasks").resolve()

    @pytest.mark.parametrize("bad", [
        "/tmp/foo;rm -rf /",   # semicolon
        "/tmp/foo&bar",        # ampersand
        "/tmp/foo|bar",        # pipe
        "/tmp/foo`whoami`",    # backtick
        "/tmp/foo$VAR",        # dollar
    ])
    def test_injection_chars_rejected(self, bad):
        with pytest.raises(SecurityError):
            validate_task_folder(bad)

    def test_control_chars_rejected(self):
        with pytest.raises(SecurityError):
            validate_task_folder("/tmp/bad\x01name")


# =============================================================================
# TaskStore constructor wiring
# =============================================================================

class TestTaskStoreConstructor:
    def test_default_no_task_folder(self, task_store):
        # Fixture builds TaskStore without task_folder → folder_mgr is None.
        assert task_store.task_folder is None
        assert task_store.folder_mgr is None

    def test_with_task_folder_instantiates_manager(
        self, temp_db_path: Path, tmp_path: Path, mock_embedding_model
    ):
        from src.task_folder import TaskFolderManager
        from src.task_store import TaskStore

        tf = tmp_path / "tasks_root"
        tf.mkdir()
        wd = tmp_path / "wd"
        wd.mkdir()

        with patch("src.task_store.get_embedding_model", return_value=mock_embedding_model):
            store = TaskStore(
                db_path=temp_db_path,
                task_folder=tf,
                working_dir=wd,
            )

        assert store.task_folder == tf
        assert store.working_dir == wd
        assert isinstance(store.folder_mgr, TaskFolderManager)
        assert store.folder_mgr.root == tf
        assert store.folder_mgr.working_dir == wd

    def test_working_dir_default_when_omitted(
        self, temp_db_path: Path, mock_embedding_model
    ):
        # When working_dir is not provided, TaskStore derives it from db_path
        # (project root = db_path.parent.parent, since memory/ sits beneath it).
        from src.task_store import TaskStore

        with patch("src.task_store.get_embedding_model", return_value=mock_embedding_model):
            store = TaskStore(db_path=temp_db_path)

        assert store.working_dir == temp_db_path.parent.parent
        assert store.folder_mgr is None  # feature off without task_folder


# =============================================================================
# main.get_task_folder
# =============================================================================

class TestGetTaskFolderCLI:
    def test_absent_returns_none(self):
        from main import get_task_folder
        with patch.object(sys, "argv", ["prog", "--working-dir", "/tmp"]):
            assert get_task_folder() is None

    def test_present_validates_and_returns_path(self, tmp_path: Path):
        from main import get_task_folder
        target = tmp_path / "cli_tasks"
        with patch.object(sys, "argv", ["prog", "--task-folder", str(target)]):
            result = get_task_folder()
        assert result == target.resolve()
        assert target.is_dir()

    def test_injection_chars_via_cli_raise(self):
        from main import get_task_folder
        with patch.object(sys, "argv", ["prog", "--task-folder", "/tmp/foo;bad"]):
            with pytest.raises(SecurityError):
                get_task_folder()

    def test_flag_without_value_returns_none(self):
        # Defensive: --task-folder is the last arg (no value provided)
        from main import get_task_folder
        with patch.object(sys, "argv", ["prog", "--task-folder"]):
            assert get_task_folder() is None