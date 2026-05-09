"""
Folder read APIs (task #216)
============================

Tests the read-side surface added in the final task of the Task Folders feature:

- ``task_get`` extension: when ``--task-folder`` is enabled and the requested
  task is a ROOT task with a non-empty ``code``, the response is enriched with
  ``folder_path`` and ``folder_files``.
- New MCP tool ``task_folder_files``: looks up a folder by ``task_id`` OR
  ``code`` (XOR), rejects subtasks, and surfaces the same ``files`` listing
  that ``task_get`` exposes.

The tests exercise the tools through FastMCP (``mcp.call_tool``) so the
registration + closure-bound argument resolution is covered end-to-end.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import patch

import pytest


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


def _build_server_with_folder(monkeypatch, working_dir: Path, folder_root: Path):
    """Spin up a FastMCP server with --task-folder enabled."""
    monkeypatch.setattr(
        "sys.argv",
        ["prog", "--working-dir", str(working_dir), "--task-folder", str(folder_root)],
    )
    from main import create_server

    with patch("src.task_store.get_embedding_model"):
        return create_server()


def _build_server_without_folder(monkeypatch, working_dir: Path):
    """Spin up a FastMCP server WITHOUT --task-folder (feature off)."""
    monkeypatch.setattr("sys.argv", ["prog", "--working-dir", str(working_dir)])
    from main import create_server

    with patch("src.task_store.get_embedding_model"):
        return create_server()


def _call_tool(mcp, name: str, arguments: dict) -> dict:
    """Invoke an MCP tool and return its parsed dict payload.

    FastMCP versions vary: call_tool may return a list of TextContent objects,
    a tuple ``(contents, structured_dict)``, or a structured dict directly.
    The defensive chain mirrors #215's read_resource handling.
    """
    raw = asyncio.run(mcp.call_tool(name, arguments))

    # Newer FastMCP: tuple of (contents, structured_data)
    if isinstance(raw, tuple) and len(raw) == 2:
        contents, structured = raw
        if isinstance(structured, dict):
            return structured
        raw = contents

    # List of TextContent / similar
    if isinstance(raw, list):
        first = raw[0] if raw else None
    else:
        first = raw

    if first is None:
        return {}

    payload_text = (
        getattr(first, "text", None)
        or getattr(first, "content", None)
        or first
    )
    if isinstance(payload_text, (bytes, bytearray)):
        payload_text = payload_text.decode("utf-8")
    if isinstance(payload_text, str):
        return json.loads(payload_text)
    return payload_text  # already dict-like


def _create_root_task(mcp, **kwargs) -> dict:
    """Create a root task via the registered MCP tool."""
    args = {
        "title": kwargs.get("title", "Root"),
        "content": kwargs.get("content", "x"),
        "tags": kwargs.get("tags", ["feature"]),
    }
    if "code" in kwargs:
        args["code"] = kwargs["code"]
    return _call_tool(mcp, "task_create", args)


# =============================================================================
# task_get — folder_files extension
# =============================================================================

class TestTaskGetFolderExtension:
    def test_root_with_feature_on_includes_folder_files(
        self, monkeypatch, working_dir: Path, folder_root: Path
    ):
        mcp = _build_server_with_folder(monkeypatch, working_dir, folder_root)
        created = _create_root_task(mcp, title="Root A", tags=["feature"])
        assert created["success"] is True

        # Drop a side-file into the folder so files_count is non-trivial.
        (folder_root / created["code"] / "notes.md").write_text("note", encoding="utf-8")

        got = _call_tool(mcp, "task_get", {"task_id": created["task_id"]})
        assert got["success"] is True
        assert "folder_path" in got
        assert "folder_files" in got
        # task.md is created by the manager + our extra notes.md
        paths = {entry["path"] for entry in got["folder_files"]}
        assert any(p.endswith("task.md") for p in paths)
        assert any(p.endswith("notes.md") for p in paths)
        # folder_path must point at the resolved folder.
        assert got["folder_path"].endswith(created["code"])

    def test_subtask_inherits_root_folder(
        self, monkeypatch, working_dir: Path, folder_root: Path
    ):
        # Subtasks share the ROOT task's folder (one folder per hierarchy).
        # task_get on a subtask must surface the root's folder fields with
        # explicit root_task_id / root_code markers.
        mcp = _build_server_with_folder(monkeypatch, working_dir, folder_root)
        root = _create_root_task(mcp, title="Root", tags=["feature"])

        sub = _call_tool(
            mcp,
            "task_create",
            {
                "title": "Sub",
                "content": "y",
                "tags": ["feature"],
                "parent_id": root["task_id"],
            },
        )
        assert sub["success"] is True

        got = _call_tool(mcp, "task_get", {"task_id": sub["task_id"]})
        assert got["success"] is True
        # Subtask query returns root's folder context.
        assert got["folder_path"].endswith(root["code"])
        assert any(f["path"].endswith("task.md") for f in got["folder_files"])
        assert got["root_task_id"] == root["task_id"]
        assert got["root_code"] == root["code"]

    def test_root_with_feature_off_no_folder_fields(
        self, monkeypatch, working_dir: Path
    ):
        mcp = _build_server_without_folder(monkeypatch, working_dir)
        created = _create_root_task(mcp, title="Off", tags=["feature"])
        assert created["success"] is True

        got = _call_tool(mcp, "task_get", {"task_id": created["task_id"]})
        assert got["success"] is True
        assert "folder_path" not in got
        assert "folder_files" not in got

    def test_root_without_code_no_folder_fields(
        self, monkeypatch, working_dir: Path, folder_root: Path
    ):
        # Force a legacy NULL-code row directly so the extension predicate
        # `task.code` falls through.
        mcp = _build_server_with_folder(monkeypatch, working_dir, folder_root)
        # We need access to the task_store the server is using. Build it via
        # the same code paths so the DB matches.
        from main import create_server  # noqa: F401  (kept for symmetry)

        # The server in `mcp` already has a TaskStore wired up — reach into
        # the same DB by replaying the path: --working-dir/memory/tasks.db.
        import sqlite3
        db_path = working_dir / "memory" / "tasks.db"
        # The db is created lazily on first MCP call — issue one to materialise it.
        _create_root_task(mcp, title="Bootstrap", tags=["feature"])

        conn = sqlite3.connect(str(db_path))
        try:
            cursor = conn.execute(
                "INSERT INTO tasks (parent_id, status, title, content, "
                "content_hash, created_at, code) "
                "VALUES (?, ?, ?, ?, ?, ?, NULL)",
                (None, "pending", "Legacy NULL code", "old",
                 "legacy_t216_taskget", "2020-01-01T00:00:00"),
            )
            legacy_id = cursor.lastrowid
            conn.commit()
        finally:
            conn.close()

        got = _call_tool(mcp, "task_get", {"task_id": legacy_id})
        assert got["success"] is True
        assert "folder_path" not in got
        assert "folder_files" not in got

    def test_missing_folder_skipped_silently(
        self, monkeypatch, working_dir: Path, folder_root: Path
    ):
        mcp = _build_server_with_folder(monkeypatch, working_dir, folder_root)
        created = _create_root_task(mcp, title="ToDelete", tags=["feature"])

        # Externally remove the folder to simulate a missing FS state.
        import shutil
        shutil.rmtree(folder_root / created["code"])

        got = _call_tool(mcp, "task_get", {"task_id": created["task_id"]})
        # task_get must still succeed.
        assert got["success"] is True
        # No resolved folder → folder_path/folder_files omitted.
        assert "folder_path" not in got


# =============================================================================
# task_folder_files MCP tool
# =============================================================================

class TestTaskFolderFilesTool:
    def test_by_task_id_success(
        self, monkeypatch, working_dir: Path, folder_root: Path
    ):
        mcp = _build_server_with_folder(monkeypatch, working_dir, folder_root)
        created = _create_root_task(mcp, title="A", tags=["feature"])

        result = _call_tool(mcp, "task_folder_files", {"task_id": created["task_id"]})
        assert result["success"] is True
        assert result["code"] == created["code"]
        assert isinstance(result["files"], list)
        # task.md is auto-generated by the manager.
        assert any(f["path"].endswith("task.md") for f in result["files"])

    def test_by_code_success(
        self, monkeypatch, working_dir: Path, folder_root: Path
    ):
        mcp = _build_server_with_folder(monkeypatch, working_dir, folder_root)
        created = _create_root_task(mcp, title="B", tags=["feature"], code="OLOM-460")
        assert created["code"] == "OLOM-460"

        result = _call_tool(mcp, "task_folder_files", {"code": "OLOM-460"})
        assert result["success"] is True
        assert result["code"] == "OLOM-460"
        assert any(f["path"].endswith("task.md") for f in result["files"])

    def test_subtask_resolves_to_root(
        self, monkeypatch, working_dir: Path, folder_root: Path
    ):
        # Subtasks share the root's folder. task_folder_files MUST walk up
        # to the root and return that folder, with root_task_id in the
        # response so callers can see the resolution.
        mcp = _build_server_with_folder(monkeypatch, working_dir, folder_root)
        root = _create_root_task(mcp, title="Root", tags=["feature"])
        sub = _call_tool(
            mcp,
            "task_create",
            {
                "title": "Sub",
                "content": "y",
                "tags": ["feature"],
                "parent_id": root["task_id"],
            },
        )

        result = _call_tool(mcp, "task_folder_files", {"task_id": sub["task_id"]})
        assert result["success"] is True
        assert result["code"] == root["code"]
        assert result["folder_path"].endswith(root["code"])
        assert result["root_task_id"] == root["task_id"]

    def test_subtask_code_resolves_to_root(
        self, monkeypatch, working_dir: Path, folder_root: Path
    ):
        # Same root-walk via the by-code branch: passing a subtask's code
        # walks the parent chain and returns the root's folder.
        mcp = _build_server_with_folder(monkeypatch, working_dir, folder_root)
        root = _create_root_task(mcp, title="Root", tags=["feature"])
        sub = _call_tool(
            mcp,
            "task_create",
            {
                "title": "Sub",
                "content": "y",
                "tags": ["feature"],
                "parent_id": root["task_id"],
            },
        )

        result = _call_tool(mcp, "task_folder_files", {"code": sub["code"]})
        assert result["success"] is True
        assert result["code"] == root["code"]
        assert result["root_task_id"] == root["task_id"]

    def test_rejects_neither_arg(
        self, monkeypatch, working_dir: Path, folder_root: Path
    ):
        mcp = _build_server_with_folder(monkeypatch, working_dir, folder_root)
        result = _call_tool(mcp, "task_folder_files", {})
        assert result["success"] is False
        assert "exactly one" in result["message"].lower()

    def test_rejects_both_args(
        self, monkeypatch, working_dir: Path, folder_root: Path
    ):
        mcp = _build_server_with_folder(monkeypatch, working_dir, folder_root)
        created = _create_root_task(mcp, title="C", tags=["feature"])
        result = _call_tool(
            mcp,
            "task_folder_files",
            {"task_id": created["task_id"], "code": created["code"]},
        )
        assert result["success"] is False
        assert "exactly one" in result["message"].lower()

    def test_feature_off_tool_not_registered(
        self, monkeypatch, working_dir: Path
    ):
        # When --task-folder is not set, the `task_folder_files` MCP tool
        # MUST NOT be advertised by the server. Clients should not see a
        # no-op endpoint for a feature that is disabled.
        mcp = _build_server_without_folder(monkeypatch, working_dir)
        tools = asyncio.run(mcp.list_tools())
        tool_names = [getattr(t, "name", None) for t in tools]
        assert "task_folder_files" not in tool_names

    def test_feature_on_tool_registered(
        self, monkeypatch, working_dir: Path, folder_root: Path
    ):
        # Sanity counterpart: when --task-folder IS set, the tool is exposed.
        mcp = _build_server_with_folder(monkeypatch, working_dir, folder_root)
        tools = asyncio.run(mcp.list_tools())
        tool_names = [getattr(t, "name", None) for t in tools]
        assert "task_folder_files" in tool_names

    def test_missing_task_returns_error(
        self, monkeypatch, working_dir: Path, folder_root: Path
    ):
        mcp = _build_server_with_folder(monkeypatch, working_dir, folder_root)
        # Bootstrap DB so the lookup hits an initialized table.
        _create_root_task(mcp, title="Bootstrap", tags=["feature"])

        result = _call_tool(mcp, "task_folder_files", {"task_id": 99999})
        assert result["success"] is False
        assert "not found" in result["message"].lower()

    def test_legacy_task_without_code_rejected(
        self, monkeypatch, working_dir: Path, folder_root: Path
    ):
        mcp = _build_server_with_folder(monkeypatch, working_dir, folder_root)
        _create_root_task(mcp, title="Bootstrap", tags=["feature"])

        # Insert a legacy NULL-code row.
        import sqlite3
        db_path = working_dir / "memory" / "tasks.db"
        conn = sqlite3.connect(str(db_path))
        try:
            cursor = conn.execute(
                "INSERT INTO tasks (parent_id, status, title, content, "
                "content_hash, created_at, code) "
                "VALUES (?, ?, ?, ?, ?, ?, NULL)",
                (None, "pending", "Legacy NULL code", "old",
                 "legacy_t216_tff", "2020-01-01T00:00:00"),
            )
            legacy_id = cursor.lastrowid
            conn.commit()
        finally:
            conn.close()

        result = _call_tool(mcp, "task_folder_files", {"task_id": legacy_id})
        assert result["success"] is False
        assert "no code" in result["message"].lower()

    def test_invalid_task_id_type_rejected(
        self, monkeypatch, working_dir: Path, folder_root: Path
    ):
        mcp = _build_server_with_folder(monkeypatch, working_dir, folder_root)
        result = _call_tool(mcp, "task_folder_files", {"task_id": 0})
        assert result["success"] is False
        assert "positive integer" in result["message"].lower()

    def test_resolved_folder_path_relative_when_inside_working_dir(
        self, monkeypatch, tmp_path: Path
    ):
        wd = tmp_path / "proj"
        wd.mkdir()
        root = wd / "tasks"
        root.mkdir()
        mcp = _build_server_with_folder(monkeypatch, wd, root)

        created = _create_root_task(mcp, title="In", tags=["feature"])
        result = _call_tool(mcp, "task_folder_files", {"task_id": created["task_id"]})
        assert result["success"] is True
        assert not Path(result["folder_path"]).is_absolute()

    # ------------------------------------------------------------------
    # Path-traversal hardening (#217 — validate_code at the public boundary)
    # ------------------------------------------------------------------

    def test_path_traversal_double_dot_rejected(
        self, monkeypatch, working_dir: Path, folder_root: Path
    ):
        mcp = _build_server_with_folder(monkeypatch, working_dir, folder_root)
        result = _call_tool(mcp, "task_folder_files", {"code": ".."})
        assert result["success"] is False
        msg = result["message"].lower()
        # Error message must come from validate_code (mentions format/PREFIX).
        assert "format" in msg or "prefix" in msg

    def test_path_traversal_relative_rejected(
        self, monkeypatch, working_dir: Path, folder_root: Path
    ):
        mcp = _build_server_with_folder(monkeypatch, working_dir, folder_root)
        result = _call_tool(mcp, "task_folder_files", {"code": "../../etc"})
        assert result["success"] is False

    def test_lowercase_code_rejected(
        self, monkeypatch, working_dir: Path, folder_root: Path
    ):
        mcp = _build_server_with_folder(monkeypatch, working_dir, folder_root)
        result = _call_tool(mcp, "task_folder_files", {"code": "feat-1"})
        assert result["success"] is False

    def test_empty_string_code_rejected(
        self, monkeypatch, working_dir: Path, folder_root: Path
    ):
        # Empty string is not None, so the XOR check allows it through;
        # validate_code rejects with "code cannot be empty".
        mcp = _build_server_with_folder(monkeypatch, working_dir, folder_root)
        result = _call_tool(mcp, "task_folder_files", {"code": ""})
        assert result["success"] is False

    def test_code_with_null_byte_rejected(
        self, monkeypatch, working_dir: Path, folder_root: Path
    ):
        mcp = _build_server_with_folder(monkeypatch, working_dir, folder_root)
        result = _call_tool(mcp, "task_folder_files", {"code": "FEAT-1\x00x"})
        assert result["success"] is False

    def test_overly_long_code_rejected(
        self, monkeypatch, working_dir: Path, folder_root: Path
    ):
        mcp = _build_server_with_folder(monkeypatch, working_dir, folder_root)
        result = _call_tool(mcp, "task_folder_files", {"code": "A" * 100 + "-1"})
        assert result["success"] is False
        msg = result["message"].lower()
        # validate_code reports max-length explicitly.
        assert "32" in msg or "length" in msg


# =============================================================================
# Version + manifest
# =============================================================================

class TestVersionBump:
    def test_pyproject_version_is_1_8_3(self):
        pyproject = Path(__file__).parent.parent / "pyproject.toml"
        text = pyproject.read_text(encoding="utf-8")
        # Match exactly the project version line, not any incidental occurrence.
        import re
        m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
        assert m is not None, "version line not found in pyproject.toml"
        assert m.group(1) == "1.8.3", f"expected 1.8.3, got {m.group(1)}"


# =============================================================================
# CLAUDE.md / README.md / CASES.md surface checks
# =============================================================================

class TestDocsSurface:
    @pytest.fixture(autouse=True)
    def _project_root(self):
        self.root = Path(__file__).parent.parent

    def test_claude_md_mentions_task_folder_feature(self):
        text = (self.root / "CLAUDE.md").read_text(encoding="utf-8")
        assert "## Task Folder Feature" in text
        assert "--task-folder" in text
        assert "task_folder_files" in text
        assert "done" in text  # status lifecycle includes done

    def test_readme_mentions_task_folder_and_done(self):
        text = (self.root / "README.md").read_text(encoding="utf-8")
        assert "--task-folder" in text
        # Status table must list `done`.
        assert "`done`" in text
        assert "task_folder_files" in text

    def test_cases_md_has_task_folder_workflow_category(self):
        text = (self.root / "src" / "CASES.md").read_text(encoding="utf-8")
        assert "## Task Folder Workflow Scenarios" in text
        assert "<!-- description:" in text