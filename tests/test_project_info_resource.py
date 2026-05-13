"""
Project info MCP resource (task #215)
======================================

Tests for the `project://info` resource handler defined in main.py and its
underlying helper `_get_task_folders_summary(task_store)`. The resource
exposes project metadata (working_dir, task_folder status, root-task folder
summaries) — first @mcp.resource in the project, establishes the pattern.

The helper is module-level and unit-testable in isolation; the @mcp.resource
decorator registration is verified via FastMCP's resource manager API.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from main import _get_task_folders_summary
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


# =============================================================================
# _get_task_folders_summary helper
# =============================================================================

class TestGetTaskFoldersSummary:
    def test_empty_when_feature_off(self, task_store):
        # task_store fixture has no --task-folder → folder_mgr is None.
        assert task_store.folder_mgr is None
        assert _get_task_folders_summary(task_store) == []

    def test_empty_when_no_root_tasks(self, store_with_folder: TaskStore):
        assert _get_task_folders_summary(store_with_folder) == []

    def test_returns_root_with_metadata(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        result = store_with_folder.create_task(
            title="Root A", content="x", tags=["feature"]
        )
        # Add an extra file to verify files_count includes children.
        (folder_root / result["code"] / "notes.md").write_text("n", encoding="utf-8")

        summary = _get_task_folders_summary(store_with_folder)
        assert len(summary) == 1
        entry = summary[0]
        assert entry["code"] == result["code"]
        assert entry["title"] == "Root A"
        assert entry["status_suffix"] == "none"
        # task.md (always) + notes.md = 2
        assert entry["files_count"] == 2

    def test_excludes_subtasks(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        root = store_with_folder.create_task(
            title="Root", content="x", tags=["feature"]
        )
        store_with_folder.create_task(
            title="Child",
            content="y",
            tags=["feature"],
            parent_id=root["task_id"],
        )

        summary = _get_task_folders_summary(store_with_folder)
        # Only root counted; subtask is filtered by `parent_id IS NULL` in SQL.
        assert len(summary) == 1
        assert summary[0]["code"] == root["code"]

    def test_excludes_canceled(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        active = store_with_folder.create_task(
            title="Active", content="a", tags=["feature"]
        )
        canceled = store_with_folder.create_task(
            title="Canceled", content="c", tags=["bugfix"]
        )
        store_with_folder.update_task(task_id=canceled["task_id"], status="canceled")

        summary = _get_task_folders_summary(store_with_folder)
        codes = [e["code"] for e in summary]
        assert active["code"] in codes
        assert canceled["code"] not in codes

    def test_excludes_legacy_null_code(
        self, store_with_folder: TaskStore
    ):
        # Insert a legacy row with NULL code directly.
        conn = store_with_folder._get_connection()
        try:
            conn.execute(
                'INSERT INTO tasks (parent_id, status, title, content, '
                'content_hash, created_at, code) '
                'VALUES (?, ?, ?, ?, ?, ?, NULL)',
                (None, "pending", "Legacy", "old", "legacy_t215_summary",
                 "2020-01-01T00:00:00"),
            )
            conn.commit()
        finally:
            conn.close()

        summary = _get_task_folders_summary(store_with_folder)
        # Legacy row has NULL code → SQL filter excludes; nothing in summary.
        assert summary == []

    def test_status_suffix_on_review(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        result = store_with_folder.create_task(
            title="ToReview", content="x", tags=["feature"]
        )
        # Side-content keeps folder alive past completed (1.8.6 deletes
        # empty-template-only folders rather than renaming them).
        (folder_root / result["code"] / "notes.md").write_text("n", encoding="utf-8")
        store_with_folder.update_task(task_id=result["task_id"], status="in_progress")
        store_with_folder.update_task(task_id=result["task_id"], status="completed")

        summary = _get_task_folders_summary(store_with_folder)
        assert len(summary) == 1
        assert summary[0]["status_suffix"] == "-on-review"

    def test_status_suffix_done(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        result = store_with_folder.create_task(
            title="ToArchive", content="x", tags=["feature"]
        )
        (folder_root / result["code"] / "notes.md").write_text("n", encoding="utf-8")
        # Walk through full lifecycle to done.
        for s in ("in_progress", "completed", "tested", "validated", "done"):
            store_with_folder.update_task(task_id=result["task_id"], status=s)

        summary = _get_task_folders_summary(store_with_folder)
        assert len(summary) == 1
        assert summary[0]["status_suffix"] == "-done"

    def test_missing_folder_skipped_gracefully(
        self, store_with_folder: TaskStore, folder_root: Path
    ):
        result = store_with_folder.create_task(
            title="ToDelete", content="x", tags=["feature"]
        )
        # Delete the folder externally to simulate missing FS state.
        import shutil
        shutil.rmtree(folder_root / result["code"])

        summary = _get_task_folders_summary(store_with_folder)
        # Folder gone → entry skipped silently.
        assert summary == []

    def test_relative_path_inside_working_dir(
        self, temp_db_path: Path, tmp_path: Path, mock_embedding_model
    ):
        # Folder root INSIDE working_dir → folder_path is relative.
        wd = tmp_path / "wd"
        wd.mkdir()
        root = wd / "tasks"
        root.mkdir()

        with patch("src.task_store.get_embedding_model", return_value=mock_embedding_model):
            store = TaskStore(
                db_path=temp_db_path,
                task_folder=root,
                working_dir=wd,
            )
            store._ensure_db_initialized_sync()
            store.create_task(title="Inside", content="x", tags=["feature"])
            summary = _get_task_folders_summary(store)
        assert len(summary) == 1
        assert not Path(summary[0]["folder_path"]).is_absolute()

    def test_absolute_path_outside_working_dir(
        self, temp_db_path: Path, tmp_path: Path, mock_embedding_model
    ):
        # Folder root OUTSIDE working_dir → folder_path is absolute.
        wd = tmp_path / "wd"
        wd.mkdir()
        outside = tmp_path / "outside_root"
        outside.mkdir()

        with patch("src.task_store.get_embedding_model", return_value=mock_embedding_model):
            store = TaskStore(
                db_path=temp_db_path,
                task_folder=outside,
                working_dir=wd,
            )
            store._ensure_db_initialized_sync()
            store.create_task(title="Outside", content="x", tags=["feature"])
            summary = _get_task_folders_summary(store)
        assert len(summary) == 1
        assert Path(summary[0]["folder_path"]).is_absolute()


# =============================================================================
# project://info resource registration
# =============================================================================

class TestResourceRegistration:
    def test_resource_registered_at_uri(self, tmp_path: Path, monkeypatch):
        # Spin up an MCP server and verify project://info is registered.
        # Use minimal CLI args so create_server runs cleanly.
        wd = tmp_path / "proj"
        wd.mkdir()

        monkeypatch.setattr("sys.argv", [
            "prog",
            "--working-dir", str(wd),
        ])

        from main import create_server
        with patch("src.task_store.get_embedding_model"):
            mcp = create_server()

        # FastMCP exposes resources via the resource manager. Use list_resources()
        # if available; otherwise probe internal mapping.
        # Safe path: run an async list_resources via the resource manager.
        import asyncio
        resources = asyncio.run(mcp.list_resources())
        uris = [str(r.uri) for r in resources]
        assert "project://info" in uris


# =============================================================================
# project_info handler shape (via direct invocation)
# =============================================================================

class TestProjectInfoShape:
    def test_handler_returns_expected_keys(
        self, tmp_path: Path, monkeypatch
    ):
        wd = tmp_path / "proj"
        wd.mkdir()
        tf = tmp_path / "tasks"
        tf.mkdir()

        monkeypatch.setattr("sys.argv", [
            "prog",
            "--working-dir", str(wd),
            "--task-folder", str(tf),
        ])

        from main import create_server
        with patch("src.task_store.get_embedding_model"):
            mcp = create_server()

        # Read the resource by URI and parse JSON.
        import asyncio, json
        contents = asyncio.run(mcp.read_resource("project://info"))
        # FastMCP returns a list of ReadResourceContents (or similar);
        # extract the first text payload.
        first = contents[0] if isinstance(contents, list) else contents
        payload_text = getattr(first, "content", None) or getattr(first, "text", None) or first
        if isinstance(payload_text, (bytes, bytearray)):
            payload_text = payload_text.decode("utf-8")
        if isinstance(payload_text, str):
            data = json.loads(payload_text)
        else:
            data = payload_text  # already dict-like

        assert set(data.keys()) >= {"working_dir", "task_folder", "task_folder_enabled", "task_folders"}
        assert data["task_folder_enabled"] is True
        assert data["task_folder"] == str(tf.resolve())
        assert data["working_dir"] == str(wd.resolve())
        assert isinstance(data["task_folders"], list)

    def test_handler_feature_off_minimal_payload(
        self, tmp_path: Path, monkeypatch
    ):
        wd = tmp_path / "proj"
        wd.mkdir()

        monkeypatch.setattr("sys.argv", [
            "prog",
            "--working-dir", str(wd),
        ])

        from main import create_server
        with patch("src.task_store.get_embedding_model"):
            mcp = create_server()

        import asyncio, json
        contents = asyncio.run(mcp.read_resource("project://info"))
        first = contents[0] if isinstance(contents, list) else contents
        payload_text = getattr(first, "content", None) or getattr(first, "text", None) or first
        if isinstance(payload_text, (bytes, bytearray)):
            payload_text = payload_text.decode("utf-8")
        if isinstance(payload_text, str):
            data = json.loads(payload_text)
        else:
            data = payload_text

        assert data["task_folder_enabled"] is False
        assert data["task_folder"] is None
        assert data["task_folders"] == []