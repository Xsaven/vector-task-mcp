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

    def test_empty_flag_value_treated_as_disabled(self, tmp_path: Path):
        # --task-folder "" must NOT enable the feature. It should fall
        # through to the .env lookup (and return None if no .env config).
        from main import get_task_folder
        with patch.object(
            sys, "argv",
            ["prog", "--working-dir", str(tmp_path), "--task-folder", ""],
        ):
            assert get_task_folder() is None

    def test_whitespace_flag_value_treated_as_disabled(self, tmp_path: Path):
        from main import get_task_folder
        with patch.object(
            sys, "argv",
            ["prog", "--working-dir", str(tmp_path), "--task-folder", "   "],
        ):
            assert get_task_folder() is None


# =============================================================================
# .env fallback (TASK_FOLDER in .brain/.env or .xbrain/.env)
# =============================================================================

class TestEnvFallback:
    def _write_env(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_brain_env_fallback_when_flag_absent(self, tmp_path: Path):
        # No --task-folder flag; .brain/.env contains TASK_FOLDER → enabled.
        from main import get_task_folder
        target = tmp_path / "envtasks"
        self._write_env(tmp_path / ".brain" / ".env", f"TASK_FOLDER={target}\n")
        with patch.object(
            sys, "argv", ["prog", "--working-dir", str(tmp_path)]
        ):
            result = get_task_folder()
        assert result == target.resolve()
        assert target.is_dir()

    def test_xbrain_env_fallback_when_brain_absent(self, tmp_path: Path):
        from main import get_task_folder
        target = tmp_path / "xbrain_tasks"
        self._write_env(tmp_path / ".xbrain" / ".env", f'TASK_FOLDER="{target}"\n')
        with patch.object(
            sys, "argv", ["prog", "--working-dir", str(tmp_path)]
        ):
            result = get_task_folder()
        assert result == target.resolve()

    def test_brain_env_wins_over_xbrain_env(self, tmp_path: Path):
        # When both files exist, .brain/.env is checked first.
        from main import get_task_folder
        brain_target = tmp_path / "from_brain"
        xbrain_target = tmp_path / "from_xbrain"
        self._write_env(tmp_path / ".brain" / ".env", f"TASK_FOLDER={brain_target}\n")
        self._write_env(tmp_path / ".xbrain" / ".env", f"TASK_FOLDER={xbrain_target}\n")
        with patch.object(
            sys, "argv", ["prog", "--working-dir", str(tmp_path)]
        ):
            result = get_task_folder()
        assert result == brain_target.resolve()

    def test_relative_env_path_resolved_against_working_dir(self, tmp_path: Path):
        # TASK_FOLDER=.tasks (relative) must resolve under working_dir,
        # not under CWD.
        from main import get_task_folder
        self._write_env(tmp_path / ".brain" / ".env", "TASK_FOLDER=.tasks\n")
        with patch.object(
            sys, "argv", ["prog", "--working-dir", str(tmp_path)]
        ):
            result = get_task_folder()
        assert result == (tmp_path / ".tasks").resolve()

    def test_empty_env_value_falls_through(self, tmp_path: Path):
        # TASK_FOLDER="" or TASK_FOLDER= must NOT enable the feature.
        from main import get_task_folder
        self._write_env(tmp_path / ".brain" / ".env", "TASK_FOLDER=\n")
        self._write_env(tmp_path / ".xbrain" / ".env", 'TASK_FOLDER=""\n')
        with patch.object(
            sys, "argv", ["prog", "--working-dir", str(tmp_path)]
        ):
            assert get_task_folder() is None

    def test_cli_flag_wins_over_env(self, tmp_path: Path):
        from main import get_task_folder
        cli_target = tmp_path / "from_cli"
        env_target = tmp_path / "from_env"
        self._write_env(tmp_path / ".brain" / ".env", f"TASK_FOLDER={env_target}\n")
        with patch.object(
            sys, "argv",
            ["prog", "--working-dir", str(tmp_path), "--task-folder", str(cli_target)],
        ):
            result = get_task_folder()
        assert result == cli_target.resolve()

    def test_empty_cli_flag_falls_through_to_env(self, tmp_path: Path):
        # Empty --task-folder "" + .env present → use .env value.
        from main import get_task_folder
        env_target = tmp_path / "from_env_after_empty_cli"
        self._write_env(tmp_path / ".brain" / ".env", f"TASK_FOLDER={env_target}\n")
        with patch.object(
            sys, "argv",
            ["prog", "--working-dir", str(tmp_path), "--task-folder", ""],
        ):
            result = get_task_folder()
        assert result == env_target.resolve()

    def test_env_file_with_comments_and_other_vars(self, tmp_path: Path):
        from main import get_task_folder
        target = tmp_path / "complex_env"
        self._write_env(
            tmp_path / ".brain" / ".env",
            "# top comment\n"
            "OTHER_VAR=ignore-me\n"
            "\n"
            f"TASK_FOLDER='{target}'\n"
            "ANOTHER=42\n",
        )
        with patch.object(
            sys, "argv", ["prog", "--working-dir", str(tmp_path)]
        ):
            result = get_task_folder()
        assert result == target.resolve()